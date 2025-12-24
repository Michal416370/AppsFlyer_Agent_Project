import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)


def _extract_requested_date_from_sql(executed_sql: str) -> str | None:
    """
    Best-effort extraction of a requested date from executed SQL.
    We only return the *requested* date (single day) if we can detect it.

    Supported patterns (examples):
    - TIMESTAMP('2025-10-24 00:00:00')
    - DATE '2025-10-24'
    - '2025-10-24'
    """
    if not executed_sql:
        return None

    # Look for YYYY-MM-DD
    m = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", executed_sql)
    if m:
        return m.group(1)

    return None


def _is_empty_markdown_table(md: str) -> bool:
    if not md or not md.strip():
        return True

    # very defensive emptiness checks
    low = md.lower()
    if "| none |" in low or "| nan |" in low:
        return True

    # if only header + separator without data rows
    lines = [ln for ln in md.strip().splitlines() if ln.strip()]
    if len(lines) <= 2 and "|" in md:
        return True

    return False


def _beautify_error_message(user_date: str | None) -> str:
    # IMPORTANT: do NOT expose internal available ranges; only show requested date.
    if user_date:
        return (
            f"לא מצאתי נתונים עבור התאריך שביקשת ({user_date}).\n"
            "יכול להיות שלא היו אירועים בתאריך הזה או שהפילטרים שהגדרת מצמצמים מדי.\n\n"
            "אם תרצי, אני יכולה לעזור לך לבדוק:\n"
            "• תאריך אחר\n"
            "• להסיר/לשנות פילטר (למשל media_source / partner)\n"
            "• להציג Top 10 במקום תוצאה אחת"
        )

    return (
        "לא מצאתי נתונים עבור הבקשה שלך.\n"
        "יכול להיות שלא היו אירועים או שהפילטרים מצמצמים מדי.\n\n"
        "אם תרצי, אני יכולה לעזור לך לבדוק תאריך אחר או לשנות פילטרים."
    )


def human_response_agent(execution_result: dict, insights_result: dict) -> str:
    """
    Formats the final response to the user with:
    1) Short contextual intro
    2) Actual markdown data table (if exists)
    3) Beautiful concise insights (final_text)
    4) Next steps (suggested questions / drilldowns)
    """
    logger.info("🟣" * 40)
    logger.info("🟣 human_response_agent (Python function) called")

    try:
        status = (execution_result or {}).get("status", "")
        data_table = (execution_result or {}).get("result", "") or ""
        row_count = int((execution_result or {}).get("row_count") or 0)
        executed_sql = (execution_result or {}).get("executed_sql", "") or ""
        from_cache = (execution_result or {}).get("from_cache", None)  # optional if you add it

        # insights payload (from LLM)
        final_text = (insights_result or {}).get("final_text", "") or ""
        next_steps = (insights_result or {}).get("next_steps", {}) or {}
        suggested_questions = next_steps.get("suggested_questions", []) or []
        suggested_drilldowns = next_steps.get("suggested_drilldowns", []) or []

        # We only show the requested date (if found), NEVER internal available ranges
        requested_date = _extract_requested_date_from_sql(executed_sql)

        is_empty_data = _is_empty_markdown_table(data_table) or row_count == 0

        # Build response
        parts: list[str] = []

        # 0) Header line (polite + contextual)
        # Keep it short and natural
        if requested_date:
            parts.append(f"בדקתי עבורך נתונים עבור התאריך שביקשת: {requested_date}.")
        else:
            parts.append("בדקתי עבורך את הנתונים לפי הבקשה שלך.")

        # 1) Error / no-data handling
        if status != "ok":
            # Prefer model message if present, but keep it user-friendly
            parts.append("")
            parts.append(_beautify_error_message(requested_date))
            return "\n".join(parts).strip()

        if is_empty_data:
            parts.append("")
            parts.append(_beautify_error_message(requested_date))
            return "\n".join(parts).strip()

        # 2) Show actual data table
        parts.append("")
        parts.append(data_table.strip())

        # 3) Add insights text (short & pretty)
        if final_text.strip():
            parts.append("")
            parts.append(final_text.strip())

        # 4) Suggested follow-ups (prioritize suggested_questions; fallback to drilldowns)
        followups: list[str] = []
        for q in suggested_questions:
            if isinstance(q, str) and q.strip():
                followups.append(q.strip())

        # fallback: drilldowns
        if not followups and suggested_drilldowns:
            followups.extend([f"פילוח לפי {d}" for d in suggested_drilldowns[:3]])

        if followups:
            parts.append("")
            parts.append("💡 אפשר להמשיך מכאן:")
            for item in followups[:3]:
                parts.append(f"• {item}")

        # Optional debug hint (ONLY if you add a flag later)
        # if from_cache is True:
        #     parts.append("\n(הערת מערכת: התשובה חזרה מהקאש)")

        response = "\n".join(parts).strip()

        logger.info(f"✅ Response built successfully ({len(response)} chars)")
        logger.info(f"Response preview:\n{response[:500]}...")
        logger.info("🟣" * 40)

        return response

    except Exception as e:
        logger.exception("❌ human_response_agent failed")
        return f"שגיאה בעיבוד התשובה: {e}"
