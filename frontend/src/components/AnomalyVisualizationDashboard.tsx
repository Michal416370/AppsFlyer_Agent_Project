import React, { useState, useEffect, useRef } from "react";
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

  // Debug logging
  console.log("AnomalyVisualizationDashboard props:", {
    rows: rows.length,
    anomalies: anomalies.length,
    stats,
    mapped: mapped ? {
      chartData: mapped.chartData.length,
      anomalies: mapped.anomalies.length,
      series: mapped.series.length
    } : null,
    finalAnomalies: finalAnomalies.length
  });

  const finalChartConfig = {
    ...chartConfig,
    series: mapped?.series ?? (chartConfig as any)?.series
  };

  const seriesList: any[] = (finalChartConfig as any)?.series ?? [];

  // Format hour to show only HH:MM
  const formatHour = (hour: any): string => {
    if (!hour) return "";
    const s = String(hour);
    // If it contains 'T', extract time part (HH:MM)
    if (s.includes("T")) {
      return s.slice(11, 16);
    }
    return s;
  };

  // State to control how many charts to show
  const [visibleCount, setVisibleCount] = useState(0);
  const lastChartRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (seriesList.length === 0) return;
    
    // Show first chart immediately
    setVisibleCount(1);
    
    // Show remaining charts one by one with 1 second delay
    const timers: number[] = [];
    for (let i = 1; i < seriesList.length; i++) {
      const timer = setTimeout(() => {
        setVisibleCount(i + 1);
      }, i * 1000);
      timers.push(timer as unknown as number);
    }
    
    return () => timers.forEach(t => clearTimeout(t));
  }, [seriesList.length]);

  // Scroll to last chart when a new one appears
  useEffect(() => {
    if (lastChartRef.current && visibleCount > 1) {
      setTimeout(() => {
        lastChartRef.current?.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'end'
        });
      }, 100);
    }
  }, [visibleCount]);

  const computedStats: Stats = {
    total: finalAnomalies.length || stats?.total || 0,
    spike_count:
      finalAnomalies.filter((a) => a.anomaly_type === "click_spike").length ||
      stats?.spike_count || 0,
    drop_count:
      finalAnomalies.filter((a) => a.anomaly_type === "click_drop").length ||
      stats?.drop_count || 0,
    max_deviation: stats?.max_deviation ?? 0
  };

  return (
    <div className="anomaly-dashboard">
      <h2 className="anomaly-title">{title}</h2>

      {/* Stats Cards */}
      <div className="anomaly-stats-container">
        <div className="anomaly-stat-card total">
          <div className="anomaly-stat-label">Total anomalies</div>
          <div className="anomaly-stat-value">{computedStats.total}</div>
        </div>

        <div className="anomaly-stat-card spike">
          <div className="anomaly-stat-label">Spikes ⇡</div>
          <div className="anomaly-stat-value">{computedStats.spike_count}</div>
        </div>

        <div className="anomaly-stat-card drop">
          <div className="anomaly-stat-label">Drops ⇣</div>
          <div className="anomaly-stat-value">{computedStats.drop_count}</div>
        </div>
      </div>

      {/* ✅ Option 1: גרף נפרד לכל media_source */}
      {seriesList.length > 0 ? (
        <div className="anomaly-charts-grid">
          {seriesList.slice(0, visibleCount).map((s: any, index: number) => {
            // Find anomalies for this media source
            const sourceAnomalies = finalAnomalies.filter((a) => a.name === s.name);
            const anomalyHour = sourceAnomalies.length > 0 ? formatHour(sourceAnomalies[0].event_hour) : null;
            
            return (
              <div 
                key={s.key} 
                className="anomaly-chart-block chart-appear"
                ref={index === visibleCount - 1 ? lastChartRef : null}
              >
                <h3 className="anomaly-chart-subtitle">
                  {s.name}
                </h3>
                {anomalyHour && (
                  <p className="anomaly-hour-info">
                    Anomaly detected at: {anomalyHour}
                  </p>
                )}

                <AnomalyChart
                  data={finalChartData}
                  // אם יש לך anomalies אמיתיים לפי source/name, זה יסנן נכון.
                  anomalies={sourceAnomalies}
                  config={{
                    ...finalChartConfig,
                    height: 260,
                    series: [s]
                  }}
                />
              </div>
            );
          })}
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
