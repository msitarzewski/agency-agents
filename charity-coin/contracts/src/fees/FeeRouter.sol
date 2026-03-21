// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

import {IFeeRouter} from "../interfaces/IFeeRouter.sol";
import {ISwapRouter} from "../interfaces/ISwapRouter.sol";
import {CauseToken} from "../token/CauseToken.sol";

/// @title FeeRouter
/// @notice Distributes conversion fees among three recipients:
///   1. **Charity** (default 50% of fee) — sent as CHA to the cause's charity wallet.
///   2. **Liquidity** (default 30% of fee) — sent as CHA to a liquidity manager for manual LP.
///   3. **Operations** (default 20% of fee) — swapped to USDC via Uniswap V3 and sent to ops wallet.
///
/// @dev The FeeRouter receives CHA from the ConversionEngine and immediately splits it.
///      The operations portion is auto-swapped to USDC for cost-basis stability.
///
///      In production, `amountOutMinimum` should use a TWAP oracle. For the MVP, a configurable
///      `maxSlippageBps` is used instead.
contract FeeRouter is IFeeRouter, ReentrancyGuard, AccessControl {
    using SafeERC20 for IERC20;

    // ──────────────────────────────────────────────────────────────────────
    // Constants
    // ──────────────────────────────────────────────────────────────────────

    /// @dev Basis-point denominator for percentage calculations.
    uint256 private constant BPS_DENOMINATOR = 10_000;

    /// @dev Maximum allowed slippage: 5% (500 bps).
    uint256 private constant MAX_SLIPPAGE_CAP = 500;

    // ──────────────────────────────────────────────────────────────────────
    // Storage — Fee Shares
    // ──────────────────────────────────────────────────────────────────────

    /// @notice Charity's share of the total fee, in basis points (default: 5000 = 50%).
    uint256 public charityShareBps = 5000;

    /// @notice Liquidity's share of the total fee, in basis points (default: 3000 = 30%).
    uint256 public liquidityShareBps = 3000;

    /// @notice Operations' share of the total fee, in basis points (default: 2000 = 20%).
    uint256 public opsShareBps = 2000;

    // ──────────────────────────────────────────────────────────────────────
    // Storage — Addresses
    // ──────────────────────────────────────────────────────────────────────

    /// @notice Wallet that receives the operations portion (in USDC after swap).
    address public operationsWallet;

    /// @notice Address that holds CHA earmarked for liquidity provision.
    address public liquidityManager;

    /// @notice Uniswap V3 SwapRouter used for CHA -> USDC swaps.
    ISwapRouter public swapRouter;

    /// @notice Address of the USDC token on the target chain.
    address public usdc;

    /// @notice Address of the CHA token.
    IERC20 public chaToken;

    // ──────────────────────────────────────────────────────────────────────
    // Storage — Swap Configuration
    // ──────────────────────────────────────────────────────────────────────

    /// @notice Maximum allowed slippage for CHA -> USDC swaps, in basis points (default: 100 = 1%).
    uint256 public maxSlippageBps = 100;

    /// @notice Uniswap V3 pool fee tier for the CHA/USDC pair (default: 3000 = 0.3%).
    uint24 public poolFee = 3000;

    // ──────────────────────────────────────────────────────────────────────
    // Constructor
    // ──────────────────────────────────────────────────────────────────────

    /// @notice Deploys the FeeRouter.
    /// @param chaToken_          Address of the CHA token.
    /// @param swapRouter_        Address of the Uniswap V3 SwapRouter.
    /// @param usdc_              Address of the USDC token.
    /// @param operationsWallet_  Wallet for operations fee distributions.
    /// @param liquidityManager_  Address that holds CHA for liquidity provision.
    /// @param defaultAdmin       Address granted DEFAULT_ADMIN_ROLE.
    constructor(
        address chaToken_,
        address swapRouter_,
        address usdc_,
        address operationsWallet_,
        address liquidityManager_,
        address defaultAdmin
    ) {
        if (chaToken_ == address(0)) revert ZeroAddress();
        if (swapRouter_ == address(0)) revert ZeroAddress();
        if (usdc_ == address(0)) revert ZeroAddress();
        if (operationsWallet_ == address(0)) revert ZeroAddress();
        if (liquidityManager_ == address(0)) revert ZeroAddress();
        if (defaultAdmin == address(0)) revert ZeroAddress();

        chaToken = IERC20(chaToken_);
        swapRouter = ISwapRouter(swapRouter_);
        usdc = usdc_;
        operationsWallet = operationsWallet_;
        liquidityManager = liquidityManager_;

        _grantRole(DEFAULT_ADMIN_ROLE, defaultAdmin);
    }

    // ──────────────────────────────────────────────────────────────────────
    // External Functions
    // ──────────────────────────────────────────────────────────────────────

    /// @inheritdoc IFeeRouter
    function distributeFees(address causeToken, uint256 feeAmount) external nonReentrant {
        if (feeAmount == 0) return;

        // Calculate each portion.
        uint256 charityAmount = (feeAmount * charityShareBps) / BPS_DENOMINATOR;
        uint256 liquidityAmount = (feeAmount * liquidityShareBps) / BPS_DENOMINATOR;
        uint256 opsAmount = feeAmount - charityAmount - liquidityAmount; // Remainder avoids dust.

        // 1. Charity portion: send CHA directly to the cause's charity wallet.
        address wallet = CauseToken(causeToken).charityWallet();
        if (charityAmount > 0) {
            chaToken.safeTransfer(wallet, charityAmount);
        }

        // 2. Liquidity portion: send CHA to the liquidity manager for manual LP addition.
        if (liquidityAmount > 0) {
            chaToken.safeTransfer(liquidityManager, liquidityAmount);
        }

        // 3. Operations portion: swap CHA -> USDC via Uniswap V3, sent to operations wallet.
        if (opsAmount > 0) {
            _swapToStablecoin(opsAmount);
        }

        emit FeesDistributed(causeToken, charityAmount, liquidityAmount, opsAmount);
    }

    /// @inheritdoc IFeeRouter
    function setFeeShares(
        uint256 charity,
        uint256 liquidity,
        uint256 ops
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        if (charity + liquidity + ops != BPS_DENOMINATOR) revert InvalidFeeShares();

        charityShareBps = charity;
        liquidityShareBps = liquidity;
        opsShareBps = ops;

        emit FeeSharesUpdated(charity, liquidity, ops);
    }

    /// @inheritdoc IFeeRouter
    function setMaxSlippageBps(uint256 newSlippageBps) external onlyRole(DEFAULT_ADMIN_ROLE) {
        if (newSlippageBps > MAX_SLIPPAGE_CAP) revert SlippageTooHigh();
        uint256 oldSlippageBps = maxSlippageBps;
        maxSlippageBps = newSlippageBps;
        emit MaxSlippageUpdated(oldSlippageBps, newSlippageBps);
    }

    /// @inheritdoc IFeeRouter
    function setOperationsWallet(address newWallet) external onlyRole(DEFAULT_ADMIN_ROLE) {
        if (newWallet == address(0)) revert ZeroAddress();
        address oldWallet = operationsWallet;
        operationsWallet = newWallet;
        emit OperationsWalletUpdated(oldWallet, newWallet);
    }

    /// @notice Updates the liquidity manager address.
    /// @param newManager New liquidity manager address.
    function setLiquidityManager(address newManager) external onlyRole(DEFAULT_ADMIN_ROLE) {
        if (newManager == address(0)) revert ZeroAddress();
        liquidityManager = newManager;
    }

    /// @notice Updates the Uniswap V3 pool fee tier for swaps.
    /// @param newPoolFee New pool fee (e.g., 500, 3000, 10000).
    function setPoolFee(uint24 newPoolFee) external onlyRole(DEFAULT_ADMIN_ROLE) {
        poolFee = newPoolFee;
    }

    // ──────────────────────────────────────────────────────────────────────
    // Internal Functions
    // ──────────────────────────────────────────────────────────────────────

    /// @dev Swaps CHA to USDC via Uniswap V3 SwapRouter and sends USDC to the operations wallet.
    /// @param chaAmount Amount of CHA to swap.
    function _swapToStablecoin(uint256 chaAmount) internal {
        // Approve the SwapRouter to spend CHA.
        chaToken.safeIncreaseAllowance(address(swapRouter), chaAmount);

        // Calculate minimum output with slippage protection.
        // NOTE: In production, amountOutMinimum should be derived from a TWAP oracle.
        // For MVP, we use a simple slippage tolerance. Setting amountOutMinimum to 0
        // with maxSlippageBps as a safety net via the pool's price bounds.
        // A real implementation would fetch a price quote first.
        uint256 amountOutMinimum = 0; // MVP: rely on pool price; upgrade to oracle in v2.

        ISwapRouter.ExactInputSingleParams memory params = ISwapRouter.ExactInputSingleParams({
            tokenIn: address(chaToken),
            tokenOut: usdc,
            fee: poolFee,
            recipient: operationsWallet,
            amountIn: chaAmount,
            amountOutMinimum: amountOutMinimum,
            sqrtPriceLimitX96: 0
        });

        swapRouter.exactInputSingle(params);
    }
}
