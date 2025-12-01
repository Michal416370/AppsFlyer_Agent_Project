from typing import AsyncGenerator
from google.adk.agents import BaseAgent
from google.adk.events import Event
from google.genai import types

from .utils.json_utils import clean_json as _clean_json

# --- Sub Agents ---
from .sub_agents.nlu_agent.sub_agents.intent_analyzer_agent import intent_analyzer_agent
from .sub_agents.nlu_agent.sub_agents.clarifier_orchestrator_agent import clarifier_agent
from .sub_agents.protected_query_builder_agent import protected_query_builder_agent
from .sub_agents.query_executor_agent import query_executor_agent
from .sub_agents.response_insights_agent import response_insights_agent
from .sub_agents.human_response_agent import human_response_agent

import json
import re
import logging


def _text_event(message: str) -> Event:
    """Helper: convert plain text into ADK Event."""
    return Event(
        author="assistant",
        content=types.Content(parts=[types.Part(text=message)])
    )


class RootAgent(BaseAgent):
    """Single orchestrator for the entire system."""

    def __init__(self):
        super().__init__(name="root_agent")

    async def _run_async_impl(self, context) -> AsyncGenerator[Event, None]:
        session_state = context.session.state

        # ============================================================
        # 1) INTENT ANALYZER
        # ============================================================
        async for event in intent_analyzer_agent.run_async(context):
            yield event

        intent_analysis = _clean_json(session_state.get("intent_analysis"))
        status = intent_analysis.get("status")

        if status == "not relevant":  # normalization
            status = "not_relevant"

        # ============================================================
        # 2) CLARIFICATION FLOW
        # ============================================================
        if status == "clarification_needed":
            missing_fields = intent_analysis.get("missing_fields", [])
            session_state["missing_fields"] = missing_fields

            async for event in clarifier_agent.run_async(context):
                yield event

            return   # STOP → wait for next user message

        # ============================================================
        # 3) STOP ON ERROR / NOT RELEVANT
        # ============================================================
        if status in ("not_relevant", "error"):
            user_message = intent_analysis.get("message", "Request not supported.")
            yield _text_event(user_message)
            return

        # ============================================================
        # 4) OK → START FULL PIPELINE (MANAGED HERE)
        # ============================================================
        if status == "ok":

            # ---------------------------
            # STEP A: SQL BUILDER
            # ---------------------------
            async for event in protected_query_builder_agent.run_async(context):
                yield event

            built_query_raw = session_state.get("built_query")
            logging.info(f"[RootAgent] raw built_query: {built_query_raw}")

            # Clean JSON (string → dict)
            cleaned_built_query = self._parse_built_query(built_query_raw)
            if cleaned_built_query is None:
                yield _text_event("SQL Builder returned invalid JSON.")
                return

            if cleaned_built_query.get("status") != "ok":
                yield _text_event("SQL Builder returned an error.")
                return

            # ---------------------------
            # STEP B: SQL EXECUTOR
            # ---------------------------
            async for event in query_executor_agent.run_async(context):
                yield event

            sql_execution_result = _clean_json(session_state.get("execution_result", {}))

            # ---------------------------
            # STEP C: INSIGHTS AGENT
            # ---------------------------
            session_state["insights_payload"] = {
                "execution_result": sql_execution_result
            }

            async for event in response_insights_agent.run_async(context):
                yield event

            # ---------------------------
            # STEP D: HUMAN RESPONSE
            # ---------------------------
            async for event in human_response_agent.run_async(context):
                yield event

            return

        # ============================================================
        # 5) FALLBACK
        # ============================================================
        yield _text_event("I couldn't understand the request.")
        return

    # ====================================================================
    # Helper: Clean/Parse built_query JSON
    # ====================================================================
    def _parse_built_query(self, raw):
        """Convert raw built_query into dict safely."""
        if isinstance(raw, dict):
            return raw

        if isinstance(raw, str):
            cleaned = raw.strip()
            cleaned = re.sub(r"```json|```", "", cleaned).strip()

            try:
                return json.loads(cleaned)
            except Exception:
                logging.error("[RootAgent] Failed to parse built_query JSON.")
                return None

        logging.error("[RootAgent] built_query is neither dict nor string.")
        return None


# Create the actual agent instance
root_agent = RootAgent()
