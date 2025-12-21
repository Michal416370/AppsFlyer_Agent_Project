-- -- -- WITH last_day AS (
-- -- --   SELECT
-- -- --     media_source,
-- -- --     hr AS event_hour,
-- -- --     SUM(total_events) AS clicks
-- -- --   FROM `practicode-2025.clicks_data_prac.partial_encoded_clicks_part`
-- -- --   WHERE DATE(event_time) = DATE('2025-10-26')
-- -- --   GROUP BY media_source, hr
-- -- -- ),

-- -- -- history AS (
-- -- --   SELECT
-- -- --     media_source,
-- -- --     hr AS event_hour,
-- -- --     AVG(hourly_clicks) AS avg_clicks,
-- -- --     STDDEV(hourly_clicks) AS std_clicks
-- -- --   FROM (
-- -- --     SELECT
-- -- --       media_source,
-- -- --       DATE(event_time) AS d,
-- -- --       hr,
-- -- --       SUM(total_events) AS hourly_clicks
-- -- --     FROM `practicode-2025.clicks_data_prac.partial_encoded_clicks_part`
-- -- --     WHERE DATE(event_time) IN (DATE('2025-10-24'), DATE('2025-10-25'))
-- -- --     GROUP BY media_source, d, hr
-- -- --   )
-- -- --   GROUP BY media_source, hr
-- -- -- )

-- -- -- SELECT
-- -- --   l.media_source,
-- -- --   l.event_hour,
-- -- --   l.clicks,
-- -- --   h.avg_clicks,
-- -- --   h.std_clicks
-- -- -- FROM last_day l
-- -- -- JOIN history h
-- -- --   ON l.media_source = h.media_source
-- -- --  AND l.event_hour   = h.event_hour
-- -- -- WHERE l.clicks > h.avg_clicks + 3*h.std_clicks
-- -- -- ORDER BY l.clicks DESC;

-- -- -- -- WITH base AS (
-- -- -- --   SELECT
-- -- -- --     event_date,
-- -- -- --     hr,
-- -- -- --     media_source,
-- -- -- --     total_events AS clicks,
-- -- -- --     -- 4 השעות הקודמות לאותו media_source
-- -- -- --     LAG(total_events, 1) OVER (
-- -- -- --       PARTITION BY media_source
-- -- -- --       ORDER BY event_date, hr
-- -- -- --     ) AS clicks_t1,
-- -- -- --     LAG(total_events, 2) OVER (
-- -- -- --       PARTITION BY media_source
-- -- -- --       ORDER BY event_date, hr
-- -- -- --     ) AS clicks_t2,
-- -- -- --     LAG(total_events, 3) OVER (
-- -- -- --       PARTITION BY media_source
-- -- -- --       ORDER BY event_date, hr
-- -- -- --     ) AS clicks_t3,
-- -- -- --     LAG(total_events, 4) OVER (
-- -- -- --       PARTITION BY media_source
-- -- -- --       ORDER BY event_date, hr
-- -- -- --     ) AS clicks_t4
-- -- -- --   FROM `practicode-2025.clicks_data_prac.hourly_clicks_by_media_source`
-- -- -- --   WHERE event_date BETWEEN DATE '2025-10-24' AND DATE '2025-10-26'
-- -- -- -- ),

-- -- -- -- calc_stats AS (
-- -- -- --   SELECT
-- -- -- --     event_date,
-- -- -- --     hr,
-- -- -- --     media_source,
-- -- -- --     clicks,
-- -- -- --     -- ממוצע משוקלל של 4 השעות הקודמות
-- -- -- --     (4 * clicks_t1 + 3 * clicks_t2 + 2 * clicks_t3 + 1 * clicks_t4)
-- -- -- --       / (4 + 3 + 2 + 1) AS baseline_mean,
-- -- -- --     -- סטיית תקן על אותן 4 שעות (לא משוקללת)
-- -- -- --     (
-- -- -- --       SELECT STDDEV_POP(x)
-- -- -- --       FROM UNNEST([clicks_t1, clicks_t2, clicks_t3, clicks_t4]) AS x
-- -- -- --     ) AS baseline_std
-- -- -- --   FROM base
-- -- -- --   -- צריך שיהיו 4 שעות קודמות מלאות
-- -- -- --   WHERE clicks_t1 IS NOT NULL
-- -- -- --     AND clicks_t2 IS NOT NULL
-- -- -- --     AND clicks_t3 IS NOT NULL
-- -- -- --     AND clicks_t4 IS NOT NULL
-- -- -- -- ),

-- -- -- -- anomalies AS (
-- -- -- --   SELECT
-- -- -- --     event_date,
-- -- -- --     hr,
-- -- -- --     media_source,
-- -- -- --     clicks,
-- -- -- --     baseline_mean,
-- -- -- --     baseline_std,
-- -- -- --     baseline_mean + 3 * baseline_std AS upper_threshold
-- -- -- --   FROM calc_stats
-- -- -- --   WHERE clicks > baseline_mean + 3 * baseline_std
-- -- -- -- )

-- -- -- -- SELECT
-- -- -- --   event_date,
-- -- -- --   hr,
-- -- -- --   media_source,
-- -- -- --   clicks,
-- -- -- --   baseline_mean,
-- -- -- --   baseline_std,
-- -- -- --   upper_threshold
-- -- -- -- FROM anomalies
-- -- -- -- ORDER BY event_date, hr, media_source;



-- -- WITH hourly_clicks AS (
-- --   SELECT
-- --     TIMESTAMP_TRUNC(event_time, HOUR) AS event_hour,
-- --     media_source,
-- --     SUM(total_events) AS clicks
-- --   FROM practicode-2025.clicks_data_prac.partial_encoded_clicks_part
-- --   WHERE DATE(event_time) BETWEEN '2025-10-24' AND '2025-10-26'
-- --   GROUP BY event_hour, media_source
-- -- )

-- -- SELECT
-- --   event_hour,
-- --   media_source,
-- --   clicks
-- -- FROM hourly_clicks
-- -- ORDER BY event_hour, media_source;

-- SELECT
--     DATE(event_time) AS event_date,
--     hr AS event_hour,
--     media_source,
--     SUM(total_events) AS total_clicks
-- FROM practicode-2025.clicks_data_prac.partial_encoded_clicks_part
-- WHERE
--   media_source IS NOT NULL
--   -- חילוץ המספר מתוך השם, למשל 'media_source_85' → 85
--   AND CAST(REGEXP_EXTRACT(media_source, r'(\d+)$') AS INT64) BETWEEN 95 AND 100
-- GROUP BY
--     event_date,
--     event_hour,
--     media_source
-- ORDER BY
--     media_source;

-- שעות חריגות (Spike) לכל media_source ב-24–26/10/2025
-- SELECT
--     DATE(event_time) AS event_date,
--     hr AS event_hour,
--     media_source,
--     SUM(total_events) AS total_clicks
-- FROM `practicode-2025.clicks_data_prac.partial_encoded_clicks_part`
-- WHERE media_source IS NOT NULL
--   AND DATE(event_time) BETWEEN '2025-10-24' AND '2025-10-26'
-- GROUP BY
--     event_date,
--     event_hour,
--     media_source
-- ORDER BY
--     event_date,
--     event_hour,
--     media_source;
-- """


-- # 2) שעות חריגות (Spike) לפי avg + 3*std לכל media_source
-- ANOMALY_SQL = """
WITH hourly_clicks AS (
  SELECT
    DATE(event_time) AS event_date,
    hr AS event_hour,
    media_source,
    SUM(total_events) AS total_clicks
  FROM `practicode-2025.clicks_data_prac.partial_encoded_clicks_part`
  WHERE media_source IS NOT NULL
    AND DATE(event_time) BETWEEN '2025-10-24' AND '2025-10-26'
  GROUP BY
    event_date,
    event_hour,
    media_source
),

media_stats AS (
  SELECT
    media_source,
    AVG(total_clicks)        AS avg_clicks,
    STDDEV_POP(total_clicks) AS std_clicks
  FROM hourly_clicks
  GROUP BY media_source
),

anomalies AS (
  SELECT
    h.event_date,
    h.event_hour,
    h.media_source,
    h.total_clicks,
    s.avg_clicks,
    s.std_clicks,
    s.avg_clicks + 3 * s.std_clicks AS upper_threshold
  FROM hourly_clicks h
  JOIN media_stats s
    ON h.media_source = s.media_source
  WHERE
    h.total_clicks > s.avg_clicks + 3 * s.std_clicks
)

SELECT
  event_date,
  event_hour,
  media_source,
  total_clicks,
  avg_clicks,
  std_clicks,
  upper_threshold
FROM anomalies
ORDER BY
  media_source,
  event_date,
  event_hour;