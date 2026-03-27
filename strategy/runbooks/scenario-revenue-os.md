# Revenue OS Runbook

> **Mode**: Manual-First Revenue OS | **Duration**: 14-30 days to first client | **Focus**: outbound sales, admin automation delivery, productization

---

## Scenario

You are building a hybrid AI automation business that sells lead recovery and admin workflow automation to SMB service businesses. The business must operate as a state-driven system that can be run by a founder today, delegated to operators later, and eventually productized into reusable modules.

## Business Model

Core loop:

`Sell -> Deliver -> Standardize -> Productize -> Scale -> Repeat`

Commercial structure:

- setup fee for installation and launch
- recurring monthly fee for optimization, support, and reporting

## Target Market

Primary wedge:

- SMB home-service businesses

Expansion niches:

- legal intake
- insurance brokers

Shared characteristics:

- inbound lead flow
- manual follow-up
- scheduling friction
- weak CRM discipline
- high admin drag

## Offer

Primary offer:

- Lead Recovery and Admin Workflow Automation

Business outcomes sold:

- faster lead response
- fewer lost opportunities
- saved admin time
- cleaner scheduling and routing
- pipeline visibility

## Core Operating Principles

1. No record without status.
2. No status without next action.
3. No opportunity without a prospect.
4. No client without a won opportunity.
5. No manual memory. Everything is logged.
6. Repeated work gets standardized into templates, fields, or workflows.

The system runs on state transitions, not memory.

## System Architecture

### Airtable

Role:

- system of record
- relational business data
- KPI tracking
- task enforcement

Tables:

- Prospects
- Opportunities
- Clients
- Workflow Modules
- KPI Records
- Tasks

### GoHighLevel

Role:

- conversations
- booking
- sales pipeline movement
- onboarding communication

Pipelines:

- Outbound Sales
- Client Onboarding
- Account Management

### Notion

Role:

- SOPs
- templates
- playbooks
- setup log

### Make

Role:

- sync between Airtable and GoHighLevel
- dedupe logic
- stage write-backs
- task enforcement

## Business Pipeline

System state flow:

`ICP -> Lead -> Qualified Prospect -> Contacted -> Replied -> Booked -> Discovery Complete -> Audit Complete -> Proposal Sent -> Won/Lost -> Onboarding -> Active Client -> Retained -> Expanded -> Product Input`

Operating flow:

`market selection -> prospect sourcing -> qualification -> outreach -> reply triage -> discovery -> audit -> proposal -> close -> onboarding -> delivery -> reporting -> retention -> upsell -> productization`

## Airtable Design

### Prospects

Purpose:

- sourcing
- qualification
- outreach state
- suppression state

Required status values:

- raw
- qualified
- queued
- contacted
- follow_up_1
- follow_up_2
- follow_up_3
- replied
- opportunity_created
- nurture
- closed
- invalid

Key control fields:

- ICP Score
- Qualified?
- Outreach Batch ID
- Email Sent Count
- Reply Type
- Bounce Detected
- Unsubscribed
- Outreach Health

### Opportunities

Purpose:

- active sales object linked to a prospect

Core stages:

- new
- replied
- qualified
- booked
- discovery_complete
- audit_complete
- proposal_sent
- won
- lost
- nurture

Key control fields:

- Pain Score
- Close Probability
- Deal Value (Weighted)
- Days in Stage
- Primary Pain Type
- Next Action

### Clients

Purpose:

- delivery and retention control center

Key fields:

- Status
- System Status
- Health Score
- At Risk?
- Build Completion %
- QA Passed
- Upsell Potential

### Workflow Modules

Purpose:

- reusable delivery modules
- productization spine

Key fields:

- Module Type
- Config Inputs
- Expected Outcome
- Failure Frequency
- Last Tested Date

### KPI Records

Purpose:

- monthly proof of value

Key derived fields:

- Lead -> Booking Rate
- Recovery Rate
- Estimated ROI

### Tasks

Purpose:

- enforce next action for every live object

Key control fields:

- Blocking?
- Recurring
- Repeat Interval
- Time to Complete (hrs)

## GoHighLevel Design

### Outbound Sales Pipeline

- New Lead
- Contacted
- Replied
- Qualified
- Booked
- Discovery Complete
- Audit Complete
- Proposal Sent
- Won
- Lost
- Nurture

### Client Onboarding Pipeline

- Payment Received
- Access Pending
- Intake Complete
- Build Mapping
- Build In Progress
- QA
- Launch Ready
- Live

### Account Management Pipeline

- Active
- Optimizing
- Expansion Opportunity
- At Risk
- Paused
- Churned

### Workflow Build Order

1. Qualified Prospect Intake
2. Reply Detection
3. Booked Call
4. Discovery Complete
5. Proposal Sent
6. Won Deal
7. No-Show Recovery

Guardrails:

- no duplicate open outbound opportunities
- inbound reply pauses future outbound automation
- won deals require minimum required fields
- unsubscribe and bounce events suppress future outreach
- no-show recovery triggers once unless intentionally retriggered

## Delivery Architecture

Standard delivery path:

`lead capture -> instant reply -> qualification -> booking / routing -> CRM update -> reminder sequence -> no-show recovery -> internal notification -> reporting`

Reusable modules:

- Capture
- Response
- Qualification
- Booking
- CRM Update
- Reminder
- Recovery
- Notification
- Reporting

Delivery sequence:

1. map current workflow
2. configure routing and inputs
3. build core automations
4. test all branches
5. pilot
6. launch
7. monitor failures
8. optimize

## Reporting and Retention

Monthly reporting must show:

- leads captured
- response time
- bookings
- recoveries
- estimated revenue recovered
- estimated hours saved
- what improved
- what broke
- what happens next

Retention is sold as ongoing performance improvement.

## Productization Strategy

Every client generates reusable assets:

- SOPs
- templates
- prompts
- schemas
- message libraries
- onboarding forms
- module records

Transformation path:

`Custom -> Template -> Module -> Product`

Shared core:

- data model
- pipeline logic
- delivery modules
- KPI framework

Variable layer:

- niche messaging
- routing rules
- service categories
- offer framing

## Delegation Path

Delegate in this order:

1. lead sourcing
2. inbox triage
3. delivery implementation
4. client communication
5. sales assistance

Founder retains early control over:

- offer design
- discovery calls
- closing
- productization decisions

## Failure Modes

Primary risks:

- weak targeting
- poor deliverability
- generic messaging
- slow reply handling
- unclear ROI framing
- excessive delivery customization
- poor onboarding access collection
- weak reporting proof

System defaults:

- narrow offer
- clear state transitions
- standard modules
- explicit ownership
- measurable outcomes

## Success Criteria

- first booked discovery calls within 14 days
- first closed client within 30 days
- every active object has an open task
- no duplicate open opportunities for the same contact
- every won opportunity creates one client and onboarding tasks
- first reusable delivery modules defined by client three
