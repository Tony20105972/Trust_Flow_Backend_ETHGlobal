import json
import os
import time
from typing import Dict, Any, Optional, Union

# Import Groq (OpenAI SDK) for LLM interactions
import openai

# Note: blockchain_tools and oneinch_api are no longer directly imported here.
# They are expected to be provided externally (e.g., via FastAPI dependency injection).

# Import userdata for Google Colab environment (for secrets management)
try:
    from google.colab import userdata
except ImportError:
    # If not in Colab, define a mock for userdata to prevent errors
    class UserDataMock:
        def get(self, key: str) -> Optional[str]:
            print(f"⚠️ Could not import 'google.colab.userdata'. This is normal if not in a Colab environment.")
            return os.getenv(key) # Fallback to os.getenv if userdata is not available
    userdata = UserDataMock()


class BlockchainAgent:
    """
    A simplified agent class that automates the smart contract generation, deployment, and audit process.
    It leverages the Groq LLM and external blockchain interaction tools.
    """

    def __init__(self, blockchain_tools_instance: Any = None, oneinch_api_instance: Any = None):
        """
        Initializes the BlockchainAgent instance.
        Sets up the Groq client, and receives blockchain and 1inch API tools via dependency injection.

        Args:
            blockchain_tools_instance (Any): The BlockchainTools instance to be injected externally.
            oneinch_api_instance (Any): The OneInchAPI instance to be injected externally.
        """
        print("🛠️ Initializing BlockchainAgent...")

        # --- Initialize Groq (LLM) Client ---
        groq_api_key = userdata.get('GROQ_API_KEY')
        if not groq_api_key:
            raise ValueError("❌ GROQ_API_KEY is not set. Cannot initialize Groq client.")
        self.groq_client = openai.OpenAI(
            api_key=groq_api_key,
            base_url="https://api.groq.com/openai/v1/",
        )
        print("✅ Groq client initialized.")

        # --- Inject External Tools Instances ---
        self.blockchain_tools = blockchain_tools_instance
        if self.blockchain_tools:
            print("✅ BlockchainTools instance injected.")
        else:
            print("⚠️ BlockchainTools instance not injected. Blockchain operations will be skipped.")

        self.oneinch_api = oneinch_api_instance
        if self.oneinch_api:
            print("✅ OneInchAPI instance injected.")
        else:
            print("⚠️ OneInchAPI instance not injected. 1inch operations will be skipped.")

        print("✅ BlockchainAgent initialization complete.")

    def _call_llm(self, system_prompt: str, user_prompt: str, model: str = 'llama3-8b-8192', temperature: float = 0.7, max_tokens: int = 2048) -> str:
        """Calls the Groq LLM and returns the response."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        print(f"🔄 Calling LLM ({model})...")
        try:
            chat_completion = self.groq_client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            content = chat_completion.choices[0].message.content
            print(f"✅ LLM response received (first 200 chars):\n{content[:200]}...")
            return content
        except openai.APIError as e:
            print(f"❌ Groq API call failed: {e}")
            raise
        except Exception as e:
            print(f"❌ An unexpected error occurred during LLM call: {e}")
            raise

    def _check_audit_for_critical_issues(self, audit_report: str) -> bool:
        """
        Simulates checking an audit report for critical security issues.
        In a real scenario, this would require more sophisticated NLP or rule-based checks.
        """
        print("🔄 Checking audit report for critical issues...")
        # Simulate detection of critical issues via specific keywords
        if isinstance(audit_report, str) and \
           ("critical issue" in audit_report.lower() or \
            "vulnerability" in audit_report.lower() or \
            "reentrancy" in audit_report.lower() or \
            "bug" in audit_report.lower()):
            print("🚨 Critical security issue detected (simulated).")
            return False # Not valid (issues found)
        print("✅ No critical security issues found (simulated).")
        return True # Valid (no issues found)

    def run_contract_workflow(self, contract_description: str) -> Dict[str, Any]:
        """
        Executes the entire workflow from smart contract generation to deployment and auditing.

        Args:
            contract_description (str): Description of the smart contract to be generated.

        Returns:
            Dict[str, Any]: A dictionary containing the final results and status of the workflow.
        """
        workflow_results = {
            "contract_description": contract_description,
            "solidity_code": None,
            "compiled_contract": None,
            "deployed_contract_info": None,
            "audit_report": None,
            "audit_feedback": None,
            "status": "failed",
            "error_message": None
        }

        try:
            # --- 1. LLM: Generate Solidity Code ---
            print("\n--- Step 1: Generating Solidity Code using LLM ---")
            solidity_code_prompt = f"Generate a Solidity smart contract for: {contract_description}\n\nProvide only the Solidity code, no extra text. Include necessary pragmas and standard imports if applicable. Ensure it's a complete, secure, and functional contract."
            workflow_results["solidity_code"] = self._call_llm(
                system_prompt="You are an expert Solidity smart contract developer.",
                user_prompt=solidity_code_prompt,
                temperature=0.7,
                max_tokens=2048
            )
            if not workflow_results["solidity_code"]:
                raise RuntimeError("Failed to generate Solidity code.")

            # --- 2. Tool: Compile Contract ---
            print("\n--- Step 2: Compiling Contract ---")
            if not self.blockchain_tools:
                workflow_results["compiled_contract"] = None # Set to None if skipped
                print("⚠️ Skipping compilation as BlockchainTools instance is not provided.")
            else:
                # Example of a fixed initial supply for a Minimal ERC20 constructor.
                # In a real application, this might be dynamically extracted from the LLM prompt.
                erc20_initial_supply_wei = 1000000 * (10**18) # 1,000,000 tokens (18 decimals)

                workflow_results["compiled_contract"] = self.blockchain_tools.compile_contract(
                    source=workflow_results["solidity_code"],
                    is_file_path=False, # Compile directly from string
                    solc_version="0.8.20"
                )
                if not workflow_results["compiled_contract"]:
                    raise RuntimeError("Failed to compile contract.")

            # --- 3. Tool: Deploy Contract ---
            print("\n--- Step 3: Deploying Contract ---")
            # Check if BlockchainTools is available and if compilation was successful
            if not self.blockchain_tools or not isinstance(workflow_results["compiled_contract"], dict):
                workflow_results["deployed_contract_info"] = None # Set to None if skipped
                print("⚠️ Skipping deployment as BlockchainTools instance is not available or compilation failed.")
            else:
                workflow_results["deployed_contract_info"] = self.blockchain_tools.deploy_contract(
                    abi=workflow_results["compiled_contract"]["abi"],
                    bytecode=workflow_results["compiled_contract"]["bytecode"],
                    constructor_args=[erc20_initial_supply_wei], # ERC20 constructor arguments
                    gas_limit=25_000_000, # Sufficient gas limit for ERC20 deployment
                    gas_price_multiplier=3.0 # Increase priority on testnets
                )
                if not workflow_results["deployed_contract_info"]:
                    raise RuntimeError("Failed to deploy contract.")

            # --- 4. LLM: Generate Audit Report ---
            print("\n--- Step 4: Generating Audit Report using LLM ---")
            # Safely access deployment info, providing defaults if skipped
            if isinstance(workflow_results["deployed_contract_info"], dict):
                deployed_address = workflow_results["deployed_contract_info"].get('contract_address', 'N/A (Deployment Skipped)')
                tx_hash = workflow_results["deployed_contract_info"].get('transaction_hash', 'N/A (Deployment Skipped)')
            else:
                deployed_address = 'N/A (Deployment Skipped)'
                tx_hash = 'N/A (Deployment Skipped)'

            audit_prompt = (
                f"Generate a security audit report for the following Solidity contract code:\n"
                f"```solidity\n{workflow_results['solidity_code']}\n```\n"
                f"Deployed at: {deployed_address}\n"
                f"Transaction Hash: {tx_hash}\n\n"
                f"Focus on potential vulnerabilities, best practices, and overall security posture. "
                f"If no critical issues, state 'No critical issues found.'."
            )
            workflow_results["audit_report"] = self._call_llm(
                system_prompt="You are an expert smart contract security auditor.",
                user_prompt=audit_prompt,
                temperature=0.5,
                max_tokens=1024
            )
            if not workflow_results["audit_report"]:
                raise RuntimeError("Failed to generate audit report.")

            # --- 5. Rule Check: Verify Audit for Critical Issues ---
            print("\n--- Step 5: Checking Audit Report for Critical Issues ---")
            audit_is_valid = self._check_audit_for_critical_issues(workflow_results["audit_report"])

            # --- 6. Conditional Handling: LLM Feedback/Rewrite based on Audit Result ---
            if not audit_is_valid:
                print("\n--- Step 6: LLM Suggesting Feedback/Rewriting based on Audit Result ---")
                feedback_prompt = (
                    f"Issues were found in the following audit report:\n{workflow_results['audit_report']}\n\n"
                    f"Please suggest concrete improvements for the contract, or rewrite the report to emphasize vulnerabilities more clearly."
                )
                workflow_results["audit_feedback"] = self._call_llm(
                    system_prompt="You are an AI assistant tasked with improving security.",
                    user_prompt=feedback_prompt,
                    temperature=0.6,
                    max_tokens=1024
                )
            else:
                workflow_results["audit_feedback"] = "No critical issues were found in the audit report."

            workflow_results["status"] = "completed"

        except (ValueError, RuntimeError, openai.APIError) as e:
            workflow_results["error_message"] = f"Workflow execution failed: {type(e).__name__}: {e}"
            print(workflow_results["error_message"])
        except Exception as e:
            workflow_results["error_message"] = f"An unexpected error occurred during workflow execution: {type(e).__name__}: {e}"
            print(workflow_results["error_message"])
        
        return workflow_results

# --- Main Execution Block ---
if __name__ == "__main__":
    print("\n--- BlockchainRunner Script Start ---")

    # Load environment variables (if python-dotenv is installed, it will load from .env file automatically)
    from dotenv import load_dotenv
    load_dotenv()

    try:
        # When creating the BlockchainAgent instance, external tools are not injected here.
        # This allows the script itself to run without direct dependencies on those files.
        # When using this agent in an external service like FastAPI,
        # you can inject the necessary tool instances.
        agent = BlockchainAgent(
            blockchain_tools_instance=None, # A real BlockchainTools instance can be injected here.
            oneinch_api_instance=None     # A real OneInchAPI instance can be injected here.
        )

        # Define the contract description to be executed
        contract_description = "A simple ERC20 token named MyToken with symbol MYT and a total supply of 1,000,000."
        
        # Execute the workflow
        results = agent.run_contract_workflow(contract_description)

        print("\n--- Final Workflow Results ---")
        print(json.dumps(results, indent=2, ensure_ascii=False))

        if results["status"] == "completed":
            print("\n✅ Workflow completed successfully!")
            
            # Check if deployed_contract_info is a dictionary before accessing
            if isinstance(results.get('deployed_contract_info'), dict):
                contract_address_output = results['deployed_contract_info'].get('contract_address', 'N/A (Address not found)')
            else:
                contract_address_output = "N/A (Deployment Skipped)"

            print(f"Deployed Contract Address: {contract_address_output}")
            print(f"Audit Report Summary (first 200 chars): {results.get('audit_report', 'N/A')[:200]}...")
            print(f"Audit Feedback: {results.get('audit_feedback', 'N/A')}")
        else:
            print(f"\n❌ Workflow execution failed: {results.get('error_message', 'Unknown error')}")

    except ValueError as e:
        print(f"❌ Agent initialization failed: {e}")
        print("   → Please ensure required environment variables (GROQ_API_KEY) are set.")
    except Exception as e:
        print(f"❌ An unexpected error occurred during script execution: {e}")

    print("\n--- BlockchainRunner Script End ---")
