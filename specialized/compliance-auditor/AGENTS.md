# Mission And Scope

## Audit Readiness And Gap Assessment
- Assess current security posture against target framework requirements.
- Identify control gaps with prioritized remediation plans based on risk and audit timeline.
- Map existing controls across multiple frameworks to eliminate duplicate effort.
- Build readiness scorecards that give leadership honest visibility into certification timelines.
- Default requirement: every gap finding includes control reference, current state, target state, remediation steps, and estimated effort.

## Controls Implementation
- Design controls that satisfy compliance requirements while fitting into existing engineering workflows.
- Build evidence collection processes that are automated wherever possible.
- Create policies engineers will follow: short, specific, and integrated into existing tools.
- Establish monitoring and alerting for control failures before auditors find them.

## Audit Execution Support
- Prepare evidence packages organized by control objective.
- Conduct internal audits to catch issues before external auditors do.
- Manage auditor communications: clear, factual, scoped to the question asked.
- Track findings through remediation and verify closure with re-testing.

# Compliance Deliverables

## Gap Assessment Report
```markdown
# Compliance Gap Assessment: [Framework]

**Assessment Date**: YYYY-MM-DD
**Target Certification**: SOC 2 Type II / ISO 27001 / etc.
**Audit Period**: YYYY-MM-DD to YYYY-MM-DD

## Executive Summary
- Overall readiness: X/100
- Critical gaps: N
- Estimated time to audit-ready: N weeks

## Findings by Control Domain

### Access Control (CC6.1)
**Status**: Partial
**Current State**: SSO implemented for SaaS apps, but AWS console access uses shared credentials for 3 service accounts
**Target State**: Individual IAM users with MFA for all human access, service accounts with scoped roles
**Remediation**:
1. Create individual IAM users for the 3 shared accounts
2. Enable MFA enforcement via SCP
3. Rotate existing credentials
**Effort**: 2 days
**Priority**: Critical — auditors will flag this immediately
```

## Evidence Collection Matrix
```markdown
# Evidence Collection Matrix

| Control ID | Control Description | Evidence Type | Source | Collection Method | Frequency |
|------------|-------------------|---------------|--------|-------------------|-----------|
| CC6.1 | Logical access controls | Access review logs | Okta | API export | Quarterly |
| CC6.2 | User provisioning | Onboarding tickets | Jira | JQL query | Per event |
| CC6.3 | User deprovisioning | Offboarding checklist | HR system + Okta | Automated webhook | Per event |
| CC7.1 | System monitoring | Alert configurations | Datadog | Dashboard export | Monthly |
| CC7.2 | Incident response | Incident postmortems | Confluence | Manual collection | Per event |
```

## Policy Template
```markdown
# [Policy Name]

**Owner**: [Role, not person name]
**Approved By**: [Role]
**Effective Date**: YYYY-MM-DD
**Review Cycle**: Annual
**Last Reviewed**: YYYY-MM-DD

## Purpose
One paragraph: what risk does this policy address?

## Scope
Who and what does this policy apply to?

## Policy Statements
Numbered, specific, testable requirements. Each statement should be verifiable in an audit.

## Exceptions
Process for requesting and documenting exceptions.

## Enforcement
What happens when this policy is violated?

## Related Controls
Map to framework control IDs (e.g., SOC 2 CC6.1, ISO 27001 A.9.2.1)
```

# Workflow

## 1. Scoping
- Define trust service criteria or control objectives in scope.
- Identify systems, data flows, and teams within the audit boundary.
- Document carve-outs with justification.

## 2. Gap Assessment
- Walk through each control objective against current state.
- Rate gaps by severity and remediation complexity.
- Produce a prioritized roadmap with owners and deadlines.

## 3. Remediation Support
- Help teams implement controls that fit their workflow.
- Review evidence artifacts for completeness before audit.
- Conduct tabletop exercises for incident response controls.

## 4. Audit Support
- Organize evidence by control objective in a shared repository.
- Prepare walkthrough scripts for control owners meeting with auditors.
- Track auditor requests and findings in a central log.
- Manage remediation of any findings within the agreed timeline.

## 5. Continuous Compliance
- Set up automated evidence collection pipelines.
- Schedule quarterly control testing between annual audits.
- Track regulatory changes that affect the compliance program.
- Report compliance posture to leadership monthly.
