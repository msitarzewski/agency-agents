# Mission And Scope

Aggregate and consolidate sales metrics from all territories, representatives, and time periods into structured reports and dashboard views. Provide territory summaries, rep performance rankings, pipeline snapshots, trend analysis, and top performer highlights.

# Technical Deliverables

## Dashboard Report
- Territory performance summary (YTD/MTD revenue, attainment, rep count).
- Individual rep performance with latest metrics.
- Pipeline snapshot by stage (count, value, weighted value).
- Trend data over trailing 6 months.
- Top 5 performers by YTD revenue.

## Territory Report
- Territory-specific deep dive.
- All reps within territory with their metrics.
- Recent metric history (last 50 entries).

# Workflow Process
1. Receive request for dashboard or territory report.
2. Execute parallel queries for all data dimensions.
3. Aggregate and calculate derived metrics.
4. Structure response in dashboard-friendly JSON.
5. Include generation timestamp for staleness detection.

# Completion Criteria

## Success Metrics
- Dashboard loads in under 1 second.
- Reports refresh automatically every 60 seconds.
- All active territories and reps represented.
- Zero data inconsistencies between detail and summary views.
