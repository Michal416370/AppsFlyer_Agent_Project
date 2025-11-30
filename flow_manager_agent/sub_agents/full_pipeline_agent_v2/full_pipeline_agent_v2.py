from google.adk.agents import BaseAgent
from google.adk.events import Event
from google.genai import types

import json
import logging
import re
from ...utils.json_utils import clean_json as _clean_json

from ..protected_query_builder_agent import protected_query_builder_agent
from ..query_executor_agent import query_executor_agent
from ..response_insights_agent import response_insights_agent
from ..human_response_agent import human_response_agent




def _text_event(msg: str) -> Event:
    return Event(
        author="assistant",
        content=types.Content(parts=[types.Part(text=msg)])
    )


class FullPipelineAgentV2(BaseAgent):
    """
    Stable pipeline:
    1. Runs SQL builder
    2. Validates built_query
    3. Runs SQL executor
    """

    def __init__(self):
        super().__init__(name="full_pipeline_agent_v2")

    async def _run_async_impl(self, ctx):
        state = ctx.session.state

        # --- Step 1: SQL Builder ---
        async for ev in protected_query_builder_agent.run_async(ctx):
            yield ev

        # הוצאת ה־built_query מה־state 
        built = state.get("built_query")
        logging.info(f"Extracted built_query raw: {built}")

        # Fix: built_query sometimes comes as a JSON string instead of dict
        # שגיאה נפוצה: built_query יכול להגיע כמחרוזת JSON ולא dict 
        if isinstance(built, str):
            cleaned = built.strip()

            # Remove code fences like ```json ... ```
            cleaned = re.sub(r"```json|```", "", cleaned).strip()

            # ניסיון להמיר ל־JSON תקין 
            try:
                built = json.loads(cleaned)
                logging.info(f"built_query parsed into dict: {built}")
            except Exception:
                logging.error("built_query is an invalid JSON string!")
                yield _text_event("SQL Builder produced invalid JSON.")
                return
                logging.info(f"built_query parsed into dict: {built}")
            except Exception:
                logging.error("built_query is an invalid JSON string!")
                yield _text_event("SQL Builder produced invalid JSON.")
                return

        # אם JSON לא תקין → עוצרים הכול 
        # אי אפשר להמשיך לשלב SQL Executor 
        if not isinstance(built, dict):
            logging.error("built_query is not a dict!")
            yield _text_event("Invalid SQL builder output.")
            return

        # בדיקת status של ה־SQL builder 
        # SQL builder צריך לחזור עם "status": "ok" 
        if built.get("status") != "ok":
            logging.error("built_query.status is not ok!")
            yield _text_event("SQL Builder returned an error.")
            return

        # --- Step 2: SQL Executor ---
        # הפעלת query_executor_agent 
        async for ev in query_executor_agent.run_async(ctx):
            yield ev

        # Retrieve execution result from session state
        execution_result = _clean_json(state.get("execution_result", {}))

        # --- Step 5: Run insights agent ---
        ctx.session.state["insights_input"] = {
            "execution_result": execution_result
        }

        async for ev in response_insights_agent.run_async(ctx):
            yield ev

        # --- Step 6: Run human response agent ---
        async for ev in human_response_agent.run_async(ctx):
            yield ev
            