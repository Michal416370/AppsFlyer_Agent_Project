import React from "react";
import AnomalyChart from "./AnomalyChart";

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
}

const AnomalyVisualizationDashboard: React.FC<Props> = ({
  chartData = [],
  anomalies = [],
  stats,
  title = "Anomaly Visualization",
  chartConfig = {}
}) => {
  const computedStats: Stats = {
    total: stats?.total ?? anomalies.length,
    spike_count: stats?.spike_count ?? anomalies.filter((a) => a.anomaly_type === "click_spike").length,
    drop_count: stats?.drop_count ?? anomalies.filter((a) => a.anomaly_type === "click_drop").length,
    max_deviation: stats?.max_deviation ?? 0
  };

  return (
    <div style={{ padding: 16 }}>
      <h3>{title}</h3>
      <div style={{ marginBottom: 8 }}>
        <strong>סה״כ אנומליות:</strong> {computedStats.total} &nbsp;
        <strong>ספיקים:</strong> {computedStats.spike_count} &nbsp;
        <strong>ירידות:</strong> {computedStats.drop_count}
      </div>
      <AnomalyChart data={chartData} anomalies={anomalies} config={chartConfig} />
    </div>
  );
};

export default AnomalyVisualizationDashboard;
