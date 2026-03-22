# Charity Coin Governance Framework

## 1. Overview

The Charity Coin governance system enables CHA token holders to collectively manage and evolve the protocol. All material changes to the ecosystem -- including fee parameters, cause onboarding, treasury operations, and emergency actions -- require approval through on-chain governance.

Governance is implemented via the `CharityCoinGovernor` smart contract, built on the OpenZeppelin Governor framework (v5), and enforced through the `CharityCoinTimelock` controller. Together these contracts ensure that every approved action undergoes a mandatory delay before execution, giving the community time to review and react.

### Core Principles

- **Decentralization.** Decision-making authority rests with CHA holders, not a central team.
- **Transparency.** All proposals, votes, and executions occur on-chain and are publicly auditable.
- **Safety.** A mandatory timelock delay protects stakeholders from hasty or malicious changes.
- **Accessibility.** Any holder meeting the proposal threshold can submit governance proposals.
- **Accountability.** Fee distribution, cause management, and parameter changes are all governed by verifiable smart contract logic.

---

## 2. Governance Architecture

| Component | Contract | Role |
|---|---|---|
| Governor | `CharityCoinGovernor` | Manages proposal lifecycle, voting, and quorum enforcement |
| Timelock | `CharityCoinTimelock` | Queues approved proposals and enforces a minimum execution delay |
| Token | CHA (ERC20Votes) | Provides voting power through balance snapshots and delegation |
| Conversion Engine | `IConversionEngine` | Governed contract -- fee rates and conversion parameters |
| Fee Router | `IFeeRouter` | Governed contract -- fee distribution shares, slippage, operations wallet |

### Execution Flow

All governance actions are executed by the Timelock controller, not the Governor directly. The Governor contract has the `PROPOSER_ROLE` on the Timelock, and execution is open (`address(0)` as executor), meaning anyone can trigger execution once the delay has elapsed.

---

## 3. Proposal Types

### 3.1 Add Cause

Register a new charitable cause within the ecosystem. This involves deploying a new cause token and registering it in the Cause Token Factory.

**Typical targets:** CauseTokenFactory, relevant registry contracts.

### 3.2 Fee Adjustment

Modify the total fee rate applied to CHA-to-cause-token conversions, or adjust the distribution shares among charity, liquidity, and operations.

**Governed parameters:**
- `ConversionEngine.setTotalFeeBps(uint256 newFeeBps)` -- Total fee rate (capped at `MAX_FEE_BPS`).
- `FeeRouter.setFeeShares(uint256 charity, uint256 liquidity, uint256 ops)` -- Distribution split (must sum to 10,000 bps).
- `FeeRouter.setMaxSlippageBps(uint256 newSlippageBps)` -- Maximum swap slippage (capped at 500 bps / 5%).

### 3.3 Parameter Change

Update protocol parameters that do not fall under fee adjustments. Examples include modifying the operations wallet address via `FeeRouter.setOperationsWallet(address)`.

### 3.4 Treasury

Proposals that allocate or move protocol-owned funds. Treasury proposals may involve transferring tokens held by the Timelock to specific recipients for grants, partnerships, or operational expenses.

### 3.5 Emergency

Critical actions required to protect the protocol from active threats. Emergency proposals follow the standard governance flow but may be accompanied by an admin pause (see Section 8) to halt affected contracts while the proposal proceeds through voting and timelock.

---

## 4. Proposal Lifecycle

Every proposal progresses through five stages:

```
Draft --> Discussion --> Voting --> Timelock --> Execution
```

### 4.1 Draft

The proposal author prepares a complete proposal using the standard template (see `proposal-template.md`). The draft should include motivation, technical specification, security considerations, and an impact analysis.

**Requirements to submit on-chain:**
- The proposer must hold or have been delegated at least **100,000 CHA** (the proposal threshold, denominated as `100_000e18`).

### 4.2 Discussion

After the proposal is submitted on-chain, there is a mandatory **voting delay of 1 day (~7,200 blocks on Base at 12 seconds per block)**. During this period:

- The community reviews the proposal details.
- Token holders may adjust their delegations.
- No votes can be cast.

This delay also ensures that voting power snapshots are taken at the block the proposal was created, preventing last-minute token transfers from influencing the vote.

### 4.3 Voting

Once the voting delay expires, the **voting period lasts 5 days (~36,000 blocks on Base)**. During this window:

- Any address with delegated CHA voting power at the snapshot block may cast a vote.
- Votes are cast as **For**, **Against**, or **Abstain** (GovernorCountingSimple).
- Each unit of delegated CHA equals one vote.

**Quorum requirement:** At least **4% of total CHA supply** (measured at the proposal snapshot block) must participate as For or Abstain votes for the proposal to be valid.

**Passing condition:** A proposal passes if it meets quorum and receives more For votes than Against votes.

### 4.4 Timelock

A passing proposal is queued in the `CharityCoinTimelock` controller with a **minimum delay of 2 days (172,800 seconds)**. During this period:

- The community can review the exact transactions that will be executed.
- Users who disagree with the outcome can take protective action (e.g., exit positions).
- The Timelock admin (if one exists) may cancel the proposal in extreme circumstances.

### 4.5 Execution

After the timelock delay has elapsed, anyone may call `execute()` on the Governor to trigger the queued operations through the Timelock. Execution is permissionless -- the Timelock is configured with `address(0)` as the executor, allowing any address to finalize the proposal.

---

## 5. Voting Mechanics

### 5.1 Parameters

| Parameter | Value | Notes |
|---|---|---|
| Voting Delay | 7,200 blocks (~1 day) | Time between proposal creation and vote start |
| Voting Period | 36,000 blocks (~5 days) | Duration of the voting window |
| Proposal Threshold | 100,000 CHA | Minimum CHA required to create a proposal |
| Quorum | 4% of total supply | Minimum participation for a valid vote |
| Timelock Delay | 172,800 seconds (2 days) | Minimum delay before execution of approved proposals |

### 5.2 Vote Types

The Governor uses `GovernorCountingSimple`, which supports three vote options:

- **For** -- Support the proposal.
- **Against** -- Oppose the proposal.
- **Abstain** -- Count toward quorum without supporting or opposing.

Each address may only vote once per proposal. Voting power is determined by the CHA balance delegated to the voter at the snapshot block (the block at which the proposal was created).

### 5.3 Proposal States

A proposal may be in one of the following states:

| State | Description |
|---|---|
| Pending | Created but voting delay has not elapsed |
| Active | Voting is in progress |
| Canceled | Proposal was canceled by its proposer or guardian |
| Defeated | Voting concluded without meeting quorum or with more Against than For votes |
| Succeeded | Voting concluded with quorum met and more For than Against votes |
| Queued | Proposal has been submitted to the Timelock |
| Expired | Queued proposal was not executed before the Timelock grace period |
| Executed | Proposal transactions have been executed successfully |

---

## 6. Delegation Mechanics

CHA uses the ERC20Votes extension, which requires explicit delegation before voting power is activated. Key points:

### 6.1 Self-Delegation

Token holders must delegate to themselves (or another address) to activate their voting power. Simply holding CHA does not grant votes. Self-delegation is a one-time on-chain transaction.

### 6.2 Third-Party Delegation

Holders may delegate their voting power to any Ethereum address. This is useful for holders who prefer to entrust their votes to a community representative or delegate who actively participates in governance.

### 6.3 Delegation Properties

- Delegation is all-or-nothing for a given address; partial delegation is not supported.
- Delegating to a new address automatically revokes the previous delegation.
- Delegation does not transfer token ownership; the delegator retains full control of their CHA.
- Voting power snapshots are taken at proposal creation time, so delegation changes after a proposal is created do not affect that proposal's vote.

### 6.4 Checkpointing

The ERC20Votes extension maintains historical checkpoints of delegated balances. This ensures that voting power for any proposal is determined by the state at the proposal's snapshot block, providing resistance against vote manipulation through token transfers.

---

## 7. Timelock Details

The `CharityCoinTimelock` wraps OpenZeppelin's `TimelockController` with the following default configuration:

| Setting | Value |
|---|---|
| Minimum Delay | 2 days (172,800 seconds) |
| Proposers | The `CharityCoinGovernor` contract |
| Executors | Open (anyone -- `address(0)`) |
| Admin | Configurable at deployment (can be renounced by setting to `address(0)`) |

### Role-Based Access

- **PROPOSER_ROLE:** Only the Governor contract can schedule operations in the Timelock.
- **EXECUTOR_ROLE:** Granted to `address(0)`, meaning any address can execute a matured operation.
- **DEFAULT_ADMIN_ROLE:** Controls role assignments. Can be renounced for full decentralization.
- **CANCELLER_ROLE:** Inherited from TimelockController. Allows cancellation of queued operations.

---

## 8. Emergency Procedures

### 8.1 Admin Pause

If an active threat is identified (e.g., a vulnerability in a governed contract), the protocol admin (if the admin role has not been renounced) may:

1. **Pause** affected contracts to prevent further damage.
2. **Submit an emergency proposal** through standard governance to deploy a fix or remediation.
3. **Cancel** any queued Timelock operations that may be compromised.

### 8.2 Timelock Cancellation

The Timelock admin or any address with the `CANCELLER_ROLE` can cancel a queued proposal before it is executed. This serves as a last-resort mechanism to block a proposal that has been identified as harmful after passing the vote.

### 8.3 Post-Emergency Recovery

After an emergency pause:

1. A governance proposal should be submitted detailing the incident and the proposed fix.
2. The fix undergoes standard voting and timelock processes.
3. Once executed, the pause is lifted and normal operations resume.
4. A post-mortem report should be published to the community.

---

## 9. Governance Participation Guide

### For Token Holders

1. **Acquire CHA** tokens.
2. **Delegate** your voting power (to yourself or a trusted delegate).
3. **Review** active proposals during the voting period.
4. **Cast your vote** (For, Against, or Abstain).
5. **Monitor** the timelock period for queued proposals.

### For Proposal Authors

1. **Accumulate or receive delegation** of at least 100,000 CHA.
2. **Draft** your proposal following the standard template.
3. **Discuss** with the community before submitting on-chain.
4. **Submit** the proposal on-chain via the Governor contract.
5. **Advocate** for your proposal during the voting period.
6. **Queue** the proposal after a successful vote.
7. **Execute** the proposal after the timelock delay.

---

## 10. Contract References

| Contract | Source |
|---|---|
| CharityCoinGovernor | `contracts/src/governance/CharityCoinGovernor.sol` |
| CharityCoinTimelock | `contracts/src/governance/CharityCoinTimelock.sol` |
| IConversionEngine | `contracts/src/interfaces/IConversionEngine.sol` |
| IFeeRouter | `contracts/src/interfaces/IFeeRouter.sol` |

---

*This document is maintained by the Charity Coin governance community. Changes to the governance framework itself require a governance proposal of type "Parameter Change."*
