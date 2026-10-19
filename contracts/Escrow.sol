// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.34;

contract Escrow {
    address payable public buyer;
    address payable public seller;
    address public arbitrator;
    uint256 public amount;

    enum State {
        AwaitingPayment, AwaitingDelivery, Complete, Disputed, Refunded, Cancelled
    }

    State public currentState;
    event Deposited(address indexed buyer, uint256 amount);
    event DeliveryConfirmed(address indexed seller, uint256 amount);
    event DisputeRaised(address indexed raisedBy);
    event DisputeResolved(bool refundedBuyer, uint256 amount);
    event DealCancelled(address indexed buyer);

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
    constructor (address payable _buyer, address payable _seller, address _arbitrator) {
        require(_buyer != address(0), "Invalid buyer");
        require(_seller != address(0), "Invalid seller");
        require(_arbitrator != address(0), "Invalid arbitrator");
        require(_buyer != _seller, "Buyer and seller must differ");

        buyer = _buyer;
        seller = _seller;
        arbitrator = _arbitrator;
        currentState = State.AwaitingPayment;
    }
    function deposit() external payable inState(State.AwaitingPayment) onlyBuyer {
        require(msg.value > 0, "Deposit amount should be > 0");
        amount = msg.value;
        currentState = State.AwaitingDelivery;
        emit Deposited(msg.sender, msg.value);
    }
    function confirmDelivery() external inState(State.AwaitingDelivery) onlyBuyer {
        currentState = State.Complete;
        uint256 payment = amount;
        amount = 0;
        (bool success, ) = seller.call{value: payment}("");
        require(success, "Seller payment failed");
        emit DeliveryConfirmed(seller, payment);
    }
    function raiseDispute() external inState(State.AwaitingDelivery){
        require(msg.sender == buyer || msg.sender == seller, "Not a transaction party");
        currentState = State.Disputed;
        emit DisputeRaised(msg.sender);
    }
    function resolveDispute(bool refundBuyer) external inState(State.Disputed) onlyArbitrator {
        uint256 payment = amount;
        amount = 0;
        if (refundBuyer) {
            currentState = State.Refunded;
            (bool success, ) = buyer.call{value: payment}("");
            require(success, "Buyer refund failed");
        } else {
            currentState = State.Complete;
            (bool success, ) = seller.call{value: payment}("");
            require(success, "Seller payment failed");
        }
        emit DisputeResolved(refundBuyer, payment);
    }
    function cancel() external onlyBuyer inState(State.AwaitingPayment) {
        currentState = State.Cancelled;
        emit DealCancelled(msg.sender);
    }
    function getDetails() external view returns (address, address, address, uint256, State) {
        return (buyer, seller, arbitrator, amount, currentState);
    }
}   