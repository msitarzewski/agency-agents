// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

/// @title ICauseToken
/// @notice Interface for lightweight cause-specific ERC-20 tokens deployed via EIP-1167 clones.
/// @dev Each cause token tracks donations toward a specific charitable cause.
interface ICauseToken is IERC20 {
    // ──────────────────────────────────────────────────────────────────────
    // Errors
    // ──────────────────────────────────────────────────────────────────────

    /// @notice Thrown when `initialize` is called more than once.
    error AlreadyInitialized();

    /// @notice Thrown when a zero address is provided where a valid address is required.
    error ZeroAddress();

    // ──────────────────────────────────────────────────────────────────────
    // Functions
    // ──────────────────────────────────────────────────────────────────────

    /// @notice Initializes the cause token clone with its metadata and minter.
    /// @param name_            ERC-20 token name.
    /// @param symbol_          ERC-20 token symbol.
    /// @param causeName_       Human-readable cause name (e.g., "Clean Water Initiative").
    /// @param causeDescription_ Short description of the charitable cause.
    /// @param charityWallet_   Wallet that receives the charity share of conversion fees.
    /// @param causeId_         Unique identifier for this cause.
    /// @param minter_          Address authorized to mint tokens (the ConversionEngine).
    function initialize(
        string calldata name_,
        string calldata symbol_,
        string calldata causeName_,
        string calldata causeDescription_,
        address charityWallet_,
        bytes32 causeId_,
        address minter_
    ) external;

    /// @notice Mints `amount` cause tokens to `to`. Only callable by the minter.
    /// @param to     Recipient of the minted tokens.
    /// @param amount Number of tokens to mint (in wei).
    function mint(address to, uint256 amount) external;

    /// @notice Returns the human-readable name of the charitable cause.
    function causeName() external view returns (string memory);

    /// @notice Returns a short description of the charitable cause.
    function causeDescription() external view returns (string memory);

    /// @notice Returns the wallet address that receives charity fee distributions.
    function charityWallet() external view returns (address);

    /// @notice Returns the unique identifier for this cause.
    function causeId() external view returns (bytes32);
}
