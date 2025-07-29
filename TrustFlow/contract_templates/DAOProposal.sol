// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract DAOProposal {
    struct Proposal {
        string description;
        uint yesVotes;
        uint noVotes;
    }

    Proposal[] public proposals;

    function createProposal(string memory _desc) public {
        proposals.push(Proposal({description: _desc, yesVotes: 0, noVotes: 0}));
    }

    function vote(uint _proposalId, bool _support) public {
        if (_support) {
            proposals[_proposalId].yesVotes++;
        } else {
            proposals[_proposalId].noVotes++;
        }
    }
}
