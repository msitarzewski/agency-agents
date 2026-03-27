# Revenue OS Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the first live version of Revenue OS inside a hybrid Airtable + GoHighLevel + Make + Notion operating model for selling and delivering admin workflow automation.

**Architecture:** Airtable is the source of truth, GoHighLevel is the execution layer, Make handles bidirectional sync and enforcement, and Notion stores SOPs and templates. Version 1 favors visible state transitions, manual review, and reliable handoffs over aggressive automation.

**Tech Stack:** Airtable, GoHighLevel, Make, Notion, Google Workspace, Twilio or GoHighLevel messaging, optional Calendly or GHL calendars

---

### Task 1: Create Airtable Revenue OS Base

**Files:**
- Reference: `strategy/runbooks/scenario-revenue-os.md`

**Step 1: Create the base and tables**

Create these tables in this order:
- `Prospects`
- `Opportunities`
- `Clients`
- `Workflow Modules`
- `KPI Records`
- `Tasks`

**Step 2: Add the full `Prospects` schema**

Include:
- identity fields
- sourcing fields
- qualification fields
- outreach control fields
- deliverability fields
- linked opportunity

**Step 3: Add formulas to `Prospects`**

Create and validate:
- `ICP Score`
- `Qualified?`
- `Outreach Health`

**Step 4: Add the remaining schemas**

Create fields for:
- `Opportunities`
- `Clients`
- `Workflow Modules`
- `KPI Records`
- `Tasks`

Use exact status values from the runbook.

**Step 5: Build the essential Airtable views**

Create:
- `Qualified Queue`
- `Ready to Contact`
- `Follow-Up Due`
- `Replies`
- `Booked Calls`
- `Stuck Deals`
- `Live Clients`
- `At Risk Clients`
- `Today`
- `Overdue`
- `Critical Tasks`

**Step 6: Seed test records**

Create:
- one sample prospect
- one linked opportunity
- one won opportunity and client
- one sample task

Expected: links and formulas work correctly.

### Task 2: Configure GoHighLevel Pipelines and Fields

**Files:**
- Reference: `strategy/runbooks/scenario-revenue-os.md`

**Step 1: Create three pipelines**

Create:
- `Outbound Sales`
- `Client Onboarding`
- `Account Management`

Use exact stage names from the runbook.

**Step 2: Create custom fields**

Add:
- Airtable IDs
- qualification fields
- sales fields
- client fields

Expected: field names use one consistent convention and avoid duplicates.

**Step 3: Create tags**

Add:
- source tags
- intent tags
- status tags
- module tags

**Step 4: Create calendars**

Create:
- `Discovery Call`
- `Client Onboarding Call`

Attach confirmation and reminder messaging.

**Step 5: Validate with a test contact**

Expected:
- contact can enter pipeline
- calendar booking works
- custom fields save correctly

### Task 3: Build Make Scenario for Qualified Prospect Intake

**Files:**
- Reference: `strategy/runbooks/scenario-revenue-os.md`

**Step 1: Trigger on Airtable qualified prospects**

Run when:
- `Prospect Status` is `qualified` or `queued`
- `Qualified?` is `Yes`
- no GHL contact ID exists

**Step 2: Add dedupe logic**

Search GHL by:
1. email
2. phone
3. company name fallback

Expected: one GHL contact per real prospect.

**Step 3: Create or update the GHL contact**

Write mapped fields and apply:
- `source:cold_email`

**Step 4: Create or verify outbound opportunity**

Ensure one open opportunity in `Outbound Sales`.

**Step 5: Write back to Airtable**

Store:
- GHL contact ID
- sync timestamp
- updated prospect status if needed

**Step 6: Test**

Expected:
- no duplicate contacts
- no duplicate opportunities

### Task 4: Build Make Scenario for Reply and Booking Sync

**Files:**
- Reference: `strategy/runbooks/scenario-revenue-os.md`

**Step 1: Capture inbound reply events from GHL**

Use webhook or native integration events for inbound email and SMS.

**Step 2: Match back to Airtable**

Use:
- Airtable ID if present
- else email
- else phone

**Step 3: Update Airtable on reply**

Set:
- `Prospect Status = replied`
- `Last Reply At`

Create or update linked opportunity:
- `Stage = replied`

**Step 4: Enforce review task**

Create one Airtable task:
- `Review reply and classify intent`

Expected: do not create duplicate open review tasks.

**Step 5: Capture booking events**

When `Discovery Call` is booked:
- set stage to `booked`
- write `Call Date`
- create task `Run discovery`

**Step 6: Test both branches**

Expected:
- reply path updates prospect and opportunity
- booking path updates opportunity and tasks

### Task 5: Build Make Scenario for Stage Progression and Won Handoff

**Files:**
- Reference: `strategy/runbooks/scenario-revenue-os.md`

**Step 1: Map GHL stages to Airtable opportunity stages**

Support:
- replied
- qualified
- booked
- discovery_complete
- audit_complete
- proposal_sent
- won
- lost
- nurture

**Step 2: Enforce next task creation**

Examples:
- `replied` -> `Qualify + book call`
- `Discovery Complete` -> `Prepare audit`
- `Proposal Sent` -> `Proposal follow-up`

**Step 3: Build won-deal handoff**

When stage becomes `Won`:
- validate required fields
- create or update client
- create onboarding tasks
- set client status to `onboarding`

**Step 4: Add failure handling**

If required fields are missing:
- do not create client
- create blocking review task
- write sync or validation note

**Step 5: Test**

Expected:
- one won deal creates one client
- rerun does not duplicate client

### Task 6: Build Native GoHighLevel Workflows

**Files:**
- Reference: `strategy/runbooks/scenario-revenue-os.md`

**Step 1: Build `Reply Detection`**

Expected:
- stage moves to `Replied`
- internal review task created
- future automated follow-up stops

**Step 2: Build `Booked Call`**

Expected:
- stage moves to `Booked`
- call confirmations and reminders send

**Step 3: Build `Proposal Sent`, `Won Deal`, and `No-Show Recovery`**

Use the runbook sequence and keep human review where specified.

**Step 4: Validate**

Simulate:
- inbound reply
- booking
- proposal stage change
- won stage change
- no-show

### Task 7: Build Notion Operating Layer

**Files:**
- Reference: `strategy/runbooks/scenario-revenue-os.md`

**Step 1: Create top-level Notion pages**

Create:
- SOPs
- Templates
- Playbooks
- Setup Log

**Step 2: Add SOPs**

At minimum:
- lead sourcing
- qualification
- manual cold email sending
- reply handling
- discovery call
- audit preparation
- onboarding

**Step 3: Add templates**

Create:
- cold email templates
- reply templates
- discovery script
- audit template
- proposal outline

**Step 4: Validate**

Expected: a VA can operate the system without relying on founder memory.

### Task 8: Launch Manual-First Outbound Motion

**Files:**
- Reference: `strategy/runbooks/scenario-revenue-os.md`

**Step 1: Build the first qualified batch**

Create 50 qualified home-service prospects in Airtable.

**Step 2: Send manually**

For each selected prospect:
- send the email manually
- increment send count
- stamp last-contacted time
- move the prospect to the next outreach state

**Step 3: Work replies daily**

Each day:
- review GHL conversations
- classify replies
- move stages
- complete tasks

**Step 4: Run calls and audits**

For booked calls:
- run the call
- log findings
- advance the opportunity

**Step 5: Review the weekly scorecard**

Measure:
- emails sent
- replies
- booked calls
- proposals
- wins

### Task 9: Build Delivery Module Library

**Files:**
- Reference: `strategy/runbooks/scenario-revenue-os.md`

**Step 1: Create v1 reusable modules**

Create records for:
- capture
- response
- qualification
- booking
- CRM update
- reminder
- recovery
- notification
- reporting

**Step 2: Add module metadata**

For each module, fill:
- trigger
- actions
- dependencies
- config inputs
- expected outcome
- common failure modes

**Step 3: Validate reuse**

Expected: modules can be reused across at least the primary niche without redesigning the system.

### Task 10: Hardening Review

**Files:**
- Modify: `strategy/runbooks/scenario-revenue-os.md`
- Modify: `strategy/runbooks/revenue-os-implementation-plan.md`

**Step 1: Review live system integrity**

Confirm:
- no object exists without status
- no active state exists without an open task
- no duplicate open opportunities exist
- every won opportunity has exactly one client

**Step 2: Test failure branches**

Test:
- bounce
- unsubscribe
- canceled booking
- no-show
- won deal with missing required data

**Step 3: Update the docs**

Capture:
- what changed
- what failed
- what remains manual

**Step 4: Commit**

```bash
git add strategy/runbooks/scenario-revenue-os.md strategy/runbooks/revenue-os-implementation-plan.md
git commit -m "docs: add revenue os runbook and implementation plan"
```

Expected: commit succeeds.
