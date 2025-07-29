// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract DutchAuction {
    address payable public seller;
    uint public startingPrice;
    uint public discountRate;
    uint public startAt;
    uint public expiresAt;
    bool public sold;

    constructor(uint _startingPrice, uint _discountRate) {
        seller = payable(msg.sender);
        startingPrice = _startingPrice;
        discountRate = _discountRate;
        startAt = block.timestamp;
        expiresAt = block.timestamp + 7 days;
    }

    function getPrice() public view returns (uint) {
        uint elapsed = block.timestamp - startAt;
        uint discount = discountRate * elapsed;
        return startingPrice - discount;
    }
}
