from __future__ import annotations

from typing import AsyncGenerator, Any
from datetime import datetime, timedelta
import json
import logging
import re
import time

import pytz
from google.adk.agents import BaseAgent
from google.adk.events import Event
from google.genai import types

from .utils.json_utils import clean_json as _clean_json

# --- Sub Agents ---
from .sub_agents.intent_analyzer_agent import intent_analyzer_agent, BASE_NLU_SPEC
from .sub_agents.react_visual_agent import react_visual_agent
from .sub_agents.clarifier_orchestrator_agent import clarifier_agent
from .sub_agents.protected_query_builder_agent import protected_query_builder_agent
from .sub_agents.query_executor_agent import query_executor_agent
from .sub_agents.response_insights_agent import response_insights_agent
from .sub_agents.human_response_agent import human_response_agent


# =========================
# Helpers
# =========================
def _text_event(message: str) -> Event:
    return Event(
        author="assistant",
        content=types.Content(parts=[types.Part(text=message)]),
    )


def _markdown_table_to_rows(md: str) -> list[dict[str, Any]]:
    if not md or "|" not in md:
        return []
    lines = [ln.strip() for ln in md.strip().splitlines() if ln.strip()]
    if len(lines) < 3:
        return []

    header = [h.strip() for h in lines[0].strip("|").split("|")]
    rows: list[dict[str, Any]] = []
    for ln in lines[2:]:
        if "|" not in ln:
            continue
        cells = [c.strip() for c in ln.strip("|").split("|")]
        if len(cells) != len(header):
            continue
        row = dict(zip(header, cells))

        # coerce numeric if possible
        for k in ("hr", "clicks", "baseline_6h", "anomaly_score"):
            if k in row:
                try:
                    row[k] = float(str(row[k]).replace(",", ""))
                except Exception:
                    pass

        rows.append(row)

    return rows


def _sanitize_key(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9_]+", "_", (s or "").strip())
    s = re.sub(r"_+", "_", s).strip("_")
    return s[:40] or "series"


def _build_multi_series_chart(
    rows: list[dict[str, Any]],
    hour_col: str = "hr",
    series_col: str = "media_source",
    value_col: str = "clicks",
):
    """
    Builds:
    - chart_data: [{hour: "10", <seriesKey1>: 123, <seriesKey2>: 55, ...}, ...]
    - series_defs: [{key: "facebook_ads", name: "facebook_ads"}, ...]
    """
    if not rows:
        return [], []

    series_names = sorted({str(r.get(series_col, "Unknown")) for r in rows})
    series_map = {name: _sanitize_key(name) for name in series_names}

    by_hour: dict[str, dict[str, Any]] = {}
    for r in rows:
        hr = r.get(hour_col, "")
        if isinstance(hr, (int, float)):
            hr_str = str(int(hr))
        else:
            hr_str = str(hr)

        if not hr_str:
            continue

        ms = str(r.get(series_col, "Unknown"))
        key = series_map.get(ms, _sanitize_key(ms))

        val = r.get(value_col, 0)
        try:
            val = float(val)
            if val != val or val < 0:
                val = 0.0
        except Exception:
            val = 0.0

        if hr_str not in by_hour:
            by_hour[hr_str] = {"hour": hr_str}
        by_hour[hr_str][key] = val

    def _hour_sort(x: str):
        try:
            return int(x)
        except Exception:
            return x

    chart_data = [by_hour[h] for h in sorted(by_hour.keys(), key=_hour_sort)]
    series_defs = [{"key": series_map[name], "name": name} for name in series_names]
    return chart_data, series_defs


def _rows_to_anomalies(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Extract anomalies for marker dots + stats.
    Requires is_anomaly column to be true-ish.
    """
    out: list[dict[str, Any]] = []
    for r in rows:
        flag = str(r.get("is_anomaly", "")).strip().lower()
        is_anom = flag in ("true", "1", "yes", "y", "t")

        if not is_anom:
            continue

        hr = r.get("hr")
        hr_str = str(int(hr)) if isinstance(hr, (int, float)) else str(hr or "")

        out.append(
            {
                "name": str(r.get("media_source", "Unknown")),
                "anomaly_type": "click_spike",  # adapt if you have click_drop etc.
                "event_hour": hr_str,
                "clicks": float(r.get("clicks", 0) or 0),
                "avg_clicks": float(r.get("baseline_6h", 0) or 0),
            }
        )
    return out


# =========================
# RootAgent
# =========================
class RootAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="root_agent")

    async def _run_async_impl(self, context) -> AsyncGenerator[Event, None]:
        session_state = context.session.state

        # ============================================================
        # STEP 0 — Inject current date into NLU instruction
        # ============================================================
        tz = pytz.timezone("Asia/Jerusalem")
        today = datetime.now(tz).date()
        yesterday = today - timedelta(days=1)
        day_before = today - timedelta(days=2)

        dynamic_date_block = f"""
# SYSTEM DATE DIRECTIVE — DO NOT IGNORE
Current real date: {today.strftime("%Y-%m-%d")}

Natural-language date mapping:
- "today" / "היום" → {today}
- "yesterday" / "אתמול" → {yesterday}
- "שלשום" → {day_before}

Dates without year (24.10, 25/10, 25.10):
→ ALWAYS use year {today.year}.

If interpreted date is in the future → return future-date error.

IMPORTANT OVERRIDE FOR ANOMALY:
- If intent is "anomaly" AND the user did NOT explicitly mention a date or date range,
  you MUST set:
  date_range = {{ "start_date": "2025-10-24", "end_date": "2025-10-26" }}
- Do NOT default to "yesterday" in anomaly when no explicit date was provided.

# END OF DATE DIRECTIVE
""".strip()

        logging.info(f"[TIME] system local now: {datetime.now()}")
        logging.info(f"[TIME] utc now: {datetime.utcnow()}")
        logging.info(f"[TIME] tz now (Asia/Jerusalem): {datetime.now(pytz.timezone('Asia/Jerusalem'))}")
        logging.info(f"[TIME] tz today: {today}")
        logging.info(f"[TIME] system time.tzname={time.tzname}")
        logging.info(f"[TIME] dynamic_date_block:\n{dynamic_date_block}")

        intent_analyzer_agent.instruction = dynamic_date_block + "\n\n" + BASE_NLU_SPEC

        # ============================================================
        # STEP 1 — Intent Analyzer
        # ============================================================
        async for event in intent_analyzer_agent.run_async(context):
            yield event

        intent_analysis = _clean_json(session_state.get("intent_analysis"))
        status = intent_analysis.get("status")

        if status == "not relevant":
            status = "not_relevant"

        # ============================================================
        # STEP 2 — Clarification needed
        # ============================================================
        if status == "clarification_needed":
            session_state["missing_fields"] = intent_analysis.get("missing_fields", [])
            async for event in clarifier_agent.run_async(context):
                yield event
            return

        # ============================================================
        # STEP 3 — Hard stop (error / not relevant)
        # ============================================================
        if status in ("not_relevant", "error"):
            yield _text_event(intent_analysis.get("message", "Request not supported."))
            return

        # ============================================================
        # STEP 4 — OK → run pipeline
        # ============================================================
        if status == "ok":
            parsed_intent = intent_analysis.get("parsed_intent", {}) or {}
            intent_type = parsed_intent.get("intent")

            # ---------------------------
            # SQL Builder
            # ---------------------------
            async for event in protected_query_builder_agent.run_async(context):
                yield event

            built_query_raw = session_state.get("built_query")
            built_query = self._parse_built_query(built_query_raw)

            if built_query.get("status") != "ok":
                yield _text_event(built_query.get("message", "SQL Builder error"))
                return

            # ---------------------------
            # Query Executor (Python function, not agent)
            # ---------------------------
            logging.info("🔴 [RootAgent] Calling query_executor_agent with built_query")
            sql_result = query_executor_agent(built_query)
            logging.info(f"🔴 [RootAgent] query_executor_agent returned: {json.dumps(sql_result, indent=2)[:500]}")

            session_state["execution_result"] = sql_result
            logging.info("🔴 [RootAgent] Set execution_result in session_state")

            # ---------------------------
            # ✅ ANOMALY → React visualization path
            # ---------------------------
            if intent_type == "anomaly" and sql_result.get("status") == "ok":
                md = (sql_result.get("result") or "").strip()
                rows = _markdown_table_to_rows(md)

                # Debug logs: verify table parsing
                logging.info(f"[ANOM] markdown_len={len(md)} parsed_rows={len(rows)}")
                if rows:
                    logging.info(f"[ANOM] sample keys={list(rows[0].keys())}")
                    logging.info(f"[ANOM] sample is_anomaly={rows[0].get('is_anomaly')}")

                chart_data, series_defs = _build_multi_series_chart(
                    rows,
                    hour_col="hr",
                    series_col="media_source",
                    value_col="clicks",
                )

                anomalies = _rows_to_anomalies(rows)
                logging.info(f"[ANOM] extracted anomalies={len(anomalies)} chart_points={len(chart_data)} series={len(series_defs)}")

                # Save what react_visual_agent expects
                session_state["anomaly_table_markdown"] = md
                session_state["anomaly_timeseries_multi"] = chart_data

                # IMPORTANT: react_visual_agent has a "no anomalies" branch that checks anomaly_timeseries
                session_state["anomaly_timeseries"] = chart_data

                session_state["anomaly_series_defs"] = series_defs
                session_state["anomaly_result"] = {"anomalies": anomalies}

                logging.info("🔥 [RootAgent] anomaly intent → calling react_visual_agent")
                async for event in react_visual_agent.run_async(context):
                    yield event
                return

            # ---------------------------
            # Insights Agent (non-anomaly path)
            # ---------------------------
            session_state["insights_payload"] = {"execution_result": sql_result}
            logging.info("🔴 [RootAgent] Running response_insights_agent...")
            async for event in response_insights_agent.run_async(context):
                yield event

            # ---------------------------
            # Human Response Agent
            # ---------------------------
            insights_result_raw = session_state.get("insights_result", {})
            insights_result = self._parse_built_query(insights_result_raw)

            logging.info("🔴 [RootAgent] Calling human_response_agent (Python function)...")
            final_response = human_response_agent(sql_result, insights_result)
            logging.info(f"🔴 [RootAgent] Final response length: {len(final_response)}")

            yield _text_event(final_response)
            logging.info("🔴 [RootAgent] Analytics flow completed")
            return

        # fallback (shouldn't reach)
        yield _text_event("I couldn't understand the request.")
        return

    # ===== JSON Parse Helper =====
    def _parse_built_query(self, raw):
        if isinstance(raw, dict):
            return raw

        if isinstance(raw, str):
            cleaned = re.sub(r"```json|```", "", raw.strip())
            try:
                return json.loads(cleaned)
            except Exception:
                return {"status": "error", "message": "Invalid JSON from builder"}

        return {"status": "error", "message": "Invalid builder output"}


root_agent = RootAgent()
