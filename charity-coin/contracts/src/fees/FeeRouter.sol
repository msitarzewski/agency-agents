// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

import {IFeeRouter} from "../interfaces/IFeeRouter.sol";
import {ISwapRouter} from "../interfaces/ISwapRouter.sol";
import {ICauseTokenFactory} from "../interfaces/ICauseTokenFactory.sol";
import {CauseToken} from "../token/CauseToken.sol";

/// @title FeeRouter
/// @notice Distributes conversion fees among three recipients:
///   1. **Charity** (default 50% of fee) — sent as CHA to the cause's charity wallet.
///   2. **Liquidity** (default 30% of fee) — sent as CHA to a liquidity manager for manual LP.
///   3. **Operations** (default 20% of fee) — swapped to USDC via Uniswap V3 and sent to ops wallet.
///
/// @dev The FeeRouter receives CHA from the ConversionEngine and immediately splits it.
///      The operations portion is auto-swapped to USDC for cost-basis stability.
///      Only addresses with DISTRIBUTOR_ROLE (typically the ConversionEngine) can call distributeFees.
contract FeeRouter is IFeeRouter, ReentrancyGuard, AccessControl {
    using SafeERC20 for IERC20;

    // ──────────────────────────────────────────────────────────────────────
    // Constants
    // ──────────────────────────────────────────────────────────────────────

    /// @dev Basis-point denominator for percentage calculations.
    uint256 private constant BPS_DENOMINATOR = 10_000;

    /// @dev Maximum allowed slippage: 5% (500 bps).
    uint256 private constant MAX_SLIPPAGE_CAP = 500;

    /// @notice Role for addresses permitted to call distributeFees (typically ConversionEngine).
    bytes32 public constant DISTRIBUTOR_ROLE = keccak256("DISTRIBUTOR_ROLE");

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

    /// @notice CauseTokenFactory for validating cause token addresses.
    ICauseTokenFactory public factory;

    // ──────────────────────────────────────────────────────────────────────
    // Storage — Swap Configuration
    // ──────────────────────────────────────────────────────────────────────

    /// @notice Maximum allowed slippage for CHA -> USDC swaps, in basis points (default: 100 = 1%).
    uint256 public maxSlippageBps = 100;

    /// @notice Uniswap V3 pool fee tier for the CHA/USDC pair (default: 3000 = 0.3%).
    uint24 public poolFee = 3000;

    /// @notice Reference price for CHA in USDC terms (scaled by 1e18). Used for slippage protection.
    /// @dev Set by admin. E.g., 1e6 means 1 CHA = 1 USDC. In production, replace with TWAP oracle.
    uint256 public chaUsdcReferencePrice;

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
    function distributeFees(address causeToken, uint256 feeAmount)
        external
        nonReentrant
        onlyRole(DISTRIBUTOR_ROLE)
    {
        if (feeAmount == 0) return;

        // Validate causeToken is registered (if factory is set)
        if (address(factory) != address(0)) {
            if (!factory.isCause(causeToken)) revert InvalidCause();
        }

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
        address oldManager = liquidityManager;
        liquidityManager = newManager;
        emit LiquidityManagerUpdated(oldManager, newManager);
    }

    /// @notice Updates the Uniswap V3 pool fee tier for swaps.
    /// @param newPoolFee New pool fee (must be 100, 500, 3000, or 10000).
    function setPoolFee(uint24 newPoolFee) external onlyRole(DEFAULT_ADMIN_ROLE) {
        if (newPoolFee != 100 && newPoolFee != 500 && newPoolFee != 3000 && newPoolFee != 10000) {
            revert InvalidPoolFee();
        }
        uint24 oldFee = poolFee;
        poolFee = newPoolFee;
        emit PoolFeeUpdated(oldFee, newPoolFee);
    }

    /// @notice Sets the CauseTokenFactory for cause validation.
    /// @param factory_ Address of the CauseTokenFactory.
    function setFactory(address factory_) external onlyRole(DEFAULT_ADMIN_ROLE) {
        if (factory_ == address(0)) revert ZeroAddress();
        factory = ICauseTokenFactory(factory_);
    }

    /// @notice Sets the reference price for CHA/USDC slippage calculation.
    /// @param price Price of 1 CHA in USDC terms, scaled by 1e18. E.g., 1e6 = $1.00.
    function setReferencePrice(uint256 price) external onlyRole(DEFAULT_ADMIN_ROLE) {
        chaUsdcReferencePrice = price;
    }

    // ──────────────────────────────────────────────────────────────────────
    // Errors
    // ──────────────────────────────────────────────────────────────────────

    /// @notice Thrown when the provided cause token is not registered in the factory.
    error InvalidCause();

    // ──────────────────────────────────────────────────────────────────────
    // Internal Functions
    // ──────────────────────────────────────────────────────────────────────

    /// @dev Swaps CHA to USDC via Uniswap V3 SwapRouter and sends USDC to the operations wallet.
    /// @param chaAmount Amount of CHA to swap.
    function _swapToStablecoin(uint256 chaAmount) internal {
        // Approve the SwapRouter to spend CHA using forceApprove to avoid stale allowance.
        chaToken.forceApprove(address(swapRouter), chaAmount);

        // Calculate minimum output with slippage protection.
        uint256 amountOutMinimum = _getMinimumOutput(chaAmount);

        ISwapRouter.ExactInputSingleParams memory params = ISwapRouter.ExactInputSingleParams({
            tokenIn: address(chaToken),
            tokenOut: usdc,
            fee: poolFee,
            recipient: operationsWallet,
            deadline: block.timestamp,
            amountIn: chaAmount,
            amountOutMinimum: amountOutMinimum,
            sqrtPriceLimitX96: 0
        });

        swapRouter.exactInputSingle(params);
    }

    /// @dev Calculate minimum acceptable USDC output using reference price and slippage tolerance.
    /// @param chaAmount Amount of CHA being swapped.
    /// @return Minimum USDC output. Returns 0 if no reference price is set (not recommended for production).
    function _getMinimumOutput(uint256 chaAmount) internal view returns (uint256) {
        if (chaUsdcReferencePrice == 0) return 0;
        uint256 expectedOutput = (chaAmount * chaUsdcReferencePrice) / 1e18;
        return expectedOutput - (expectedOutput * maxSlippageBps / BPS_DENOMINATOR);
    }
}
