from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from flow_manager_agent.agent import root_agent
from backend.bq import BQClient
from google.adk.apps import App
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types
from google.adk.utils.context_utils import Aclosing
import uuid
import logging
import logging

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
runner = Runner(
    app=adk_app,
    session_service=session_service,
)

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


# ---- Helper: run agent ----
async def run_agent(message: str):
    # יצירת session אם לא קיים
    session = await session_service.get_session(
        app_name=adk_app.name,
        user_id=USER_ID,
        session_id=SESSION_ID
    )
    
    if not session:
        session = await session_service.create_session(
            app_name=adk_app.name,
            user_id=USER_ID,
            session_id=SESSION_ID
        )
    
    # יצירת תוכן ההודעה
    content = types.Content(role='user', parts=[types.Part(text=message)])
    
    last_event = None
    
    # הרצת האגנט
    async with Aclosing(
        runner.run_async(
            user_id=USER_ID,
            session_id=SESSION_ID,
            new_message=content
        )
    ) as agen:
        async for event in agen:
            last_event = event

    if not last_event:
        return {"error": "No response from agent"}

    if not last_event.content or not last_event.content.parts:
        return {"error": "Empty response from agent"}

    part = last_event.content.parts[0]

    if part.text:
        return part.text

    if part.inline_data:
        return part.inline_data

    return {"error": "Unknown agent response"}


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
                    message=req.message
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
                    message=str(response)
                )
            except Exception as e:
                logger.error(f"Failed to save assistant message: {e}")
        
        return response
    except Exception as e:
        import traceback
        traceback.print_exc()  # 👈 זה מה שחשוב עכשיו
        raise HTTPException(status_code=500, detail=str(e))