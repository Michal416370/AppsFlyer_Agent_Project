type RawRow = {
  media_source: string;
  anomaly_hour_ts?: string | null;
  [k: string]: any; // h_20251024_00 וכו'
};

const hourColRe = /^h_(\d{8})_(\d{2})$/;

function toIsoHour(date8: string, hh: string) {
  const y = date8.slice(0, 4);
  const m = date8.slice(4, 6);
  const d = date8.slice(6, 8);
  return `${y}-${m}-${d}T${hh}:00:00Z`;
}

function anomalyTsToIsoHour(anomalyTs: string) {
  // "2025-10-24 09:00:00 UTC" -> "2025-10-24T09:00:00Z"
  const s = anomalyTs.replace(" UTC", "").replace(" ", "T");
  return s.endsWith("Z") ? s : `${s}Z`;
}

export function buildChartFromRows(rows: RawRow[]) {
  const byHour = new Map<string, any>();

  // series = כל קו בגרף (כל media_source)
  const series = rows.map(r => ({ key: r.media_source, name: r.media_source }));

  // chartData = נקודה לכל שעה
  for (const r of rows) {
    for (const [col, val] of Object.entries(r)) {
      const m = col.match(hourColRe);
      if (!m) continue;

      const isoHour = toIsoHour(m[1], m[2]);
      if (!byHour.has(isoHour)) byHour.set(isoHour, { hour: isoHour });

      byHour.get(isoHour)![r.media_source] = Number(val ?? 0);
    }
  }

  const chartData = Array.from(byHour.values()).sort(
    (a, b) => new Date(a.hour).getTime() - new Date(b.hour).getTime()
  );

  // anomalies (אופציונלי): נקודה בשעת האנומלי
  const anomalies = rows
    .filter(r => r.anomaly_hour_ts)
    .map(r => {
      const hour = anomalyTsToIsoHour(String(r.anomaly_hour_ts));
      const clicks = byHour.get(hour)?.[r.media_source] ?? null;
      return {
        name: r.media_source,
        anomaly_type: "click_spike",
        event_hour: hour,
        clicks
      };
    });

  return { chartData, series, anomalies };
}
