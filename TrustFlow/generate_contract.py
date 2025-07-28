import os
import openai
from typing import Optional, Dict, Any
import getpass # getpass module is needed for hidden input

# 1. Groq API Key Setup
# Retrieve GROQ_API_KEY from environment variables, or prompt for it if not set.
groq_api_key = os.getenv("GROQ_API_KEY")

if not groq_api_key:
    print("⚠️ GROQ_API_KEY environment variable is not set.")
    user_choice = input("Do you want to proceed by entering the API key directly? (y/n): ").strip().lower()
    if user_choice == 'y':
        # Use getpass to hide the API key input
        groq_api_key = getpass.getpass("🔐 Enter your Groq API Key (input will be hidden): ").strip()
    else:
        print("Cannot proceed without an API key. Exiting program.")
        exit()

# Set OpenAI SDK's base_url to the Groq API endpoint.
openai.base_url = "https://api.groq.com/openai/v1/"
openai.api_key = groq_api_key

# Create Groq client instance (it's good practice to create and reuse it globally)
# In a real application, it's more efficient to create this client globally.
groq_client = openai.OpenAI(
    api_key=groq_api_key,
    base_url="https://api.groq.com/openai/v1/",
)


def _call_groq_api(messages: list, model: str = "llama3-8b-8192", temperature: float = 0.5, max_tokens: int = 1024) -> str:
    """
    Internal helper function to call the Groq API.
    """
    try:
        chat_completion = groq_client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return chat_completion.choices[0].message.content
    except openai.APIStatusError as e:
        print(f"Groq API Error Status: {e.status_code}")
        print(f"Groq API Error Message: {e.response}")
        raise RuntimeError(f"Groq API Error: {e.status_code} - {e.response}")
    except openai.APITimeoutError as e:
        raise RuntimeError(f"Groq API Timeout Error: {e}")
    except openai.APIConnectionError as e:
        raise RuntimeError(f"Groq API Connection Error: {e}")
    except Exception as e:
        raise RuntimeError(f"Unexpected Error: {e}")


def contract_audit_chatbot_groq(user_prompt: str, contract_code: Optional[str] = None) -> str:
    """
    A chatbot using Groq API to answer questions or analyze Solidity smart contracts.

    Args:
        user_prompt (str): User's question or request for explanation.
        contract_code (Optional[str]): Solidity code (optional).

    Returns:
        str: Chatbot's response.
    """
    full_prompt = user_prompt
    if contract_code:
        full_prompt += f"\n\nPlease also analyze this Solidity code:\n{contract_code}"

    messages = [
        {"role": "system", "content": "You are a Web3 AI auditor who explains, audits, and simplifies smart contracts."},
        {"role": "user", "content": full_prompt}
    ]

    return _call_groq_api(messages, model="llama3-8b-8192", temperature=0.5)


def contract_generate_solidity_groq(user_description: str, model: str = "llama3-8b-8192") -> Dict[str, str]:
    """
    Generates Solidity smart contract code from a natural language description using Groq API,
    and returns a natural language explanation of the generated code in JSON format.

    Args:
        user_description (str): Natural language description of the smart contract to be generated.
        model (str): Groq model to use (default: llama3-8b-8192).

    Returns:
        Dict[str, str]: A dictionary containing 'solidity_code' and 'explanation'.
    """
    # Step 1: Generate Solidity code
    code_generation_messages = [
        {"role": "system", "content": "You are an expert Solidity smart contract developer. Your task is to generate clean, secure, and functional Solidity code based on the user's natural language description. Provide only the Solidity code, without any additional explanations or text. Ensure the code is production-ready and follows best practices. Add clear and concise comments to the code for readability and maintainability. Prioritize security in your code generation."},
        {"role": "user", "content": user_description}
    ]
    solidity_code = _call_groq_api(code_generation_messages, model=model, temperature=0.7, max_tokens=2048)

    # Step 2: Generate natural language explanation for the created code
    explanation_messages = [
        {"role": "system", "content": "You are a helpful AI assistant. Your task is to provide a concise and easy-to-understand natural language explanation of the provided Solidity smart contract code. Focus on what the contract does and its main functionalities. Do not include the code itself in your explanation."},
        {"role": "user", "content": f"Please explain the following Solidity smart contract code in natural language:\n\n{solidity_code}"}
    ]
    explanation_text = _call_groq_api(explanation_messages, model=model, temperature=0.5, max_tokens=512)

    return {
        "solidity_code": solidity_code,
        "explanation": explanation_text
    }


# --- Usage Example ---
if __name__ == "__main__":
    print("--- Groq-powered Smart Contract Chatbot and Generator Test ---")
    try:
        # 1. Contract auditing chatbot example
        user_q1 = "What is the role of the 'require' function in Solidity?"
        response1 = contract_audit_chatbot_groq(user_q1)
        print(f"\n[User]: {user_q1}")
        print(f"[Chatbot Response]: {response1}")

        print("\n" + "-"*50 + "\n")

        # 2. Code analysis request example
        user_q2 = "Are there any potential security vulnerabilities in this Solidity code?"
        contract_example_code = """
pragma solidity ^0.8.0;

contract SimpleAuction {
    address public beneficiary;
    uint public auctionEndTime;
    address public highestBidder;
    uint public highestBid;
    mapping(address => uint) public pendingReturns;
    bool public ended;

    event HighestBidIncreased(address bidder, uint amount);
    event AuctionEnded(address winner, uint amount);

    constructor(uint _biddingTime, address _beneficiary) payable {
        beneficiary = _beneficiary;
        auctionEndTime = block.timestamp + _biddingTime;
    }

    function bid() public payable {
        require(block.timestamp < auctionEndTime, "Auction has already ended");
        require(msg.value > highestBid, "There is already a higher or equal bid");

        if (highestBidder != address(0)) {
            pendingReturns[highestBidder] += highestBid;
        }
        highestBidder = msg.sender;
        highestBid = msg.value;
        emit HighestBidIncreased(msg.sender, msg.value);
    }

    function withdraw() public {
        uint amount = pendingReturns[msg.sender];
        require(amount > 0, "No pending returns");

        pendingReturns[msg.sender] = 0; // Prevent reentrancy
        // Send funds
        (bool sent, ) = msg.sender.call{value: amount}("");
        require(sent, "Failed to send Ether");
    }

    function auctionEnd() public {
        require(block.timestamp >= auctionEndTime, "Auction has not ended yet");
        require(!ended, "auctionEnd has already been called");

        ended = true;
        emit AuctionEnded(highestBidder, highestBid);

        (bool sent, ) = beneficiary.call{value: highestBid}("");
        require(sent, "Failed to send Ether to beneficiary");
    }
}
        """
        response2 = contract_audit_chatbot_groq(user_q2, contract_example_code)
        print(f"[User]: {user_q2}\n[Code]:\n{contract_example_code}")
        print(f"\n[Chatbot Response]: {response2}")

        print("\n" + "="*70 + "\n")

        # 3. Smart contract code generation and natural language explanation example
        user_gen_desc = "Create a smart contract that issues an ERC-20 token. Name it MyToken, symbol MTK, and total supply 1000."
        generated_output = contract_generate_solidity_groq(user_gen_desc, model="llama3-70b-8192") # Example using 70B model
        print(f"[User]: {user_gen_desc}")
        print(f"\n[Generated Solidity Code]:\n{generated_output['solidity_code']}")
        print(f"\n[Code Explanation]:\n{generated_output['explanation']}")

        print("\n" + "="*70 + "\n")

        user_gen_desc_2 = "Create an ERC-721 contract that issues NFTs. Each NFT should have a unique URI, and only the owner can mint them."
        generated_output_2 = contract_generate_solidity_groq(user_gen_desc_2)
        print(f"[User]: {user_gen_desc_2}")
        print(f"\n[Generated Solidity Code]:\n{generated_output_2['solidity_code']}")
        print(f"\n[Code Explanation]:\n{generated_output_2['explanation']}")


    except RuntimeError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected Error: {e}")

