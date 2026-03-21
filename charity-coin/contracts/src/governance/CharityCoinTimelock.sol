// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {TimelockController} from "@openzeppelin/contracts/governance/TimelockController.sol";

/// @title CharityCoinTimelock
/// @notice Timelock controller for the Charity Coin governance system.
/// @dev Wraps OpenZeppelin's TimelockController with ecosystem-specific defaults.
///      All governance-approved proposals must wait for the minimum delay before execution,
///      providing a safety window for users to react to approved changes.
///
///      Default configuration:
///        - Minimum delay: 2 days (172800 seconds)
///        - Proposers: the Governor contract
///        - Executors: open (address(0) means anyone can execute after delay)
contract CharityCoinTimelock is TimelockController {
    /// @notice Deploys the CharityCoinTimelock.
    /// @param minDelay   Minimum delay in seconds before a queued operation can be executed.
    /// @param proposers  Array of addresses allowed to schedule (propose) operations.
    /// @param executors  Array of addresses allowed to execute operations (address(0) = anyone).
    /// @param admin      Address granted the DEFAULT_ADMIN_ROLE (set to address(0) to renounce).
    constructor(
        uint256 minDelay,
        address[] memory proposers,
        address[] memory executors,
        address admin
    ) TimelockController(minDelay, proposers, executors, admin) {}
}
