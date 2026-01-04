# from typing import AsyncGenerator
# import logging
# import json

# from google.adk.agents import BaseAgent
# from google.adk.events import Event
# from google.genai import types

# logger = logging.getLogger(__name__)


# def _text_event(msg: str) -> Event:
#     """Helper: convert plain text into ADK Event."""
#     return Event(
#         author="assistant",
#         content=types.Content(parts=[types.Part(text=msg)])
#     )


# class ReactVisualizationAgent(BaseAgent):
#     """
#     ADK React Visualization Agent.
    
#     מטרה:
#     - קוראת את JSON של אנומליות מה-state
#     - בונה React component definition
#     - מחזירה לADK כדי שירנדר גרף אינטראקטיבי
#     """

#     def __init__(self):
#         super().__init__(name="react_visual_agent")

#     async def _run_async_impl(self, context) -> AsyncGenerator[Event, None]:
#         yield _text_event("🚨 REACT VISUAL AGENT WAS CALLED 🚨")
#         """
#         מריצה ממשק ויזואליזציה ל-ADK.
#         """
#         state = context.session.state
        
#         # ============================================================
#         # STEP 1 — משיכת תוצאות האנומליות מה-state
#         # ============================================================
#         anomaly_result = state.get("anomaly_result")
#         timeseries = state.get("anomaly_timeseries")
#         timeseries_multi = state.get("anomaly_timeseries_multi") or state.get("anomaly_timeseries")
#         series_defs_state = state.get("anomaly_series_defs") or []
#         table_markdown = state.get("anomaly_table_markdown") or ""
        
#         if not anomaly_result:
#             yield _text_event("⚠️ אין נתוני אנומליות להצגה. אנא הרץ סוכן אנומליות קודם.")
#             return
        
#         # Parse the JSON if it's a string
#         if isinstance(anomaly_result, str):
#             try:
#                 anomaly_data = json.loads(anomaly_result)
#             except json.JSONDecodeError:
#                 yield _text_event("❌ שגיאה בעיבוד נתוני אנומליות.")
#                 return
#         else:
#             anomaly_data = anomaly_result
        
#         # ============================================================
#         # STEP 2 — בדיקה אם יש אנומליות בכלל
#         # ============================================================
#         anomalies = anomaly_data.get("anomalies", [])
#         # זמנית לדיבוג
#         yield _text_event(f"DEBUG anomalies count = {len(anomalies)}")
        
#         if not anomalies:
#             # If no anomalies, but we have timeseries, render it as the main chart
#             if isinstance(timeseries, list) and timeseries:
#                 chart_data = []
#                 try:
#                     for p in timeseries:
#                         chart_data.append({
#                             "hour": str(p.get("hour", "")),
#                             "clicks": float(p.get("clicks", 0) or 0),
#                             "baseline": float(p.get("baseline", 0) or 0),
#                             "source": p.get("source", "All"),
#                             "type": p.get("type", "baseline")
#                         })
#                 except Exception:
#                     chart_data = []

#                 stats = {"total": 0, "spike_count": 0, "drop_count": 0, "max_deviation": 0}
#                 react_component = {
#                     "component": "AnomalyVisualizationDashboard",
#                     "props": {
#                         "chartData": chart_data,
#                         "anomalies": [],
#                         "stats": stats,
#                         "title": "זיהוי אנומליות בקליקים"
#                     }
#                 }
#                 json_str = json.dumps(react_component, ensure_ascii=False)
#                 yield _text_event(f"__REACT_COMPONENT__{json_str}")
#                 return
#             # No anomalies and no timeseries → render an empty dashboard
#             yield _text_event("✅ לא נמצאו אנומליות בנתונים. מציגה דשבורד ריק לתצוגה.")
#             chart_data = []
#             stats = {"total": 0, "spike_count": 0, "drop_count": 0, "max_deviation": 0}
#             react_component = {
#                 "component": "AnomalyVisualizationDashboard",
#                 "props": {
#                     "chartData": chart_data,
#                     "anomalies": [],
#                     "stats": stats,
#                     "title": "זיהוי אנומליות בקליקים"
#                 }
#             }
#             json_str = json.dumps(react_component, ensure_ascii=False)
#             yield _text_event(f"__REACT_COMPONENT__{json_str}")
#             return
        
#         # ============================================================
#         # STEP 3 — בניית הנתונים עבור הגרף
#         # ============================================================
#         # Prefer a full timeseries for the chart if available
#         chart_data = []
#         try:
#             # Multi-series (points contain multiple keys)
#             used_multi = isinstance(timeseries_multi, list) and len(timeseries_multi) > 0
#             if used_multi:
#                 chart_data = []
#                 for p in timeseries_multi:
#                         # Sanitize values to be non-negative numbers
#                         safe_values = {}
#                         for k, v in p.items():
#                             if k in ("hour","source","type"):
#                                 continue
#                             try:
#                                 num = float(v)
#                                 if not (num == num):  # NaN check
#                                     num = 0.0
#                                 if num < 0:
#                                     num = 0.0
#                                 safe_values[k] = num
#                             except Exception:
#                                 safe_values[k] = 0.0
#                         chart_data.append({
#                         "hour": str(p.get("hour", "")),
#                             # Copy over sanitized series values
#                             **safe_values
#                     })
#             else:
#                 chart_data = self._build_chart_data(anomalies)
#         except Exception:
#             chart_data = self._build_chart_data(anomalies)
#         stats = self._calculate_stats(anomalies)
        
#         # ============================================================
#         # STEP 4 — בניית קומפוננט React
#         # ============================================================
#         # Use series definitions only when multi-series data is present
#         series_defs_to_use = series_defs_state if 'chart_data' in locals() and isinstance(timeseries_multi, list) and len(timeseries_multi) > 0 else []

#         # Filter series definitions to only keys present in chartData
#         # keys_present = set()
#         # if chart_data:
#         #     for k, v in chart_data[0].items():
#         #         if k != "hour":
#         #             keys_present.add(k)
#         # filtered_series = [s for s in (series_defs_state or []) if s.get("key") in keys_present]
#         keys_present = set()
#         for p in (chart_data or []):
#             for k in p.keys():
#                 if k != "hour":
#                     keys_present.add(k)

#         filtered_series = [
#             s for s in (series_defs_state or [])
#             if s.get("key") in keys_present
#         ]
#         react_component = {
#             "component": "AnomalyVisualizationDashboard",
#             "props": {
#                 "chartData": chart_data,
#                 "anomalies": anomalies,
#                 "stats": stats,
#                 "title": "זיהוי אנומליות בקליקים",
#                 "chartConfig": {
#                     "height": 400,
#                     "series": filtered_series
#                 },
#                 "tableMarkdown": table_markdown
#             }
#         }
        
#         # ============================================================
#         # STEP 5 — שליחה ל-frontend כ-JSON string מסומן
#         # ============================================================
#         # נשלח כטקסט עם סימן מיוחד שה-frontend יזהה
#         json_str = json.dumps(react_component, ensure_ascii=False)
#         yield _text_event(f"__REACT_COMPONENT__{json_str}")
        
#         return

#     def _build_chart_data(self, anomalies: list) -> list:
#         """
#         המרת רשימת אנומליות לפורמט שהגרף מבין.
        
#         Input:
#         [
#             {"name": "media_source_123", "event_hour": 10, "clicks": 100, "avg_clicks": 50},
#             ...
#         ]
        
#         Output:
#         [
#             {"hour": 10, "clicks": 100, "baseline": 50, "source": "media_source_123"},
#             ...
#         ]
#         """
#         data = []
#         for anomaly in anomalies:
#             data.append({
#                 # "hour": anomaly.get("event_hour", 0),
#                 "hour": str(anomaly.get("event_hour", "")), # כדאי להפוך תמיד לסטרינג
#                 "clicks": anomaly.get("clicks", 0),
#                 # "baseline": anomaly.get("avg_clicks", 0),
#                 "baseline": float(anomaly["avg_clicks"]) if anomaly.get("avg_clicks") is not None else 0, # אנומליות עם נתונים חסרים
#                 "source": anomaly.get("name", "Unknown"),
#                 "type": anomaly.get("anomaly_type", "unknown")
#             })
        
#         # מיון לפי שעה
#         # data.sort(key=lambda x: x["hour"])
#         data.sort(key=lambda x: int(x["hour"])) # אחרי שהפכנו לסטרינג צריך למיין בהתאם
#         return data

#     def _calculate_stats(self, anomalies: list) -> dict:
#         """
#         חישוב סטטיסטיקה בסיסית על האנומליות.
#         """
#         if not anomalies:
#             return {"total": 0, "spike_count": 0, "drop_count": 0, "max_deviation": 0}
        
#         spikes = [a for a in anomalies if a.get("anomaly_type") == "click_spike"]
#         drops = [a for a in anomalies if a.get("anomaly_type") == "click_drop"]
        
#         max_deviation = 0
#         for a in anomalies:
#             clicks = a.get("clicks")
#             baseline = a.get("avg_clicks")
#             # הגנה מ-None
#             if clicks is None or baseline is None:
#                 continue
#             deviation = abs(float(clicks) - float(baseline))
#             if deviation > max_deviation:
#                 max_deviation = deviation
        
#         return {
#             "total": len(anomalies),
#             "spike_count": len(spikes),
#             "drop_count": len(drops),
#             "max_deviation": max_deviation
#         }

#     def _build_react_component(self, chart_data: list, anomalies: list, stats: dict) -> dict:
#         """
#         בניית component definition שה-ADK ירנדר כ-React.
        
#         זה לא קוד React בעצמו, אלא JSON שמתאר מה להציג.
#         ADK יזהה את זה ויביא React component בצד שלו שמרנדר את הנתונים.
#         """
#         return {
#             "type": "react_component",
#             "name": "AnomalyVisualizationDashboard",
#             "props": {
#                 # נתונים עבור הגרף
#                 "chartData": chart_data,
#                 "anomalies": anomalies,
                
#                 # סטטיסטיקה לתצוגה
#                 "stats": stats,
                
#                 # תצורה בסיסית
#                 "title": "📊 זיהוי אנומליות בקליקים",
#                 # "description": f"נמצאו {stats['total']} אנומליות: {stats['spike_count']} ספיקים, {stats['drop_count']} ירידות",
#                 "description": f"נמצאו {stats['total']} אנומליות (Spike בלבד)",
                
#                 # צבעים לשימוש בגרף
#                 "colors": {
#                     "spike": "#FF6B6B",      # אדום - לספיקים
#                     "drop": "#4ECDC4",       # טורקיז - לירידות
#                     "baseline": "#95E1D3",   # ירוק בהיר - baseline
#                     "line": "#4285F4"        # כחול - קו הנתונים
#                 },
                
#                 # אפשרויות הגרף
#                 "chartConfig": {
#                     "width": 800,
#                     "height": 400,
#                     "showLegend": True,
#                     "showTooltip": True,
#                     "interactive": True
#                 }
#             }
#         }


# # Instance for easy import in RootAgent
# react_visual_agent = ReactVisualizationAgent()

from typing import AsyncGenerator
import logging
import json
from datetime import datetime

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
    - קוראת תוצאות מה-state
    - שולחת ל-frontend JSON שמרנדר AnomalyVisualizationDashboard
    - תומכת גם ב: rows רחבים עם עמודות h_YYYYMMDD_HH (Pivot ב-frontend)
    """

    def __init__(self):
        super().__init__(name="react_visual_agent")

    async def _run_async_impl(self, context) -> AsyncGenerator[Event, None]:
        yield _text_event("🚨 REACT VISUAL AGENT WAS CALLED 🚨")

        state = context.session.state
        execution_result = state.get("execution_result") or {}

        raw_rows = (
            state.get("anomaly_rows")
            or state.get("anomaly_raw_rows")
            or state.get("execution_rows")
            or state.get("query_rows")
            or state.get("bq_rows")
            or state.get("anomaly_table_rows")
            or execution_result.get("rows")   # ✅ חשוב: רק אם אין אחרים
            or []
        )

        yield _text_event(f"DEBUG raw_rows type={type(raw_rows).__name__} len={len(raw_rows) if isinstance(raw_rows, list) else 'NA'}")


        # ============================================================
        # STEP 1 — משיכת תוצאות האנומליות מה-state
        # ============================================================
        anomaly_result = state.get("anomaly_result")
        timeseries = state.get("anomaly_timeseries")
        timeseries_multi = state.get("anomaly_timeseries_multi") or state.get("anomaly_timeseries")
        series_defs_state = state.get("anomaly_series_defs") or []
        table_markdown = state.get("anomaly_table_markdown") or ""

        if not anomaly_result:
            # אם אין anomaly_result אבל יש raw_rows – עדיין אפשר להציג גרף מהטבלה
            if isinstance(raw_rows, list) and raw_rows:
                react_component = {
                    "component": "AnomalyVisualizationDashboard",
                    "props": {
                        "rows": raw_rows,  # ✅ שולחים טבלה גולמית
                        "anomalies": [],
                        "stats": {"total": 0, "spike_count": 0, "drop_count": 0, "max_deviation": 0},
                        "title": "Clicks per hour"
                    }
                }
                json_str = json.dumps(react_component, ensure_ascii=False)
                yield _text_event(f"__REACT_COMPONENT__{json_str}")
                return

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
        yield _text_event(f"DEBUG anomalies count = {len(anomalies)}")

        # ✅ אם אין אנומליות:
        # - אם יש raw_rows (הטבלה הרחבה) -> נציג גרף מהטבלה (frontend יעשה mapping)
        # - אחרת ננסה timeseries
        if not anomalies:
            if isinstance(raw_rows, list) and raw_rows:
                stats = {"total": 0, "spike_count": 0, "drop_count": 0, "max_deviation": 0}
                react_component = {
                    "component": "AnomalyVisualizationDashboard",
                    "props": {
                        "rows": raw_rows,          # ✅ הכי חשוב: זה מה שיצייר גרף
                        "anomalies": [],
                        "stats": stats,
                        "title": "זיהוי אנומליות בקליקים (גרף מהטבלה)",
                        "tableMarkdown": table_markdown
                    }
                }
                json_str = json.dumps(react_component, ensure_ascii=False)
                yield _text_event(f"__REACT_COMPONENT__{json_str}")
                return

            # fallback: timeseries אם קיים
            if isinstance(timeseries, list) and timeseries:
                chart_data = []
                try:
                    for p in timeseries:
                        chart_data.append({
                            "hour": str(p.get("hour", "")),
                            "clicks": float(p.get("clicks", 0) or 0),
                            "baseline": float(p.get("baseline", 0) or 0),
                            "source": p.get("source", "All"),
                            "type": p.get("type", "baseline")
                        })
                except Exception:
                    chart_data = []

                stats = {"total": 0, "spike_count": 0, "drop_count": 0, "max_deviation": 0}
                react_component = {
                    "component": "AnomalyVisualizationDashboard",
                    "props": {
                        "chartData": chart_data,
                        "anomalies": [],
                        "stats": stats,
                        "title": "זיהוי אנומליות בקליקים",
                        "tableMarkdown": table_markdown
                    }
                }
                json_str = json.dumps(react_component, ensure_ascii=False)
                yield _text_event(f"__REACT_COMPONENT__{json_str}")
                return

            yield _text_event("✅ לא נמצאו אנומליות בנתונים. מציגה דשבורד ריק לתצוגה.")
            react_component = {
                "component": "AnomalyVisualizationDashboard",
                "props": {
                    "chartData": [],
                    "anomalies": [],
                    "stats": {"total": 0, "spike_count": 0, "drop_count": 0, "max_deviation": 0},
                    "title": "זיהוי אנומליות בקליקים",
                    "tableMarkdown": table_markdown
                }
            }
            json_str = json.dumps(react_component, ensure_ascii=False)
            yield _text_event(f"__REACT_COMPONENT__{json_str}")
            return

        # ============================================================
        # STEP 3 — בניית הנתונים עבור הגרף (כשיש anomalies)
        # ============================================================
        chart_data = []
        try:
            used_multi = isinstance(timeseries_multi, list) and len(timeseries_multi) > 0
            if used_multi:
                chart_data = []
                for p in timeseries_multi:
                    safe_values = {}
                    for k, v in p.items():
                        if k in ("hour", "source", "type"):
                            continue
                        try:
                            num = float(v)
                            if not (num == num):  # NaN check
                                num = 0.0
                            if num < 0:
                                num = 0.0
                            safe_values[k] = num
                        except Exception:
                            safe_values[k] = 0.0

                    chart_data.append({
                        "hour": str(p.get("hour", "")),
                        **safe_values
                    })
            else:
                chart_data = self._build_chart_data(anomalies)
        except Exception:
            chart_data = self._build_chart_data(anomalies)

        stats = self._calculate_stats(anomalies)

        # ============================================================
        # STEP 4 — בניית קומפוננט React
        # ============================================================
        keys_present = set()
        for p in (chart_data or []):
            for k in p.keys():
                if k != "hour":
                    keys_present.add(k)

        filtered_series = [
            s for s in (series_defs_state or [])
            if s.get("key") in keys_present
        ]

        react_component = {
            "component": "AnomalyVisualizationDashboard",
            "props": {
                "rows": raw_rows,  # ✅ תמיד שולחים את כל הנתונים לטבלה
                "chartData": chart_data,
                "anomalies": anomalies,
                "stats": stats,
                "title": "זיהוי אנומליות בקליקים",
                "chartConfig": {
                    "height": 400,
                    "series": filtered_series
                },
                "tableMarkdown": table_markdown
            }
        }

        json_str = json.dumps(react_component, ensure_ascii=False)
        yield _text_event(f"__REACT_COMPONENT__{json_str}")
        return

    def _build_chart_data(self, anomalies: list) -> list:
        """
        המרת רשימת אנומליות לפורמט שהגרף מבין.
        """
        data = []
        for anomaly in anomalies:
            data.append({
                "hour": str(anomaly.get("event_hour", "")),
                "clicks": anomaly.get("clicks", 0) or 0,
                "baseline": float(anomaly["avg_clicks"]) if anomaly.get("avg_clicks") is not None else 0,
                "source": anomaly.get("name", "Unknown"),
                "type": anomaly.get("anomaly_type", "unknown")
            })

        # ✅ תיקון מיון: hour יכול להיות ISO, לא תמיד מספר
        def sort_key(p):
            h = p.get("hour", "")
            # אם זה מספר
            try:
                return float(h)
            except Exception:
                pass
            # אם זה תאריך ISO
            try:
                return datetime.fromisoformat(h.replace("Z", "+00:00")).timestamp()
            except Exception:
                return 0

        data.sort(key=sort_key)
        return data

    def _calculate_stats(self, anomalies: list) -> dict:
        if not anomalies:
            return {"total": 0, "spike_count": 0, "drop_count": 0, "max_deviation": 0}

        spikes = [a for a in anomalies if a.get("anomaly_type") == "click_spike"]
        drops = [a for a in anomalies if a.get("anomaly_type") == "click_drop"]

        max_deviation = 0
        for a in anomalies:
            clicks = a.get("clicks")
            baseline = a.get("avg_clicks")
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


# Instance for easy import in RootAgent
react_visual_agent = ReactVisualizationAgent()
