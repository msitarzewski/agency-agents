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
///      Transfers all admin roles to the governance timelock and renounces deployer access.
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

        // ── 4. Deploy CauseTokenFactory first (with deployer as temp minter) ──
        // Deploy factory with deployer as temporary minter; updated to engine below.
        CauseTokenFactory factory = new CauseTokenFactory(
            address(causeTokenImpl),
            deployer,
            deployer // Temporary minter — updated to ConversionEngine below.
        );
        console2.log("CauseTokenFactory:", address(factory));

        // ── 5. Deploy ConversionEngine with real factory address ─────────
        ConversionEngine engine = new ConversionEngine(
            address(chaToken),
            address(factory),
            address(feeRouter),
            deployer
        );
        console2.log("ConversionEngine:", address(engine));

        // Update factory minter to ConversionEngine.
        factory.setMinter(address(engine));

        // Grant DISTRIBUTOR_ROLE on FeeRouter to ConversionEngine.
        feeRouter.grantRole(feeRouter.DISTRIBUTOR_ROLE(), address(engine));

        // Set factory on FeeRouter for cause validation.
        feeRouter.setFactory(address(factory));

        // ── 6. Deploy Governance (Timelock + Governor) ──────────────────
        // Timelock: 2-day delay. Use empty arrays — roles granted explicitly below.
        address[] memory proposers = new address[](0);
        address[] memory executors = new address[](1);
        executors[0] = address(0); // Anyone can execute after delay.

        CharityCoinTimelock timelock = new CharityCoinTimelock(
            2 days,     // minDelay
            proposers,
            executors,
            deployer    // Admin (to configure roles, then renounce).
        );
        console2.log("CharityCoinTimelock:", address(timelock));

        CharityCoinGovernor governor = new CharityCoinGovernor(
            IVotes(address(chaToken)),
            TimelockController(payable(address(timelock)))
        );
        console2.log("CharityCoinGovernor:", address(governor));

        // Grant the governor the PROPOSER_ROLE and CANCELLER_ROLE on the timelock.
        timelock.grantRole(timelock.PROPOSER_ROLE(), address(governor));
        timelock.grantRole(timelock.CANCELLER_ROLE(), address(governor));

        // ── 7. Create the 5 launch causes ───────────────────────────────
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

        // ── 8. Transfer admin roles to timelock ─────────────────────────
        // CharityCoin: transfer admin to timelock, renounce deployer
        chaToken.grantRole(chaToken.DEFAULT_ADMIN_ROLE(), address(timelock));
        chaToken.renounceRole(chaToken.DEFAULT_ADMIN_ROLE(), deployer);

        // ConversionEngine: transfer admin to timelock, renounce deployer
        engine.grantRole(engine.DEFAULT_ADMIN_ROLE(), address(timelock));
        engine.renounceRole(engine.DEFAULT_ADMIN_ROLE(), deployer);

        // FeeRouter: transfer admin to timelock, renounce deployer
        feeRouter.grantRole(feeRouter.DEFAULT_ADMIN_ROLE(), address(timelock));
        feeRouter.renounceRole(feeRouter.DEFAULT_ADMIN_ROLE(), deployer);

        // CauseTokenFactory: transfer admin to timelock, renounce deployer
        factory.grantRole(factory.DEFAULT_ADMIN_ROLE(), address(timelock));
        factory.grantRole(factory.CAUSE_CREATOR_ROLE(), address(timelock));
        factory.renounceRole(factory.CAUSE_CREATOR_ROLE(), deployer);
        factory.renounceRole(factory.DEFAULT_ADMIN_ROLE(), deployer);

        // Timelock: renounce deployer admin
        timelock.renounceRole(timelock.DEFAULT_ADMIN_ROLE(), deployer);

        // ── 9. Log summary ──────────────────────────────────────────────
        console2.log("=== Deployment Complete ===");
        console2.log("Total causes created:", factory.causeCount());
        console2.log("Deployer:", deployer);
        console2.log("All admin roles transferred to timelock");

        vm.stopBroadcast();
    }
}
