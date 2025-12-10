WITH last_day AS (
  SELECT
    media_source,
    hr AS event_hour,
    SUM(total_events) AS clicks
  FROM `practicode-2025.clicks_data_prac.partial_encoded_clicks_part`
  WHERE DATE(event_time) = DATE('2025-10-26')
  GROUP BY media_source, hr
),

history AS (
  SELECT
    media_source,
    hr AS event_hour,
    AVG(hourly_clicks) AS avg_clicks,
    STDDEV(hourly_clicks) AS std_clicks
  FROM (
    SELECT
      media_source,
      DATE(event_time) AS d,
      hr,
      SUM(total_events) AS hourly_clicks
    FROM `practicode-2025.clicks_data_prac.partial_encoded_clicks_part`
    WHERE DATE(event_time) IN (DATE('2025-10-24'), DATE('2025-10-25'))
    GROUP BY media_source, d, hr
  )
  GROUP BY media_source, hr
)

SELECT
  l.media_source,
  l.event_hour,
  l.clicks,
  h.avg_clicks,
  h.std_clicks
FROM last_day l
JOIN history h
  ON l.media_source = h.media_source
 AND l.event_hour   = h.event_hour
WHERE l.clicks > h.avg_clicks + 3*h.std_clicks
ORDER BY l.clicks DESC;
