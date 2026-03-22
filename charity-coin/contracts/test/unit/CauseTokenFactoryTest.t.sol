// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {CauseToken} from "../../src/token/CauseToken.sol";
import {CauseTokenFactory} from "../../src/factory/CauseTokenFactory.sol";
import {ICauseTokenFactory} from "../../src/interfaces/ICauseTokenFactory.sol";

contract CauseTokenFactoryTest is Test {
    CauseTokenFactory public factory;
    CauseToken public impl;

    address admin = makeAddr("admin");
    address minter = makeAddr("minter");
    address charity = makeAddr("charity");
    address alice = makeAddr("alice");

    function setUp() public {
        impl = new CauseToken();
        factory = new CauseTokenFactory(address(impl), admin, minter);
    }

    function test_createCause() public {
        vm.prank(admin);
        address token = factory.createCause(
            "Global Health Token", "HEALTH", "Global Health", "Fund research", charity
        );

        assertTrue(token != address(0));
        assertEq(CauseToken(token).name(), "Global Health Token");
        assertEq(CauseToken(token).symbol(), "HEALTH");
        assertEq(CauseToken(token).charityWallet(), charity);
        assertTrue(factory.isCause(token));
    }

    function test_getCause() public {
        vm.prank(admin);
        address token = factory.createCause(
            "Global Health Token", "HEALTH", "Global Health", "Fund research", charity
        );

        bytes32 causeId = keccak256(abi.encodePacked("Global Health Token"));
        assertEq(factory.getCause(causeId), token);
    }

    function test_getAllCauses() public {
        vm.startPrank(admin);
        address t1 = factory.createCause("Token A", "A", "Cause A", "Desc A", charity);
        address t2 = factory.createCause("Token B", "B", "Cause B", "Desc B", charity);
        vm.stopPrank();

        address[] memory all = factory.getAllCauses();
        assertEq(all.length, 2);
        assertEq(all[0], t1);
        assertEq(all[1], t2);
    }

    function test_duplicateCauseReverts() public {
        vm.startPrank(admin);
        factory.createCause("Token A", "A", "Cause A", "Desc A", charity);

        vm.expectRevert(ICauseTokenFactory.CauseAlreadyExists.selector);
        factory.createCause("Token A", "A2", "Cause A2", "Desc A2", charity);
        vm.stopPrank();
    }

    function test_isCause() public {
        vm.prank(admin);
        address token = factory.createCause(
            "Token A", "A", "Cause A", "Desc", charity
        );

        assertTrue(factory.isCause(token));
        assertFalse(factory.isCause(address(0x1234)));
    }

    function test_onlyCreatorRole() public {
        vm.prank(alice);
        vm.expectRevert();
        factory.createCause("Token", "T", "Cause", "Desc", charity);
    }

    function test_causeCount() public {
        assertEq(factory.causeCount(), 0);

        vm.startPrank(admin);
        factory.createCause("Token A", "A", "Cause A", "Desc A", charity);
        assertEq(factory.causeCount(), 1);

        factory.createCause("Token B", "B", "Cause B", "Desc B", charity);
        assertEq(factory.causeCount(), 2);
        vm.stopPrank();
    }
}
