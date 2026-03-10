DRISK — UK Police Crime API Integration Spec
Technical Integration Document

OVERVIEW
This document defines how DRISK integrates with the UK Police open data API (data.police.uk) to automatically populate crime intelligence into the DRISK Intelligence module and External Threat scoring domain.
API Base URL: https://data.police.uk/api
Authentication: None required (fully public API)
Cost: Free
Coverage: England, Wales, and Northern Ireland
Data Freshness: Updated monthly (typically 2–3 months in arrears)
Format: JSON
Methods: HTTP GET (and POST for polygon searches)

WHY THIS MATTERS FOR DRISK
Currently, External Threat context in DRISK relies on the assessor manually answering questions about local crime. This creates:

Inconsistency between assessors
Outdated information (assessor may not know recent trends)
No audit trail for threat score justification

By integrating the UK Police API, DRISK can:

Auto-populate crime context when a site is created (using stored lat/lng)
Refresh threat data monthly without requiring a new assessment
Justify threat scores with real, citable police data
Trigger live residual-risk updates when crime patterns shift near a site


API ENDPOINTS USED BY DRISK
1. Street-Level Crimes — All Crime
Pulls all crimes within approximately 1 mile of a site's coordinates.
GET https://data.police.uk/api/crimes-street/all-crime
  ?lat={site_latitude}
  &lng={site_longitude}
  &date={YYYY-MM}
Parameters:
ParameterRequiredDescriptionlatYesSite latitude (decimal degrees)lngYesSite longitude (decimal degrees)dateNoMonth to query (YYYY-MM). Defaults to latest available month
Example Request:
GET https://data.police.uk/api/crimes-street/all-crime?lat=51.509865&lng=-0.118092&date=2025-01
Example Response (single item):
json{
  "category": "violent-crime",
  "persistent_id": "a1b2c3d4e5f6...",
  "id": 82394750,
  "month": "2025-01",
  "location": {
    "latitude": "51.5099",
    "longitude": "-0.1181",
    "street": {
      "id": 884343,
      "name": "On or near High Street"
    }
  },
  "context": "",
  "location_type": "Force",
  "location_subtype": "",
  "outcome_status": {
    "category": "Under investigation",
    "date": "2025-02"
  }
}
Fields Used by DRISK:
FieldDRISK UsecategoryClassify crime type and map to threat scoremonthTrack crime trend over timelocation.street.nameConfirm proximity to siteoutcome_status.categoryAssess policing effectiveness

2. Street-Level Crimes — By Category
Pull specific crime types that are most relevant to physical security risk.
High-relevance categories for DRISK:
Category CodeNameDRISK Relevanceviolent-crimeViolence and sexual offencesHighest threat weightanti-social-behaviourAnti-social behaviourExternal threat and ASB scoreburglaryBurglaryPhysical security vulnerabilityrobberyRobberyThreat and response urgencycriminal-damage-arsonCriminal damage and arsonVulnerability and exposurepublic-orderPublic orderDisorder / protest sensitivitypossession-of-weaponsPossession of weaponsElevated threat contextdrugsDrugsEnvironmental risk contextvehicle-crimeVehicle crimeSite perimeter exposuretheft-from-the-personTheft from the personPublic-facing site risk
Example — Violent Crime Only:
GET https://data.police.uk/api/crimes-street/violent-crime?lat=51.509865&lng=-0.118092&date=2025-01

3. Crime Outcomes at Location
Returns how crimes near the site were resolved — useful for measuring policing effectiveness as a response factor.
GET https://data.police.uk/api/crimes-street-outcomes
  ?lat={site_latitude}
  &lng={site_longitude}
  &date={YYYY-MM}
Outcome categories returned:
OutcomeDRISK SignalCharged / SummonsedStrong policing responseCommunity resolutionModerate responseUnable to proceedWeak enforcementLocal resolutionLowInvestigation complete – no suspect identifiedVery weakNo further actionWeak
DRISK Use: High rates of "no further action" or "unable to proceed" near a site reduce the response capability component for that location.

4. Stop and Search Data
Returns stop and search activity near the site — an indicator of elevated police attention or disorder activity.
GET https://data.police.uk/api/stops-street
  ?lat={site_latitude}
  &lng={site_longitude}
  &date={YYYY-MM}
DRISK Use: High stop-and-search volume near a site indicates active disorder, drug activity, or elevated street crime — contributing to the External Threat domain score.

5. Crime Categories (Reference)
Retrieves the full list of valid crime category codes for a given month. Used to validate and map crime types during ingestion.
GET https://data.police.uk/api/crime-categories?date={YYYY-MM}
Example Response:
json[
  { "url": "all-crime", "name": "All crime and ASB" },
  { "url": "anti-social-behaviour", "name": "Anti-social behaviour" },
  { "url": "burglary", "name": "Burglary" },
  { "url": "violent-crime", "name": "Violence and sexual offences" },
  ...
]

6. Data Last Updated
Check when crime data was last refreshed. Use this to display data freshness to the assessor.
GET https://data.police.uk/api/crime-last-updated
Response:
json{ "date": "2025-01" }
DRISK Use: Display to assessor: "Crime data last updated: January 2025" — ensuring transparency.

RATE LIMITS
LimitValueAverage requests per second15Burst limit30 per secondError on exceedHTTP 429 Too Many RequestsRetry strategyExponential backoff — wait 2s, then 4s, then 8s
Recommendation for DRISK: Run crime data pulls as a background job triggered on site creation and monthly refresh — not in real time during an assessment. This prevents rate limit issues and keeps the UX fast.

HOW DRISK PROCESSES THE DATA
Step 1: Site Creation
When an assessor creates a new site and enters the address, DRISK:

Geocodes the address to lat/lng (using a geocoding service or stored co-ordinates)
Queues a background job to call the Police API
Pulls all-crime data for the last 3 months at that lat/lng
Stores results in the site_intelligence table

Step 2: Crime Volume Calculation
DRISK aggregates raw crime counts by category:
total_violent   = count of "violent-crime" records
total_asb       = count of "anti-social-behaviour" records
total_burglary  = count of "burglary" records
total_disorder  = count of "public-order" + "possession-of-weapons"
total_all       = count of all records
Step 3: Threat Score Mapping
Crime volumes are mapped to a 1–5 threat score for the External Threat domain:
Monthly Crime Count (all crime within 1 mile)Threat Score0–201 (Very Low)21–502 (Low)51–1003 (Moderate)101–2004 (High)200+5 (Very High)
Violent crime and weapons possession carry a higher weighting multiplier (e.g., ×1.5) in the calculation.
Step 4: Domain Score Contribution
The auto-calculated threat score pre-fills answers in the External Threat domain questions:

Q5: "Is the site located in a high-crime or disorder area?" — auto-answered from crime volume score
Q6: "Is trespass or anti-social behaviour evident?" — auto-answered from ASB count
Q7: "Is the site isolated during low occupancy?" — remains manual (not available from API)

Assessors can review and override any pre-filled answer with a comment explaining the change.
Step 5: Monthly Refresh (Live Residual-Risk Engine)
A scheduled job runs monthly to:

Pull latest crime data for all active sites
Recalculate crime-based threat scores
If score changes by more than 1 band (e.g., Moderate → High), flag the site with:

Dashboard alert: "Crime data updated — threat score changed"
Notification to Contract Manager
Residual risk recalculated automatically



This is the core of Innovation 1: Live Residual-Risk Engine.

DATA STORAGE
New table: site_crime_intelligence
ColumnTypeDescriptionidUUIDPrimary keysite_idUUIDForeign key → sitesdata_monthVARCHAR(7)YYYY-MM of datatotal_crimesINTEGERAll crimes countviolent_crimesINTEGERViolent crime countasb_countINTEGERAnti-social behaviour countburglary_countINTEGERBurglary countdisorder_countINTEGERPublic order + weaponsvehicle_crime_countINTEGERVehicle crime countdrug_countINTEGERDrug offences countcalculated_threat_scoreINTEGER1–5 scoreraw_responseJSONBFull API response storedfetched_atTIMESTAMPWhen data was pulleddata_sourceVARCHAR"uk-police-api"

DISPLAYING CRIME DATA IN THE UI
On the Site Profile Screen
Add a Crime Context panel showing:

Threat level badge (Low / Moderate / High / Very High / Critical)
Monthly crime count (last 3 months average)
Crime type breakdown (bar chart: violent, ASB, burglary, disorder, other)
Data timestamp: "Based on UK Police data — last updated January 2025"
Link: "View on data.police.uk"

On the Assessment Screen (External Threat Domain)

Pre-filled answers shown with a data badge: [Auto: Police API]
Assessor can click to override with a comment
Override triggers a confidence score note: "Assessor overrode API data — manual review required"

On the Dashboard

Sites with a recent crime score change are flagged: 🔴 Crime data updated
Estate heatmap updated to reflect new threat levels


ERROR HANDLING
ScenarioDRISK BehaviourAPI returns 429 (rate limit)Retry with exponential backoff; max 3 retriesAPI returns 503 (maintenance)Queue job for retry in 1 hour; notify adminAPI returns empty resultsFlag as "no crime data available" — assessor must answer manuallySite has no lat/lng storedSkip API call; show message in assessment: "Enter site coordinates to enable crime data"Data is more than 4 months oldShow warning: "Crime data may be outdated — check manually"

SECURITY & COMPLIANCE NOTES

No personal data is transmitted — the API only receives lat/lng coordinates and a date
No API key is stored or required
All API responses are stored in DRISK's own database — the raw data is cached to reduce repeat calls
Crime data is attributed to data.police.uk in all reports and displays
DRISK does not guarantee accuracy — data is approximate (locations are anonymised by the Police API by design)

Required disclaimer in DRISK UI and reports:

"Crime data sourced from data.police.uk. Locations are approximated and may not reflect all incidents near this site. Data is typically published 2–3 months in arrears."


IMPLEMENTATION PLAN
Phase 1 — MVP Integration

Store lat/lng on site creation
Pull all-crime data on site creation (background job)
Display raw crime count on Site Profile screen
Pre-fill External Threat domain Q5 and Q6 from crime data
Store results in site_crime_intelligence table

Phase 2 — Scoring Integration

Map crime volumes to 1–5 threat score
Auto-update inherent risk calculation when crime score changes
Monthly refresh job for all active sites
Dashboard flagging when crime score changes

Phase 3 — Live Risk Engine

Automated residual risk recalculation on monthly crime data refresh
Notifications to Contract Manager on significant score changes
Trend chart on Site Profile: crime count over 12 months
Crime breakdown chart by category

Phase 4 — Advanced

Polygon-based crime queries for sites with large perimeters
Stop and search integration as a disorder indicator
Crime outcome rates feeding policing effectiveness score
Multi-site crime comparison for estate heatmap


SUMMARY
The UK Police API integration transforms DRISK's External Threat domain from assessor opinion into evidence-backed, automatically refreshed intelligence. It requires no API key, costs nothing, and is updated monthly. For DRISK, it directly strengthens three core features:

DRISK Intelligence module — auto-populated with real crime data per site
Inherent Risk scoring — threat score grounded in police-reported data
Live Residual-Risk Engine — risk automatically updates when crime patterns change near a site

This integration is one of the clearest demonstrations that DRISK is a risk intelligence platform, not just a digital form.