// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.34;

contract Escrow {
    address public buyer;
    address payable public seller;
    address public arbitrator;
    uint256 public amount;

    enum State {
        AwaitingPayment, AwaitingDelivery, Complete, Disputed, Refunded
    }
    State public currentState;
    modifier onlyBuyer {
        require(msg.sender == buyer, "Only buyer can call this");
        _;
    }
    modifier onlyArbitrator {
        require(msg.sender == arbitrator, "Only arbitrator can call this");
        _;
    }
    modifier inState(State _state) {
        require(currentState == _state, "Invalid state for operator");
        _;
    }
    constructor (address payable _seller, address _arbitrator) {
        buyer = msg.sender;
        seller = _seller;
        arbitrator = _arbitrator;
        currentState = State.AwaitingPayment;
    }
    function deposit() external payable inState(State.AwaitingPayment) onlyBuyer {
        require(msg.value > 0, "Deposit amount should be > 0");
        amount = msg.value;
        currentState = State.AwaitingDelivery;
    }
    function confirmDelivery() external inState(State.AwaitingDelivery) onlyBuyer {
        currentState = State.Complete;
        seller.transfer(amount);
    }
    function raiseDispute() external inState(State.Disputed) {
        require(msg.sender == buyer || msg.sender == seller, "Not transaction party");
        currentState = State.Disputed;
    }
    function resolveDispute(bool refundBuyer) external inState(State.Disputed) onlyArbitrator {
        if (refundBuyer) {
            currentState = State.Refunded;
            payable(buyer).transfer(amount);
        } else {
            currentState = State.Complete;
            seller.transfer(amount);
        }
    }
    function getDetails() external view returns (address, address, address, uint256, State) {
        return (buyer, seller, arbitrator, amount, currentState);
    }
}   