// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title ISwapRouter
/// @notice Minimal interface for Uniswap V3 SwapRouter's exactInputSingle function.
/// @dev Only includes the subset needed by FeeRouter for CHA -> USDC swaps.
interface ISwapRouter {
    /// @notice Parameters for a single-hop exact-input swap.
    struct ExactInputSingleParams {
        address tokenIn;
        address tokenOut;
        uint24 fee;
        address recipient;
        uint256 amountIn;
        uint256 amountOutMinimum;
        uint160 sqrtPriceLimitX96;
    }

    /// @notice Executes a single-hop exact-input swap.
    /// @param params The swap parameters.
    /// @return amountOut The amount of the output token received.
    function exactInputSingle(ExactInputSingleParams calldata params) external payable returns (uint256 amountOut);
}
