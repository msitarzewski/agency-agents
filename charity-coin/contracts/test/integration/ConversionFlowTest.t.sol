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

contract ConversionFlowTest is Test {
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

    address healthToken;
    address eduToken;

    function setUp() public {
        // 1. Deploy core tokens
        cha = new CharityCoin(admin, admin);
        usdc = new MockERC20("USDC", "USDC", 6);
        swapRouter = new MockSwapRouter();

        // 2. Deploy FeeRouter
        feeRouter = new FeeRouter(
            address(cha), address(swapRouter), address(usdc),
            opsWallet, liquidityMgr, admin
        );

        // 3. Deploy factory with admin as temp minter
        CauseToken impl = new CauseToken();
        factory = new CauseTokenFactory(address(impl), admin, admin);

        // 4. Deploy ConversionEngine
        engine = new ConversionEngine(
            address(cha), address(factory), address(feeRouter), admin
        );

        // 5. Set engine as minter on factory
        vm.prank(admin);
        factory.setMinter(address(engine));

        // 6. Create causes
        vm.startPrank(admin);
        healthToken = factory.createCause(
            "Global Health Token", "HEALTH", "Global Health",
            "Fund medical research", charity
        );
        eduToken = factory.createCause(
            "Education Token", "EDU", "Education",
            "Fund education access", makeAddr("eduCharity")
        );
        vm.stopPrank();

        // 7. Mint CHA to alice
        vm.prank(admin);
        cha.mint(alice, 100_000e18);
    }

    function test_fullConversionFlow() public {
        uint256 convertAmount = 10_000e18;
        uint256 expectedFee = (convertAmount * 500) / 10_000; // 500 CHA
        uint256 expectedBurn = convertAmount - expectedFee; // 9500 CHA
        uint256 expectedCharityFee = (expectedFee * 5000) / 10_000; // 250 CHA
        uint256 expectedLiqFee = (expectedFee * 3000) / 10_000; // 150 CHA
        uint256 expectedOpsFee = expectedFee - expectedCharityFee - expectedLiqFee; // 100 CHA

        // Record balances
        uint256 aliceCHABefore = cha.balanceOf(alice);
        uint256 supplyBefore = cha.totalSupply();

        // Execute conversion
        vm.startPrank(alice);
        cha.approve(address(engine), convertAmount);
        engine.convert(healthToken, convertAmount);
        vm.stopPrank();

        // Verify CHA was taken from alice
        assertEq(cha.balanceOf(alice), aliceCHABefore - convertAmount);

        // Verify CHA was burned
        assertEq(cha.totalSupply(), supplyBefore - expectedBurn);

        // Verify cause tokens minted 1:1 with burn
        assertEq(CauseToken(healthToken).balanceOf(alice), expectedBurn);

        // Verify charity wallet received CHA
        assertEq(cha.balanceOf(charity), expectedCharityFee);

        // Verify liquidity manager received CHA
        assertEq(cha.balanceOf(liquidityMgr), expectedLiqFee);

        // Verify ops wallet received USDC (via mock swap)
        uint256 expectedUsdc = (expectedOpsFee * 1e6) / 1e18;
        assertEq(usdc.balanceOf(opsWallet), expectedUsdc);

        // Verify accounting
        assertEq(engine.totalChaBurned(), expectedBurn);
        assertEq(engine.userConversions(alice, healthToken), expectedBurn);
    }

    function test_multipleConversionsMultipleCauses() public {
        // Convert to health
        vm.startPrank(alice);
        cha.approve(address(engine), 20_000e18);
        engine.convert(healthToken, 5_000e18);
        engine.convert(eduToken, 3_000e18);
        vm.stopPrank();

        // Both cause tokens should have correct balances
        assertEq(CauseToken(healthToken).balanceOf(alice), 4750e18); // 95% of 5000
        assertEq(CauseToken(eduToken).balanceOf(alice), 2850e18); // 95% of 3000

        // Total burned should be sum of both burns
        assertEq(engine.totalChaBurned(), 4750e18 + 2850e18);
    }

    function test_conversionAfterFeeChange() public {
        // Change fee to 3%
        vm.prank(admin);
        engine.setTotalFeeBps(300);

        vm.startPrank(alice);
        cha.approve(address(engine), 1000e18);
        engine.convert(healthToken, 1000e18);
        vm.stopPrank();

        // 3% fee = 30, burn = 970
        assertEq(CauseToken(healthToken).balanceOf(alice), 970e18);
        assertEq(engine.totalChaBurned(), 970e18);
    }
}
