import React from "react";
import AnomalyChart from "./anomalyChart";
import "../styles/anomalyVisualizationDashboard.css";

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
  chartData?: ChartPoint[];
  anomalies?: Anomaly[];
  stats?: Partial<Stats>;
  title?: string;
  chartConfig?: { height?: number };
  tableMarkdown?: string;
}

const AnomalyVisualizationDashboard: React.FC<Props> = ({
  chartData = [],
  anomalies = [],
  stats,
  title = "Anomaly Visualization",
  chartConfig = {},
  tableMarkdown = ""
}) => {
  const computedStats: Stats = {
    total: stats?.total ?? anomalies.length,
    spike_count: stats?.spike_count ?? anomalies.filter((a) => a.anomaly_type === "click_spike").length,
    drop_count: stats?.drop_count ?? anomalies.filter((a) => a.anomaly_type === "click_drop").length,
    max_deviation: stats?.max_deviation ?? 0
  };

  return (
    <div className="anomaly-dashboard">
      <h2 className="anomaly-title">
        {title}
      </h2>

      {/* Stats Cards */}
      <div className="anomaly-stats-container">
        <div className="anomaly-stat-card total">
          <div className="anomaly-stat-label">
            סה״כ אנומליות
          </div>
          <div className="anomaly-stat-value">
            {computedStats.total}
          </div>
        </div>

        <div className="anomaly-stat-card spike">
          <div className="anomaly-stat-label">
            ספייקים ⬆️
          </div>
          <div className="anomaly-stat-value">
            {computedStats.spike_count}
          </div>
        </div>

        <div className="anomaly-stat-card drop">
          <div className="anomaly-stat-label">
            ירידות ⬇️
          </div>
          <div className="anomaly-stat-value">
            {computedStats.drop_count}
          </div>
        </div>
      </div>

      <AnomalyChart data={chartData} anomalies={anomalies} config={chartConfig} />

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
