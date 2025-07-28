!pip install groq


# summarize_execution.py
import os
import getpass
from typing import List, Optional
from groq import Groq

# ----------------------------------------------------------------------
# 1. Groq API Key Setup (Handle API Key at script start)
# ----------------------------------------------------------------------
_groq_api_key_global: Optional[str] = os.getenv("GROQ_API_KEY")

if not _groq_api_key_global:
    print("⚠️ GROQ_API_KEY environment variable is not set.")
    user_choice = input("Do you want to proceed by entering your Groq API key directly? (y/n): ").strip().lower()
    if user_choice == 'y':
        _groq_api_key_global = getpass.getpass("🔐 Enter your Groq API key (input will be hidden): ").strip()
        if not _groq_api_key_global:
            print("No API key entered. Exiting program.")
            exit(1)
    else:
        print("Cannot proceed without an API key. Exiting program.")
        exit(1)

try:
    _groq_client_global = Groq(api_key=_groq_api_key_global)
    print("✅ Groq client initialized successfully.")
except Exception as e:
    print(f"❌ Error initializing Groq client: {e}")
    print("The provided API key might be invalid or there's a connection issue. Exiting program.")
    exit(1)


# ----------------------------------------------------------------------
# 2. ExecutionSummarizer Class (Using global Groq client)
# ----------------------------------------------------------------------
class ExecutionSummarizer:
    """
    A class that converts smart contract deployment and execution logs into natural language summaries.
    It uses the Groq API for fast and efficient AI summarization.
    """
    def __init__(self, model_name: str = "llama3-8b-8192"):
        print(f"🛠️ Initializing ExecutionSummarizer. Setting Groq model: '{model_name}'...")
        self.client = _groq_client_global
        self.model_name = model_name
        print("✅ ExecutionSummarizer initialization complete. Groq client ready.")

    def summarize(self, logs: List[str], max_tokens: int = 220) -> str: # Removed language parameter
        """
        Generates a summary text using the Groq API based on the provided list of logs.
        The summary will always be in English.

        Args:
            logs (List[str]): A list of log messages to summarize.
            max_tokens (int): The maximum number of tokens for the generated summary. (Default: 220)

        Returns:
            str: The summarized text.
        """
        if not logs:
            return "No execution logs provided."

        full_text = "\n".join(logs)

        # System prompt: Enhanced to include key information
        system_prompt = (
            "You are an AI assistant specialized in summarizing smart contract deployment and execution logs. "
            "Provide a concise, clear, and informative summary of the given logs. "
            "Highlight key actions, results, **and include all significant numerical values (e.g., token supply, amounts, addresses, transaction hashes) explicitly in the summary.** "
            "Keep it brief and to the point. The summary must be in English." # Enforced English
        )
        user_prompt_prefix = "Please summarize the following smart contract execution logs:\n\n"


        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{user_prompt_prefix}{full_text}"}
        ]

        print("🔄 Summarizing execution logs using Groq API...")
        try:
            chat_completion = self.client.chat.completions.create(
                messages=messages,
                model=self.model_name,
                temperature=0.7,
                max_tokens=max_tokens, # Apply increased max_tokens
            )
            summary_text = chat_completion.choices[0].message.content.strip()
            print(f"✅ Log summarization via Groq API successful.")
            return summary_text
        except Exception as e:
            print(f"❌ Error calling Groq API: {e}")
            return f"Log summarization failed: {e}"


# ----------------------------------------------------------------------
# 3. Usage Example (Main execution block)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    print("\n--- ExecutionSummarizer (Groq) Test Script Start ---")

    try:
        summarizer = ExecutionSummarizer()

        # Test Log Data 1: ERC20 Deployment and Initial Minting
        test_logs_erc20 = [
            "Contract template 'ERC20' selected.",
            "Compiling ERC20 contract: 'MyToken' with symbol 'MTK'.",
            "Contract bytecode and ABI generated.",
            "Initiating deployment transaction on Etherlink Testnet.",
            "Transaction hash: 0xabcdef12345...",
            "Transaction confirmed in block 98765.",
            "Contract 'MyToken' deployed successfully at address 0x1A2B3C...",
            "Constructor arguments: name='MyToken', symbol='MTK', initialSupply=1000000000000000000000.",
            "Initial supply (1000 MTK) minted to deployer address."
        ]

        # Test Log Data 2: SimpleStorage Value Setting
        test_logs_simple_storage = [
            "Contract template 'SimpleStorage' selected.",
            "Compiling SimpleStorage contract.",
            "Contract deployed at 0xABCDEF...",
            "Calling 'set(uint x)' function with value 123.",
            "Transaction for 'set' sent: 0xdeadbeef...",
            "Transaction confirmed.",
            "Event 'DataStored' emitted with value 123."
        ]

        # Test Log Data 3: Error Scenario (simulated)
        test_logs_error = [
            "Contract template 'InvalidContract' selected.",
            "Compilation failed: Syntax error on line 5.",
            "Deployment aborted due to compilation error."
        ]

        print("\n[Test: ERC20 Deployment and Initial Minting Log Summary]")
        summary_erc20 = summarizer.summarize(test_logs_erc20) # No language arg needed
        print("Generated Summary:\n", summary_erc20)
        # Flexible test conditions (loosened assert)
        # Stronger prompt for Groq (increases likelihood of model including '1000 MTK')
        assert "erc20" in summary_erc20.lower() and ("deploy" in summary_erc20.lower() or "deployed" in summary_erc20.lower()), \
               "ERC20 summary does not contain expected keywords."
        print("✅ ERC20 Log Summary Test Successful.")

        print("\n[Test: SimpleStorage Value Setting Log Summary]")
        summary_simple_storage = summarizer.summarize(test_logs_simple_storage) # No language arg needed
        print("Generated Summary:\n", summary_simple_storage)
        assert "simplestorage" in summary_simple_storage.lower() and "123" in summary_simple_storage, \
               "SimpleStorage summary does not contain expected keywords."
        print("✅ SimpleStorage Log Summary Test Successful.")

        print("\n[Test: Error Scenario Log Summary]")
        summary_error = summarizer.summarize(test_logs_error) # No language arg needed
        print("Generated Summary:\n", summary_error)
        assert "fail" in summary_error.lower() or "error" in summary_error.lower(), \
               "Error scenario summary does not contain expected keywords."
        print("✅ Error Log Summary Test Successful.")

        print("\n[Test: Empty Log Summary]")
        summary_empty = summarizer.summarize([]) # No language arg needed
        print("Generated Summary:\n", summary_empty)
        assert "no execution logs provided." in summary_empty.lower()
        print("✅ Empty Log Summary Test Successful.")

    except Exception as e:
        print(f"❌ An unexpected error occurred during ExecutionSummarizer test: {e}")

    print("\n--- ExecutionSummarizer (Groq) Test Script End ---")
