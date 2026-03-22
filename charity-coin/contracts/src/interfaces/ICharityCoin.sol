// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {IERC20Permit} from "@openzeppelin/contracts/token/ERC20/extensions/IERC20Permit.sol";

/// @title ICharityCoin
/// @notice Interface for the CHA token — the primary ERC-20 of the Charity Coin ecosystem.
/// @dev Extends IERC20 and IERC20Permit with burn capabilities.
interface ICharityCoin is IERC20, IERC20Permit {
    // ──────────────────────────────────────────────────────────────────────
    // Errors
    // ──────────────────────────────────────────────────────────────────────

    /// @notice Thrown when minting would exceed the maximum supply cap.
    error MaxSupplyExceeded();

    // ──────────────────────────────────────────────────────────────────────
    // Functions
    // ──────────────────────────────────────────────────────────────────────

    /// @notice Returns the hard-capped maximum supply of CHA tokens.
    function MAX_SUPPLY() external view returns (uint256);

    /// @notice Mints `amount` CHA tokens to `to`.
    /// @param to     Recipient of the newly minted tokens.
    /// @param amount Number of tokens to mint (in wei).
    function mint(address to, uint256 amount) external;

    /// @notice Burns `amount` CHA tokens from the caller's balance.
    /// @param amount Number of tokens to burn (in wei).
    function burn(uint256 amount) external;

    /// @notice Burns `amount` CHA tokens from `account`, deducting from the caller's allowance.
    /// @param account Owner of the tokens to burn.
    /// @param amount  Number of tokens to burn (in wei).
    function burnFrom(address account, uint256 amount) external;

    /// @notice Pauses all token transfers.
    function pause() external;

    /// @notice Unpauses all token transfers.
    function unpause() external;
}
