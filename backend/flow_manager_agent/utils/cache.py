# import json
# from datetime import datetime, timezone, timedelta
# from google.cloud import bigquery
# import logging

# logger = logging.getLogger(__name__)


# def _normalize_numbers(obj):
#     """
#     מעבר רקורסיבי על כל ה-JSON:
#     - "3" -> 3
#     """
#     if isinstance(obj, dict):
#         return {k: _normalize_numbers(v) for k, v in obj.items()}

#     if isinstance(obj, list):
#         return [_normalize_numbers(x) for x in obj]

#     if isinstance(obj, str):
#         s = obj.strip()
#         if s.isdigit():
#             return int(s)
#         return s

#     return obj


# def normalize_intent_key(
#     parsed_intent: dict | None = None,
#     user_message: str | None = None,
#     sql: str | None = None,
#     default_scope: str = "time_bounded",
# ) -> str:
#     """
#     בונה intent_key יציב ואחיד.

#     עדיפות:
#     1) SQL מנורמל (רווחים)
#     2) parsed_intent מנורמל (כולל scope, מספרים)
#     3) user_message
#     """

#     if sql and sql.strip():
#         normalized_sql = " ".join(sql.strip().split())
#         return normalized_sql

#     base = parsed_intent or {}
#     if isinstance(base, dict) and base:
#         normalized = dict(base)

#         scope = normalized.get("scope")
#         if scope in (None, "", []):
#             normalized["scope"] = default_scope

#         normalized = _normalize_numbers(normalized)

#         return json.dumps(normalized, sort_keys=True, ensure_ascii=False).strip()

#     if user_message and user_message.strip():
#         return user_message.strip()

#     return ""


# class CacheService:
#     """
#     Cache מבוסס BigQuery.
#     טבלה: practicode-2025.cache.cached_queries

#     שדות:
#       intent_key   (STRING)
#       sql          (STRING)
#       result       (STRING, nullable)  # JSON string של rows
#       last_updated (TIMESTAMP, nullable)
#       use_count    (INT64)
#     """

#     TTL = timedelta(seconds=300)
#     MAX_COUNT = 3

#     def __init__(self):
#         self.project = "practicode-2025"
#         self.dataset = "cache"
#         self.table = "cached_queries"
#         self.client = bigquery.Client(project=self.project, location="EU")

#     # -------------------------------------------------------
#     # Public: בדיקה אם יש תשובה בקאש (רק אם use_count==3 ו TTL בתוקף)
#     # -------------------------------------------------------
#     def get_valid_cached_result(self, intent_key: str):
#         """
#         מחזירה dict עם rows/sql/row_count אם:
#           - יש result
#           - use_count == 3 (אצלנו capped ל-3)
#           - TTL בתוקף
#           - JSON תקין
#         אחרת None
#         """
#         entry = self._load_entry(intent_key)
#         if not entry:
#             return None

#         use_count = int(entry.get("use_count") or 0)
#         if use_count < self.MAX_COUNT:
#             return None

#         result_json = entry.get("result")
#         if not result_json:
#             return None

#         last_updated = entry.get("last_updated")
#         if not last_updated:
#             return None

#         if last_updated.tzinfo is None:
#             last_updated = last_updated.replace(tzinfo=timezone.utc)

#         now = datetime.now(timezone.utc)
#         if (now - last_updated) > self.TTL:
#             return None

#         try:
#             rows = json.loads(result_json)
#         except Exception:
#             return None

#         return {
#             "rows": rows,
#             "executed_sql": entry.get("sql") or "",
#             "row_count": len(rows),
#         }

#     # -------------------------------------------------------
#     # Public: Pipeline ראשי לפי הדרישה שלך
#     # -------------------------------------------------------
#     def run_or_cache(self, *, intent_key: str, sql: str, run_bigquery_fn):
#         """
#         אלגוריתם לפי הדרישה:

#         1) אם יש תשובה בקאש (use_count==3 + TTL) => מחזירים אותה (בלי להתחבר לביג)
#         2) אחרת:
#            - מגדילים use_count עד 3 בלבד (cap)
#            - מריצים BigQuery
#            - אם אחרי ההגדלה use_count==3 => שומרים result + last_updated
#            - אם עדיין <3 => לא שומרים result
#         """

#         cached = self.get_valid_cached_result(intent_key)
#         if cached is not None:
#             logger.info(f"[CACHE] HIT (TTL valid, use_count=3). key={intent_key[:80]}...")
#             return cached["rows"], True

#         now = datetime.now(timezone.utc)

#         # מעלה מונה capped ל-3
#         use_count = self._upsert_and_increment_capped(intent_key=intent_key, sql=sql)
#         logger.info(f"[CACHE] MISS. use_count(after increment, capped)={use_count}. key={intent_key[:80]}...")

#         # מריצים ביג (אין תשובה תקפה בקאש)
#         rows = run_bigquery_fn(sql)
#         safe_rows = self._make_json_safe(rows)

#         # שומרים תוצאה רק אם הגענו ל-3
#         if use_count >= self.MAX_COUNT:
#             logger.info("[CACHE] Reached 3rd ask => saving result + last_updated (count capped at 3).")
#             self._save_result(intent_key=intent_key, sql=sql, rows=safe_rows, now=now)
#         else:
#             logger.info("[CACHE] Warming (<3) => NOT saving result (only count updated).")

#         return safe_rows, False

#     # -------------------------------------------------------
#     # INTERNALS
#     # -------------------------------------------------------
#     def _load_entry(self, intent_key: str):
#         query = f"""
#             SELECT intent_key, sql, result, last_updated, use_count
#             FROM `{self.project}.{self.dataset}.{self.table}`
#             WHERE intent_key = @key
#             LIMIT 1
#         """

#         job = self.client.query(
#             query,
#             job_config=bigquery.QueryJobConfig(
#                 query_parameters=[bigquery.ScalarQueryParameter("key", "STRING", intent_key)]
#             ),
#         )

#         rows = list(job)
#         return dict(rows[0]) if rows else None

#     def _upsert_and_increment_capped(self, *, intent_key: str, sql: str) -> int:
#         """
#         מעלה use_count עד 3 בלבד (cap), בלי לגעת ב-last_updated/result.
#         אם אין רשומה — יוצר use_count=1.
#         מחזיר את הערך בפועל אחרי העדכון.
#         """
#         merge_sql = f"""
#             MERGE `{self.project}.{self.dataset}.{self.table}` T
#             USING (SELECT @key AS intent_key, @sql AS sql) S
#             ON T.intent_key = S.intent_key
#             WHEN MATCHED THEN
#               UPDATE SET
#                 use_count = LEAST(IFNULL(T.use_count, 0) + 1, {self.MAX_COUNT}),
#                 sql = S.sql
#             WHEN NOT MATCHED THEN
#               INSERT (intent_key, sql, result, last_updated, use_count)
#               VALUES (S.intent_key, S.sql, CAST(NULL AS STRING), CAST(NULL AS TIMESTAMP), 1)
#         """

#         job_config = bigquery.QueryJobConfig(
#             query_parameters=[
#                 bigquery.ScalarQueryParameter("key", "STRING", intent_key),
#                 bigquery.ScalarQueryParameter("sql", "STRING", sql),
#             ]
#         )

#         self.client.query(merge_sql, job_config=job_config).result()

#         entry = self._load_entry(intent_key)
#         return int(entry.get("use_count") or 0) if entry else 0

#     def _save_result(self, *, intent_key: str, sql: str, rows, now: datetime):
#         json_string = json.dumps(rows, ensure_ascii=False)

#         update_sql = f"""
#             UPDATE `{self.project}.{self.dataset}.{self.table}`
#             SET
#                 result = @res,
#                 last_updated = @ts,
#                 sql = @sql,
#                 use_count = {self.MAX_COUNT}
#             WHERE intent_key = @key
#         """

#         job_config = bigquery.QueryJobConfig(
#             query_parameters=[
#                 bigquery.ScalarQueryParameter("res", "STRING", json_string),
#                 bigquery.ScalarQueryParameter("ts", "TIMESTAMP", now.isoformat()),
#                 bigquery.ScalarQueryParameter("sql", "STRING", sql),
#                 bigquery.ScalarQueryParameter("key", "STRING", intent_key),
#             ]
#         )

#         self.client.query(update_sql, job_config=job_config).result()

#     def _make_json_safe(self, result_list):
#         from datetime import datetime as _dt

#         def fix(v):
#             return v.isoformat() if isinstance(v, _dt) else v

#         return [{k: fix(v) for k, v in row.items()} for row in result_list]

import json
from datetime import datetime, timezone, timedelta
from google.cloud import bigquery
import logging

logger = logging.getLogger(__name__)


def _normalize_numbers(obj):
    """
    מעבר רקורסיבי על כל ה-JSON:
    - "3" -> 3
    """
    if isinstance(obj, dict):
        return {k: _normalize_numbers(v) for k, v in obj.items()}

    if isinstance(obj, list):
        return [_normalize_numbers(x) for x in obj]

    if isinstance(obj, str):
        s = obj.strip()
        if s.isdigit():
            return int(s)
        return s

    return obj


def normalize_intent_key(
    parsed_intent: dict | None = None,
    user_message: str | None = None,
    sql: str | None = None,
    default_scope: str = "time_bounded",
) -> str:
    """
    בונה intent_key יציב ואחיד.

    עדיפות:
    1) SQL מנורמל (רווחים)
    2) parsed_intent מנורמל (כולל scope, מספרים)
    3) user_message
    """

    if sql and sql.strip():
        normalized_sql = " ".join(sql.strip().split())
        return normalized_sql

    base = parsed_intent or {}
    if isinstance(base, dict) and base:
        normalized = dict(base)

        scope = normalized.get("scope")
        if scope in (None, "", []):
            normalized["scope"] = default_scope

        normalized = _normalize_numbers(normalized)

        return json.dumps(normalized, sort_keys=True, ensure_ascii=False).strip()

    if user_message and user_message.strip():
        return user_message.strip()

    return ""


class CacheService:
    """
    Cache מבוסס BigQuery.
    טבלה: practicode-2025.cache.cached_queries

    שדות:
      intent_key   (STRING)
      sql          (STRING)
      result       (STRING, nullable)  # JSON string של rows
      last_updated (TIMESTAMP, nullable)
      use_count    (INT64)
    """

    TTL = timedelta(seconds=300)
    MAX_COUNT = 3

    def __init__(self):
        self.project = "practicode-2025"
        self.dataset = "cache"
        self.table = "cached_queries"
        self.client = bigquery.Client(project=self.project, location="EU")

    # -------------------------------------------------------
    # Public: בדיקה אם יש תשובה בקאש (רק אם use_count==3 ו TTL בתוקף)
    # -------------------------------------------------------
    def get_valid_cached_result(self, intent_key: str):
        """
        מחזירה dict עם rows/sql/row_count אם:
          - יש result
          - use_count == 3 (אצלנו capped ל-3)
          - TTL בתוקף
          - JSON תקין
        אחרת None
        """
        entry = self._load_entry(intent_key)
        if not entry:
            return None

        use_count = int(entry.get("use_count") or 0)
        if use_count < self.MAX_COUNT:
            return None

        result_json = entry.get("result")
        if not result_json:
            return None

        last_updated = entry.get("last_updated")
        if not last_updated:
            return None

        if last_updated.tzinfo is None:
            last_updated = last_updated.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        if (now - last_updated) > self.TTL:
            return None

        try:
            rows = json.loads(result_json)
        except Exception:
            return None

        return {
            "rows": rows,
            "executed_sql": entry.get("sql") or "",
            "row_count": len(rows),
        }

    # -------------------------------------------------------
    # Public: Pipeline ראשי לפי הדרישה שלך
    # -------------------------------------------------------
    def run_or_cache(self, *, intent_key: str, sql: str, run_bigquery_fn):
        """
        אלגוריתם לפי הדרישה:

        1) אם יש תשובה בקאש (use_count==3 + TTL) => מחזירים אותה (בלי להתחבר לביג)
        2) אחרת:
           - מגדילים use_count עד 3 בלבד (cap)
           - מריצים BigQuery
           - אם אחרי ההגדלה use_count==3 => שומרים result + last_updated
           - אם עדיין <3 => לא שומרים result
        """

        cached = self.get_valid_cached_result(intent_key)
        if cached is not None:
            logger.info(f"[CACHE] HIT (TTL valid, use_count=3). key={intent_key[:80]}...")
            return cached["rows"], True

        now = datetime.now(timezone.utc)

        # מעלה מונה capped ל-3
        use_count = self._upsert_and_increment_capped(intent_key=intent_key, sql=sql)
        logger.info(f"[CACHE] MISS. use_count(after increment, capped)={use_count}. key={intent_key[:80]}...")

        # מריצים ביג (אין תשובה תקפה בקאש)
        rows = run_bigquery_fn(sql)
        safe_rows = self._make_json_safe(rows)

        # שומרים תוצאה רק אם הגענו ל-3
        if use_count >= self.MAX_COUNT:
            logger.info("[CACHE] Reached 3rd ask => saving result + last_updated (count capped at 3).")
            self._save_result(intent_key=intent_key, sql=sql, rows=safe_rows, now=now)
        else:
            logger.info("[CACHE] Warming (<3) => NOT saving result (only count updated).")

        return safe_rows, False

    # -------------------------------------------------------
    # INTERNALS
    # -------------------------------------------------------
    def _load_entry(self, intent_key: str):
        query = f"""
            SELECT intent_key, sql, result, last_updated, use_count
            FROM `{self.project}.{self.dataset}.{self.table}`
            WHERE intent_key = @key
            LIMIT 1
        """

        job = self.client.query(
            query,
            job_config=bigquery.QueryJobConfig(
                query_parameters=[bigquery.ScalarQueryParameter("key", "STRING", intent_key)]
            ),
        )

        rows = list(job)
        return dict(rows[0]) if rows else None

    def _upsert_and_increment_capped(self, *, intent_key: str, sql: str) -> int:
        """
        מעלה use_count עד 3 בלבד (cap), בלי לגעת ב-last_updated/result.
        אם אין רשומה — יוצר use_count=1.
        מחזיר את הערך בפועל אחרי העדכון.
        """
        merge_sql = f"""
            MERGE `{self.project}.{self.dataset}.{self.table}` T
            USING (SELECT @key AS intent_key, @sql AS sql) S
            ON T.intent_key = S.intent_key
            WHEN MATCHED THEN
              UPDATE SET
                use_count = LEAST(IFNULL(T.use_count, 0) + 1, {self.MAX_COUNT}),
                sql = S.sql
            WHEN NOT MATCHED THEN
              INSERT (intent_key, sql, result, last_updated, use_count)
              VALUES (S.intent_key, S.sql, CAST(NULL AS STRING), CAST(NULL AS TIMESTAMP), 1)
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("key", "STRING", intent_key),
                bigquery.ScalarQueryParameter("sql", "STRING", sql),
            ]
        )

        self.client.query(merge_sql, job_config=job_config).result()

        entry = self._load_entry(intent_key)
        return int(entry.get("use_count") or 0) if entry else 0

    def _save_result(self, *, intent_key: str, sql: str, rows, now: datetime):
        json_string = json.dumps(rows, ensure_ascii=False)

        update_sql = f"""
            UPDATE `{self.project}.{self.dataset}.{self.table}`
            SET
                result = @res,
                last_updated = @ts,
                sql = @sql,
                use_count = {self.MAX_COUNT}
            WHERE intent_key = @key
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("res", "STRING", json_string),
                bigquery.ScalarQueryParameter("ts", "TIMESTAMP", now.isoformat()),
                bigquery.ScalarQueryParameter("sql", "STRING", sql),
                bigquery.ScalarQueryParameter("key", "STRING", intent_key),
            ]
        )

        self.client.query(update_sql, job_config=job_config).result()

    def _make_json_safe(self, result_list):
        from datetime import datetime as _dt, date as _date

        def fix(v):
            if isinstance(v, _dt):
                return v.isoformat()
            if isinstance(v, _date):  # date (no time)
                return v.isoformat()
            return v

        return [{k: fix(v) for k, v in row.items()} for row in result_list]