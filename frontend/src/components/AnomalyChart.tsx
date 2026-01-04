import React from "react";
import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceDot,
  Legend
} from "recharts";
import type { ChartPoint, Anomaly } from "./anomalyVisualizationDashboard";
import "../styles/anomalyChart.css";

interface SeriesDef { key: string; name: string; color?: string }
interface Props {
  data?: ChartPoint[];
  anomalies?: Anomaly[];
  config?: { height?: number; series?: SeriesDef[] };
}

const formatHour = (v: any) => {
  if (!v) return "";
  const s = String(v);
  if (s.includes("T")) return s.slice(11, 16);
  return s;
};

// Custom Tooltip מעוצב
const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload || !payload.length) return null;

  return (
    <div className="anomaly-tooltip">
      <p className="anomaly-tooltip-label">
        {formatHour(label)}
      </p>
      {payload.map((entry: any, index: number) => (
        <div key={index} className="anomaly-tooltip-item-wrapper">
          <p className="anomaly-tooltip-item">
            <span className="anomaly-tooltip-name">{entry.name}:</span>{" "}
            <span className="anomaly-tooltip-value" data-series={entry.name.toLowerCase()}>
              {entry.value?.toLocaleString()}
            </span>
          </p>
        </div>
      ))}
    </div>
  );
};

const AnomalyChart: React.FC<Props> = ({ data = [], anomalies = [], config = {} }) => {
  const chartHeight = config.height ?? 400;
  const series: SeriesDef[] = (config as any)?.series || [];

  return (
    <div className="anomaly-chart-container" data-chart-height={chartHeight}>
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="colorClicks" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#667eea" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#667eea" stopOpacity={0.05} />
            </linearGradient>
            <linearGradient id="colorBaseline" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#48bb78" stopOpacity={0.2} />
              <stop offset="95%" stopColor="#48bb78" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          
          <CartesianGrid strokeDasharray="3 3" stroke="#ffffff" opacity={0.2} />
          
          <XAxis
            dataKey="hour"
            tickFormatter={formatHour}
            allowDuplicatedCategory={true}
            minTickGap={4}
            stroke="#ffffff"
            style={{ fontSize: "12px", fontWeight: 500, fill: "#ffffff" }}
          />
          
          <YAxis
            stroke="#ffffff"
            style={{ fontSize: "12px", fontWeight: 500, fill: "#ffffff" }}
            tickFormatter={(value) => value.toLocaleString()}
            domain={[0, 'dataMax']}
          />
          
          <Tooltip content={<CustomTooltip />} />
          
          <Legend
            wrapperStyle={{
              fontSize: "13px",
              fontWeight: 500,
              paddingTop: "10px"
            }}
          />

          {/* Dynamic multiple lines for selected anomaly sources */}
          {series.length > 0 ? (
            series.map((s, idx) => (
              <Line
                key={s.key}
                type="monotone"
                dataKey={s.key}
                stroke={s.color || ["#ffcae7","#F5D5E8","#ffc0e0","#ffe0f0","#ffb0d8"][idx % 5]}
                strokeWidth={2.5}
                dot={false}
                connectNulls={true}
                name={s.name}
                isAnimationActive={true}
                animationDuration={2000}
                animationEasing="ease-in-out"
              />
            ))
          ) : (
            <>
              {/* Fallback single-series rendering */}
              <Area
                type="monotone"
                dataKey="clicks"
                stroke="#ffcae7"
                strokeWidth={2.5}
                fill="url(#colorClicks)"
                name="Clicks"
                isAnimationActive={true}
                animationDuration={1500}
                animationEasing="ease-in-out"
              />
              <Line
                type="monotone"
                dataKey="baseline"
                stroke="#48bb78"
                strokeWidth={2}
                strokeDasharray="8 4"
                dot={false}
                name="Baseline"
                isAnimationActive={true}
                animationDuration={1500}
                animationEasing="ease-in-out"
              />
            </>
          )}

          {/* Anomaly markers (optional) */}
          {anomalies.map((a, i) => (
            <ReferenceDot
              key={i}
              x={String(a.event_hour ?? "")}
              y={a.clicks ?? 0}
              r={6}
              stroke={a.anomaly_type === "click_spike" ? "#fc8181" : "#4fd1c5"}
              strokeWidth={2}
              fill={a.anomaly_type === "click_spike" ? "#feb2b2" : "#9decf9"}
              isFront={true}
            />
          ))}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};

export default AnomalyChart;
