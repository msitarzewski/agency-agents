// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ISwapRouter} from "../../src/interfaces/ISwapRouter.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {MockERC20} from "./MockERC20.sol";

contract MockSwapRouter is ISwapRouter {
    using SafeERC20 for IERC20;

    uint256 public exchangeRate = 1e6; // 1 token in = 1 USDC out (6 decimals)

    function setExchangeRate(uint256 newRate) external {
        exchangeRate = newRate;
    }

    function exactInputSingle(ExactInputSingleParams calldata params) external payable returns (uint256 amountOut) {
        // Take tokenIn from caller
        IERC20(params.tokenIn).safeTransferFrom(msg.sender, address(this), params.amountIn);

        // Calculate output: amountIn * exchangeRate / 1e18
        amountOut = (params.amountIn * exchangeRate) / 1e18;

        // Mint mock USDC to recipient
        MockERC20(params.tokenOut).mint(params.recipient, amountOut);
    }
}
