// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract SimpleConditional {
    address public owner;
    bool public conditionMet;

    constructor() {
        owner = msg.sender;
    }

    function setCondition(bool _state) public {
        require(msg.sender == owner, "Only owner");
        conditionMet = _state;
    }

    function execute() public view returns (string memory) {
        if (conditionMet) {
            return "✅ Condition met, execution allowed.";
        } else {
            return "❌ Condition not met.";
        }
    }
}
