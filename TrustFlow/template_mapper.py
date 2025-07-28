import json
from typing import Dict, Any, List, Union

class TemplateMapper:
    """
    Manages various smart contract templates and maps (generates) actual Solidity code
    using provided variables.
    Includes templates optimized for ETHGlobal hackathon demonstrations.
    """
    def __init__(self):
        # Template dictionary: template name (key) and Solidity code string (value)
        self.templates: Dict[str, str] = {
            "ERC20": """
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract {TOKEN_NAME}Token is ERC20, Ownable {
    constructor(string memory name, string memory symbol, uint256 initialSupply) ERC20(name, symbol) {
        // Mints initial supply to the deployer (msg.sender).
        _mint(owner(), initialSupply);
    }
}
            """,
            "ERC721": """
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

contract {NFT_NAME}Collection is ERC721, Ownable {
    using Counters for Counters.Counter;
    Counters.Counter private _tokenIdCounter;

    string private _baseTokenURI;

    constructor(string memory name, string memory symbol, string memory baseTokenURI)
        ERC721(name, symbol) {
        _baseTokenURI = baseTokenURI;
    }

    // Function to mint a new NFT (callable only by the owner)
    function safeMint(address to) public onlyOwner {
        uint250 tokenId = _tokenIdCounter.current();
        _tokenIdCounter.increment();
        _safeMint(to, tokenId);
    }

    // Optional: set token URI
    function _baseURI() internal view override returns (string memory) {
        return _baseTokenURI;
    }

    // Function to set a new baseTokenURI (callable only by the owner)
    function setBaseTokenURI(string memory newBaseURI) public onlyOwner {
        _baseTokenURI = newBaseURI;
    }
}
            """,
            "SimpleStorage": """
pragma solidity ^0.8.0;

contract SimpleStorage {
    uint public storedData;

    event DataStored(uint indexed data);

    function set(uint x) public {
        storedData = x;
        emit DataStored(x);
    }

    function get() public view returns (uint) {
        return storedData;
    }
}
            """,
            "SimpleDAO": """
pragma solidity ^0.8.0;

// A basic DAO with voting functionality (highly simplified example)
contract SimpleDAO {
    struct Proposal {
        uint id;
        string description;
        uint voteCount;
        bool executed;
        mapping(address => bool) voters;
    }

    address public owner;
    uint public nextProposalId;
    mapping(uint => Proposal) public proposals;

    event ProposalCreated(uint id, string description);
    event Voted(uint proposalId, address voter);
    event ProposalExecuted(uint id);

    constructor() {
        owner = msg.sender;
        nextProposalId = 0;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function.");
        _;
    }

    function createProposal(string memory _description) public onlyOwner {
        proposals[nextProposalId] = Proposal(nextProposalId, _description, 0, false);
        emit ProposalCreated(nextProposalId, _description);
        nextProposalId++;
    }

    function vote(uint _proposalId) public {
        Proposal storage proposal = proposals[_proposalId];
        require(proposal.id == _proposalId, "Proposal does not exist.");
        require(!proposal.executed, "Proposal already executed.");
        require(!proposal.voters[msg.sender], "You have already voted for this proposal.");

        proposal.voteCount++;
        proposal.voters[msg.sender] = true;
        emit Voted(_proposalId, msg.sender);
    }

    // Simple execution condition: assumed executable with 1 or more votes (actual DAOs are far more complex)
    function executeProposal(uint _proposalId) public onlyOwner {
        Proposal storage proposal = proposals[_proposalId];
        require(proposal.id == _proposalId, "Proposal does not exist.");
        require(!proposal.executed, "Proposal already executed.");
        require(proposal.voteCount >= 1, "Not enough votes to execute."); // Example condition

        proposal.executed = true;
        emit ProposalExecuted(_proposalId);
        // In a real DAO, execution logic (e.g., calling another contract) would go here.
    }
}
            """,
            "DutchAuction": """
pragma solidity ^0.8.0;

contract DutchAuction {
    address payable public seller;
    uint public reservePrice; // Minimum selling price
    uint public numBlocksAuctionOpen; // Number of blocks the auction will run
    uint public offerPriceDecrement; // Price decrement per block
    uint public initialPrice; // Starting price

    uint public auctionEndBlock; // Block when auction ends
    bool public ended; // Whether the auction has ended
    address public winner; // Winner of the auction

    event AuctionEnded(address winner, uint price);

    constructor(
        uint _reservePrice,
        uint _numBlocksAuctionOpen,
        uint _offerPriceDecrement,
        uint _initialPrice
    ) {
        seller = payable(msg.sender);
        reservePrice = _reservePrice;
        numBlocksAuctionOpen = _numBlocksAuctionOpen;
        offerPriceDecrement = _offerPriceDecrement;
        initialPrice = _initialPrice;
        auctionEndBlock = block.number + numBlocksAuctionOpen;
        ended = false;
    }

    function getPrice() public view returns (uint) {
        if (block.number < auctionEndBlock) {
            return initialPrice - (block.number - (auctionEndBlock - numBlocksAuctionOpen)) * offerPriceDecrement;
        } else {
            return reservePrice;
        }
    }

    function bid() public payable {
        require(!ended, "Auction already ended.");
        uint currentPrice = getPrice();
        require(msg.value >= currentPrice, "Bid price is too low.");

        if (msg.value > currentPrice) {
            // Return excess bid amount
            payable(msg.sender).transfer(msg.value - currentPrice);
        }

        winner = msg.sender;
        ended = true;
        seller.transfer(currentPrice); // Transfer sales amount to seller
        emit AuctionEnded(winner, currentPrice);
    }

    function withdraw() public {
        require(ended, "Auction has not ended yet.");
        require(msg.sender == seller || msg.sender == winner, "Only seller or winner can withdraw.");
        // Since funds are already transferred to the seller in the bid function, no additional logic is needed here.
        // However, this function can typically be used to retrieve remaining funds in other types of auctions.
    }
}
            """
        }
        print("📝 TemplateMapper initialized. Available templates:", list(self.templates.keys()))

    def map_to_template(self, template_name: str, variables: Dict[str, Any]) -> str:
        """
        Finds the specified template and fills placeholders with provided variables
        to return the complete Solidity code.

        Args:
            template_name (str): The name of the template to use.
            variables (Dict[str, Any]): Variables to fill placeholders in the template.

        Returns:
            str: The final Solidity source code with variables applied.

        Raises:
            ValueError: If the template name is invalid or a required variable is missing.
        """
        if template_name not in self.templates:
            raise ValueError(
                f"❌ Error: Template '{template_name}' not found. "
                f"Available templates: {list(self.templates.keys())}"
            )

        solidity_code = self.templates[template_name]

        # Template-specific variable validation and replacement logic
        if template_name == "ERC20":
            required_vars = ["TOKEN_NAME", "TOKEN_SYMBOL", "initialSupply"]
            for var in required_vars:
                if var not in variables:
                    raise ValueError(f"❌ ERC20 template is missing required variable '{var}'.")
            solidity_code = solidity_code.replace("{TOKEN_NAME}", variables["TOKEN_NAME"])
            solidity_code = solidity_code.replace("{TOKEN_SYMBOL}", variables["TOKEN_SYMBOL"])
            # initialSupply is passed directly as a constructor argument, no need to replace in code
        elif template_name == "ERC721":
            required_vars = ["NFT_NAME", "NFT_SYMBOL", "baseTokenURI"]
            for var in required_vars:
                if var not in variables:
                    raise ValueError(f"❌ ERC721 template is missing required variable '{var}'.")
            solidity_code = solidity_code.replace("{NFT_NAME}", variables["NFT_NAME"])
            solidity_code = solidity_code.replace("{NFT_SYMBOL}", variables["NFT_SYMBOL"])
            # baseTokenURI is passed directly as a constructor argument, no need to replace in code
        elif template_name == "DutchAuction":
            required_vars = ["reservePrice", "numBlocksAuctionOpen", "offerPriceDecrement", "initialPrice"]
            for var in required_vars:
                if var not in variables:
                    raise ValueError(f"❌ DutchAuction template is missing required variable '{var}'.")
            # DutchAuction variables are passed as constructor_args, not directly replaced in code
        elif template_name == "SimpleStorage":
            pass # SimpleStorage currently has no variables to replace in code
        elif template_name == "SimpleDAO":
            pass # SimpleDAO currently has no variables to replace in code

        print(f"✅ Template '{template_name}' successfully mapped to Solidity code.")
        return solidity_code

    def get_constructor_args_for_template(self, template_name: str, variables: Dict[str, Any]) -> List[Any]:
        """
        Returns a list of arguments to pass to the contract constructor based on
        the given template name and variables.

        Args:
            template_name (str): The name of the template.
            variables (Dict[str, Any]): Variables used in the template.

        Returns:
            List[Any]: A list of arguments to be passed to the contract constructor.
        """
        if template_name == "ERC20":
            # ERC20 Constructor: string name, string symbol, uint256 initialSupply
            return [
                variables["TOKEN_NAME"],
                variables["TOKEN_SYMBOL"],
                variables["initialSupply"]
            ]
        elif template_name == "ERC721":
            # ERC721 Constructor: string name, string symbol, string baseTokenURI
            return [
                variables["NFT_NAME"],
                variables["NFT_SYMBOL"],
                variables["baseTokenURI"]
            ]
        elif template_name == "SimpleStorage":
            return [] # SimpleStorage has no constructor arguments
        elif template_name == "SimpleDAO":
            return [] # SimpleDAO has no constructor arguments
        elif template_name == "DutchAuction":
            # DutchAuction Constructor: uint _reservePrice, uint _numBlocksAuctionOpen, uint _offerPriceDecrement, uint _initialPrice
            return [
                variables["reservePrice"],
                variables["numBlocksAuctionOpen"],
                variables["offerPriceDecrement"],
                variables["initialPrice"]
            ]
        else:
            return [] # Other templates have no constructor arguments by default

if __name__ == "__main__":
    print("\n--- TemplateMapper Test Script Start ---")

    # Test ERC20 Template
    print("\n[Test: ERC20 Template]")
    tm_erc20 = TemplateMapper()
    try:
        erc20_code = tm_erc20.map_to_template("ERC20", {
            "TOKEN_NAME": "TestToken",
            "TOKEN_SYMBOL": "TTK",
            "initialSupply": 1000 * (10**18) # 1000 tokens with 18 decimals
        })
        print("\n=== 🔥 [Generated ERC20 Solidity Code] ===\n")
        print(erc20_code)
        print("\n=== 🔥 [ERC20 Constructor Arguments] ===\n")
        erc20_args = tm_erc20.get_constructor_args_for_template("ERC20", {
            "TOKEN_NAME": "TestToken",
            "TOKEN_SYMBOL": "TTK",
            "initialSupply": 1000 * (10**18)
        })
        print(erc20_args)
    except ValueError as e:
        print(f"❌ ERC20 Template Test Failed: {e}")

    # Test ERC721 Template
    print("\n[Test: ERC721 Template]")
    tm_erc721 = TemplateMapper()
    try:
        erc721_code = tm_erc721.map_to_template("ERC721", {
            "NFT_NAME": "MyHackathonNFT",
            "NFT_SYMBOL": "HNFT",
            "baseTokenURI": "ipfs://your_ipfs_cid/"
        })
        print("\n=== 🔥 [Generated ERC721 Solidity Code] ===\n")
        print(erc721_code)
        print("\n=== 🔥 [ERC721 Constructor Arguments] ===\n")
        erc721_args = tm_erc721.get_constructor_args_for_template("ERC721", {
            "NFT_NAME": "MyHackathonNFT",
            "NFT_SYMBOL": "HNFT",
            "baseTokenURI": "ipfs://your_ipfs_cid/"
        })
        print(erc721_args)
    except ValueError as e:
        print(f"❌ ERC721 Template Test Failed: {e}")

    # Test SimpleStorage Template
    print("\n[Test: SimpleStorage Template]")
    tm_simple = TemplateMapper()
    try:
        simple_storage_code = tm_simple.map_to_template("SimpleStorage", {})
        print("\n=== 🔥 [Generated SimpleStorage Solidity Code] ===\n")
        print(simple_storage_code)
        print("\n=== 🔥 [SimpleStorage Constructor Arguments] ===\n")
        simple_storage_args = tm_simple.get_constructor_args_for_template("SimpleStorage", {})
        print(simple_storage_args)
    except ValueError as e:
        print(f"❌ SimpleStorage Template Test Failed: {e}")

    # Test for non-existent template (expect error)
    print("\n[Test: Non-existent Template]")
    tm_invalid = TemplateMapper()
    try:
        tm_invalid.map_to_template("NonExistentTemplate", {})
    except ValueError as e:
        print(f"✅ Expected error occurred: {e}")

    print("\n--- TemplateMapper Test Script End ---")
