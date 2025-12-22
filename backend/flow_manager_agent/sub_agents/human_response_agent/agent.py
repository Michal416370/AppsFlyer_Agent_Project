import logging

logger = logging.getLogger(__name__)


def human_response_agent(execution_result: dict, insights_result: dict) -> str:
    logger.info("🟣 human_response_agent called")

    data_table = execution_result.get("result", "")
    row_count = execution_result.get("row_count", 0)

    final_text = insights_result.get("final_text", "")
    suggested_drilldowns = insights_result.get("suggested_drilldowns", [])

    response_parts = []

    if row_count == 0 or not data_table.strip():
        response_parts.append("❌ לא נמצאו נתונים עבור הבקשה.")
    else:
        response_parts.append(data_table)

    if final_text:
        response_parts.append("")
        response_parts.append(final_text)

    if suggested_drilldowns:
        response_parts.append("")
        response_parts.append("💡 אפשרויות לבדיקה נוספת:")
        for d in suggested_drilldowns[:3]:
            response_parts.append(f"  • {d}")

    return "\n".join(response_parts)
