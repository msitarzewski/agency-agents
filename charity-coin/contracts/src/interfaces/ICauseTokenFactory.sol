// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title ICauseTokenFactory
/// @notice Interface for the factory that deploys cause token clones via EIP-1167.
interface ICauseTokenFactory {
    // ──────────────────────────────────────────────────────────────────────
    // Events
    // ──────────────────────────────────────────────────────────────────────

    /// @notice Emitted when a new cause token is created.
    /// @param causeId      Unique identifier derived from the token name.
    /// @param causeToken   Address of the newly deployed cause token clone.
    /// @param causeName    Human-readable cause name.
    /// @param charityWallet Wallet that receives charity fee distributions.
    event CauseCreated(
        bytes32 indexed causeId,
        address indexed causeToken,
        string causeName,
        address charityWallet
    );

    // ──────────────────────────────────────────────────────────────────────
    // Errors
    // ──────────────────────────────────────────────────────────────────────

    /// @notice Thrown when a cause with the given id already exists.
    error CauseAlreadyExists();

    /// @notice Thrown when a zero address is provided where a valid address is required.
    error ZeroAddress();

    // ──────────────────────────────────────────────────────────────────────
    // Functions
    // ──────────────────────────────────────────────────────────────────────

    /// @notice Deploys a new cause token clone.
    /// @param name             ERC-20 token name.
    /// @param symbol           ERC-20 token symbol.
    /// @param causeName_       Human-readable cause name.
    /// @param causeDescription Short description of the cause.
    /// @param charityWallet    Wallet for charity fee distributions.
    /// @return causeToken      Address of the deployed clone.
    function createCause(
        string calldata name,
        string calldata symbol,
        string calldata causeName_,
        string calldata causeDescription,
        address charityWallet
    ) external returns (address causeToken);

    /// @notice Returns the cause token address for a given cause id.
    /// @param causeId Unique cause identifier.
    /// @return causeToken Address of the cause token (zero if not found).
    function getCause(bytes32 causeId) external view returns (address causeToken);

    /// @notice Returns all deployed cause token addresses.
    /// @return An array of cause token addresses.
    function getAllCauses() external view returns (address[] memory);

    /// @notice Checks whether an address is a registered cause token.
    /// @param causeToken Address to check.
    /// @return True if the address is a registered cause token.
    function isCause(address causeToken) external view returns (bool);

    /// @notice Returns the total number of causes created.
    /// @return The number of deployed cause tokens.
    function causeCount() external view returns (uint256);
}
