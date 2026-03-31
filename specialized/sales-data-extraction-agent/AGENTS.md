# Mission And Scope

Monitor designated Excel file directories for new or updated sales reports. Extract key metrics (MTD, YTD, Year End projections), then normalize and persist them for downstream reporting and distribution.

# Technical Deliverables

## File Monitoring
- Watch directory for `.xlsx` and `.xls` files using filesystem watchers.
- Ignore temporary Excel lock files (`~$`).
- Wait for file write completion before processing.

## Metric Extraction
- Parse all sheets in a workbook.
- Map columns flexibly: `revenue/sales/total_sales`, `units/qty/quantity`, and similar.
- Calculate quota attainment automatically when quota and revenue are present.
- Handle currency formatting ($, commas) in numeric fields.

## Data Persistence
- Bulk insert extracted metrics into PostgreSQL.
- Use transactions for atomicity.
- Record source file in every metric row for audit trail.

# Workflow Process
1. File detected in watch directory.
2. Log import as "processing."
3. Read workbook and iterate sheets.
4. Detect metric type per sheet.
5. Map rows to representative records.
6. Insert validated metrics into database.
7. Update import log with results.
8. Emit completion event for downstream agents.

# Completion Criteria

## Success Metrics
- 100% of valid Excel files processed without manual intervention.
- Under 2% row-level failures on well-formatted reports.
- Under 5 seconds processing time per file.
- Complete audit trail for every import.
