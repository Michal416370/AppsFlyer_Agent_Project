from typing import AsyncGenerator, Any, Dict
import json
import re
from .utils.json_utils import clean_json as _clean_json

from google.genai import types
from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event

from .sub_agents.nlu_agent.sub_agents.intent_analyzer_agent import intent_analyzer_agent
from .sub_agents.nlu_agent.sub_agents.clarifier_orchestrator_agent import clarifier_agent
from .sub_agents.full_pipeline_agent import full_pipeline_agent
from .sub_agents.full_pipeline_agent_v2 import FullPipelineAgentV2

full_pipeline_v2 = FullPipelineAgentV2()

def _text_event(msg: str) -> Event:
    # ADK expects Content object, not raw string
    return Event(
        author="assistant",
        content=types.Content(parts=[types.Part(text=msg)])
    )

# FlowManagerFrontdoor - השער הראשי של כל המערכת 
# כל הודעת משתמש נכנסת קודם למקום הזה. הוא זה שמחליט איזה Agent ירוץ ומתי 
class FlowManagerFrontdoor(BaseAgent):
    """
    Behavior:
    - Each user turn runs ONLY intent_analyzer_agent.
    - If clarification_needed -> run clarifier_agent, ask, STOP.
    - If ok -> run full_pipeline_agent.
    - If not_relevant/error -> explain, STOP.
    """

    def __init__(self):
        super().__init__(name="flow_manager_agent")

    #  פונקציה שמופעלת אוטומטית עבור כל הודעת משתמש חדשה - _run_async_impl 
    # ctx:InvocationContext - דרכו אפשר לגשת לsession שמחזיק state 
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        state = ctx.session.state

        # --- Step 1: run ONLY Agent1 (intent analyzer) ---
        async for ev in intent_analyzer_agent.run_async(ctx):
            yield ev

        #קריאת ניתוח הכוונה והסקת ה־status 
        analysis = _clean_json(state.get("intent_analysis"))
        status = analysis.get("status")

        # normalize possible typo
        if status == "not relevant":
            status = "not_relevant"

        # --- Step 2: if clarification needed, ask ONE question and STOP ---
        # אם חסר מידע לביצוע שאילתה 
        # FlowManager שומר את השדות שחסרים → last_missing_fields 
        # ואז מפעיל את clarifier_agent, ה־clarifier מחזיר שאלה אחת בלבד ואז המערכת עוצרת לגמרי ומחכה להודעת המשתמש הבאה 
        if status == "clarification_needed":
            # save missing fields for next turn (optional)
            state["last_missing_fields"] = analysis.get("missing_fields", [])

            async for ev in clarifier_agent.run_async(ctx):
                yield ev

            # question = state.get("clarification_question") or analysis.get("message") or "Can you clarify?"
            # yield _text_event(question)
            return  # <-- STOP. Next user msg will re-run Step 1 only.

        # --- Step 3: not relevant / error -> explain and STOP ---
        # not relevant או error → מחזירים הודעה ועוצרים 
        if status in ("not_relevant", "error"):
            msg = analysis.get("message", "Request not supported.")
            yield _text_event(msg)
            return

        # --- Step 4: ok -> enter full pipeline (Agent2->3) ---
        if status == "ok":
            # async for ev in full_pipeline_agent.run_async(ctx):
            # הכל תקין → כניסה ל־Full Pipeline (SQL builder + executor) 
            # protected_query_builder_agent בונה SQL 
            # FullPipelineAgentV2 מוודא שה־JSON תקין 
            # query_executor_agent מריץ את השאילתה 
            # מחזירים למשתמש את תוצאת ה־BigQuery 
            async for ev in full_pipeline_v2.run_async(ctx):
                yield ev
            return

        # --- Fallback ---
        # מקרה קצה שלא אמור לקרות 
        yield _text_event("I couldn't understand the request.")
        return

# הAgent הראשי 
root_agent = FlowManagerFrontdoor()