from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .flow_manager_agent.agent import root_agent
from .bq import BQClient

from google.adk.apps import App
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.utils.context_utils import Aclosing
from google.genai import types

import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# ---- CORS ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # אפשר ["*"] לבדיקה
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- יצירת ADK App ו-Runner ----
adk_app = App(name="appsflyer_agent", root_agent=root_agent)
session_service = InMemorySessionService()
runner = Runner(app=adk_app, session_service=session_service)

# קבועים למזהים
USER_ID = "default_user"
SESSION_ID = "default_session"

# ---- אתחול BigQuery ----
try:
    bq_client = BQClient()
    bq_client.ensure_chat_history_table()
    logger.info("BigQuery chat history table ready")
except Exception as e:
    logger.warning(f"Failed to initialize BigQuery: {e}")
    bq_client = None


# ---- בדיקת חיים ----
@app.get("/health")
def health():
    return {"ok": True}


# ---- Request schema ----
class ChatRequest(BaseModel):
    message: str


def _extract_text_from_event(event) -> Optional[str]:
    """
    Extracts text from an ADK Event safely.
    ADK events may contain multiple parts and not always in parts[0].
    """
    if not event or not getattr(event, "content", None):
        return None

    parts = getattr(event.content, "parts", None) or []
    if not parts:
        return None

    texts: list[str] = []
    for p in parts:
        t = getattr(p, "text", None)
        if isinstance(t, str) and t.strip():
            texts.append(t)

    if not texts:
        return None

    return "\n".join(texts).strip()


# ---- Helper: run agent ----
async def run_agent(message: str):
    # 1) get/create session
    session = await session_service.get_session(
        app_name=adk_app.name,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )
    if not session:
        session = await session_service.create_session(
            app_name=adk_app.name,
            user_id=USER_ID,
            session_id=SESSION_ID,
        )

    # 2) build user content
    content = types.Content(
        role="user",
        parts=[types.Part(text=message)],
    )

    last_text = None
    final_root_text = None
    final_react_text = None

    # 3) run and consume stream
    async with Aclosing(
        runner.run_async(
            user_id=USER_ID,
            session_id=SESSION_ID,
            new_message=content,
        )
    ) as agen:
        async for event in agen:
            txt = _extract_text_from_event(event)
            if not txt:
                continue

            last_text = txt
            author = getattr(event, "author", None)
            logger.info(f"[run_agent] author={author} prefix={txt[:80]!r}")

            # Debug (אפשר להוריד אחרי שתעבוד)
            logger.debug(f"event.author={author} text_prefix={txt[:60]}")

            # ✅ prefer react component if it appears anywhere
            if isinstance(txt, str) and txt.startswith("__REACT_COMPONENT__"):
                final_react_text = txt

            # keep latest root text too
            if author == "root_agent":
                final_root_text = txt

    # 4) return with priority: react > root > last
    if final_react_text:
        return final_react_text
    if final_root_text:
        return final_root_text
    if last_text:
        return last_text

    return {"error": "No response from agent"}


# ---- API endpoint ----
@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        # שמירת הודעת המשתמש
        if bq_client:
            try:
                bq_client.save_chat_message(
                    session_id=SESSION_ID,
                    user_id=USER_ID,
                    role="user",
                    message=req.message,
                )
            except Exception as e:
                logger.error(f"Failed to save user message: {e}")

        # הרצת האגנט
        response = await run_agent(req.message)

        # שמירת תשובת האגנט
        if bq_client:
            try:
                bq_client.save_chat_message(
                    session_id=SESSION_ID,
                    user_id=USER_ID,
                    role="assistant",
                    message=str(response),
                )
            except Exception as e:
                logger.error(f"Failed to save assistant message: {e}")

        return response

    except Exception as e:
        logger.exception("Chat endpoint failed")
        raise HTTPException(status_code=500, detail=str(e))
