// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {ERC20Burnable} from "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import {ERC20Permit} from "@openzeppelin/contracts/token/ERC20/extensions/ERC20Permit.sol";
import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";
import {Pausable} from "@openzeppelin/contracts/utils/Pausable.sol";

/// @title CharityCoin (CHA)
/// @notice The primary ERC-20 token of the Charity Coin ecosystem.
/// @dev Features:
///   - Hard-capped supply of 1 billion tokens.
///   - Role-based minting (MINTER_ROLE) and pausing (PAUSER_ROLE).
///   - EIP-2612 permit for gasless approvals.
///   - Burnable to enable the CHA -> CauseToken conversion flow.
///
/// Built with OpenZeppelin v5 contracts. Uses the `_update` hook for pausable behavior.
contract CharityCoin is ERC20, ERC20Burnable, ERC20Permit, AccessControl, Pausable {
    // ──────────────────────────────────────────────────────────────────────
    // Constants & Roles
    // ──────────────────────────────────────────────────────────────────────

    /// @notice Maximum supply cap: 1 billion CHA (18 decimals).
    uint256 public constant MAX_SUPPLY = 1_000_000_000 * 10 ** 18;

    /// @notice Role identifier for addresses permitted to mint new CHA tokens.
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");

    /// @notice Role identifier for addresses permitted to pause/unpause transfers.
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");

    // ──────────────────────────────────────────────────────────────────────
    // Errors
    // ──────────────────────────────────────────────────────────────────────

    /// @notice Thrown when a mint would push total supply beyond MAX_SUPPLY.
    error MaxSupplyExceeded();

    // ──────────────────────────────────────────────────────────────────────
    // Constructor
    // ──────────────────────────────────────────────────────────────────────

    /// @notice Deploys the CharityCoin token.
    /// @param defaultAdmin Address granted DEFAULT_ADMIN_ROLE (can manage all roles).
    /// @param minter       Address granted MINTER_ROLE (can mint tokens).
    constructor(
        address defaultAdmin,
        address minter
    ) ERC20("CharityCoin", "CHA") ERC20Permit("CharityCoin") {
        _grantRole(DEFAULT_ADMIN_ROLE, defaultAdmin);
        _grantRole(MINTER_ROLE, minter);
        _grantRole(PAUSER_ROLE, defaultAdmin);
    }

    // ──────────────────────────────────────────────────────────────────────
    // External / Public Functions
    // ──────────────────────────────────────────────────────────────────────

    /// @notice Mints `amount` CHA tokens to `to`.
    /// @dev Reverts with `MaxSupplyExceeded` if the mint would exceed the cap.
    /// @param to     Recipient of the minted tokens.
    /// @param amount Number of tokens to mint (in wei).
    function mint(address to, uint256 amount) external onlyRole(MINTER_ROLE) {
        if (totalSupply() + amount > MAX_SUPPLY) {
            revert MaxSupplyExceeded();
        }
        _mint(to, amount);
    }

    /// @notice Pauses all token transfers, mints, and burns.
    function pause() external onlyRole(PAUSER_ROLE) {
        _pause();
    }

    /// @notice Unpauses all token transfers, mints, and burns.
    function unpause() external onlyRole(PAUSER_ROLE) {
        _unpause();
    }

    // ──────────────────────────────────────────────────────────────────────
    // Internal Overrides (OZ v5 pattern)
    // ──────────────────────────────────────────────────────────────────────

    /// @dev Hook that enforces the Pausable check on every token movement.
    ///      OpenZeppelin v5 uses `_update` instead of the legacy `_beforeTokenTransfer`.
    function _update(
        address from,
        address to,
        uint256 value
    ) internal override(ERC20) whenNotPaused {
        super._update(from, to, value);
    }
}
