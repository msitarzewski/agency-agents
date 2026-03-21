// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Governor} from "@openzeppelin/contracts/governance/Governor.sol";
import {GovernorSettings} from "@openzeppelin/contracts/governance/extensions/GovernorSettings.sol";
import {GovernorCountingSimple} from "@openzeppelin/contracts/governance/extensions/GovernorCountingSimple.sol";
import {GovernorVotes} from "@openzeppelin/contracts/governance/extensions/GovernorVotes.sol";
import {GovernorVotesQuorumFraction} from "@openzeppelin/contracts/governance/extensions/GovernorVotesQuorumFraction.sol";
import {GovernorTimelockControl} from "@openzeppelin/contracts/governance/extensions/GovernorTimelockControl.sol";
import {TimelockController} from "@openzeppelin/contracts/governance/TimelockController.sol";
import {IVotes} from "@openzeppelin/contracts/governance/utils/IVotes.sol";

/// @title CharityCoinGovernor
/// @notice On-chain governance for the Charity Coin ecosystem.
/// @dev Built on OpenZeppelin v5 Governor with the following configuration:
///   - Voting delay:     1 day  (~7200 blocks on Base at 12s/block)
///   - Voting period:    5 days (~36000 blocks on Base)
///   - Proposal threshold: 100,000 CHA
///   - Quorum:           4% of total supply
///   - Timelock:         2-day minimum delay before execution
///
/// All governance actions (fee changes, new causes, parameter updates) flow through
/// this governor and its associated timelock.
contract CharityCoinGovernor is
    Governor,
    GovernorSettings,
    GovernorCountingSimple,
    GovernorVotes,
    GovernorVotesQuorumFraction,
    GovernorTimelockControl
{
    /// @notice Deploys the CharityCoinGovernor.
    /// @param token_    The CHA token (must implement IVotes / ERC20Votes).
    /// @param timelock_ The TimelockController that executes approved proposals.
    constructor(
        IVotes token_,
        TimelockController timelock_
    )
        Governor("CharityCoinGovernor")
        GovernorSettings(
            7200,       // votingDelay: ~1 day on Base (12s blocks)
            36000,      // votingPeriod: ~5 days on Base
            100_000e18  // proposalThreshold: 100k CHA
        )
        GovernorVotes(token_)
        GovernorVotesQuorumFraction(4) // 4% quorum
        GovernorTimelockControl(timelock_)
    {}

    // ──────────────────────────────────────────────────────────────────────
    // Required Overrides (OZ v5 Governor diamond)
    // ──────────────────────────────────────────────────────────────────────

    /// @dev Returns the delay (in blocks) before voting begins on a proposal.
    function votingDelay() public view override(Governor, GovernorSettings) returns (uint256) {
        return super.votingDelay();
    }

    /// @dev Returns the duration (in blocks) of the voting period.
    function votingPeriod() public view override(Governor, GovernorSettings) returns (uint256) {
        return super.votingPeriod();
    }

    /// @dev Returns the minimum CHA balance required to create a proposal.
    function proposalThreshold() public view override(Governor, GovernorSettings) returns (uint256) {
        return super.proposalThreshold();
    }

    /// @dev Returns the current quorum requirement (number of votes needed).
    function quorum(uint256 blockNumber)
        public
        view
        override(Governor, GovernorVotesQuorumFraction)
        returns (uint256)
    {
        return super.quorum(blockNumber);
    }

    /// @dev Returns the state of a given proposal, incorporating timelock status.
    function state(uint256 proposalId)
        public
        view
        override(Governor, GovernorTimelockControl)
        returns (ProposalState)
    {
        return super.state(proposalId);
    }

    /// @dev Returns whether `account` needs to delegate to themselves before voting.
    function proposalNeedsQueuing(uint256 proposalId)
        public
        view
        override(Governor, GovernorTimelockControl)
        returns (bool)
    {
        return super.proposalNeedsQueuing(proposalId);
    }

    /// @dev Internal hook to queue operations in the timelock.
    function _queueOperations(
        uint256 proposalId,
        address[] memory targets,
        uint256[] memory values,
        bytes[] memory calldatas,
        bytes32 descriptionHash
    ) internal override(Governor, GovernorTimelockControl) returns (uint48) {
        return super._queueOperations(proposalId, targets, values, calldatas, descriptionHash);
    }

    /// @dev Internal hook to execute operations via the timelock.
    function _executeOperations(
        uint256 proposalId,
        address[] memory targets,
        uint256[] memory values,
        bytes[] memory calldatas,
        bytes32 descriptionHash
    ) internal override(Governor, GovernorTimelockControl) {
        super._executeOperations(proposalId, targets, values, calldatas, descriptionHash);
    }

    /// @dev Internal hook to cancel operations in the timelock.
    function _cancel(
        address[] memory targets,
        uint256[] memory values,
        bytes[] memory calldatas,
        bytes32 descriptionHash
    ) internal override(Governor, GovernorTimelockControl) returns (uint256) {
        return super._cancel(targets, values, calldatas, descriptionHash);
    }

    /// @dev Returns the executor address (the timelock).
    function _executor() internal view override(Governor, GovernorTimelockControl) returns (address) {
        return super._executor();
    }
}
