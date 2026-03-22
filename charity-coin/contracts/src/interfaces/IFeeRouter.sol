// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title IFeeRouter
/// @notice Interface for the fee distribution router that splits conversion fees
///         among charity, liquidity, and operations.
interface IFeeRouter {
    // ──────────────────────────────────────────────────────────────────────
    // Events
    // ──────────────────────────────────────────────────────────────────────

    /// @notice Emitted when fees are distributed for a conversion.
    /// @param causeToken     Cause token associated with the conversion.
    /// @param charityAmount  CHA sent to the charity wallet.
    /// @param liquidityAmount CHA sent to the liquidity manager.
    /// @param opsAmount      CHA swapped to USDC and sent to operations.
    event FeesDistributed(
        address indexed causeToken,
        uint256 charityAmount,
        uint256 liquidityAmount,
        uint256 opsAmount
    );

    /// @notice Emitted when the fee share percentages are updated.
    /// @param charityShareBps   New charity share in basis points.
    /// @param liquidityShareBps New liquidity share in basis points.
    /// @param opsShareBps       New operations share in basis points.
    event FeeSharesUpdated(uint256 charityShareBps, uint256 liquidityShareBps, uint256 opsShareBps);

    /// @notice Emitted when the operations wallet is updated.
    /// @param oldWallet Previous operations wallet.
    /// @param newWallet New operations wallet.
    event OperationsWalletUpdated(address oldWallet, address newWallet);

    /// @notice Emitted when the max slippage setting is updated.
    /// @param oldSlippageBps Previous max slippage in basis points.
    /// @param newSlippageBps New max slippage in basis points.
    event MaxSlippageUpdated(uint256 oldSlippageBps, uint256 newSlippageBps);

    /// @notice Emitted when the liquidity manager address is updated.
    event LiquidityManagerUpdated(address oldManager, address newManager);

    /// @notice Emitted when the Uniswap V3 pool fee tier is updated.
    event PoolFeeUpdated(uint24 oldFee, uint24 newFee);

    // ──────────────────────────────────────────────────────────────────────
    // Errors
    // ──────────────────────────────────────────────────────────────────────

    /// @notice Thrown when fee shares do not sum to 10,000 bps.
    error InvalidFeeShares();

    /// @notice Thrown when a zero address is provided where a valid address is required.
    error ZeroAddress();

    /// @notice Thrown when the slippage setting exceeds the allowed maximum.
    error SlippageTooHigh();

    /// @notice Thrown when an invalid Uniswap V3 pool fee tier is provided.
    error InvalidPoolFee();

    // ──────────────────────────────────────────────────────────────────────
    // Functions
    // ──────────────────────────────────────────────────────────────────────

    /// @notice Distributes fee CHA among charity, liquidity, and operations.
    /// @param causeToken Address of the cause token (used to look up charity wallet).
    /// @param feeAmount  Total CHA fee to distribute.
    function distributeFees(address causeToken, uint256 feeAmount) external;

    /// @notice Returns the charity share percentage in basis points.
    function charityShareBps() external view returns (uint256);

    /// @notice Returns the liquidity share percentage in basis points.
    function liquidityShareBps() external view returns (uint256);

    /// @notice Returns the operations share percentage in basis points.
    function opsShareBps() external view returns (uint256);

    /// @notice Updates the fee distribution shares.
    /// @param charity   Charity share in basis points.
    /// @param liquidity Liquidity share in basis points.
    /// @param ops       Operations share in basis points.
    function setFeeShares(uint256 charity, uint256 liquidity, uint256 ops) external;

    /// @notice Updates the maximum allowed slippage for swaps.
    /// @param newSlippageBps New max slippage in basis points (max 500 = 5%).
    function setMaxSlippageBps(uint256 newSlippageBps) external;

    /// @notice Updates the operations wallet address.
    /// @param newWallet New operations wallet address.
    function setOperationsWallet(address newWallet) external;
}
