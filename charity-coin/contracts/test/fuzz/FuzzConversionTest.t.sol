// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {CharityCoin} from "../../src/token/CharityCoin.sol";
import {CauseToken} from "../../src/token/CauseToken.sol";
import {CauseTokenFactory} from "../../src/factory/CauseTokenFactory.sol";
import {ConversionEngine} from "../../src/engine/ConversionEngine.sol";
import {FeeRouter} from "../../src/fees/FeeRouter.sol";
import {MockSwapRouter} from "../mocks/MockSwapRouter.sol";
import {MockERC20} from "../mocks/MockERC20.sol";

contract FuzzConversionTest is Test {
    CharityCoin public cha;
    CauseTokenFactory public factory;
    ConversionEngine public engine;
    FeeRouter public feeRouter;
    MockSwapRouter public swapRouter;
    MockERC20 public usdc;

    address admin = makeAddr("admin");
    address charity = makeAddr("charity");
    address opsWallet = makeAddr("opsWallet");
    address liquidityMgr = makeAddr("liquidityMgr");
    address fuzzer = makeAddr("fuzzer");

    address causeToken;

    uint256 constant MIN_CONVERSION = 1e18;
    uint256 constant MAX_FUZZ_AMOUNT = 100_000e18;
    uint256 constant BPS_DENOMINATOR = 10_000;

    function setUp() public {
        cha = new CharityCoin(admin, admin);
        usdc = new MockERC20("USDC", "USDC", 6);
        swapRouter = new MockSwapRouter();

        feeRouter = new FeeRouter(
            address(cha), address(swapRouter), address(usdc),
            opsWallet, liquidityMgr, admin
        );

        CauseToken impl = new CauseToken();
        factory = new CauseTokenFactory(address(impl), admin, admin);

        engine = new ConversionEngine(
            address(cha), address(factory), address(feeRouter), admin
        );

        vm.prank(admin);
        factory.setMinter(address(engine));

        // Cache the role hash before using vm.prank to avoid consuming the prank
        bytes32 distRole = feeRouter.DISTRIBUTOR_ROLE();
        vm.prank(admin);
        feeRouter.grantRole(distRole, address(engine));

        vm.prank(admin);
        feeRouter.setFactory(address(factory));

        vm.prank(admin);
        causeToken = factory.createCause(
            "Global Health Token", "HEALTH", "Global Health", "Fund research", charity
        );

        // Mint a large amount of CHA to the fuzzer
        vm.prank(admin);
        cha.mint(fuzzer, 10_000_000e18);
    }

    /// @notice Verify that burnAmount = chaAmount - fee for any valid chaAmount.
    function testFuzz_conversionBurnAmount(uint256 chaAmount) public {
        chaAmount = bound(chaAmount, MIN_CONVERSION, MAX_FUZZ_AMOUNT);

        uint256 totalFeeBps = engine.totalFeeBps();
        uint256 expectedFee = (chaAmount * totalFeeBps) / BPS_DENOMINATOR;
        uint256 expectedBurn = chaAmount - expectedFee;

        vm.startPrank(fuzzer);
        cha.approve(address(engine), chaAmount);
        engine.convert(causeToken, chaAmount);
        vm.stopPrank();

        // The engine tracks totalChaBurned which equals burnAmount
        assertEq(engine.totalChaBurned(), expectedBurn, "burn amount mismatch");
    }

    /// @notice Verify that fee + burn = chaAmount exactly (no rounding loss).
    function testFuzz_feeCalculation(uint256 chaAmount) public {
        chaAmount = bound(chaAmount, MIN_CONVERSION, MAX_FUZZ_AMOUNT);

        uint256 totalFeeBps = engine.totalFeeBps();
        uint256 fee = (chaAmount * totalFeeBps) / BPS_DENOMINATOR;
        uint256 burnAmount = chaAmount - fee;

        // fee + burn must equal the original amount exactly
        assertEq(fee + burnAmount, chaAmount, "fee + burn != chaAmount");

        // Also verify via actual conversion
        vm.startPrank(fuzzer);
        cha.approve(address(engine), chaAmount);
        engine.convert(causeToken, chaAmount);
        vm.stopPrank();

        assertEq(
            engine.totalFeesCollected() + engine.totalChaBurned(),
            chaAmount,
            "on-chain fee + burn != chaAmount"
        );
    }

    /// @notice Verify that cause tokens minted == burn amount.
    function testFuzz_causeTokensMintedEqualBurn(uint256 chaAmount) public {
        chaAmount = bound(chaAmount, MIN_CONVERSION, MAX_FUZZ_AMOUNT);

        uint256 totalFeeBps = engine.totalFeeBps();
        uint256 fee = (chaAmount * totalFeeBps) / BPS_DENOMINATOR;
        uint256 expectedBurn = chaAmount - fee;

        vm.startPrank(fuzzer);
        cha.approve(address(engine), chaAmount);
        engine.convert(causeToken, chaAmount);
        vm.stopPrank();

        assertEq(
            CauseToken(causeToken).balanceOf(fuzzer),
            expectedBurn,
            "cause tokens minted != burn amount"
        );
        assertEq(
            CauseToken(causeToken).totalSupply(),
            expectedBurn,
            "cause token total supply != burn amount"
        );
    }

    /// @notice Verify CHA totalSupply decreases by exactly burnAmount.
    function testFuzz_totalSupplyDecrease(uint256 chaAmount) public {
        chaAmount = bound(chaAmount, MIN_CONVERSION, MAX_FUZZ_AMOUNT);

        uint256 totalFeeBps = engine.totalFeeBps();
        uint256 fee = (chaAmount * totalFeeBps) / BPS_DENOMINATOR;
        uint256 expectedBurn = chaAmount - fee;

        uint256 supplyBefore = cha.totalSupply();

        vm.startPrank(fuzzer);
        cha.approve(address(engine), chaAmount);
        engine.convert(causeToken, chaAmount);
        vm.stopPrank();

        uint256 supplyAfter = cha.totalSupply();
        assertEq(
            supplyBefore - supplyAfter,
            expectedBurn,
            "total supply did not decrease by burn amount"
        );
    }

    /// @notice Verify that fee shares always sum to 10000 bps for any valid inputs.
    function testFuzz_feeSharesSumTo100(uint256 charityShare, uint256 liquidityShare) public {
        charityShare = bound(charityShare, 0, BPS_DENOMINATOR);
        liquidityShare = bound(liquidityShare, 0, BPS_DENOMINATOR - charityShare);
        uint256 opsShare = BPS_DENOMINATOR - charityShare - liquidityShare;

        vm.prank(admin);
        feeRouter.setFeeShares(charityShare, liquidityShare, opsShare);

        assertEq(
            feeRouter.charityShareBps() + feeRouter.liquidityShareBps() + feeRouter.opsShareBps(),
            BPS_DENOMINATOR,
            "fee shares do not sum to 10000"
        );
    }
}
