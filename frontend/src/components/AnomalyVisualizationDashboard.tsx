import React from "react";
import { buildChartFromRows } from "./chartMapper";
import AnomalyChart from "./AnomalyChart";
import "../styles/anomalyVisualizationDashboard.css";

type RawRow = {
  media_source: string;
  anomaly_hour_ts?: string | null;
  [k: string]: any; // h_20251024_00 וכו'
};

export type Anomaly = {
  name: string;
  anomaly_type: string;
  event_hour?: string | number | null;
  clicks?: number | null;
  avg_clicks?: number | null;
};

export type ChartPoint = {
  hour: string;
  clicks: number;
  baseline?: number | null;
  source?: string;
  type?: string;
};

export type Stats = {
  total: number;
  spike_count: number;
  drop_count: number;
  max_deviation?: number;
};

interface Props {
  rows?: RawRow[]; // ✅ הטבלה המקורית
  chartData?: ChartPoint[]; // אופציונלי (אם כבר שולחים מוכן)
  anomalies?: Anomaly[];
  stats?: Partial<Stats>;
  title?: string;
  chartConfig?: { height?: number; series?: any[] };
  tableMarkdown?: string;
}

const AnomalyVisualizationDashboard: React.FC<Props> = ({
  rows = [],
  chartData = [],
  anomalies = [],
  stats,
  title = "Anomaly Visualization",
  chartConfig = {},
  tableMarkdown = ""
}) => {
  const mapped = rows.length ? buildChartFromRows(rows) : null;

  const finalChartData = mapped?.chartData ?? chartData;
  const finalAnomalies = mapped?.anomalies ?? anomalies;

  const finalChartConfig = {
    ...chartConfig,
    series: mapped?.series ?? (chartConfig as any)?.series
  };

  const seriesList: any[] = (finalChartConfig as any)?.series ?? [];

  const computedStats: Stats = {
    total: stats?.total ?? finalAnomalies.length,
    spike_count:
      stats?.spike_count ??
      finalAnomalies.filter((a) => a.anomaly_type === "click_spike").length,
    drop_count:
      stats?.drop_count ??
      finalAnomalies.filter((a) => a.anomaly_type === "click_drop").length,
    max_deviation: stats?.max_deviation ?? 0
  };

  return (
    <div className="anomaly-dashboard">
      <h2 className="anomaly-title">{title}</h2>

      {/* Stats Cards */}
      <div className="anomaly-stats-container">
        <div className="anomaly-stat-card total">
          <div className="anomaly-stat-label">סה״כ אנומליות</div>
          <div className="anomaly-stat-value">{computedStats.total}</div>
        </div>

        <div className="anomaly-stat-card spike">
          <div className="anomaly-stat-label">ספייקים ⬆️</div>
          <div className="anomaly-stat-value">{computedStats.spike_count}</div>
        </div>

        <div className="anomaly-stat-card drop">
          <div className="anomaly-stat-label">ירידות ⬇️</div>
          <div className="anomaly-stat-value">{computedStats.drop_count}</div>
        </div>
      </div>

      {/* ✅ Option 1: גרף נפרד לכל media_source */}
      {seriesList.length > 0 ? (
        <div style={{ display: "grid", gap: 16 }}>
          {seriesList.map((s: any) => (
            <div key={s.key} className="anomaly-chart-block">
              <h3 className="anomaly-chart-subtitle" style={{ margin: "8px 0" }}>
                {s.name}
              </h3>

              <AnomalyChart
                data={finalChartData}
                // אם יש לך anomalies אמיתיים לפי source/name, זה יסנן נכון.
                anomalies={finalAnomalies.filter((a) => a.name === s.name)}
                config={{
                  ...finalChartConfig,
                  height: 260,
                  series: [s]
                }}
              />
            </div>
          ))}
        </div>
      ) : (
        // fallback אם אין series (למשל במקרה של Clicks/Baseline)
        <AnomalyChart
          data={finalChartData}
          anomalies={finalAnomalies}
          config={finalChartConfig}
        />
      )}

      {tableMarkdown && (
        <div className="anomaly-table">
          <h3 className="anomaly-table-title">טבלת תצוגה</h3>
          <pre className="anomaly-table-content">{tableMarkdown}</pre>
        </div>
      )}
    </div>
  );
};

export default AnomalyVisualizationDashboard;
