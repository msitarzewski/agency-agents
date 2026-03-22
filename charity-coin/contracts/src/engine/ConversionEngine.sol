// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {Pausable} from "@openzeppelin/contracts/utils/Pausable.sol";
import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

import {IConversionEngine} from "../interfaces/IConversionEngine.sol";
import {IFeeRouter} from "../interfaces/IFeeRouter.sol";
import {ICauseTokenFactory} from "../interfaces/ICauseTokenFactory.sol";
import {CauseToken} from "../token/CauseToken.sol";
import {CharityCoin} from "../token/CharityCoin.sol";

/// @title ConversionEngine
/// @notice Core business logic for converting CHA tokens into cause tokens.
/// @dev Flow:
///   1. User approves ConversionEngine to spend their CHA.
///   2. User calls `convert(causeToken, chaAmount)`.
///   3. Engine calculates fee (default 5%) and burn amount (95%).
///   4. CHA is transferred from user -> engine.
///   5. Burn amount of CHA is burned forever.
///   6. Fee amount of CHA is transferred to FeeRouter for distribution.
///   7. Cause tokens are minted 1:1 with the burn amount to the user.
///
/// This creates deflationary pressure on CHA while funding charitable causes.
contract ConversionEngine is IConversionEngine, ReentrancyGuard, Pausable, AccessControl {
    using SafeERC20 for IERC20;

    // ──────────────────────────────────────────────────────────────────────
    // Constants
    // ──────────────────────────────────────────────────────────────────────

    /// @notice Maximum allowed fee rate: 10% (1000 bps).
    uint256 public constant MAX_FEE_BPS = 1000;

    /// @notice Basis-point denominator for percentage calculations.
    uint256 public constant BPS_DENOMINATOR = 10_000;

    /// @notice Minimum conversion amount: 1 CHA (prevents fee bypass on dust amounts).
    uint256 public constant MIN_CONVERSION = 1e18;

    // ──────────────────────────────────────────────────────────────────────
    // Errors
    // ──────────────────────────────────────────────────────────────────────

    /// @notice Thrown when a zero address is provided.
    error ZeroAddress();

    /// @notice Thrown when the conversion amount is below the minimum.
    error AmountTooSmall();

    /// @notice Thrown when the FeeRouter address is updated.
    event FeeRouterUpdated(address oldRouter, address newRouter);

    /// @notice Thrown when the Factory address is updated.
    event FactoryUpdated(address oldFactory, address newFactory);

    /// @notice Emitted when the total fees collected counter increases.
    event TotalFeesCollectedUpdated(uint256 newTotal);

    // ──────────────────────────────────────────────────────────────────────
    // Storage
    // ──────────────────────────────────────────────────────────────────────

    /// @notice The CHA token contract.
    CharityCoin public chaToken;

    /// @notice The cause token factory used to validate cause tokens.
    ICauseTokenFactory public factory;

    /// @notice The fee router that distributes fees among charity, liquidity, and ops.
    IFeeRouter public feeRouter;

    /// @notice Current total fee rate in basis points (default: 500 = 5%).
    uint256 public totalFeeBps = 500;

    /// @notice Tracks per-user, per-cause conversion amounts.
    mapping(address => mapping(address => uint256)) public userConversions;

    /// @notice Cumulative CHA burned through all conversions.
    uint256 public totalChaBurned;

    /// @notice Cumulative fees collected through all conversions.
    uint256 public totalFeesCollected;

    // ──────────────────────────────────────────────────────────────────────
    // Constructor
    // ──────────────────────────────────────────────────────────────────────

    /// @notice Deploys the ConversionEngine.
    /// @param chaToken_    Address of the CharityCoin (CHA) token.
    /// @param factory_     Address of the CauseTokenFactory (can be address(0) if set later via setFactory).
    /// @param feeRouter_   Address of the FeeRouter.
    /// @param defaultAdmin Address granted DEFAULT_ADMIN_ROLE.
    constructor(
        address chaToken_,
        address factory_,
        address feeRouter_,
        address defaultAdmin
    ) {
        if (chaToken_ == address(0)) revert ZeroAddress();
        if (feeRouter_ == address(0)) revert ZeroAddress();
        if (defaultAdmin == address(0)) revert ZeroAddress();

        chaToken = CharityCoin(chaToken_);
        factory = ICauseTokenFactory(factory_);
        feeRouter = IFeeRouter(feeRouter_);

        _grantRole(DEFAULT_ADMIN_ROLE, defaultAdmin);
    }

    // ──────────────────────────────────────────────────────────────────────
    // External Functions
    // ──────────────────────────────────────────────────────────────────────

    /// @inheritdoc IConversionEngine
    function convert(address causeToken, uint256 chaAmount) external nonReentrant whenNotPaused {
        if (chaAmount < MIN_CONVERSION) revert AmountTooSmall();
        if (!factory.isCause(causeToken)) revert InvalidCause();

        // Calculate fee and burn amounts (cache totalFeeBps to save an SLOAD).
        uint256 _totalFeeBps = totalFeeBps;
        uint256 fee = (chaAmount * _totalFeeBps) / BPS_DENOMINATOR;
        uint256 burnAmount = chaAmount - fee;

        // Transfer CHA from the user to this contract.
        IERC20(address(chaToken)).safeTransferFrom(msg.sender, address(this), chaAmount);

        // Burn the non-fee portion of CHA permanently.
        chaToken.burn(burnAmount);

        // Transfer the fee portion to the FeeRouter for distribution.
        if (fee > 0) {
            IERC20(address(chaToken)).safeTransfer(address(feeRouter), fee);
            feeRouter.distributeFees(causeToken, fee);
        }

        // Mint cause tokens 1:1 with the burned CHA amount.
        CauseToken(causeToken).mint(msg.sender, burnAmount);

        // Update accounting.
        userConversions[msg.sender][causeToken] += burnAmount;
        totalChaBurned += burnAmount;
        totalFeesCollected += fee;

        emit Converted(msg.sender, causeToken, chaAmount, burnAmount, fee, burnAmount);
    }

    /// @inheritdoc IConversionEngine
    function getConversionPreview(uint256 chaAmount)
        external
        view
        returns (
            uint256 burnAmount,
            uint256 charityFee,
            uint256 liquidityFee,
            uint256 opsFee,
            uint256 causeTokensOut
        )
    {
        uint256 totalFee = (chaAmount * totalFeeBps) / BPS_DENOMINATOR;
        burnAmount = chaAmount - totalFee;
        causeTokensOut = burnAmount;

        // Break fee down according to FeeRouter shares.
        charityFee = (totalFee * feeRouter.charityShareBps()) / BPS_DENOMINATOR;
        liquidityFee = (totalFee * feeRouter.liquidityShareBps()) / BPS_DENOMINATOR;
        opsFee = totalFee - charityFee - liquidityFee; // Remainder to ops to avoid rounding dust.
    }

    /// @inheritdoc IConversionEngine
    function setTotalFeeBps(uint256 newFeeBps) external onlyRole(DEFAULT_ADMIN_ROLE) {
        if (newFeeBps > MAX_FEE_BPS) revert FeeTooHigh();

        uint256 oldFeeBps = totalFeeBps;
        totalFeeBps = newFeeBps;

        emit FeeRateUpdated(oldFeeBps, newFeeBps);
    }

    /// @notice Pauses all conversions. Only callable by admin.
    function pause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _pause();
    }

    /// @notice Unpauses conversions. Only callable by admin.
    function unpause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _unpause();
    }

    /// @notice Updates the FeeRouter address. Only callable by admin.
    /// @param newFeeRouter Address of the new FeeRouter.
    function setFeeRouter(address newFeeRouter) external onlyRole(DEFAULT_ADMIN_ROLE) {
        if (newFeeRouter == address(0)) revert ZeroAddress();
        address oldRouter = address(feeRouter);
        feeRouter = IFeeRouter(newFeeRouter);
        emit FeeRouterUpdated(oldRouter, newFeeRouter);
    }

    /// @notice Updates the CauseTokenFactory address. Only callable by admin.
    /// @param newFactory Address of the new factory.
    function setFactory(address newFactory) external onlyRole(DEFAULT_ADMIN_ROLE) {
        if (newFactory == address(0)) revert ZeroAddress();
        address oldFactory = address(factory);
        factory = ICauseTokenFactory(newFactory);
        emit FactoryUpdated(oldFactory, newFactory);
    }
}
