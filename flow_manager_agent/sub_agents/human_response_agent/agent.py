import logging

logger = logging.getLogger(__name__)


def human_response_agent(execution_result: dict, insights_result: dict) -> str:
    """
    Pure Python function that formats the final response to the user.
    Shows the ACTUAL data table from BigQuery + insights text.
    
    Args:
        execution_result: Result from query execution with the actual data table
        insights_result: Analysis and insights from response_insights_agent
    
    Returns:
        Formatted response string with data table and insights
    """
    logger.info("🟣" * 40)
    logger.info("🟣 human_response_agent (Python function) called")
    
    try:
        # Extract the actual data table
        data_table = execution_result.get("result", "")
        row_count = execution_result.get("row_count", 0)
        
        # Extract insights text
        final_text = insights_result.get("final_text", "")
        suggested_drilldowns = insights_result.get("suggested_drilldowns", [])
        
        logger.info(f"🟣 Data table length: {len(data_table)} chars")
        logger.info(f"🟣 Row count: {row_count}")
        logger.info(f"🟣 Final text length: {len(final_text)} chars")
        
        # Check if data is empty/null
        is_empty_data = (
            not data_table 
            or data_table.strip() == "" 
            or "|                |" in data_table  # Empty cell in markdown table
            or "| None |" in data_table
            or "| nan |" in data_table.lower()
        )
        
        # Build the response - ACTUAL DATA FIRST, then insights
        response_parts = []
        
        # 1. Show the ACTUAL data table OR no data message
        if is_empty_data:
            response_parts.append("❌ **לא נמצאו נתונים** עבור השאילתה.")
            response_parts.append("ייתכן שהמדיה/אפליקציה/תאריך שביקשת לא קיימים בטבלה.")
            response_parts.append("")
        elif data_table:
            response_parts.append(data_table)
            response_parts.append("")  # Empty line
        
        # 2. Add insights text
        if final_text:
            response_parts.append(final_text)
        
        # 3. Add suggested drilldowns if any
        if suggested_drilldowns:
            response_parts.append("")
            response_parts.append("💡 אפשרויות לבדיקה נוספת:")
            for drilldown in suggested_drilldowns[:3]:  # Max 3
                response_parts.append(f"  • {drilldown}")
        
        response = "\n".join(response_parts)
        
        logger.info(f"✅ Response built successfully ({len(response)} chars)")
        logger.info(f"Response preview:\n{response[:500]}...")
        logger.info("🟣" * 40)
        
        return response
        
    except Exception as e:
        logger.exception("❌ human_response_agent failed")
        return f"שגיאה בעיבוד התשובה: {e}"