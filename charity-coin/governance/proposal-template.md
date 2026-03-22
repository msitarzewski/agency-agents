# Charity Coin Governance Proposal Template

Use this template when drafting a governance proposal for the Charity Coin protocol. Complete every section. If a section is not applicable, state "N/A" with a brief explanation.

---

## Proposal Header

| Field | Value |
|---|---|
| **Title** | [Short, descriptive title -- e.g., "Reduce Conversion Fee to 200 bps"] |
| **Author** | [Name or pseudonym and Ethereum address] |
| **Date** | [Date of initial draft, YYYY-MM-DD] |
| **Type** | [Add Cause / Fee Adjustment / Parameter Change / Treasury / Emergency] |
| **Status** | [Draft / Discussion / On-Chain / Voting / Queued / Executed / Defeated / Canceled] |

---

## Summary

Provide a concise overview of the proposal in two to four sentences. State what is being proposed, the primary motivation, and the expected outcome.

> *Example: This proposal adjusts the total conversion fee from 300 bps to 200 bps to increase the competitiveness of CHA conversions and encourage higher conversion volume.*

---

## Motivation

Explain the problem or opportunity that this proposal addresses. Include relevant context, data, or community feedback that supports the need for this change.

- What is the current situation?
- What problem does this proposal solve?
- Why is this change needed now?
- What evidence supports this proposal?

---

## Specification

Provide the complete technical details of the proposal.

### Target Contracts

List every contract that will be called by this proposal.

| Contract | Address | Function |
|---|---|---|
| *e.g., ConversionEngine* | `0x...` | `setTotalFeeBps(uint256)` |

### Function Calls

For each function call, specify:

```
Target:    [Contract address]
Function:  [Function signature]
Arguments: [Argument values]
Value:     [ETH value, typically 0]
```

### Parameter Changes

If the proposal modifies protocol parameters, provide a before-and-after comparison.

| Parameter | Current Value | Proposed Value | Unit |
|---|---|---|---|
| *e.g., totalFeeBps* | 300 | 200 | basis points |

### On-Chain Actions

Describe the exact sequence of operations that will be executed through the Timelock.

---

## Security Considerations

Analyze the security implications of this proposal.

- **Smart contract risk:** Could this change introduce a vulnerability or interact unexpectedly with existing contracts?
- **Economic risk:** Could this change be exploited for economic gain at the expense of the protocol or its users?
- **Centralization risk:** Does this proposal increase or decrease centralization of control?
- **Audit status:** Has the proposed change been reviewed or audited? If so, provide links to audit reports.
- **Invariants:** List any protocol invariants that must hold after execution and explain why they will be preserved.

---

## Impact Analysis

### Affected Stakeholders

Identify all parties affected by this proposal and describe the impact on each.

| Stakeholder | Impact |
|---|---|
| CHA holders | *e.g., Reduced fee increases net value received per conversion* |
| Charity recipients | *e.g., Lower fee share may reduce charity distributions* |
| Liquidity providers | *e.g., Lower liquidity fee share may reduce incentives* |
| Operations team | *e.g., Lower ops fee share reduces operational funding* |

### Economic Impact

- How does this proposal affect protocol revenue?
- How does this proposal affect user costs?
- Are there any second-order effects (e.g., changes in user behavior)?

### Compatibility

- Is this proposal backward-compatible with existing integrations?
- Does it require any off-chain changes (front-end updates, API changes, documentation)?

---

## Implementation Steps

Provide a step-by-step plan for implementing and deploying this proposal.

1. **Pre-submission**
   - [ ] Draft proposal and solicit community feedback.
   - [ ] Conduct technical review of proposed contract calls.
   - [ ] Verify proposer holds at least 100,000 CHA (delegated or owned).

2. **On-chain submission**
   - [ ] Submit proposal to `CharityCoinGovernor` with the specified targets, values, calldatas, and description.
   - [ ] Record the proposal ID.

3. **Voting period**
   - [ ] Monitor vote counts during the 5-day voting period.
   - [ ] Engage with the community to address questions or concerns.

4. **Post-vote**
   - [ ] If passed, queue the proposal in the Timelock.
   - [ ] Monitor the 2-day timelock delay.

5. **Execution**
   - [ ] Execute the proposal after the timelock delay has elapsed.
   - [ ] Verify on-chain state matches expected outcomes.

6. **Post-execution**
   - [ ] Update relevant documentation.
   - [ ] Communicate results to the community.
   - [ ] Monitor protocol behavior for any unexpected effects.

---

## Timeline

| Phase | Duration | Dates (estimated) |
|---|---|---|
| Draft and community discussion | [e.g., 3-7 days] | [Start -- End] |
| On-chain submission | 1 transaction | [Date] |
| Voting delay | ~1 day (7,200 blocks) | [Start -- End] |
| Voting period | ~5 days (36,000 blocks) | [Start -- End] |
| Timelock delay | 2 days (172,800 seconds) | [Start -- End] |
| Execution | 1 transaction | [Date] |
| **Total (on-chain)** | **~8 days minimum** | |

---

## References

List any supporting documents, forum discussions, audit reports, or related proposals.

- [Link to forum discussion]
- [Link to related proposal]
- [Link to audit report]
- [Link to relevant contract source code]

---

## Changelog

Track revisions to this proposal.

| Date | Author | Description |
|---|---|---|
| YYYY-MM-DD | [Author] | Initial draft |

---

*By submitting this proposal, the author affirms that they have reviewed the Charity Coin Governance Framework and that the proposal complies with all governance requirements.*
