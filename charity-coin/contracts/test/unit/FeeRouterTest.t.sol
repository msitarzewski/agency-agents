// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {CharityCoin} from "../../src/token/CharityCoin.sol";
import {CauseToken} from "../../src/token/CauseToken.sol";
import {CauseTokenFactory} from "../../src/factory/CauseTokenFactory.sol";
import {FeeRouter} from "../../src/fees/FeeRouter.sol";
import {IFeeRouter} from "../../src/interfaces/IFeeRouter.sol";
import {MockSwapRouter} from "../mocks/MockSwapRouter.sol";
import {MockERC20} from "../mocks/MockERC20.sol";
import {Clones} from "@openzeppelin/contracts/proxy/Clones.sol";

contract FeeRouterTest is Test {
    CharityCoin public cha;
    FeeRouter public router;
    MockSwapRouter public swapRouter;
    MockERC20 public usdc;
    CauseToken public causeToken;
    CauseTokenFactory public factory;

    address admin = makeAddr("admin");
    address minter = makeAddr("minter");
    address charity = makeAddr("charity");
    address opsWallet = makeAddr("opsWallet");
    address liquidityMgr = makeAddr("liquidityMgr");
    address distributor = makeAddr("distributor");

    function setUp() public {
        cha = new CharityCoin(admin, minter);
        usdc = new MockERC20("USDC", "USDC", 6);
        swapRouter = new MockSwapRouter();

        router = new FeeRouter(
            address(cha), address(swapRouter), address(usdc),
            opsWallet, liquidityMgr, admin
        );

        // Grant DISTRIBUTOR_ROLE to the distributor address
        bytes32 distRole = router.DISTRIBUTOR_ROLE();
        vm.prank(admin);
        router.grantRole(distRole, distributor);

        // Create a cause token clone and factory for validation
        CauseToken impl = new CauseToken();
        factory = new CauseTokenFactory(address(impl), admin, admin);

        vm.prank(admin);
        address causeAddr = factory.createCause(
            "Health Token", "HEALTH", "Global Health", "Fund research", charity
        );
        causeToken = CauseToken(causeAddr);

        // Set factory on router for cause validation
        vm.prank(admin);
        router.setFactory(address(factory));

        // Mint CHA to the router for distribution
        vm.prank(minter);
        cha.mint(address(router), 1000e18);
    }

    function test_distributeFees() public {
        vm.prank(distributor);
        router.distributeFees(address(causeToken), 100e18);

        // 50% to charity = 50
        assertEq(cha.balanceOf(charity), 50e18);
        // 30% to liquidity = 30
        assertEq(cha.balanceOf(liquidityMgr), 30e18);
        // 20% to ops = 20 (swapped via mock router)
        // swap router takes 20 CHA from router
        assertEq(cha.balanceOf(address(swapRouter)), 20e18);
    }

    function test_distributeFeesRequiresRole() public {
        vm.prank(makeAddr("attacker"));
        vm.expectRevert();
        router.distributeFees(address(causeToken), 100e18);
    }

    function test_charityReceivesFees() public {
        vm.prank(distributor);
        router.distributeFees(address(causeToken), 200e18);
        assertEq(cha.balanceOf(charity), 100e18); // 50% of 200
    }

    function test_liquidityReceivesFees() public {
        vm.prank(distributor);
        router.distributeFees(address(causeToken), 200e18);
        assertEq(cha.balanceOf(liquidityMgr), 60e18); // 30% of 200
    }

    function test_opsSwapCalled() public {
        vm.prank(distributor);
        router.distributeFees(address(causeToken), 200e18);

        // Ops amount = 40 CHA (20% of 200), swapped to USDC
        // Mock router mints USDC at 1:1e6/1e18 rate
        uint256 expectedUsdc = (40e18 * 1e6) / 1e18;
        assertEq(usdc.balanceOf(opsWallet), expectedUsdc);
    }

    function test_setFeeShares() public {
        vm.prank(admin);
        router.setFeeShares(4000, 4000, 2000);

        assertEq(router.charityShareBps(), 4000);
        assertEq(router.liquidityShareBps(), 4000);
        assertEq(router.opsShareBps(), 2000);
    }

    function test_feeSharesMustSumTo10000() public {
        vm.prank(admin);
        vm.expectRevert(IFeeRouter.InvalidFeeShares.selector);
        router.setFeeShares(5000, 3000, 1000); // sums to 9000
    }

    function test_setMaxSlippage() public {
        vm.prank(admin);
        router.setMaxSlippageBps(300);
        assertEq(router.maxSlippageBps(), 300);
    }

    function test_maxSlippageExceedsCap() public {
        vm.prank(admin);
        vm.expectRevert(IFeeRouter.SlippageTooHigh.selector);
        router.setMaxSlippageBps(501);
    }

    function test_setOperationsWallet() public {
        address newOps = makeAddr("newOps");
        vm.prank(admin);
        router.setOperationsWallet(newOps);
        assertEq(router.operationsWallet(), newOps);
    }

    function test_setOperationsWalletZeroReverts() public {
        vm.prank(admin);
        vm.expectRevert(IFeeRouter.ZeroAddress.selector);
        router.setOperationsWallet(address(0));
    }

    function test_setPoolFeeValidation() public {
        vm.startPrank(admin);
        router.setPoolFee(500);
        assertEq(router.poolFee(), 500);

        vm.expectRevert(IFeeRouter.InvalidPoolFee.selector);
        router.setPoolFee(200); // Invalid tier
        vm.stopPrank();
    }

    function test_setLiquidityManagerEmitsEvent() public {
        address newMgr = makeAddr("newMgr");
        vm.prank(admin);
        router.setLiquidityManager(newMgr);
        assertEq(router.liquidityManager(), newMgr);
    }

    function test_zeroFeeDoesNothing() public {
        uint256 charityBefore = cha.balanceOf(charity);
        vm.prank(distributor);
        router.distributeFees(address(causeToken), 0);
        assertEq(cha.balanceOf(charity), charityBefore);
    }
}
