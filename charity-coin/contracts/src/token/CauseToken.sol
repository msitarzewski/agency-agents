// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";

/// @title CauseToken
/// @notice A lightweight ERC-20 token representing donations toward a specific charitable cause.
/// @dev Deployed as an EIP-1167 minimal proxy clone. Uses an initializable pattern instead of
///      a constructor so that the same implementation bytecode can be reused across all causes.
///
///      Key design decisions:
///        - No supply cap: cause tokens are minted 1:1 with burned CHA.
///        - MINTER_ROLE is granted exclusively to the ConversionEngine.
///        - Cause metadata (name, description, wallet, id) is set once during initialization.
contract CauseToken is ERC20, AccessControl {
    // ──────────────────────────────────────────────────────────────────────
    // Constants & Roles
    // ──────────────────────────────────────────────────────────────────────

    /// @notice Role identifier for addresses permitted to mint cause tokens.
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");

    // ──────────────────────────────────────────────────────────────────────
    // Storage (set once via `initialize`)
    // ──────────────────────────────────────────────────────────────────────

    /// @notice Human-readable name of the charitable cause.
    string public causeName;

    /// @notice Short description of the charitable cause.
    string public causeDescription;

    /// @notice Wallet that receives the charity share of conversion fees.
    address public charityWallet;

    /// @notice Unique identifier for this cause (keccak256 of the token name).
    bytes32 public causeId;

    /// @dev Guard to ensure `initialize` can only be called once.
    bool private _initialized;

    /// @dev Stored token name (overrides ERC20 immutable name).
    string private _tokenName;

    /// @dev Stored token symbol (overrides ERC20 immutable symbol).
    string private _tokenSymbol;

    // ──────────────────────────────────────────────────────────────────────
    // Errors
    // ──────────────────────────────────────────────────────────────────────

    /// @notice Thrown when `initialize` is called more than once.
    error AlreadyInitialized();

    /// @notice Thrown when a zero address is provided where a valid address is required.
    error ZeroAddress();

    // ──────────────────────────────────────────────────────────────────────
    // Constructor
    // ──────────────────────────────────────────────────────────────────────

    /// @dev The constructor is only used for the implementation contract.
    ///      Clones skip the constructor and rely on `initialize` instead.
    constructor() ERC20("CauseToken", "CAUSE") {
        // Mark the implementation as initialized to prevent misuse.
        _initialized = true;
    }

    // ──────────────────────────────────────────────────────────────────────
    // Initialization (for clones)
    // ──────────────────────────────────────────────────────────────────────

    /// @notice Initializes a freshly cloned CauseToken with its metadata and minter role.
    /// @dev Can only be called once. Reverts with `AlreadyInitialized` on subsequent calls.
    /// @param name_             ERC-20 token name.
    /// @param symbol_           ERC-20 token symbol.
    /// @param causeName_        Human-readable cause name.
    /// @param causeDescription_ Short description of the cause.
    /// @param charityWallet_    Wallet for charity fee distributions.
    /// @param causeId_          Unique cause identifier.
    /// @param minter_           Address authorized to mint (the ConversionEngine).
    function initialize(
        string calldata name_,
        string calldata symbol_,
        string calldata causeName_,
        string calldata causeDescription_,
        address charityWallet_,
        bytes32 causeId_,
        address minter_
    ) external {
        if (_initialized) revert AlreadyInitialized();
        if (charityWallet_ == address(0)) revert ZeroAddress();
        if (minter_ == address(0)) revert ZeroAddress();

        _initialized = true;

        // Store ERC-20 metadata (overridden via name()/symbol() below).
        _tokenName = name_;
        _tokenSymbol = symbol_;

        // Store cause metadata.
        causeName = causeName_;
        causeDescription = causeDescription_;
        charityWallet = charityWallet_;
        causeId = causeId_;

        // Grant roles: minter gets MINTER_ROLE; minter also becomes admin
        // so that the ConversionEngine (or governance) can manage roles later.
        _grantRole(DEFAULT_ADMIN_ROLE, minter_);
        _grantRole(MINTER_ROLE, minter_);
    }

    // ──────────────────────────────────────────────────────────────────────
    // ERC-20 Metadata Overrides
    // ──────────────────────────────────────────────────────────────────────

    /// @dev Returns the token name set during initialization.
    function name() public view override returns (string memory) {
        return bytes(_tokenName).length > 0 ? _tokenName : super.name();
    }

    /// @dev Returns the token symbol set during initialization.
    function symbol() public view override returns (string memory) {
        return bytes(_tokenSymbol).length > 0 ? _tokenSymbol : super.symbol();
    }

    // ──────────────────────────────────────────────────────────────────────
    // Minting
    // ──────────────────────────────────────────────────────────────────────

    /// @notice Mints `amount` cause tokens to `to`.
    /// @dev Only callable by addresses with MINTER_ROLE (the ConversionEngine).
    /// @param to     Recipient of the minted tokens.
    /// @param amount Number of tokens to mint (in wei).
    function mint(address to, uint256 amount) external onlyRole(MINTER_ROLE) {
        _mint(to, amount);
    }
}
