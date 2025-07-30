import os
import getpass
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

# Import the Groq client
from groq import Groq
from groq import APIStatusError, APITimeoutError, APIConnectionError # Specific Groq API exceptions

# --- Global Groq Client Management ---
# Using a global variable for the client, initialized once,
# to avoid re-initializing on every function call for efficiency.
_groq_client: Optional[Groq] = None

def get_groq_client() -> Groq:
    """
    Initializes and returns a singleton Groq client instance.
    Handles API key retrieval from environment or user input.
    """
    global _groq_client

    if _groq_client is None:
        groq_api_key = os.getenv("GROQ_API_KEY")

        if not groq_api_key:
            print("⚠️ GROQ_API_KEY environment variable is not set.")
            user_choice = input("Do you want to proceed by entering the API key directly? (y/n): ").strip().lower()
            if user_choice == 'y':
                groq_api_key = getpass.getpass("🔐 Enter your Groq API Key (input will be hidden): ").strip()
                if not groq_api_key:
                    raise ValueError("Groq API Key cannot be empty.")
            else:
                raise RuntimeError("Cannot proceed without an API key. Please set GROQ_API_KEY or provide it directly.")

        try:
            _groq_client = Groq(api_key=groq_api_key)
            print("✅ Groq client initialized successfully.")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Groq client: {e}")
            
    return _groq_client


def _call_groq_api(messages: List[Dict[str, str]], model: str = "llama3-8b-8192", temperature: float = 0.5, max_tokens: int = 1024) -> str:
    """
    Internal helper function to call the Groq API.
    """
    client = get_groq_client() # Get the initialized client

    try:
        chat_completion = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return chat_completion.choices[0].message.content
    except APIStatusError as e:
        print(f"Groq API Error Status: {e.status_code}")
        print(f"Groq API Error Message: {e.response}")
        raise RuntimeError(f"Groq API Error: {e.status_code} - {e.response}")
    except APITimeoutError as e:
        raise RuntimeError(f"Groq API Timeout Error: {e}")
    except APIConnectionError as e:
        raise RuntimeError(f"Groq API Connection Error: {e}")
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred during Groq API call: {e}")


def contract_audit_chatbot_groq(user_prompt: str, contract_code: Optional[str] = None, model: str = "llama3-8b-8192") -> str:
    """
    A chatbot using Groq API to answer questions or analyze Solidity smart contracts.

    Args:
        user_prompt (str): User's question or request for explanation.
        contract_code (Optional[str]): Solidity code (optional).
        model (str): Groq model to use (default: llama3-8b-8192).

    Returns:
        str: Chatbot's response.
    """
    full_prompt = user_prompt
    if contract_code:
        full_prompt += f"\n\nPlease also analyze this Solidity code:\n```solidity\n{contract_code}\n```"

    messages = [
        {"role": "system", "content": "You are a Web3 AI auditor who explains, audits, and simplifies smart contracts. Provide clear, concise, and accurate information, highlighting any potential security concerns or best practices."},
        {"role": "user", "content": full_prompt}
    ]

    return _call_groq_api(messages, model=model, temperature=0.5)


def contract_generate_solidity_groq(user_description: str, model: str = "llama3-8b-8192") -> Dict[str, str]:
    """
    Generates Solidity smart contract code from a natural language description using Groq API,
    and returns a natural language explanation of the generated code.

    Args:
        user_description (str): Natural language description of the smart contract to be generated.
        model (str): Groq model to use (default: llama3-8b-8192).

    Returns:
        Dict[str, str]: A dictionary containing 'solidity_code' and 'explanation'.
    """
    # Step 1: Generate Solidity code
    code_generation_messages = [
        {"role": "system", "content": "You are an expert Solidity smart contract developer. Your task is to generate clean, secure, and functional Solidity code based on the user's natural language description. Provide only the Solidity code, without any additional explanations or text. Ensure the code is production-ready and follows best practices. Add clear and concise comments to the code for readability and maintainability. Prioritize security in your code generation. Wrap the code in ```solidity``` markdown blocks."},
        {"role": "user", "content": user_description}
    ]
    solidity_code_raw = _call_groq_api(code_generation_messages, model=model, temperature=0.7, max_tokens=2048)
    
    # Extract only the code from the markdown block if present
    # This makes the output cleaner for subsequent use (e.g., compilation)
    if "```solidity" in solidity_code_raw and "```" in solidity_code_raw:
        solidity_code = solidity_code_raw.split("```solidity")[1].split("```")[0].strip()
    else:
        solidity_code = solidity_code_raw.strip() # Fallback if no markdown block


    # Step 2: Generate natural language explanation for the created code
    explanation_messages = [
        {"role": "system", "content": "You are a helpful AI assistant. Your task is to provide a concise and easy-to-understand natural language explanation of the provided Solidity smart contract code. Focus on what the contract does and its main functionalities, potential uses, and any important considerations. Do not include the code itself in your explanation."},
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
        # Client will be initialized on the first API call via get_groq_client()

        # 1. Contract auditing chatbot example
        user_q1 = "What is the role of the 'require' function in Solidity?"
        response1 = contract_audit_chatbot_groq(user_q1)
        print(f"\n[User]: {user_q1}")
        print(f"[Chatbot Response]: {response1}")

        print("\n" + "-"*50 + "\n")

        # 2. Code analysis request example
        user_q2 = "Are there any potential security vulnerabilities in this Solidity code? Please analyze it thoroughly."
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

        pendingReturns[msg.sender] = 0; // Prevent reentrancy - This is good!
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
        response2 = contract_audit_chatbot_groq(user_q2, contract_example_code, model="llama3-70b-8192") # Using 70B model for audit
        print(f"[User]: {user_q2}\n[Code]:\n{contract_example_code}")
        print(f"\n[Chatbot Response]: {response2}")

        print("\n" + "="*70 + "\n")

        # 3. Smart contract code generation and natural language explanation example
        user_gen_desc = "Create a simple ERC-20 token contract named 'MyStableCoin' with symbol 'MSC' and a fixed total supply of 1,000,000 tokens. The contract owner should be able to pause and unpause transfers."
        generated_output = contract_generate_solidity_groq(user_gen_desc, model="llama3-70b-8192") # Example using 70B model
        print(f"[User]: {user_gen_desc}")
        print(f"\n[Generated Solidity Code]:\n{generated_output['solidity_code']}")
        print(f"\n[Code Explanation]:\n{generated_output['explanation']}")

        print("\n" + "="*70 + "\n")

        user_gen_desc_2 = "Create an ERC-721 contract that issues NFTs. Each NFT should have a unique URI, and only the owner can mint them. Add a function to set a base URI and another function to burn NFTs."
        generated_output_2 = contract_generate_solidity_groq(user_gen_desc_2, model="llama3-70b-8192")
        print(f"[User]: {user_gen_desc_2}")
        print(f"\n[Generated Solidity Code]:\n{generated_output_2['solidity_code']}")
        print(f"\n[Code Explanation]:\n{generated_output_2['explanation']}")

    except RuntimeError as e:
        print(f"Error during execution: {e}")
    except ValueError as e: # Catch for empty API key
        print(f"Configuration Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred in the main execution block: {type(e).__name__}: {e}")

    print("\n--- Groq-powered Smart Contract Chatbot and Generator Test End ---")
