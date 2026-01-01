from __future__ import annotations

from typing import AsyncGenerator, Any, Optional
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
from .sub_agents.response_insights_agent import response_insights_agent, INSIGHTS_SPEC
from .sub_agents.human_response_agent import human_response_agent

logger = logging.getLogger(__name__)


# =========================
# Helpers
# =========================
def _text_event(message: str) -> Event:
    return Event(
        author="assistant",
        content=types.Content(parts=[types.Part(text=message)]),
    )


def _extract_first_yyyy_mm_dd(text: str) -> Optional[str]:
    if not text:
        return None
    m = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", text)
    return m.group(1) if m else None


def _parse_date_yyyy_mm_dd(s: str):
    return datetime.strptime(s, "%Y-%m-%d").date()


def _is_future_date_range(dr: dict, today_date) -> bool:
    if not isinstance(dr, dict):
        return False
    sd = dr.get("start_date")
    ed = dr.get("end_date")
    if not sd or not ed:
        return False
    try:
        return _parse_date_yyyy_mm_dd(sd) > today_date or _parse_date_yyyy_mm_dd(ed) > today_date
    except Exception:
        return False


def _extract_total_events_from_rows(sql_result: dict) -> Optional[int]:
    """
    Extract total_events from sql_result rows if present.
    Returns int or None.
    """
    if not isinstance(sql_result, dict):
        return None
    rows = sql_result.get("rows") or []
    if not rows or not isinstance(rows[0], dict):
        return None
    v = rows[0].get("total_events")
    if v is None:
        return None
    try:
        return int(v)
    except Exception:
        try:
            return int(float(v))
        except Exception:
            return None


def _compute_has_data(sql_result: dict) -> bool:
    """
    True if we have a meaningful numeric result (e.g. total_events not null),
    or if you later want to support non-aggregate outputs.
    """
    if not isinstance(sql_result, dict):
        return False
    if sql_result.get("status") != "ok":
        return False

    v = _extract_total_events_from_rows(sql_result)
    if v is not None:
        return True

    # fallback: if non-aggregate tables return rows, treat as has_data
    try:
        rc = int(sql_result.get("row_count") or 0)
    except Exception:
        rc = 0
    return rc > 0


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

CRITICAL (YEAR PRESERVATION):
- If the user explicitly provides a year (e.g., 24/10/2025, 2025-10-24),
  you MUST keep that exact year and MUST NOT override it.

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

        logger.info(f"[TIME] system local now: {datetime.now()}")
        logger.info(f"[TIME] utc now: {datetime.utcnow()}")
        logger.info(f"[TIME] tz now (Asia/Jerusalem): {datetime.now(pytz.timezone('Asia/Jerusalem'))}")
        logger.info(f"[TIME] tz today: {today}")
        logger.info(f"[TIME] system time.tzname={time.tzname}")
        logger.info(f"[TIME] dynamic_date_block:\n{dynamic_date_block}")

        intent_analyzer_agent.instruction = dynamic_date_block + "\n\n" + BASE_NLU_SPEC

        # ============================================================
        # STEP 1 — Intent Analyzer
        # ============================================================
        async for event in intent_analyzer_agent.run_async(context):
            yield event

        intent_analysis = _clean_json(session_state.get("intent_analysis"))
        status = (intent_analysis or {}).get("status")

        if status == "not relevant":
            status = "not_relevant"

        # ============================================================
        # STEP 1.5 — Hard stop future date (server-side enforcement)
        # ============================================================
        if status == "ok":
            parsed = (intent_analysis or {}).get("parsed_intent") or {}
            dr = parsed.get("date_range") or {}
            if _is_future_date_range(dr, today):
                yield _text_event("Future dates are not supported because no events have occurred yet.")
                return

        # ============================================================
        # STEP 2 — Clarification needed
        # ============================================================
        if status == "clarification_needed":
            session_state["missing_fields"] = (intent_analysis or {}).get("missing_fields", [])
            async for event in clarifier_agent.run_async(context):
                yield event
            return

        # ============================================================
        # STEP 3 — Hard stop (error / not relevant)
        # ============================================================
        if status in ("not_relevant", "error"):
            yield _text_event((intent_analysis or {}).get("message", "Request not supported."))
            return

        # ============================================================
        # STEP 4 — OK → run pipeline
        # ============================================================
        if status == "ok":
            parsed_intent = (intent_analysis or {}).get("parsed_intent", {}) or {}
            intent_type = parsed_intent.get("intent")

            # ---------------------------
            # SQL Builder
            # ---------------------------
            async for event in protected_query_builder_agent.run_async(context):
                yield event

            built_query_raw = session_state.get("built_query")
            built_query = self._parse_json_block(built_query_raw)

            if built_query.get("status") != "ok":
                yield _text_event(built_query.get("message", "SQL Builder error"))
                return

            # ---------------------------
            # Query Executor (Python function)
            # ---------------------------
            logger.info("🔴 [RootAgent] Calling query_executor_agent with built_query")
            sql_result = query_executor_agent(built_query)
            logger.info(f"🔴 [RootAgent] query_executor_agent returned: {json.dumps(sql_result, indent=2)[:900]}")

            session_state["execution_result"] = sql_result
            logger.info("🔴 [RootAgent] Set execution_result in session_state")

            # ---------------------------
            # ANOMALY → React path
            # ---------------------------
            if intent_type == "anomaly" and sql_result.get("status") == "ok":
                # Keep your existing anomaly visualization pipeline here
                async for event in react_visual_agent.run_async(context):
                    yield event
                return

            # ---------------------------
            # LLM INSIGHTS (MANDATORY)
            # Inject payload into the LLM instruction so it CANNOT miss the flags
            # ---------------------------
            requested_date = _extract_first_yyyy_mm_dd(sql_result.get("executed_sql", "") or "")
            is_future_date = False
            if requested_date:
                try:
                    is_future_date = _parse_date_yyyy_mm_dd(requested_date) > today
                except Exception:
                    is_future_date = False

            total_events_val = _extract_total_events_from_rows(sql_result)
            has_data = _compute_has_data(sql_result)

            insights_payload = {
                "execution_result": {
                    "status": sql_result.get("status"),
                    "row_count": sql_result.get("row_count"),
                    "executed_sql": sql_result.get("executed_sql"),
                    # NOTE: we do NOT paste the markdown table in strings in the LLM output,
                    # but giving it here is fine as input. Still, keep it minimal:
                    "result": sql_result.get("result"),
                },
                "requested_date": requested_date,
                "is_future_date": is_future_date,
                "has_data": has_data,
                "extracted_values": {
                    "total_events": total_events_val
                }
            }

            logger.info(
                f"🔴 [RootAgent] insights flags: requested_date={requested_date} "
                f"is_future_date={is_future_date} has_data={has_data} total_events={total_events_val}"
            )

            # ✅ THIS is the key fix: put the input JSON inside the agent's instruction
            response_insights_agent.instruction = (
                "INSIGHTS_INPUT_JSON:\n"
                + json.dumps(insights_payload, ensure_ascii=False)
                + "\n\n"
                + INSIGHTS_SPEC
            )

            logger.info("🔴 [RootAgent] Running response_insights_agent (LLM)...")
            async for event in response_insights_agent.run_async(context):
                yield event

            # ---------------------------
            # Human Response Agent
            # ---------------------------
            insights_result_raw = session_state.get("insights_result", {})
            insights_result = self._parse_json_block(insights_result_raw)

            logger.info("🔴 [RootAgent] Calling human_response_agent...")
            final_response = human_response_agent(sql_result, insights_result)
            logger.info(f"🔴 [RootAgent] Final response length: {len(final_response)}")

            yield _text_event(final_response)
            logger.info("🔴 [RootAgent] Analytics flow completed")
            return

        yield _text_event("I couldn't understand the request.")
        return

    # ===== JSON Parse Helper =====
    def _parse_json_block(self, raw):
        if isinstance(raw, dict):
            return raw
        if isinstance(raw, str):
            cleaned = re.sub(r"```json|```", "", raw.strip(), flags=re.IGNORECASE)
            try:
                return json.loads(cleaned)
            except Exception:
                return {"status": "error", "message": "Invalid JSON from agent"}
        return {"status": "error", "message": "Invalid agent output"}


root_agent = RootAgent()
