// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {CharityCoin} from "../../src/token/CharityCoin.sol";

contract CharityCoinTest is Test {
    CharityCoin public cha;

    address admin = makeAddr("admin");
    address minter = makeAddr("minter");
    address alice = makeAddr("alice");
    address bob = makeAddr("bob");

    function setUp() public {
        cha = new CharityCoin(admin, minter);
    }

    function test_initialState() public view {
        assertEq(cha.name(), "CharityCoin");
        assertEq(cha.symbol(), "CHA");
        assertEq(cha.totalSupply(), 0);
        assertEq(cha.MAX_SUPPLY(), 1_000_000_000 * 10 ** 18);
    }

    function test_mint() public {
        vm.prank(minter);
        cha.mint(alice, 1000e18);
        assertEq(cha.balanceOf(alice), 1000e18);
        assertEq(cha.totalSupply(), 1000e18);
    }

    function test_mintExceedsMaxSupply() public {
        vm.startPrank(minter);
        cha.mint(alice, cha.MAX_SUPPLY());

        vm.expectRevert(CharityCoin.MaxSupplyExceeded.selector);
        cha.mint(alice, 1);
        vm.stopPrank();
    }

    function test_burn() public {
        vm.prank(minter);
        cha.mint(alice, 1000e18);

        vm.prank(alice);
        cha.burn(400e18);

        assertEq(cha.balanceOf(alice), 600e18);
        assertEq(cha.totalSupply(), 600e18);
    }

    function test_pause() public {
        vm.prank(minter);
        cha.mint(alice, 1000e18);

        vm.prank(admin);
        cha.pause();

        vm.prank(alice);
        vm.expectRevert();
        cha.transfer(bob, 100e18);
    }

    function test_unpause() public {
        vm.prank(minter);
        cha.mint(alice, 1000e18);

        vm.prank(admin);
        cha.pause();

        vm.prank(admin);
        cha.unpause();

        vm.prank(alice);
        cha.transfer(bob, 100e18);
        assertEq(cha.balanceOf(bob), 100e18);
    }

    function test_nonMinterCannotMint() public {
        vm.prank(alice);
        vm.expectRevert();
        cha.mint(alice, 100e18);
    }

    function test_nonPauserCannotPause() public {
        vm.prank(alice);
        vm.expectRevert();
        cha.pause();
    }

    function test_transfer() public {
        vm.prank(minter);
        cha.mint(alice, 1000e18);

        vm.prank(alice);
        cha.transfer(bob, 250e18);

        assertEq(cha.balanceOf(alice), 750e18);
        assertEq(cha.balanceOf(bob), 250e18);
    }

    function test_totalSupplyAfterMintAndBurn() public {
        vm.prank(minter);
        cha.mint(alice, 500e18);

        vm.prank(alice);
        cha.burn(200e18);

        vm.prank(minter);
        cha.mint(bob, 300e18);

        assertEq(cha.totalSupply(), 600e18);
    }
}
