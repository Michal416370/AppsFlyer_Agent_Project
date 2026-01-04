import React, { useState, useEffect, useRef, useMemo } from "react";
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
  rows?: RawRow[]; // ✅ raw table rows (authoritative for Full Table)
  chartData?: ChartPoint[]; // optional fallback if already provided
  anomalies?: Anomaly[];
  stats?: Partial<Stats>;
  title?: string;
  chartConfig?: { height?: number; series?: any[] };
  tableMarkdown?: string; // optional debug / legacy
}

function getAllColumns(rows: any[]): string[] {
  const set = new Set<string>();
  for (const r of rows || []) {
    Object.keys(r || {}).forEach((k) => set.add(k));
  }

  // nice ordering: common cols first, then the rest
  const preferred = ["media_source", "anomaly_hour_ts"];
  const cols = Array.from(set);

  const preferredExisting = preferred.filter((c) => set.has(c));
  const rest = cols.filter((c) => !preferredExisting.includes(c));

  return [...preferredExisting, ...rest];
}

function formatHourLabel(hour: any): string {
  if (!hour) return "";
  const s = String(hour);
  if (s.includes("T")) return s.slice(11, 16);
  return s;
}

function formatAnomalyDateTime(hour: any): string {
  if (!hour) return "";
  const s = String(hour);
  // Format: 2025-10-26T22:00:00Z -> 26/10/25 22:00
  if (s.includes("T")) {
    const date = s.slice(8, 10) + "/" + s.slice(5, 7) + "/" + s.slice(2, 4);
    const time = s.slice(11, 16);
    return date + " " + time;
  }
  return s;
}

function formatColumnName(col: string): string {
  // Format h_20251024_00 -> 00:00
  const hourMatch = col.match(/^h_\d{8}_(\d{2})$/);
  if (hourMatch) {
    return hourMatch[1] + ":00";
  }
  
  return col
    .split("_")
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function formatDateTime(value: any): string {
  if (!value) return "";
  const s = String(value);
  // Format: 2025-10-26T22:00:00+00:00 -> 26/10/25 22:00
  if (s.includes("T")) {
    const date = s.slice(8, 10) + "/" + s.slice(5, 7) + "/" + s.slice(2, 4);
    const time = s.slice(11, 16);
    return date + " " + time;
  }
  return s;
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
  // If we got wide rows (h_YYYYMMDD_HH...), build chart from them
  const mapped = useMemo(() => (rows.length ? buildChartFromRows(rows) : null), [rows]);

  const finalChartData = mapped?.chartData ?? chartData;
  const finalAnomalies = mapped?.anomalies ?? anomalies;

  const finalChartConfig = {
    ...chartConfig,
    series: mapped?.series ?? (chartConfig as any)?.series
  };

  const seriesList: any[] = (finalChartConfig as any)?.series ?? [];

  // progressive reveal of per-source charts (your existing UX)
  const [visibleCount, setVisibleCount] = useState(0);
  const [showTable, setShowTable] = useState(false);
  const lastChartRef = useRef<HTMLDivElement>(null);
  const tableRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (seriesList.length === 0) return;

    setVisibleCount(1);
    const timers: number[] = [];

    // Each chart appears 1500ms after the previous one starts
    for (let i = 1; i < seriesList.length; i++) {
      const timer = window.setTimeout(() => setVisibleCount(i + 1), i * 1500);
      timers.push(timer);
    }

    return () => timers.forEach((t) => window.clearTimeout(t));
  }, [seriesList.length]);

  useEffect(() => {
    if (lastChartRef.current && visibleCount > 1) {
      window.setTimeout(() => {
        lastChartRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
      }, 100);
    }
  }, [visibleCount]);

  // Show table 1 second after all charts are done
  useEffect(() => {
    if (seriesList.length > 0 && visibleCount === seriesList.length) {
      const timer = window.setTimeout(() => {
        setShowTable(true);
      }, 1000);
      return () => window.clearTimeout(timer);
    }
  }, [visibleCount, seriesList.length]);

  // Scroll to table when it appears
  useEffect(() => {
    if (showTable && tableRef.current) {
      window.setTimeout(() => {
        tableRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 100);
    }
  }, [showTable]);

  const computedStats: Stats = {
    total: finalAnomalies.length || stats?.total || 0,
    spike_count:
      finalAnomalies.filter((a) => a.anomaly_type === "click_spike").length ||
      stats?.spike_count ||
      0,
    drop_count:
      finalAnomalies.filter((a) => a.anomaly_type === "click_drop").length ||
      stats?.drop_count ||
      0,
    max_deviation: stats?.max_deviation ?? 0
  };

  const allColumns = useMemo(() => getAllColumns(rows), [rows]);

  // Full data table pagination (simple + fast enough)
  const [showAllRows, setShowAllRows] = useState(false);
  const PAGE_SIZE = 200;
  const visibleRows = showAllRows ? rows : rows.slice(0, PAGE_SIZE);

  return (
    <div className="anomaly-dashboard">
      <h2 className="anomaly-title">Clicks per hour (Graphs)</h2>

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

      {/* Option 1: Separate chart per media_source */}
      {seriesList.length > 0 ? (
        <>
          <div className="anomaly-charts-grid">
          {seriesList.slice(0, visibleCount).map((s: any, index: number) => {
            const sourceAnomalies = finalAnomalies.filter((a) => a.name === s.name);
            const anomalyHour =
              sourceAnomalies.length > 0 ? formatAnomalyDateTime(sourceAnomalies[0].event_hour) : null;

            // Check if this series has any data
            const hasData = finalChartData.some((point: any) => point[s.key] !== undefined && point[s.key] !== null);
            
            if (!hasData) return null; // Skip charts with no data

            return (
              <div
                key={s.key}
                className="anomaly-chart-block chart-appear"
                ref={index === visibleCount - 1 ? lastChartRef : null}
              >
                <h3 className="anomaly-chart-subtitle">{s.name}</h3>

                {anomalyHour && (
                  <p className="anomaly-hour-info">Anomaly detected at: {anomalyHour}</p>
                )}

                <AnomalyChart
                  data={finalChartData}
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
        </>
      ) : (
        // fallback: Clicks/Baseline single chart
        <AnomalyChart data={finalChartData} anomalies={finalAnomalies} config={finalChartConfig} />
      )}

      {/* ✅ Full Data Table (authoritative): renders from rows */}
      {rows.length > 0 && showTable && (
        <div className="anomaly-table" ref={tableRef}>
          <div className="table-header">
            <h3 className="anomaly-title anomaly-table-main-title">Clicks per hour (table)</h3>

            <div className="table-controls">
              <div className="table-row-count">
                Showing {visibleRows.length.toLocaleString()} of {rows.length.toLocaleString()}
              </div>

              {rows.length > PAGE_SIZE && (
                <button
                  onClick={() => setShowAllRows((v) => !v)}
                  className="table-toggle-button"
                >
                  {showAllRows ? "Show first 200" : "Show all"}
                </button>
              )}
            </div>
          </div>

          <div className="table-scroll-container">
            <div className="table-scroll-inner">
              <table className="data-table">
                <thead>
                  <tr>
                    {allColumns.map((col) => (
                      <th key={col}>
                        {formatColumnName(col)}
                      </th>
                    ))}
                  </tr>
                </thead>

                <tbody>
                  {visibleRows.map((r, idx) => (
                    <tr key={idx}>
                      {allColumns.map((col) => (
                        <td key={col}>
                          {r?.[col] == null ? "" : 
                           col === "anomaly_hour_ts" ? formatDateTime(r[col]) : String(r[col])}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Optional legacy/debug markdown */}
          {tableMarkdown && (
            <details className="debug-details">
              <summary className="debug-summary">Debug: markdown table</summary>
              <pre className="anomaly-table-content debug-pre">
                {tableMarkdown}
              </pre>
            </details>
          )}
        </div>
      )}
    </div>
  );
};

export default AnomalyVisualizationDashboard;
