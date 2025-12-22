from backend.bq import BQClient
from backend.flow_manager_agent.utils.cache import CacheService, normalize_intent_key
import pandas as pd
import logging
import json

logger = logging.getLogger(__name__)


def run_bigquery(query: str, intent_key: str | None = None):
    """Executes a BigQuery SQL query and returns results as markdown, with cache in front."""
    logger.info("=" * 80)
    logger.info("🔵 run_bigquery called")
    logger.info("SQL to execute:\n%s", query)
    logger.info("=" * 80)

    try:
        # ✅ Cache FIRST (before BQClient is created)
        cs = CacheService()

        # Prefer intent_key (parsed_intent-based) if provided
        effective_intent_key = intent_key or normalize_intent_key(sql=query)
        logger.info(f"🔵 Cache key: {effective_intent_key[:200]}")

        # Runner connects to BQ ONLY when needed
        def _runner(sql: str):
            logger.info("🔵 _runner creating BQClient (only on cache miss)...")
            bq = BQClient()

            logger.info("🔵 _runner executing query...")
            it = bq.execute_query(sql, 'adk_query')

            logger.info("✅ Query executed, converting to dataframe...")
            df = it.to_dataframe()
            logger.info(f"✅ DataFrame created with {len(df)} rows")
            return df.to_dict(orient='records')

        rows, from_cache = cs.run_or_cache(
            intent_key=effective_intent_key,
            sql=query,
            run_bigquery_fn=_runner
        )

        df_out = pd.DataFrame(rows)
        markdown = df_out.to_markdown(index=False) if not df_out.empty else ""

        result = {
            "status": "ok",
            "result": markdown,
            "message": None,
            "row_count": len(rows),
            "executed_sql": query,
            "from_cache": from_cache,
        }

        logger.info(f"✅ run_bigquery completed (rows={len(rows)}, from_cache={from_cache})")
        logger.info("=" * 80)
        return result

    except Exception as e:
        logger.exception("❌ BigQuery execution failed")
        return {
            "status": "error",
            "result": None,
            "message": f"BigQuery execution error: {e}",
            "executed_sql": query,
        }


def query_executor_agent(previous_output: dict) -> dict:
    """
    Executes SQL query from the previous agent's output.
    Expects optional built_query['intent_key'] provided by RootAgent (parsed_intent-based).
    """
    logger.info("🟢" * 40)
    logger.info("🟢 query_executor_agent (Python function) called")
    logger.info(f"🟢 Input type: {type(previous_output)}")
    logger.info(f"🟢 Input: {json.dumps(previous_output, indent=2) if isinstance(previous_output, dict) else previous_output}")

    try:
        if isinstance(previous_output, str):
            previous_output = json.loads(previous_output)

        built_query = previous_output.get("built_query", previous_output)

        status = built_query.get("status")
        if status != "ok":
            return {
                "status": "error",
                "result": None,
                "message": "SQL cannot be executed because status is not ok."
            }

        sql = built_query.get("sql")
        if not sql:
            return {
                "status": "error",
                "result": None,
                "message": "No SQL found in built_query"
            }

        # ✅ Intent key from RootAgent (parsed_intent-based)
        intent_key = built_query.get("intent_key")
        if intent_key:
            logger.info("🟢 Using intent_key provided by RootAgent (parsed_intent-based).")
        else:
            logger.warning("🟡 No intent_key provided; falling back to SQL-based key.")

        return run_bigquery(sql, intent_key=intent_key)

    except Exception as e:
        logger.exception("❌ query_executor_agent failed")
        return {
            "status": "error",
            "result": None,
            "message": f"Query executor error: {e}"
        }