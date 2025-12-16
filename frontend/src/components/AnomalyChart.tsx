import React from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceDot,
  Legend
} from "recharts";
import type { ChartPoint, Anomaly } from "./AnomalyVisualizationDashboard";

interface Props {
  data?: ChartPoint[];
  anomalies?: Anomaly[];
  config?: { height?: number };
}

const formatHour = (v: any) => {
  if (!v) return "";
  const s = String(v);
  if (s.includes("T")) return s.slice(11, 16);
  return s;
};

const AnomalyChart: React.FC<Props> = ({ data = [], anomalies = [], config = {} }) => {
  return (
    <div style={{ width: "100%", height: config.height ?? 360 }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid stroke="#eee" />
          <XAxis dataKey="hour" tickFormatter={formatHour} />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="clicks" stroke="#4285F4" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="baseline" stroke="#95E1D3" strokeWidth={1} strokeDasharray="4 4" dot={false} />
          {anomalies.map((a, i) => (
            <ReferenceDot
              key={i}
              x={String(a.event_hour ?? "")}
              y={a.clicks ?? 0}
              r={6}
              stroke={a.anomaly_type === "click_spike" ? "#FF6B6B" : "#4ECDC4"}
              fill={a.anomaly_type === "click_spike" ? "#FF6B6B" : "#4ECDC4"}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default AnomalyChart;
