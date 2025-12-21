from typing import AsyncGenerator
import logging
import json

from google.adk.agents import BaseAgent
from google.adk.events import Event
from google.genai import types

logger = logging.getLogger(__name__)


def _text_event(msg: str) -> Event:
    """Helper: convert plain text into ADK Event."""
    return Event(
        author="assistant",
        content=types.Content(parts=[types.Part(text=msg)])
    )


class ReactVisualizationAgent(BaseAgent):
    """
    ADK React Visualization Agent.
    
    מטרה:
    - קוראת את JSON של אנומליות מה-state
    - בונה React component definition
    - מחזירה לADK כדי שירנדר גרף אינטראקטיבי
    """

    def __init__(self):
        super().__init__(name="react_visual_agent")

    async def _run_async_impl(self, context) -> AsyncGenerator[Event, None]:
        """
        מריצה ממשק ויזואליזציה ל-ADK.
        """
        state = context.session.state
        
        # ============================================================
        # STEP 1 — משיכת תוצאות האנומליות מה-state
        # ============================================================
        anomaly_result = state.get("anomaly_result")
        
        if not anomaly_result:
            yield _text_event("⚠️ אין נתוני אנומליות להצגה. אנא הרץ סוכן אנומליות קודם.")
            return
        
        # Parse the JSON if it's a string
        if isinstance(anomaly_result, str):
            try:
                anomaly_data = json.loads(anomaly_result)
            except json.JSONDecodeError:
                yield _text_event("❌ שגיאה בעיבוד נתוני אנומליות.")
                return
        else:
            anomaly_data = anomaly_result
        
        # ============================================================
        # STEP 2 — בדיקה אם יש אנומליות בכלל
        # ============================================================
        anomalies = anomaly_data.get("anomalies", [])
        
        if not anomalies:
            yield _text_event("✅ לא נמצאו אנומליות בנתונים.")
            return
        
        # ============================================================
        # STEP 3 — בניית הנתונים עבור הגרף
        # ============================================================
        chart_data = self._build_chart_data(anomalies)
        stats = self._calculate_stats(anomalies)
        
        # ============================================================
        # STEP 4 — בניית קומפוננט React
        # ============================================================
        react_component = {
            "component": "AnomalyVisualizationDashboard",
            "props": {
                "chartData": chart_data,
                "anomalies": anomalies,
                "stats": stats,
                "title": "זיהוי אנומליות בקליקים"
            }
        }
        
        # ============================================================
        # STEP 5 — שליחה ל-frontend כ-JSON string מסומן
        # ============================================================
        # נשלח כטקסט עם סימן מיוחד שה-frontend יזהה
        json_str = json.dumps(react_component, ensure_ascii=False)
        yield _text_event(f"__REACT_COMPONENT__{json_str}")
        
        return

    def _build_chart_data(self, anomalies: list) -> list:
        """
        המרת רשימת אנומליות לפורמט שהגרף מבין.
        
        Input:
        [
            {"name": "media_source_123", "event_hour": 10, "clicks": 100, "avg_clicks": 50},
            ...
        ]
        
        Output:
        [
            {"hour": 10, "clicks": 100, "baseline": 50, "source": "media_source_123"},
            ...
        ]
        """
        data = []
        for anomaly in anomalies:
            data.append({
                # "hour": anomaly.get("event_hour", 0),
                "hour": str(anomaly.get("event_hour", "")), # כדאי להפוך תמיד לסטרינג
                "clicks": anomaly.get("clicks", 0),
                # "baseline": anomaly.get("avg_clicks", 0),
                "baseline": float(anomaly["avg_clicks"]) if anomaly.get("avg_clicks") is not None else 0, # אנומליות עם נתונים חסרים
                "source": anomaly.get("name", "Unknown"),
                "type": anomaly.get("anomaly_type", "unknown")
            })
        
        # מיון לפי שעה
        # data.sort(key=lambda x: x["hour"])
        data.sort(key=lambda x: int(x["hour"])) # אחרי שהפכנו לסטרינג צריך למיין בהתאם
        return data

    def _calculate_stats(self, anomalies: list) -> dict:
        """
        חישוב סטטיסטיקה בסיסית על האנומליות.
        """
        if not anomalies:
            return {"total": 0, "spike_count": 0, "drop_count": 0, "max_deviation": 0}
        
        spikes = [a for a in anomalies if a.get("anomaly_type") == "click_spike"]
        drops = [a for a in anomalies if a.get("anomaly_type") == "click_drop"]
        
        max_deviation = 0
        for a in anomalies:
            clicks = a.get("clicks")
            baseline = a.get("avg_clicks")
            # הגנה מ-None
            if clicks is None or baseline is None:
                continue
            deviation = abs(float(clicks) - float(baseline))
            if deviation > max_deviation:
                max_deviation = deviation
        
        return {
            "total": len(anomalies),
            "spike_count": len(spikes),
            "drop_count": len(drops),
            "max_deviation": max_deviation
        }

    def _build_react_component(self, chart_data: list, anomalies: list, stats: dict) -> dict:
        """
        בניית component definition שה-ADK ירנדר כ-React.
        
        זה לא קוד React בעצמו, אלא JSON שמתאר מה להציג.
        ADK יזהה את זה ויביא React component בצד שלו שמרנדר את הנתונים.
        """
        return {
            "type": "react_component",
            "name": "AnomalyVisualizationDashboard",
            "props": {
                # נתונים עבור הגרף
                "chartData": chart_data,
                "anomalies": anomalies,
                
                # סטטיסטיקה לתצוגה
                "stats": stats,
                
                # תצורה בסיסית
                "title": "📊 זיהוי אנומליות בקליקים",
                # "description": f"נמצאו {stats['total']} אנומליות: {stats['spike_count']} ספיקים, {stats['drop_count']} ירידות",
                "description": f"נמצאו {stats['total']} אנומליות (Spike בלבד)",
                
                # צבעים לשימוש בגרף
                "colors": {
                    "spike": "#FF6B6B",      # אדום - לספיקים
                    "drop": "#4ECDC4",       # טורקיז - לירידות
                    "baseline": "#95E1D3",   # ירוק בהיר - baseline
                    "line": "#4285F4"        # כחול - קו הנתונים
                },
                
                # אפשרויות הגרף
                "chartConfig": {
                    "width": 800,
                    "height": 400,
                    "showLegend": True,
                    "showTooltip": True,
                    "interactive": True
                }
            }
        }


# Instance for easy import in RootAgent
react_visual_agent = ReactVisualizationAgent()