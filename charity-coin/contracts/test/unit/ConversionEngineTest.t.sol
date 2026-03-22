// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {CharityCoin} from "../../src/token/CharityCoin.sol";
import {CauseToken} from "../../src/token/CauseToken.sol";
import {CauseTokenFactory} from "../../src/factory/CauseTokenFactory.sol";
import {ConversionEngine} from "../../src/engine/ConversionEngine.sol";
import {FeeRouter} from "../../src/fees/FeeRouter.sol";
import {IConversionEngine} from "../../src/interfaces/IConversionEngine.sol";
import {MockSwapRouter} from "../mocks/MockSwapRouter.sol";
import {MockERC20} from "../mocks/MockERC20.sol";

contract ConversionEngineTest is Test {
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
    address alice = makeAddr("alice");

    address causeToken;

    function setUp() public {
        cha = new CharityCoin(admin, admin);
        usdc = new MockERC20("USDC", "USDC", 6);
        swapRouter = new MockSwapRouter();

        // Deploy FeeRouter first (need engine address for factory minter, but engine needs factory)
        feeRouter = new FeeRouter(
            address(cha), address(swapRouter), address(usdc),
            opsWallet, liquidityMgr, admin
        );

        CauseToken impl = new CauseToken();

        // We'll use a temporary address for factory minter, then update
        // Actually ConversionEngine needs factory address, but factory needs minter (engine) address
        // Deploy engine with a placeholder, then set factory minter
        factory = new CauseTokenFactory(address(impl), admin, admin);

        engine = new ConversionEngine(
            address(cha), address(factory), address(feeRouter), admin
        );

        // Grant engine the minter role on factory so it can mint cause tokens
        vm.prank(admin);
        factory.setMinter(address(engine));

        // Create a cause
        vm.prank(admin);
        causeToken = factory.createCause(
            "Global Health Token", "HEALTH", "Global Health", "Fund research", charity
        );

        // Mint CHA to alice
        vm.prank(admin);
        cha.mint(alice, 10_000e18);
    }

    function test_convert() public {
        vm.startPrank(alice);
        cha.approve(address(engine), 1000e18);
        engine.convert(causeToken, 1000e18);
        vm.stopPrank();

        // 5% fee = 50 CHA, 95% burned = 950 CHA
        assertEq(CauseToken(causeToken).balanceOf(alice), 950e18);
        assertEq(cha.balanceOf(alice), 9000e18);
    }

    function test_convertFeeCalculation() public {
        vm.startPrank(alice);
        cha.approve(address(engine), 1000e18);
        engine.convert(causeToken, 1000e18);
        vm.stopPrank();

        // totalFeeBps = 500 (5%), so fee = 50, burn = 950
        uint256 expectedFee = 50e18;
        uint256 expectedBurn = 950e18;

        // Charity gets 50% of fee = 25 CHA
        assertEq(cha.balanceOf(charity), (expectedFee * 5000) / 10000);
        // Liquidity gets 30% of fee = 15 CHA
        assertEq(cha.balanceOf(liquidityMgr), (expectedFee * 3000) / 10000);
    }

    function test_convertBurnsCorrectAmount() public {
        uint256 supplyBefore = cha.totalSupply();

        vm.startPrank(alice);
        cha.approve(address(engine), 1000e18);
        engine.convert(causeToken, 1000e18);
        vm.stopPrank();

        // 950 CHA burned + 10 CHA swapped (ops portion goes through swap router which takes it)
        // Actual burn: 950 CHA via burn(), plus the fee portion is transferred not burned
        // Total supply should decrease by burnAmount (950) only
        // But ops portion (10 CHA) is also transferred to swap router
        // So supply decreased by: 950 (burned) = burned via burn()
        // The fee (50) is transferred to fee router which distributes:
        //   25 to charity, 15 to liquidity mgr, 10 to swap router
        // Those are transfers, not burns
        uint256 supplyAfter = cha.totalSupply();
        assertEq(supplyBefore - supplyAfter, 950e18);
    }

    function test_convertMintsCauseTokens() public {
        vm.startPrank(alice);
        cha.approve(address(engine), 1000e18);
        engine.convert(causeToken, 1000e18);
        vm.stopPrank();

        // Cause tokens minted 1:1 with burn amount
        assertEq(CauseToken(causeToken).balanceOf(alice), 950e18);
        assertEq(CauseToken(causeToken).totalSupply(), 950e18);
    }

    function test_convertZeroReverts() public {
        vm.startPrank(alice);
        cha.approve(address(engine), 1000e18);

        vm.expectRevert(IConversionEngine.ZeroAmount.selector);
        engine.convert(causeToken, 0);
        vm.stopPrank();
    }

    function test_convertInvalidCauseReverts() public {
        vm.startPrank(alice);
        cha.approve(address(engine), 1000e18);

        vm.expectRevert(IConversionEngine.InvalidCause.selector);
        engine.convert(address(0xdead), 100e18);
        vm.stopPrank();
    }

    function test_conversionPreview() public view {
        (uint256 burn, uint256 charityFee, uint256 liqFee, uint256 opsFee, uint256 out) =
            engine.getConversionPreview(1000e18);

        assertEq(burn, 950e18);
        assertEq(out, 950e18);
        assertEq(charityFee + liqFee + opsFee, 50e18);
        assertEq(charityFee, 25e18); // 50% of 50
        assertEq(liqFee, 15e18);     // 30% of 50
        assertEq(opsFee, 10e18);     // 20% of 50
    }

    function test_setFeeBps() public {
        vm.prank(admin);
        engine.setTotalFeeBps(300); // 3%

        assertEq(engine.totalFeeBps(), 300);
    }

    function test_setFeeBpsExceedsMaxReverts() public {
        vm.prank(admin);
        vm.expectRevert(IConversionEngine.FeeTooHigh.selector);
        engine.setTotalFeeBps(1001);
    }

    function test_pauseConversion() public {
        vm.prank(admin);
        engine.pause();

        vm.startPrank(alice);
        cha.approve(address(engine), 1000e18);
        vm.expectRevert();
        engine.convert(causeToken, 100e18);
        vm.stopPrank();
    }

    function test_tracksTotalBurned() public {
        assertEq(engine.totalChaBurned(), 0);

        vm.startPrank(alice);
        cha.approve(address(engine), 2000e18);
        engine.convert(causeToken, 1000e18);
        assertEq(engine.totalChaBurned(), 950e18);

        engine.convert(causeToken, 500e18);
        assertEq(engine.totalChaBurned(), 950e18 + 475e18);
        vm.stopPrank();
    }
}
