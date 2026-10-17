// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.34;

interface IEscrow {
    function resolveDispute(bool refundBuyer) external;
}

contract Arbitrator {
    address public arbitratorOwner;
    modifier onlyAtribator() {
        require(msg.sender == arbitratorOwner, "Not authorized arbitrator");
        _;
    }
    constructor() {
        arbitratorOwner = msg.sender;
    }
    function resolve(address escrowAddress, bool refundBuyer) external onlyAtribator {
        IEscrow(escrowAddress).resolveDispute(refundBuyer);
    }
}