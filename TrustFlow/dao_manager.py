"""
dao_manager.py
------------------
Simple DAO Proposal / Voting / Execution Management Module (for Hackathon MVP)
"""

import json
import time
from typing import Dict, Any, List, Optional

class DAOManager:
    """
    DAO Proposal/Voting/Execution Management Class.
    The MVP uses an in-memory storage (dict); future versions can integrate with DB/smart contracts.
    """

    def __init__(self):
        self.proposals: Dict[int, Dict[str, Any]] = {}  # proposal_id → proposal data
        self.votes: Dict[int, Dict[str, int]] = {}      # proposal_id → {address: vote} (1 for Yes, 0 for No)
        self.proposal_counter = 0

    def create_proposal(self, title: str, description: str, proposer: str) -> int:
        """
        Creates a new DAO proposal.
        Args:
            title (str): The title of the proposal.
            description (str): The description of the proposal.
            proposer (str): The address of the proposer (wallet address).
        Returns:
            proposal_id (int): The ID of the created proposal.
        """
        self.proposal_counter += 1
        proposal_id = self.proposal_counter

        self.proposals[proposal_id] = {
            "id": proposal_id,
            "title": title,
            "description": description,
            "proposer": proposer,
            "status": "ACTIVE",  # ACTIVE, EXECUTED, REJECTED
            "created_at": time.time()
        }

        self.votes[proposal_id] = {}
        print(f"✅ [DAO] Proposal created: {proposal_id} – {title}")
        return proposal_id

    def vote(self, proposal_id: int, voter: str, support: bool):
        """
        Casts a vote on a DAO proposal.
        Args:
            proposal_id (int): The ID of the proposal to vote on.
            voter (str): The address of the voter.
            support (bool): True for 'Yes' (support), False for 'No' (oppose).
        Raises:
            ValueError: If the proposal does not exist or is not in an 'ACTIVE' state.
        """
        if proposal_id not in self.proposals:
            raise ValueError("❌ Proposal does not exist.")
        if self.proposals[proposal_id]["status"] != "ACTIVE":
            raise ValueError("❌ Proposal is not in a votable state.")

        self.votes[proposal_id][voter] = 1 if support else 0
        print(f"🗳 [DAO] {voter} → {'Yes' if support else 'No'} (Proposal {proposal_id})")

    def tally_votes(self, proposal_id: int) -> Dict[str, int]:
        """
        Tallies the votes for a given proposal.
        Args:
            proposal_id (int): The ID of the proposal to tally votes for.
        Returns:
            Dict[str, int]: A dictionary with 'yes' and 'no' vote counts. E.g., {"yes": X, "no": Y}
        Raises:
            ValueError: If the proposal does not exist.
        """
        if proposal_id not in self.votes:
            raise ValueError("❌ Proposal does not exist.")

        yes_votes = sum(v for v in self.votes[proposal_id].values() if v == 1)
        no_votes = sum(1 for v in self.votes[proposal_id].values() if v == 0)

        return {"yes": yes_votes, "no": no_votes}

    def execute_proposal(self, proposal_id: int) -> str:
        """
        Executes a DAO proposal.
        - Can only be executed if 'Yes' votes are a majority.
        Args:
            proposal_id (int): The ID of the proposal to execute.
        Returns:
            str: The new status of the proposal ("EXECUTED" or "REJECTED").
        Raises:
            ValueError: If the proposal does not exist or is already processed.
        """
        if proposal_id not in self.proposals:
            raise ValueError("❌ Proposal does not exist.")
        if self.proposals[proposal_id]["status"] != "ACTIVE":
            raise ValueError("❌ Proposal has already been processed.")

        results = self.tally_votes(proposal_id)
        if results["yes"] > results["no"]:
            self.proposals[proposal_id]["status"] = "EXECUTED"
            print(f"🚀 [DAO] Proposal {proposal_id} executed!")
            return "EXECUTED"
        else:
            self.proposals[proposal_id]["status"] = "REJECTED"
            print(f"❌ [DAO] Proposal {proposal_id} rejected.")
            return "REJECTED"

    def get_proposal(self, proposal_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieves details of a specific proposal.
        Args:
            proposal_id (int): The ID of the proposal.
        Returns:
            Optional[Dict[str, Any]]: The proposal details, or None if not found.
        """
        return self.proposals.get(proposal_id)

    def list_proposals(self) -> List[Dict[str, Any]]:
        """
        Returns a list of all proposals.
        Returns:
            List[Dict[str, Any]]: A list of all proposal details.
        """
        return list(self.proposals.values())

# --- Example Usage / Main Execution Block ---
if __name__ == "__main__":
    print("\n--- DAOManager Example Usage Start ---")

    dao_manager = DAOManager()

    # 1. Create Proposals
    print("\n--- Creating Proposals ---")
    prop_id_1 = dao_manager.create_proposal(
        "Fund AI Agent Development",
        "Allocate 1000 ETH for the development of the next-gen AI agent.",
        "0xProposer1Address"
    )
    prop_id_2 = dao_manager.create_proposal(
        "Community Event Grant",
        "Approve 500 ETH for a community hackathon event.",
        "0xProposer2Address"
    )
    prop_id_3 = dao_manager.create_proposal(
        "Website Redesign",
        "Redesign the DAO's official website for better UX.",
        "0xProposer3Address"
    )

    # 2. List all Proposals
    print("\n--- Listing All Proposals ---")
    all_proposals = dao_manager.list_proposals()
    for prop in all_proposals:
        print(f"Proposal {prop['id']}: {prop['title']} (Status: {prop['status']})")

    # 3. Vote on Proposals
    print("\n--- Casting Votes ---")
    try:
        dao_manager.vote(prop_id_1, "0xVoterA", True)  # Yes
        dao_manager.vote(prop_id_1, "0xVoterB", True)  # Yes
        dao_manager.vote(prop_id_1, "0xVoterC", False) # No

        dao_manager.vote(prop_id_2, "0xVoterA", False) # No
        dao_manager.vote(prop_id_2, "0xVoterB", False) # No
        dao_manager.vote(prop_id_2, "0xVoterC", True)  # Yes

        dao_manager.vote(prop_id_3, "0xVoterD", True) # Yes
        dao_manager.vote(prop_id_3, "0xVoterE", True) # Yes
        dao_manager.vote(prop_id_3, "0xVoterF", True) # Yes

    except ValueError as e:
        print(f"Error during voting: {e}")

    # 4. Tally Votes
    print("\n--- Tallying Votes ---")
    tally_1 = dao_manager.tally_votes(prop_id_1)
    print(f"Proposal {prop_id_1} Vote Tally: Yes={tally_1['yes']}, No={tally_1['no']}")

    tally_2 = dao_manager.tally_votes(prop_id_2)
    print(f"Proposal {prop_id_2} Vote Tally: Yes={tally_2['yes']}, No={tally_2['no']}")

    tally_3 = dao_manager.tally_votes(prop_id_3)
    print(f"Proposal {prop_id_3} Vote Tally: Yes={tally_3['yes']}, No={tally_3['no']}")

    # 5. Execute Proposals
    print("\n--- Executing Proposals ---")
    try:
        status_1 = dao_manager.execute_proposal(prop_id_1)
        print(f"Proposal {prop_id_1} execution result: {status_1}")

        status_2 = dao_manager.execute_proposal(prop_id_2)
        print(f"Proposal {prop_id_2} execution result: {status_2}")

        status_3 = dao_manager.execute_proposal(prop_id_3)
        print(f"Proposal {prop_id_3} execution result: {status_3}")

    except ValueError as e:
        print(f"Error during execution: {e}")

    # 6. Check final status of proposals
    print("\n--- Final Proposal Status ---")
    for prop_id in [prop_id_1, prop_id_2, prop_id_3]:
        prop = dao_manager.get_proposal(prop_id)
        if prop:
            print(f"Proposal {prop['id']}: {prop['title']} (Final Status: {prop['status']})")

    print("\n--- DAOManager Example Usage End ---")
