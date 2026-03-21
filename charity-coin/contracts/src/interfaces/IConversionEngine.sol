// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title IConversionEngine
/// @notice Interface for the core conversion engine that burns CHA and mints cause tokens.
interface IConversionEngine {
    // ──────────────────────────────────────────────────────────────────────
    // Events
    // ──────────────────────────────────────────────────────────────────────

    /// @notice Emitted when a user converts CHA into a cause token.
    /// @param user         Address of the converting user.
    /// @param causeToken   Address of the cause token received.
    /// @param chaAmount    Total CHA input amount.
    /// @param burnAmount   CHA burned (after fees).
    /// @param feeAmount    CHA directed to fees.
    /// @param causeTokensOut Cause tokens minted to the user.
    event Converted(
        address indexed user,
        address indexed causeToken,
        uint256 chaAmount,
        uint256 burnAmount,
        uint256 feeAmount,
        uint256 causeTokensOut
    );

    /// @notice Emitted when the total fee rate is updated.
    /// @param oldFeeBps Previous fee rate in basis points.
    /// @param newFeeBps New fee rate in basis points.
    event FeeRateUpdated(uint256 oldFeeBps, uint256 newFeeBps);

    // ──────────────────────────────────────────────────────────────────────
    // Errors
    // ──────────────────────────────────────────────────────────────────────

    /// @notice Thrown when the conversion amount is zero.
    error ZeroAmount();

    /// @notice Thrown when the cause token is not registered in the factory.
    error InvalidCause();

    /// @notice Thrown when the proposed fee exceeds the maximum allowed.
    error FeeTooHigh();

    // ──────────────────────────────────────────────────────────────────────
    // Functions
    // ──────────────────────────────────────────────────────────────────────

    /// @notice Converts CHA into cause tokens. Burns CHA (minus fee) and mints cause tokens 1:1.
    /// @param causeToken Address of the target cause token.
    /// @param chaAmount  Amount of CHA to convert.
    function convert(address causeToken, uint256 chaAmount) external;

    /// @notice Previews the outcome of a conversion without executing it.
    /// @param chaAmount Amount of CHA to preview.
    /// @return burnAmount      CHA that will be burned.
    /// @return charityFee      Portion of fee directed to charity.
    /// @return liquidityFee    Portion of fee directed to liquidity.
    /// @return opsFee          Portion of fee directed to operations.
    /// @return causeTokensOut  Cause tokens the user would receive.
    function getConversionPreview(uint256 chaAmount)
        external
        view
        returns (
            uint256 burnAmount,
            uint256 charityFee,
            uint256 liquidityFee,
            uint256 opsFee,
            uint256 causeTokensOut
        );

    /// @notice Updates the total fee rate applied to conversions.
    /// @param newFeeBps New fee rate in basis points (must be <= MAX_FEE_BPS).
    function setTotalFeeBps(uint256 newFeeBps) external;

    /// @notice Returns the current total fee rate in basis points.
    function totalFeeBps() external view returns (uint256);

    /// @notice Returns the maximum allowed fee rate in basis points.
    function MAX_FEE_BPS() external view returns (uint256);

    /// @notice Returns the basis points denominator (10,000).
    function BPS_DENOMINATOR() external view returns (uint256);

    /// @notice Returns the total amount of CHA burned through conversions.
    function totalChaBurned() external view returns (uint256);
}
