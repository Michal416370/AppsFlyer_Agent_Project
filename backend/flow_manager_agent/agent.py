from typing import AsyncGenerator
from google.adk.agents import BaseAgent
from google.adk.events import Event
from google.genai import types

from .utils.json_utils import clean_json as _clean_json
from .utils.cache import normalize_intent_key  # ✅ stable intent key

# --- Sub Agents ---
from .sub_agents.intent_analyzer_agent import intent_analyzer_agent, BASE_NLU_SPEC
from .sub_agents.anomaly_agent import anomaly_agent
from .sub_agents.react_visual_agent import react_visual_agent
from .sub_agents.clarifier_orchestrator_agent import clarifier_agent
from .sub_agents.protected_query_builder_agent import protected_query_builder_agent
from .sub_agents.query_executor_agent import query_executor_agent
from .sub_agents.response_insights_agent import response_insights_agent
from .sub_agents.human_response_agent import human_response_agent

import json
import re
import logging
from datetime import datetime, timedelta, date
import pytz


def _text_event(message: str) -> Event:
    return Event(
        author="assistant",
        content=types.Content(parts=[types.Part(text=message)])
    )


# ============================================================
# DATA AVAILABILITY WINDOW (internal only; user won't see it)
# ============================================================
DATA_AVAILABLE_FROM = date(2025, 10, 24)
DATA_AVAILABLE_TO = date(2025, 10, 26)


def _parse_iso_date(s: str) -> date | None:
    """Parse YYYY-MM-DD safely."""
    if not s or not isinstance(s, str):
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None


def _requested_range_outside_available(parsed_intent: dict) -> tuple[bool, str]:
    """
    Returns:
      (is_outside, message_to_user_if_outside)
    User message includes ONLY requested date/range (not availability window).
    """
    dr = (parsed_intent or {}).get("date_range")
    if not isinstance(dr, dict):
        return (False, "")

    start_s = dr.get("start_date")
    end_s = dr.get("end_date")

    start_d = _parse_iso_date(start_s)
    end_d = _parse_iso_date(end_s)

    # If date_range exists but parsing failed, let the pipeline handle it
    if not start_d and not end_d:
        return (False, "")

    # Normalize single-date cases
    if start_d and not end_d:
        end_d = start_d
    if end_d and not start_d:
        start_d = end_d

    # Outside internal window?
    if start_d < DATA_AVAILABLE_FROM or end_d > DATA_AVAILABLE_TO:
        requested_txt = (
            start_d.strftime("%Y-%m-%d")
            if start_d == end_d
            else f"{start_d.strftime('%Y-%m-%d')} עד {end_d.strftime('%Y-%m-%d')}"
        )

        msg = (
            f"❌ אין לי מידע על התאריך/טווח שביקשת: **{requested_txt}**.\n"
            f"אם תרצי, נסי לשאול על תאריך אחר."
        )
        return (True, msg)

    return (False, "")


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

            # END OF DATE DIRECTIVE
        """
        intent_analyzer_agent.instruction = dynamic_date_block + BASE_NLU_SPEC

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
            parsed_intent = intent_analysis.get("parsed_intent", {})
            intent_type = parsed_intent.get("intent")

            # ---------------------------
            # ✅ ANOMALY FLOW
            # ---------------------------
            if intent_type == "anomaly":
                logging.info("[RootAgent] === ANOMALY FLOW START ===")
                async for event in anomaly_agent.run_async(context):
                    yield event
                async for event in react_visual_agent.run_async(context):
                    yield event
                logging.info("[RootAgent] === ANOMALY FLOW END ===")
                return

            # ---------------------------
            # ✅ Date availability guard (user sees only requested date)
            # ---------------------------
            outside, msg = _requested_range_outside_available(parsed_intent)
            if outside:
                yield _text_event(msg)
                return

            # ---------------------------
            # Normal analytics / retrieval flow
            # ---------------------------

            # SQL Builder
            async for event in protected_query_builder_agent.run_async(context):
                yield event

            built_query_raw = session_state.get("built_query")
            built_query = self._parse_built_query(built_query_raw)

            if built_query.get("status") != "ok":
                yield _text_event(built_query.get("message", "SQL Builder error"))
                return

            # ✅ stable intent_key based on parsed_intent (not SQL formatting)
            try:
                stable_intent_key = normalize_intent_key(parsed_intent=parsed_intent)
                built_query["intent_key"] = stable_intent_key
                logging.info(f"🟣 [RootAgent] Added parsed_intent-based intent_key (len={len(stable_intent_key)})")
            except Exception as e:
                logging.warning(f"🟡 [RootAgent] Failed to create parsed_intent intent_key, fallback to SQL. err={e}")

            # Query Executor
            logging.info("🔴 [RootAgent] Calling query_executor_agent with built_query")
            sql_result = query_executor_agent(built_query)
            logging.info(f"🔴 [RootAgent] query_executor_agent returned: {json.dumps(sql_result, indent=2)[:500]}")

            session_state["execution_result"] = sql_result
            logging.info("🔴 [RootAgent] Set execution_result in session_state")

            # Insights Agent
            session_state["insights_payload"] = {"execution_result": sql_result}
            logging.info("🔴 [RootAgent] Running response_insights_agent...")
            async for event in response_insights_agent.run_async(context):
                yield event

            # Human Response Agent
            insights_result_raw = session_state.get("insights_result", {})
            insights_result = self._parse_built_query(insights_result_raw)

            logging.info("🔴 [RootAgent] Calling human_response_agent (Python function)...")
            final_response = human_response_agent(sql_result, insights_result)

            yield _text_event(final_response)

            logging.info("🔴 [RootAgent] Analytics flow completed")
            return

        yield _text_event("I couldn't understand the request.")
        return

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
