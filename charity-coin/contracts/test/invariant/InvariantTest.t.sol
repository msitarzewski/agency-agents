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
/// @title Handler
/// @notice Performs random conversions for invariant testing.
contract Handler is Test {
    ConversionEngine public engine;
    CharityCoin public cha;
    address public causeToken;
    address public caller;

    uint256 constant MIN_CONVERSION = 1e18;
    uint256 constant MAX_CONVERSION = 10_000e18;

    constructor(ConversionEngine engine_, CharityCoin cha_, address causeToken_, address caller_) {
        engine = engine_;
        cha = cha_;
        causeToken = causeToken_;
        caller = caller_;
    }

    /// @notice Bound amount and perform a conversion.
    function convert(uint256 amount) external {
        amount = bound(amount, MIN_CONVERSION, MAX_CONVERSION);

        // Skip if caller doesn't have enough CHA
        if (cha.balanceOf(caller) < amount) return;

        vm.startPrank(caller);
        cha.approve(address(engine), amount);
        engine.convert(causeToken, amount);
        vm.stopPrank();
    }
}

contract InvariantTest is Test {
    CharityCoin public cha;
    CauseTokenFactory public factory;
    ConversionEngine public engine;
    FeeRouter public feeRouter;
    MockSwapRouter public swapRouter;
    MockERC20 public usdc;
    Handler public handler;

    address admin = makeAddr("admin");
    address charity = makeAddr("charity");
    address opsWallet = makeAddr("opsWallet");
    address liquidityMgr = makeAddr("liquidityMgr");
    address caller = makeAddr("caller");

    address causeToken;

    /// @notice Total CHA minted to the caller at setup time.
    uint256 public originalMinted;

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

        // Mint CHA to the caller
        originalMinted = 10_000_000e18;
        vm.prank(admin);
        cha.mint(caller, originalMinted);

        // Deploy handler and target it for invariant calls
        handler = new Handler(engine, cha, causeToken, caller);
        targetContract(address(handler));
    }

    /// @notice Total CHA burned + current totalSupply = original minted amount.
    /// @dev CHA burned via engine is tracked in engine.totalChaBurned(). The fee portion
    ///      is transferred (not burned), so totalSupply decreases only by burnAmount.
    ///      Invariant: totalChaBurned + totalSupply = originalMinted
    function invariant_burnedPlusCirculatingEqualsOriginalMinted() public view {
        uint256 burned = engine.totalChaBurned();
        uint256 currentSupply = cha.totalSupply();
        assertEq(
            burned + currentSupply,
            originalMinted,
            "burned + circulating != original minted"
        );
    }

    /// @notice Total cause tokens minted across all causes = total CHA burned.
    /// @dev Since cause tokens are minted 1:1 with burn amount, the cause token
    ///      total supply should equal the engine's totalChaBurned counter.
    function invariant_causeTokensMintedMatchBurned() public view {
        uint256 causeSupply = CauseToken(causeToken).totalSupply();
        uint256 totalBurned = engine.totalChaBurned();
        assertEq(
            causeSupply,
            totalBurned,
            "cause token supply != total CHA burned"
        );
    }

    /// @notice Fee shares always sum to 10000 bps.
    function invariant_feeSharesAlwaysSumTo10000() public view {
        uint256 total = feeRouter.charityShareBps()
            + feeRouter.liquidityShareBps()
            + feeRouter.opsShareBps();
        assertEq(total, 10_000, "fee shares do not sum to 10000");
    }
}
