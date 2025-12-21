from backend.bq import BQClient
from backend.flow_manager_agent.utils.cache import CacheService, normalize_intent_key
import pandas as pd
import logging
import json

logger = logging.getLogger(__name__) 


def run_bigquery(query: str):
    """Executes a BigQuery SQL query and returns results as markdown."""
    logger.info("=" * 80)
    logger.info("🔵 run_bigquery called")
    logger.info("SQL to execute:\n%s", query)
    logger.info("=" * 80)
    
    try:
        logger.info("🔵 Creating BQClient instance...")
        bq = BQClient()
        logger.info("✅ BQClient created successfully")

        # Runner that returns list[dict] rows
        def _runner(sql: str):
            logger.info("🔵 _runner executing query...")
            it = bq.execute_query(sql, 'adk_query')
            logger.info("✅ Query executed, converting to dataframe...")
            df = it.to_dataframe()
            logger.info(f"✅ DataFrame created with {len(df)} rows")
            records = df.to_dict(orient='records')
            logger.info(f"✅ Converted to {len(records)} records")
            return records

        logger.info("🔵 Creating CacheService...")
        cs = CacheService()
        intent_key = normalize_intent_key(sql=query)
        logger.info(f"🔵 Cache key: {intent_key}")
        
        logger.info("🔵 Running query with cache...")
        rows, from_cache = cs.run_query_with_cache(sql=query, intent_key=intent_key, run_bigquery_fn=_runner)
        logger.info(f"✅ Query completed! Got {len(rows)} rows (from_cache={from_cache})")

        # Build markdown result for downstream agents
        logger.info("🔵 Building markdown output...")
        df_out = pd.DataFrame(rows)
        markdown = df_out.to_markdown(index=False) if not df_out.empty else ""
        logger.info(f"✅ Markdown length: {len(markdown)} chars")
        logger.info(f"Markdown preview:\n{markdown[:500]}")

        result = {
            "status": "ok",
            "result": markdown,
            "message": None,
            "row_count": len(rows),
            "executed_sql": query,
            "from_cache": from_cache,
        }
        logger.info("✅ run_bigquery completed successfully")
        logger.info("=" * 80)
        return result
        
    except Exception as e:
        logger.exception("❌ BigQuery execution failed")
        error_result = {
            "status": "error",
            "result": None,
            "message": f"BigQuery execution error: {e}",
            "executed_sql": query,
        }
        logger.error(f"Error result: {error_result}")
        logger.info("=" * 80)
        return error_result


def query_executor_agent(previous_output: dict) -> dict:
    """
    Pure Python function that executes SQL query from the previous agent's output.
    
    Args:
        previous_output: JSON object from the previous agent, either:
            - { "built_query": {...} } or
            - { "status": "...", "sql": "...", ... } directly
    
    Returns:
        Result of the BigQuery execution
    """
    logger.info("🟢" * 40)
    logger.info("🟢 query_executor_agent (Python function) called")
    logger.info(f"🟢 Input type: {type(previous_output)}")
    logger.info(f"🟢 Input: {json.dumps(previous_output, indent=2) if isinstance(previous_output, dict) else previous_output}")
    
    try:
        # Parse input if it's a string
        if isinstance(previous_output, str):
            logger.info("🟢 Input is string, parsing JSON...")
            previous_output = json.loads(previous_output)
            logger.info("✅ JSON parsed successfully")
        
        # Extract built_query
        if "built_query" in previous_output:
            logger.info("🟢 Found 'built_query' key, extracting...")
            built_query = previous_output["built_query"]
        else:
            logger.info("🟢 No 'built_query' key, using entire input as built_query")
            built_query = previous_output
        
        logger.info(f"🟢 built_query: {json.dumps(built_query, indent=2)}")
        
        # Check status
        status = built_query.get("status")
        logger.info(f"🟢 Status check: '{status}'")
        
        if status != "ok":
            logger.warning(f"⚠️ Status is not 'ok', returning error")
            return {
                "status": "error",
                "result": None,
                "message": "SQL cannot be executed because status is not ok."
            }
        
        # Extract and execute SQL
        sql = built_query.get("sql")
        logger.info(f"🟢 Extracted SQL: {sql[:100] if sql else 'None'}...")
        
        if not sql:
            logger.error("❌ No SQL found in built_query")
            return {
                "status": "error",
                "result": None,
                "message": "No SQL found in built_query"
            }
        
        # Execute the query
        logger.info("🟢 Calling run_bigquery...")
        result = run_bigquery(sql)
        logger.info(f"✅ run_bigquery returned: {json.dumps(result, indent=2)[:500]}...")
        logger.info("🟢" * 40)
        return result
        
    except Exception as e:
        logger.exception("❌ query_executor_agent failed")
        error_result = {
            "status": "error",
            "result": None,
            "message": f"Query executor error: {e}"
        }
        logger.error(f"Error result: {error_result}")
        logger.info("🟢" * 40)
        return error_result
