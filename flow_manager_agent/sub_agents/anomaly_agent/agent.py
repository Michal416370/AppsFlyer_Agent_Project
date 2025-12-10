from typing import AsyncGenerator
from pathlib import Path
import logging
import json

from pydantic import PrivateAttr
from google.adk.agents import BaseAgent
from google.adk.events import Event
from google.genai import types

from bq import BQClient  # import מוחלט ויציב

logger = logging.getLogger(__name__)


def _text_event(msg: str) -> Event:
    """Helper: convert plain text into ADK Event."""
    return Event(
        author="assistant",
        content=types.Content(parts=[types.Part(text=msg)])
    )


# --- SQL loading ---
BASE_DIR = Path(__file__).parent
SPIKE_SQL = (BASE_DIR / "queries" / "spike_clicks.sql").read_text(encoding="utf-8")
DROP_SQL = (BASE_DIR / "queries" / "drop_clicks.sql").read_text(encoding="utf-8")


class AnomalyAgent(BaseAgent):
    """
    ADK anomaly agent.
    Returns JSON anomalies with name, clicks, avg_clicks (and event_hour).
    """

    _client: BQClient = PrivateAttr()

    def __init__(self):
        super().__init__(name="anomaly_agent")
        self._client = BQClient()

    def pull_data(self):
        logger.info("[AnomalyAgent] Pulling anomaly data from BQ")

        spike_df = self._client.execute_query(SPIKE_SQL, "anomaly_spike").to_dataframe()
        drop_df = self._client.execute_query(DROP_SQL, "anomaly_drop").to_dataframe()

        return {"spike": spike_df, "drop": drop_df}

    def detect_anomalies(self, results):
        """
        Keep dataframes here; convert to JSON in report().
        """
        anomalies = {}

        if not results["spike"].empty:
            anomalies["click_spike"] = results["spike"]

        if not results["drop"].empty:
            anomalies["click_drop"] = results["drop"]

        return anomalies

    def report(self, anomalies):
        """
        Convert DataFrames to JSON list:
        [
          { "name": "click_spike", "event_hour": 10, "clicks": 123, "avg_clicks": 50.5 },
          ...
        ]
        """
        if not anomalies:
            return {
                "status": "ok",
                "message": "לא נמצאו אנומליות.",
                "anomalies": []
            }

        json_anomalies = []
        for name, df in anomalies.items():
            # Expect columns: media_source, event_hour, clicks, avg_clicks, std_clicks
            for _, row in df.iterrows():
                json_anomalies.append({
                    "name": str(row["media_source"]),
                    "anomaly_type": name,
                    "event_hour": int(row["event_hour"]),
                    "clicks": int(row["clicks"]),
                    "avg_clicks": float(row["avg_clicks"]),
                })

        summary = f"נמצאו {len(json_anomalies)} אנומליות."
        return {
            "status": "ok",
            "message": summary,
            "anomalies": json_anomalies
        }

    def run_daily(self):
        data = self.pull_data()
        anomalies = self.detect_anomalies(data)
        return self.report(anomalies)

    async def _run_async_impl(self, context) -> AsyncGenerator[Event, None]:
        state = context.session.state

        res = self.run_daily()

        # לשמירה ב-state
        state["anomaly_result"] = res

        # 1) הודעת סיכום קצרה
        yield _text_event(res["message"])

        # 2) הדפסת ה-JSON למשתמש (יפה ומסודר)
        pretty_json = json.dumps(res, ensure_ascii=False, indent=2)
        yield _text_event(pretty_json)

        return


# instance for easy import in RootAgent
anomaly_agent = AnomalyAgent()
