// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title ArbitrageExecutor
 * @dev Smart contract for executing arbitrage trades across DEXs
 */
contract ArbitrageExecutor is Ownable {
    // Events
    event ArbitrageExecuted(
        address indexed token,
        address indexed buyDex,
        address indexed sellDex,
        uint256 amount,
        uint256 profit
    );
    
    event FundsWithdrawn(address token, address to, uint256 amount);
    
    // Allowed DEX router addresses
    mapping(address => bool) public approvedDexRouters;
    
    // Constructor
    constructor() Ownable(msg.sender) {}
    
    /**
     * @dev Add or remove a DEX router from the approved list
     * @param router Address of the DEX router
     * @param approved Whether to approve or remove the router
     */
    function setDexRouterApproval(address router, bool approved) external onlyOwner {
        approvedDexRouters[router] = approved;
    }
    
    /**
     * @dev Execute a flash loan arbitrage across two DEXs
     * @param token Address of the token to arbitrage
     * @param buyDex Address of the DEX to buy from
     * @param sellDex Address of the DEX to sell to
     * @param buyData Encoded buy transaction data
     * @param sellData Encoded sell transaction data
     * @param amount Amount of tokens to arbitrage
     */
    function executeArbitrage(
        address token,
        address buyDex,
        address sellDex,
        bytes calldata buyData,
        bytes calldata sellData,
        uint256 amount
    ) external onlyOwner {
        require(approvedDexRouters[buyDex], "Buy DEX not approved");
        require(approvedDexRouters[sellDex], "Sell DEX not approved");
        
        // Record initial balance
        uint256 initialBalance = IERC20(token).balanceOf(address(this));
        
        // Execute buy transaction
        (bool buySuccess, ) = buyDex.call(buyData);
        require(buySuccess, "Buy transaction failed");
        
        // Execute sell transaction
        (bool sellSuccess, ) = sellDex.call(sellData);
        require(sellSuccess, "Sell transaction failed");
        
        // Calculate profit
        uint256 finalBalance = IERC20(token).balanceOf(address(this));
        require(finalBalance > initialBalance, "No profit generated");
        uint256 profit = finalBalance - initialBalance;
        
        emit ArbitrageExecuted(token, buyDex, sellDex, amount, profit);
    }
    
    /**
     * @dev Withdraw funds from the contract
     * @param token Address of the token to withdraw
     * @param to Address to send the tokens to
     * @param amount Amount of tokens to withdraw
     */
    function withdrawFunds(address token, address to, uint256 amount) external onlyOwner {
        IERC20(token).transfer(to, amount);
        emit FundsWithdrawn(token, to, amount);
    }
    
    /**
     * @dev Approve a token for trading on a DEX
     * @param token Address of the token
     * @param spender Address of the DEX router
     * @param amount Amount to approve
     */
    function approveToken(address token, address spender, uint256 amount) external onlyOwner {
        IERC20(token).approve(spender, amount);
    }
}