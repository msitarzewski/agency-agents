// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Script, console2} from "forge-std/Script.sol";

import {CharityCoin} from "../src/token/CharityCoin.sol";
import {CauseToken} from "../src/token/CauseToken.sol";
import {CauseTokenFactory} from "../src/factory/CauseTokenFactory.sol";
import {ConversionEngine} from "../src/engine/ConversionEngine.sol";
import {FeeRouter} from "../src/fees/FeeRouter.sol";
import {CharityCoinGovernor} from "../src/governance/CharityCoinGovernor.sol";
import {CharityCoinTimelock} from "../src/governance/CharityCoinTimelock.sol";
import {IVotes} from "@openzeppelin/contracts/governance/utils/IVotes.sol";
import {TimelockController} from "@openzeppelin/contracts/governance/TimelockController.sol";

/// @title Deploy
/// @notice Foundry deployment script for the Charity Coin ecosystem.
/// @dev Deploys all core contracts, sets up roles, and creates the 5 launch causes.
///
/// Usage:
///   forge script script/Deploy.s.sol:Deploy --rpc-url $BASE_RPC_URL --broadcast --verify
///
/// Environment variables:
///   - DEPLOYER_PRIVATE_KEY:  Private key of the deploying account.
///   - SWAP_ROUTER:           Uniswap V3 SwapRouter address on target chain.
///   - USDC:                  USDC token address on target chain.
///   - OPERATIONS_WALLET:     Wallet that receives ops fee distributions.
///   - LIQUIDITY_MANAGER:     Address that holds CHA for liquidity provision.
///   - CHARITY_WALLET_HEALTH: Charity wallet for HEALTH cause.
///   - CHARITY_WALLET_EDU:    Charity wallet for EDU cause.
///   - CHARITY_WALLET_ENV:    Charity wallet for ENV cause.
///   - CHARITY_WALLET_WATER:  Charity wallet for WATER cause.
///   - CHARITY_WALLET_HUNGER: Charity wallet for HUNGER cause.
contract Deploy is Script {
    function run() external {
        // ── Load configuration from environment ─────────────────────────
        uint256 deployerPrivateKey = vm.envUint("DEPLOYER_PRIVATE_KEY");
        address deployer = vm.addr(deployerPrivateKey);

        address swapRouter = vm.envAddress("SWAP_ROUTER");
        address usdc = vm.envAddress("USDC");
        address operationsWallet = vm.envAddress("OPERATIONS_WALLET");
        address liquidityManager = vm.envAddress("LIQUIDITY_MANAGER");

        // Charity wallets for each launch cause.
        address healthWallet = vm.envAddress("CHARITY_WALLET_HEALTH");
        address eduWallet = vm.envAddress("CHARITY_WALLET_EDU");
        address envWallet = vm.envAddress("CHARITY_WALLET_ENV");
        address waterWallet = vm.envAddress("CHARITY_WALLET_WATER");
        address hungerWallet = vm.envAddress("CHARITY_WALLET_HUNGER");

        vm.startBroadcast(deployerPrivateKey);

        // ── 1. Deploy CharityCoin (CHA) ─────────────────────────────────
        // Deployer is both default admin and initial minter.
        CharityCoin chaToken = new CharityCoin(deployer, deployer);
        console2.log("CharityCoin (CHA):", address(chaToken));

        // ── 2. Deploy CauseToken implementation ─────────────────────────
        CauseToken causeTokenImpl = new CauseToken();
        console2.log("CauseToken implementation:", address(causeTokenImpl));

        // ── 3. Deploy FeeRouter ─────────────────────────────────────────
        FeeRouter feeRouter = new FeeRouter(
            address(chaToken),
            swapRouter,
            usdc,
            operationsWallet,
            liquidityManager,
            deployer
        );
        console2.log("FeeRouter:", address(feeRouter));

        // ── 4. Deploy ConversionEngine ──────────────────────────────────
        ConversionEngine engine = new ConversionEngine(
            address(chaToken),
            address(0), // Factory placeholder — updated below.
            address(feeRouter),
            deployer
        );
        console2.log("ConversionEngine:", address(engine));

        // ── 5. Deploy CauseTokenFactory ─────────────────────────────────
        // The ConversionEngine address is the minter for all cause tokens.
        CauseTokenFactory factory = new CauseTokenFactory(
            address(causeTokenImpl),
            deployer,
            address(engine)
        );
        console2.log("CauseTokenFactory:", address(factory));

        // Point the ConversionEngine at the factory.
        engine.setFactory(address(factory));

        // ── 6. Deploy Governance (Timelock + Governor) ──────────────────
        // Timelock: 2-day delay, governor is proposer, anyone can execute.
        address[] memory proposers = new address[](1);
        address[] memory executors = new address[](1);
        proposers[0] = address(0); // Placeholder — updated after governor deployment.
        executors[0] = address(0); // Anyone can execute after delay.

        CharityCoinTimelock timelock = new CharityCoinTimelock(
            2 days,     // minDelay
            proposers,  // Updated below to include governor.
            executors,
            deployer    // Admin (to configure roles, then renounce).
        );
        console2.log("CharityCoinTimelock:", address(timelock));

        CharityCoinGovernor governor = new CharityCoinGovernor(
            IVotes(address(chaToken)),
            TimelockController(payable(address(timelock)))
        );
        console2.log("CharityCoinGovernor:", address(governor));

        // Grant the governor the PROPOSER_ROLE on the timelock.
        timelock.grantRole(timelock.PROPOSER_ROLE(), address(governor));
        // Grant the governor the CANCELLER_ROLE on the timelock.
        timelock.grantRole(timelock.CANCELLER_ROLE(), address(governor));

        // ── 7. Set up roles ─────────────────────────────────────────────
        // Grant MINTER_ROLE on CHA to the ConversionEngine (for future use if needed).
        // Note: The engine burns CHA, it doesn't mint it. But the factory's minter
        // (the engine) has MINTER_ROLE on each CauseToken via factory.createCause().

        // ── 8. Create the 5 launch causes ───────────────────────────────
        factory.createCause(
            "CharityCoin Health",
            "chHEALTH",
            "Global Health Initiative",
            "Supporting healthcare access and medical research worldwide",
            healthWallet
        );
        console2.log("Created cause: HEALTH");

        factory.createCause(
            "CharityCoin Education",
            "chEDU",
            "Education For All",
            "Funding educational programs and scholarships globally",
            eduWallet
        );
        console2.log("Created cause: EDU");

        factory.createCause(
            "CharityCoin Environment",
            "chENV",
            "Environmental Protection",
            "Fighting climate change and protecting natural ecosystems",
            envWallet
        );
        console2.log("Created cause: ENV");

        factory.createCause(
            "CharityCoin Water",
            "chWATER",
            "Clean Water Access",
            "Providing clean drinking water to underserved communities",
            waterWallet
        );
        console2.log("Created cause: WATER");

        factory.createCause(
            "CharityCoin Hunger",
            "chHUNGER",
            "End Hunger",
            "Combating food insecurity and supporting sustainable agriculture",
            hungerWallet
        );
        console2.log("Created cause: HUNGER");

        // ── 9. Log summary ──────────────────────────────────────────────
        console2.log("=== Deployment Complete ===");
        console2.log("Total causes created:", factory.causeCount());
        console2.log("Deployer:", deployer);

        vm.stopBroadcast();
    }
}
