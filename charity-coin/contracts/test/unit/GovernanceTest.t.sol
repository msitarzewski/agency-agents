// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {IGovernor} from "@openzeppelin/contracts/governance/IGovernor.sol";
import {TimelockController} from "@openzeppelin/contracts/governance/TimelockController.sol";
import {IVotes} from "@openzeppelin/contracts/governance/utils/IVotes.sol";
import {CharityCoin} from "../../src/token/CharityCoin.sol";
import {CharityCoinGovernor} from "../../src/governance/CharityCoinGovernor.sol";
import {CharityCoinTimelock} from "../../src/governance/CharityCoinTimelock.sol";

contract GovernanceTest is Test {
    CharityCoin public cha;
    CharityCoinGovernor public governor;
    CharityCoinTimelock public timelock;

    address admin = makeAddr("admin");
    address minter = makeAddr("minter");
    address proposer = makeAddr("proposer");
    address voterA = makeAddr("voterA");
    address voterB = makeAddr("voterB");
    address voterC = makeAddr("voterC");

    // Governance settings
    uint256 constant VOTING_DELAY = 7200;
    uint256 constant VOTING_PERIOD = 36000;
    uint256 constant PROPOSAL_THRESHOLD = 100_000e18;
    uint256 constant TIMELOCK_MIN_DELAY = 2 days; // 172800 seconds

    // Proposal target: a simple ETH transfer
    address payable proposalTarget = payable(makeAddr("proposalTarget"));

    function setUp() public {
        // Deploy token
        cha = new CharityCoin(admin, minter);

        // Deploy timelock with empty proposers/executors; roles granted below
        address[] memory proposers = new address[](0);
        address[] memory executors = new address[](1);
        executors[0] = address(0); // anyone can execute
        timelock = new CharityCoinTimelock(TIMELOCK_MIN_DELAY, proposers, executors, admin);

        // Deploy governor
        governor = new CharityCoinGovernor(IVotes(address(cha)), TimelockController(payable(address(timelock))));

        // Grant PROPOSER_ROLE to governor on the timelock
        vm.startPrank(admin);
        timelock.grantRole(timelock.PROPOSER_ROLE(), address(governor));
        // Also grant CANCELLER_ROLE to governor
        timelock.grantRole(timelock.CANCELLER_ROLE(), address(governor));
        vm.stopPrank();

        // Mint tokens to proposer and voters, then delegate
        vm.startPrank(minter);
        cha.mint(proposer, 200_000e18);
        cha.mint(voterA, 5_000_000e18);
        cha.mint(voterB, 3_000_000e18);
        cha.mint(voterC, 50_000e18); // small holder
        vm.stopPrank();

        // Delegates must self-delegate to activate voting power
        vm.prank(proposer);
        cha.delegate(proposer);

        vm.prank(voterA);
        cha.delegate(voterA);

        vm.prank(voterB);
        cha.delegate(voterB);

        vm.prank(voterC);
        cha.delegate(voterC);

        // Advance one block so checkpoints are recorded
        vm.roll(block.number + 1);
        vm.warp(block.timestamp + 12);

        // Fund the timelock with some ETH so it can execute transfers
        vm.deal(address(timelock), 10 ether);
    }

    // ─────────────────────────────────────────────────────────────────────
    // Helpers
    // ─────────────────────────────────────────────────────────────────────

    function _buildProposal()
        internal
        view
        returns (
            address[] memory targets,
            uint256[] memory values,
            bytes[] memory calldatas,
            string memory description
        )
    {
        targets = new address[](1);
        targets[0] = proposalTarget;

        values = new uint256[](1);
        values[0] = 1 ether;

        calldatas = new bytes[](1);
        calldatas[0] = "";

        description = "Send 1 ETH to proposalTarget";
    }

    function _proposeAndGetId() internal returns (uint256 proposalId) {
        (
            address[] memory targets,
            uint256[] memory values,
            bytes[] memory calldatas,
            string memory description
        ) = _buildProposal();

        vm.prank(proposer);
        proposalId = governor.propose(targets, values, calldatas, description);
    }

    function _advancePastVotingDelay() internal {
        vm.roll(block.number + VOTING_DELAY + 1);
        vm.warp(block.timestamp + (VOTING_DELAY + 1) * 12);
    }

    function _advancePastVotingPeriod() internal {
        vm.roll(block.number + VOTING_PERIOD + 1);
        vm.warp(block.timestamp + (VOTING_PERIOD + 1) * 12);
    }

    // ─────────────────────────────────────────────────────────────────────
    // 1. Deployment / Settings
    // ─────────────────────────────────────────────────────────────────────

    function test_governorDeploysWithCorrectName() public view {
        assertEq(governor.name(), "CharityCoinGovernor");
    }

    function test_votingDelayIsCorrect() public view {
        assertEq(governor.votingDelay(), VOTING_DELAY);
    }

    function test_votingPeriodIsCorrect() public view {
        assertEq(governor.votingPeriod(), VOTING_PERIOD);
    }

    function test_proposalThresholdIsCorrect() public view {
        assertEq(governor.proposalThreshold(), PROPOSAL_THRESHOLD);
    }

    function test_quorumNumeratorIs4Percent() public view {
        assertEq(governor.quorumNumerator(), 4);
    }

    function test_quorumMatchesFourPercentOfSupply() public view {
        uint256 totalSupply = cha.totalSupply();
        uint256 expectedQuorum = (totalSupply * 4) / 100;
        // quorum is based on past block, use current block - 1
        uint256 actualQuorum = governor.quorum(block.number - 1);
        assertEq(actualQuorum, expectedQuorum);
    }

    function test_timelockMinDelayIsCorrect() public view {
        assertEq(timelock.getMinDelay(), TIMELOCK_MIN_DELAY);
    }

    function test_governorIsTimelockProposer() public view {
        assertTrue(timelock.hasRole(timelock.PROPOSER_ROLE(), address(governor)));
    }

    function test_anyoneCanExecuteOnTimelock() public view {
        // address(0) as executor means EXECUTOR_ROLE is open to everyone
        assertTrue(timelock.hasRole(timelock.EXECUTOR_ROLE(), address(0)));
    }

    // ─────────────────────────────────────────────────────────────────────
    // 2. Creating Proposals
    // ─────────────────────────────────────────────────────────────────────

    function test_createProposal() public {
        uint256 proposalId = _proposeAndGetId();
        assertTrue(proposalId != 0);
        assertEq(uint256(governor.state(proposalId)), uint256(IGovernor.ProposalState.Pending));
    }

    function test_cannotProposeWithoutThreshold() public {
        // voterC has only 50k CHA, below the 100k threshold
        (
            address[] memory targets,
            uint256[] memory values,
            bytes[] memory calldatas,
            string memory description
        ) = _buildProposal();

        vm.prank(voterC);
        vm.expectRevert();
        governor.propose(targets, values, calldatas, description);
    }

    function test_cannotProposeWithoutDelegation() public {
        // Mint tokens to a new address that has NOT delegated
        address noDelegator = makeAddr("noDelegator");
        vm.prank(minter);
        cha.mint(noDelegator, 200_000e18);

        // Advance a block so the checkpoint would exist (but it won't since no delegation)
        vm.roll(block.number + 1);
        vm.warp(block.timestamp + 12);

        (
            address[] memory targets,
            uint256[] memory values,
            bytes[] memory calldatas,
            string memory description
        ) = _buildProposal();

        vm.prank(noDelegator);
        vm.expectRevert();
        governor.propose(targets, values, calldatas, description);
    }

    // ─────────────────────────────────────────────────────────────────────
    // 3. Voting (For / Against / Abstain)
    // ─────────────────────────────────────────────────────────────────────

    function test_voteFor() public {
        uint256 proposalId = _proposeAndGetId();
        _advancePastVotingDelay();

        vm.prank(voterA);
        governor.castVote(proposalId, 1); // 1 = For

        (uint256 against, uint256 forVotes, uint256 abstain) = governor.proposalVotes(proposalId);
        assertEq(forVotes, 5_000_000e18);
        assertEq(against, 0);
        assertEq(abstain, 0);
    }

    function test_voteAgainst() public {
        uint256 proposalId = _proposeAndGetId();
        _advancePastVotingDelay();

        vm.prank(voterA);
        governor.castVote(proposalId, 0); // 0 = Against

        (uint256 against, uint256 forVotes, uint256 abstain) = governor.proposalVotes(proposalId);
        assertEq(against, 5_000_000e18);
        assertEq(forVotes, 0);
        assertEq(abstain, 0);
    }

    function test_voteAbstain() public {
        uint256 proposalId = _proposeAndGetId();
        _advancePastVotingDelay();

        vm.prank(voterA);
        governor.castVote(proposalId, 2); // 2 = Abstain

        (uint256 against, uint256 forVotes, uint256 abstain) = governor.proposalVotes(proposalId);
        assertEq(abstain, 5_000_000e18);
        assertEq(against, 0);
        assertEq(forVotes, 0);
    }

    function test_cannotVoteBeforeVotingDelay() public {
        uint256 proposalId = _proposeAndGetId();
        // Do NOT advance past voting delay

        vm.prank(voterA);
        vm.expectRevert();
        governor.castVote(proposalId, 1);
    }

    function test_cannotVoteTwice() public {
        uint256 proposalId = _proposeAndGetId();
        _advancePastVotingDelay();

        vm.startPrank(voterA);
        governor.castVote(proposalId, 1);

        vm.expectRevert();
        governor.castVote(proposalId, 0);
        vm.stopPrank();
    }

    // ─────────────────────────────────────────────────────────────────────
    // 4. Proposal Passes Quorum -> Queue to Timelock
    // ─────────────────────────────────────────────────────────────────────

    function test_proposalSucceedsAndCanBeQueued() public {
        uint256 proposalId = _proposeAndGetId();
        _advancePastVotingDelay();

        // voterA votes For (5M CHA, well above 4% quorum of ~8.25M total = ~330k needed)
        vm.prank(voterA);
        governor.castVote(proposalId, 1);

        _advancePastVotingPeriod();

        // State should be Succeeded
        assertEq(uint256(governor.state(proposalId)), uint256(IGovernor.ProposalState.Succeeded));

        // Queue the proposal
        (
            address[] memory targets,
            uint256[] memory values,
            bytes[] memory calldatas,
            string memory description
        ) = _buildProposal();

        governor.queue(targets, values, calldatas, keccak256(bytes(description)));

        // State should be Queued
        assertEq(uint256(governor.state(proposalId)), uint256(IGovernor.ProposalState.Queued));
    }

    // ─────────────────────────────────────────────────────────────────────
    // 5. Execute After Timelock Delay
    // ─────────────────────────────────────────────────────────────────────

    function test_executeProposalAfterTimelockDelay() public {
        uint256 proposalId = _proposeAndGetId();
        _advancePastVotingDelay();

        vm.prank(voterA);
        governor.castVote(proposalId, 1);

        _advancePastVotingPeriod();

        (
            address[] memory targets,
            uint256[] memory values,
            bytes[] memory calldatas,
            string memory description
        ) = _buildProposal();

        governor.queue(targets, values, calldatas, keccak256(bytes(description)));

        // Advance past timelock delay
        vm.warp(block.timestamp + TIMELOCK_MIN_DELAY + 1);
        vm.roll(block.number + 1);

        uint256 balanceBefore = proposalTarget.balance;

        governor.execute(targets, values, calldatas, keccak256(bytes(description)));

        // State should be Executed
        assertEq(uint256(governor.state(proposalId)), uint256(IGovernor.ProposalState.Executed));

        // Target should have received 1 ETH
        assertEq(proposalTarget.balance, balanceBefore + 1 ether);
    }

    // ─────────────────────────────────────────────────────────────────────
    // 6. Proposal Fails if Quorum Not Met
    // ─────────────────────────────────────────────────────────────────────

    function test_proposalDefeatedIfQuorumNotMet() public {
        uint256 proposalId = _proposeAndGetId();
        _advancePastVotingDelay();

        // Only voterC votes (50k CHA), which is far below quorum (~330k needed)
        vm.prank(voterC);
        governor.castVote(proposalId, 1);

        _advancePastVotingPeriod();

        // State should be Defeated (quorum not reached)
        assertEq(uint256(governor.state(proposalId)), uint256(IGovernor.ProposalState.Defeated));
    }

    function test_proposalDefeatedIfMoreAgainstThanFor() public {
        uint256 proposalId = _proposeAndGetId();
        _advancePastVotingDelay();

        // voterA votes Against with 5M
        vm.prank(voterA);
        governor.castVote(proposalId, 0);

        // voterB votes For with 3M (quorum met since total votes > 4% but against > for)
        vm.prank(voterB);
        governor.castVote(proposalId, 1);

        _advancePastVotingPeriod();

        assertEq(uint256(governor.state(proposalId)), uint256(IGovernor.ProposalState.Defeated));
    }

    function test_cannotQueueDefeatedProposal() public {
        uint256 proposalId = _proposeAndGetId();
        _advancePastVotingDelay();

        // Nobody votes, quorum not met
        _advancePastVotingPeriod();

        assertEq(uint256(governor.state(proposalId)), uint256(IGovernor.ProposalState.Defeated));

        (
            address[] memory targets,
            uint256[] memory values,
            bytes[] memory calldatas,
            string memory description
        ) = _buildProposal();

        vm.expectRevert();
        governor.queue(targets, values, calldatas, keccak256(bytes(description)));
    }

    // ─────────────────────────────────────────────────────────────────────
    // 7. Cannot Execute Before Timelock Delay
    // ─────────────────────────────────────────────────────────────────────

    function test_cannotExecuteBeforeTimelockDelay() public {
        uint256 proposalId = _proposeAndGetId();
        _advancePastVotingDelay();

        vm.prank(voterA);
        governor.castVote(proposalId, 1);

        _advancePastVotingPeriod();

        (
            address[] memory targets,
            uint256[] memory values,
            bytes[] memory calldatas,
            string memory description
        ) = _buildProposal();

        governor.queue(targets, values, calldatas, keccak256(bytes(description)));

        // Try to execute immediately without advancing time
        vm.expectRevert();
        governor.execute(targets, values, calldatas, keccak256(bytes(description)));
    }

    function test_cannotExecuteOneSecondBeforeDelay() public {
        uint256 proposalId = _proposeAndGetId();
        _advancePastVotingDelay();

        vm.prank(voterA);
        governor.castVote(proposalId, 1);

        _advancePastVotingPeriod();

        (
            address[] memory targets,
            uint256[] memory values,
            bytes[] memory calldatas,
            string memory description
        ) = _buildProposal();

        governor.queue(targets, values, calldatas, keccak256(bytes(description)));

        // Advance to just 1 second before the delay expires
        vm.warp(block.timestamp + TIMELOCK_MIN_DELAY - 1);
        vm.roll(block.number + 1);

        vm.expectRevert();
        governor.execute(targets, values, calldatas, keccak256(bytes(description)));
    }

    // ─────────────────────────────────────────────────────────────────────
    // Additional edge cases
    // ─────────────────────────────────────────────────────────────────────

    function test_proposalStateIsPendingBeforeVotingDelay() public {
        uint256 proposalId = _proposeAndGetId();
        assertEq(uint256(governor.state(proposalId)), uint256(IGovernor.ProposalState.Pending));
    }

    function test_proposalStateIsActiveDuringVoting() public {
        uint256 proposalId = _proposeAndGetId();
        _advancePastVotingDelay();
        assertEq(uint256(governor.state(proposalId)), uint256(IGovernor.ProposalState.Active));
    }

    function test_abstainVotesCountTowardQuorum() public {
        uint256 proposalId = _proposeAndGetId();
        _advancePastVotingDelay();

        // voterA abstains with 5M (above quorum threshold)
        // voterC votes For with 50k
        // With GovernorCountingSimple, abstain votes DO count toward quorum
        // but since forVotes (50k) > againstVotes (0), and quorum is met via abstain,
        // the proposal should succeed
        vm.prank(voterA);
        governor.castVote(proposalId, 2); // Abstain

        vm.prank(voterC);
        governor.castVote(proposalId, 1); // For

        _advancePastVotingPeriod();

        assertEq(uint256(governor.state(proposalId)), uint256(IGovernor.ProposalState.Succeeded));
    }

    function test_executorIsTimelock() public view {
        // The Governor's executor (where proposals are executed through) should be the timelock
        assertEq(governor.timelock(), address(timelock));
    }

    function test_proposalNeedsQueuing() public {
        uint256 proposalId = _proposeAndGetId();
        assertTrue(governor.proposalNeedsQueuing(proposalId));
    }

    function test_fullLifecycle_proposeVoteQueueExecute() public {
        // End-to-end: propose -> vote -> queue -> wait -> execute
        (
            address[] memory targets,
            uint256[] memory values,
            bytes[] memory calldatas,
            string memory description
        ) = _buildProposal();
        bytes32 descriptionHash = keccak256(bytes(description));

        // Propose
        vm.prank(proposer);
        uint256 proposalId = governor.propose(targets, values, calldatas, description);
        assertEq(uint256(governor.state(proposalId)), uint256(IGovernor.ProposalState.Pending));

        // Advance past voting delay
        _advancePastVotingDelay();
        assertEq(uint256(governor.state(proposalId)), uint256(IGovernor.ProposalState.Active));

        // Vote
        vm.prank(voterA);
        governor.castVote(proposalId, 1);
        vm.prank(voterB);
        governor.castVote(proposalId, 1);

        // Advance past voting period
        _advancePastVotingPeriod();
        assertEq(uint256(governor.state(proposalId)), uint256(IGovernor.ProposalState.Succeeded));

        // Queue
        governor.queue(targets, values, calldatas, descriptionHash);
        assertEq(uint256(governor.state(proposalId)), uint256(IGovernor.ProposalState.Queued));

        // Cannot execute yet
        vm.expectRevert();
        governor.execute(targets, values, calldatas, descriptionHash);

        // Wait for timelock delay
        vm.warp(block.timestamp + TIMELOCK_MIN_DELAY + 1);
        vm.roll(block.number + 1);

        // Execute
        uint256 balBefore = proposalTarget.balance;
        governor.execute(targets, values, calldatas, descriptionHash);
        assertEq(uint256(governor.state(proposalId)), uint256(IGovernor.ProposalState.Executed));
        assertEq(proposalTarget.balance, balBefore + 1 ether);
    }
}
