-- Rows per run (average of successful runs)
SELECT round(avg(rows_loaded), 1) AS avg_rows_per_run
FROM pipeline_runs WHERE status = 'success';

-- Validation failure rate (latest run)
SELECT round(100.0 * rows_quarantined
       / nullif(rows_loaded + rows_quarantined, 0), 1) AS pct_failing
FROM pipeline_runs ORDER BY started_at DESC LIMIT 1;

-- Freshness lag (time since last successful run)
SELECT now() - max(finished_at) AS freshness_lag
FROM pipeline_runs WHERE status = 'success';

-- Success rate over all runs
SELECT round(100.0 * count(*) FILTER (WHERE status = 'success')
       / count(*), 1) AS success_rate_pct
FROM pipeline_runs;