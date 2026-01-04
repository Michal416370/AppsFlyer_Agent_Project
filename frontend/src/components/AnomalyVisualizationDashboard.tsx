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
  const lastChartRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (seriesList.length === 0) return;

    setVisibleCount(1);
    const timers: number[] = [];

    for (let i = 1; i < seriesList.length; i++) {
      const timer = window.setTimeout(() => setVisibleCount(i + 1), i * 1000);
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

      {/* Option 1: Separate chart per media_source */}
      {seriesList.length > 0 ? (
        <div className="anomaly-charts-grid">
          {seriesList.slice(0, visibleCount).map((s: any, index: number) => {
            const sourceAnomalies = finalAnomalies.filter((a) => a.name === s.name);
            const anomalyHour =
              sourceAnomalies.length > 0 ? formatHourLabel(sourceAnomalies[0].event_hour) : null;

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
      ) : (
        // fallback: Clicks/Baseline single chart
        <AnomalyChart data={finalChartData} anomalies={finalAnomalies} config={finalChartConfig} />
      )}

      {/* ✅ Full Data Table (authoritative): renders from rows */}
      {rows.length > 0 && (
        <div className="anomaly-table">
          <div
            style={{
              display: "flex",
              alignItems: "baseline",
              justifyContent: "space-between",
              gap: 12
            }}
          >
            <h3 className="anomaly-table-title">Full data table</h3>

            <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
              <div style={{ fontSize: 12, opacity: 0.85 }}>
                Showing {visibleRows.length.toLocaleString()} of {rows.length.toLocaleString()}
              </div>

              {rows.length > PAGE_SIZE && (
                <button
                  onClick={() => setShowAllRows((v) => !v)}
                  style={{
                    padding: "6px 10px",
                    borderRadius: 10,
                    border: "1px solid rgba(255,255,255,0.18)",
                    background: "rgba(255,255,255,0.06)",
                    color: "white",
                    cursor: "pointer",
                    fontSize: 12,
                    fontWeight: 600
                  }}
                >
                  {showAllRows ? "Show first 200" : "Show all"}
                </button>
              )}
            </div>
          </div>

          <div
            style={{
              overflow: "auto",
              maxHeight: 420,
              borderRadius: 12,
              border: "1px solid rgba(255,255,255,0.12)"
            }}
          >
            <table style={{ borderCollapse: "collapse", width: "max-content", minWidth: "100%" }}>
              <thead
                style={{
                  position: "sticky",
                  top: 0,
                  background: "rgba(0,0,0,0.35)",
                  backdropFilter: "blur(6px)",
                  zIndex: 1
                }}
              >
                <tr>
                  {allColumns.map((col) => (
                    <th
                      key={col}
                      style={{
                        textAlign: "left",
                        padding: "10px 12px",
                        fontSize: 12,
                        fontWeight: 700,
                        whiteSpace: "nowrap",
                        borderBottom: "1px solid rgba(255,255,255,0.15)"
                      }}
                    >
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>

              <tbody>
                {visibleRows.map((r, idx) => (
                  <tr key={idx}>
                    {allColumns.map((col) => (
                      <td
                        key={col}
                        style={{
                          padding: "8px 12px",
                          fontSize: 12,
                          whiteSpace: "nowrap",
                          borderBottom: "1px solid rgba(255,255,255,0.08)"
                        }}
                      >
                        {r?.[col] == null ? "" : String(r[col])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Optional legacy/debug markdown */}
          {tableMarkdown && (
            <details style={{ marginTop: 12, opacity: 0.9 }}>
              <summary style={{ cursor: "pointer", fontSize: 12 }}>Debug: markdown table</summary>
              <pre className="anomaly-table-content" style={{ marginTop: 10 }}>
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
