import logging
import re
from typing import Optional
from datetime import datetime, date

logger = logging.getLogger(__name__)

# =========================
# 2) human_response_agent (ENGLISH renderer + converts table to key:value)
# =========================

SUPPORTED_DATES = {"2025-10-24", "2025-10-25", "2025-10-26"}


def _extract_requested_date_from_sql(executed_sql: str) -> Optional[str]:
    if not executed_sql:
        return None

    # 1) Prefer YYYY-MM-DD anywhere in the SQL
    m = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", executed_sql)
    if m:
        return m.group(1)

    # 2) Support DD.MM.YY or DD.MM.YYYY (e.g., 25.10.25 or 25.10.2025)
    m2 = re.search(r"\b(\d{2})\.(\d{2})\.(\d{2,4})\b", executed_sql)
    if m2:
        dd, mm, yy = m2.group(1), m2.group(2), m2.group(3)
        if len(yy) == 2:
            yy = "20" + yy
        return f"{yy}-{mm}-{dd}"

    return None


def _parse_yyyy_mm_dd(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None


def _is_future_date(user_date: Optional[str]) -> bool:
    d = _parse_yyyy_mm_dd(user_date)
    if not d:
        return False
    return d > date.today()


def _is_supported_date(user_date: Optional[str]) -> bool:
    return bool(user_date) and user_date in SUPPORTED_DATES


def _is_empty_markdown_table(md: str) -> bool:
    if not md or not md.strip():
        return True

    low = md.lower()
    if "| none |" in low or "| nan |" in low:
        return True

    lines = [ln for ln in md.strip().splitlines() if ln.strip()]
    if len(lines) <= 2 and "|" in md:
        return True

    return False


def _beautify_error_message(user_date: Optional[str]) -> str:
    # ✅ New rule: future dates
    if _is_future_date(user_date):
        return "Future dates are not supported because no events have occurred yet."

    # ✅ New rule: any date outside the supported set
    if user_date and not _is_supported_date(user_date):
        return (
            f"I don't have information for that date ({user_date}). "
            "If you'd like, I can help you with another date."
        )

    # Existing behavior for supported dates (no data found)
    if user_date:
        return (
            f"No data was found for the date you requested ({user_date}).\n"
            "This may happen if there were no events for that date/time slice, or your filters are too restrictive.\n\n"
            "Next steps you can try:\n"
            "• Try a different date or hour\n"
            "• Remove/change a filter (e.g., media_source / partner)\n"
            "• Ask for Top 10 results instead of a single result"
        )

    return (
        "No data was found for your request.\n"
        "This may happen if there were no events, or your filters are too restrictive.\n\n"
        "Next steps you can try:\n"
        "• Try a different date/time\n"
        "• Adjust filters\n"
        "• Ask for Top 10 results"
    )


def _parse_first_row_as_kv(md_table: str) -> dict:
    """
    Extract the first data row of a markdown table as {column: value}.
    Returns {} on failure.
    """
    if not md_table or "|" not in md_table:
        return {}

    lines = [ln.strip() for ln in md_table.strip().splitlines() if ln.strip()]
    if len(lines) < 3:
        return {}

    header = lines[0]
    sep = lines[1]
    if "|" not in header or "|" not in sep:
        return {}

    def split_row(line: str):
        s = line.strip()
        if s.startswith("|"):
            s = s[1:]
        if s.endswith("|"):
            s = s[:-1]
        return [c.strip() for c in s.split("|")]

    cols = split_row(header)

    data = None
    for ln in lines[2:]:
        if "|" in ln:
            data = split_row(ln)
            break

    if not data or len(data) != len(cols):
        return {}

    return {cols[i]: data[i] for i in range(len(cols))}


def _format_kv_block(kv: dict) -> str:
    """
    Formats dict into:
    total_events: 107051
    hr: 2
    """
    out = []
    for k, v in kv.items():
        if k and v is not None and str(v).strip():
            out.append(f"{k}: {v}")
    return "\n".join(out).strip()


def human_response_agent(execution_result: dict, insights_result: dict) -> str:
    logger.info("🟣" * 40)
    logger.info("🟣 human_response_agent (Python function) called")

    try:
        status = (execution_result or {}).get("status", "")
        data_table = (execution_result or {}).get("result", "") or ""
        row_count = int((execution_result or {}).get("row_count") or 0)
        executed_sql = (execution_result or {}).get("executed_sql", "") or ""

        requested_date = _extract_requested_date_from_sql(executed_sql)

        # ✅ New early exits (do NOT touch anything else)
        if _is_future_date(requested_date):
            return "Future dates are not supported because no events have occurred yet."
        if requested_date and not _is_supported_date(requested_date):
            return (
                f"I don't have information for that date ({requested_date}). "
                "If you'd like, I can help you with another date."
            )

        is_empty_data = _is_empty_markdown_table(data_table) or row_count == 0

        # insights payload
        final_text = (insights_result or {}).get("final_text", "") or ""
        next_steps = (insights_result or {}).get("next_steps", {}) or {}
        suggested_questions = next_steps.get("suggested_questions", []) or []

        presentation = (insights_result or {}).get("presentation", {}) or {}
        title = (presentation or {}).get("title", "") or ""
        show_table = bool((presentation or {}).get("show_table", True))
        sections = (presentation or {}).get("sections", []) or []

        parts: list[str] = []

        # error/no-data
        if status != "ok" or is_empty_data:
            if sections:
                if title.strip():
                    parts.append(title.strip())
                    parts.append("")

                for sec in sections:
                    heading = (sec or {}).get("heading", "") or ""
                    style = (sec or {}).get("style", "both") or "both"
                    text = (sec or {}).get("text", "") or ""
                    bullets = (sec or {}).get("bullets", []) or []

                    if heading.strip():
                        parts.append(f"{heading.strip()}:")
                    if style in ("sentence", "both") and text.strip():
                        parts.append(text.strip())
                    if style in ("bullets", "both"):
                        for b in bullets[:3]:
                            if isinstance(b, str) and b.strip():
                                parts.append(f"• {b.strip()}")
                    parts.append("")

                if suggested_questions:
                    parts.append("Next steps you can try:")
                    for q in suggested_questions[:3]:
                        if isinstance(q, str) and q.strip():
                            parts.append(f"• {q.strip()}")

                return "\n".join(parts).strip()

            return _beautify_error_message(requested_date)

        # normal
        if title.strip():
            parts.append(title.strip())
            parts.append("")

        if sections:
            for sec in sections:
                heading = (sec or {}).get("heading", "") or ""
                style = (sec or {}).get("style", "both") or "both"
                text = (sec or {}).get("text", "") or ""
                bullets = (sec or {}).get("bullets", []) or []

                if heading.strip():
                    parts.append(f"{heading.strip()}:")
                if style in ("sentence", "both") and text.strip():
                    parts.append(text.strip())
                if style in ("bullets", "both"):
                    for b in bullets[:3]:
                        if isinstance(b, str) and b.strip():
                            parts.append(f"• {b.strip()}")
                parts.append("")
        else:
            # fallback minimal intro
            if requested_date:
                parts.append(f"I checked the data for the date you requested: {requested_date}.")
            else:
                parts.append("I checked the data based on your request.")
            parts.append("")

        # Details: prefer key:value over markdown pipes
        if show_table and data_table.strip():
            kv = _parse_first_row_as_kv(data_table)
            parts.append("Details:")
            if kv:
                parts.append(_format_kv_block(kv))
            else:
                # fallback if parsing failed
                parts.append(data_table.strip())
            parts.append("")

        # wrap-up
        if final_text.strip():
            parts.append(final_text.strip())
            parts.append("")

        # next steps
        followups: list[str] = []
        for q in suggested_questions:
            if isinstance(q, str) and q.strip():
                followups.append(q.strip())

        if followups:
            parts.append("💡 Next steps you can try:")
            for item in followups[:3]:
                parts.append(f"• {item}")

        response = "\n".join(parts).strip()
        logger.info(f"✅ Response built successfully ({len(response)} chars)")
        logger.info(f"Response preview:\n{response[:500]}...")
        logger.info("🟣" * 40)
        return response

    except Exception as e:
        
        logger.exception("❌ human_response_agent failed")
        return f"Error while formatting the response: {e}"
