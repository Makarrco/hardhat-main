
 // SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import "./Escrow.sol";

contract EscrowFactory {
    address public immutable arbitrator;

    address[] public allEscrows;

    mapping(address => address[]) private userEscrows;

    event EscrowCreated(
        address indexed escrowAddress,
        address indexed buyer,
        address indexed seller,
        uint256 escrowId
    );

    constructor(address _arbitrator) {
        require(_arbitrator != address(0), "Invalid arbitrator");
        arbitrator = _arbitrator;
    }
    function createEscrow(address payable seller) external returns (address escrowAddress){
        require(seller != address(0), "Invalid seller");
        require(seller != msg.sender, "Cannot buy from yourself");
        Escrow escrow = new Escrow(
            payable(msg.sender),
            seller,
            arbitrator
        );

        escrowAddress = address(escrow);
        allEscrows.push(escrowAddress);
        userEscrows[msg.sender].push(escrowAddress);
        userEscrows[seller].push(escrowAddress);
        emit EscrowCreated(
            escrowAddress,
            msg.sender,
            seller,
            allEscrows.length - 1
        );
    }
    function getEscrowCount() external view returns (uint256) {
        return allEscrows.length;
    }

    function getAllEscrows() external view returns (address[] memory) {
        return allEscrows;
    }
    function getUserEscrows(address user) external view returns (address[] memory){
        return userEscrows[user];
    }
}
