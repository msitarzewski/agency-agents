// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {Clones} from "@openzeppelin/contracts/proxy/Clones.sol";
import {CauseToken} from "../../src/token/CauseToken.sol";

contract CauseTokenTest is Test {
    CauseToken public impl;
    CauseToken public token;

    address minter = makeAddr("minter");
    address charity = makeAddr("charity");
    address alice = makeAddr("alice");

    bytes32 causeId = keccak256("Global Health");

    function setUp() public {
        impl = new CauseToken();

        address clone = Clones.clone(address(impl));
        token = CauseToken(clone);
        token.initialize(
            "Global Health Token",
            "HEALTH",
            "Global Health",
            "Fund medical research",
            charity,
            causeId,
            minter
        );
    }

    function test_initialize() public view {
        assertEq(token.name(), "Global Health Token");
        assertEq(token.symbol(), "HEALTH");
        assertEq(token.causeName(), "Global Health");
        assertEq(token.causeDescription(), "Fund medical research");
        assertEq(token.charityWallet(), charity);
        assertEq(token.causeId(), causeId);
    }

    function test_cannotReinitialize() public {
        vm.expectRevert(CauseToken.AlreadyInitialized.selector);
        token.initialize(
            "Dup", "DUP", "Dup", "Dup", charity, causeId, minter
        );
    }

    function test_implementationCannotBeInitialized() public {
        vm.expectRevert(CauseToken.AlreadyInitialized.selector);
        impl.initialize(
            "Dup", "DUP", "Dup", "Dup", charity, causeId, minter
        );
    }

    function test_mint() public {
        vm.prank(minter);
        token.mint(alice, 500e18);
        assertEq(token.balanceOf(alice), 500e18);
    }

    function test_nonMinterCannotMint() public {
        vm.prank(alice);
        vm.expectRevert();
        token.mint(alice, 100e18);
    }

    function test_zeroAddressCharityReverts() public {
        address clone2 = Clones.clone(address(impl));
        CauseToken token2 = CauseToken(clone2);

        vm.expectRevert(CauseToken.ZeroAddress.selector);
        token2.initialize(
            "Test", "TST", "Test", "Test", address(0), causeId, minter
        );
    }
}
