import os
import json
import time
from typing import Dict, Any, Optional, Union
from web3 import Web3
from web3.middleware.proof_of_authority import ExtraDataToPOAMiddleware
from solcx import compile_source, install_solc, set_solc_version, get_solc_version
from solcx.exceptions import SolcError
from web3.exceptions import TransactionNotFound, TimeExhausted, ContractLogicError

# Import userdata for Google Colab environment
try:
    from google.colab import userdata
except ImportError:
    # If not in Colab, define a mock for userdata to prevent errors
    class UserDataMock:
        def get(self, key: str) -> Optional[str]:
            # print(f"⚠️ 'google.colab.userdata' could not be imported. User data for '{key}' is not available.")
            return None
    userdata = UserDataMock()


class BlockchainTools:
    """
    Utility class for interacting with Ethereum blockchains.
    Provides functionalities for smart contract compilation, deployment,
    function calls, and transaction sending.
    Supports both legacy and EIP-1559 gas pricing.
    """

    def __init__(self, rpc_url: Optional[str] = None, private_key: Optional[str] = None):
        """
        Initializes the BlockchainTools instance.
        RPC URL and private key are set from environment variables or directly passed arguments.
        Private key is searched in Colab secrets, then OS environment variables.

        Args:
            rpc_url (Optional[str]): URL of the Ethereum RPC node. Defaults to ETH_RPC_URL env var or 'https://node.ghostnet.etherlink.com'.
            private_key (Optional[str]): Private key to be used for signing transactions.

        Raises:
            ValueError: If PRIVATE_KEY is not set.
            ConnectionError: If the Web3 instance fails to connect to the RPC.
        """
        self.rpc_url: str = rpc_url or os.getenv("ETH_RPC_URL", "https://node.ghostnet.etherlink.com")
        self.private_key: Optional[str] = private_key or userdata.get('PRIVATE_KEY') or os.getenv("PRIVATE_KEY")

        if not self.private_key:
            raise ValueError(
                "❌ PRIVATE_KEY environment variable is not set. "
                "Please add your private key to Colab secrets or system environment variables."
            )

        self.w3: Optional[Web3] = None
        self.account = None
        self._initialize_web3()

    def _initialize_web3(self):
        """Initializes the Web3 instance and sets up network connection and account."""
        print(f"🔄 Attempting to connect to RPC URL: {self.rpc_url}...")
        try:
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
            # Inject middleware for PoA networks (e.g., Etherlink)
            self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

            if not self.w3.is_connected():
                raise ConnectionError(f"Failed to connect to RPC: {self.rpc_url}")

            self.account = self.w3.eth.account.from_key(self.private_key)
            print(f"✅ Network connection successful: {self.rpc_url}")
            print(f"    → Using account: {self.account.address}")
        except ConnectionError as e:
            print(f"❌ Connection error: {e}")
            self.w3 = None # Ensure w3 is None if connection fails
            raise
        except Exception as e:
            print(f"❌ Unexpected error during Web3 initialization: {e}")
            self.w3 = None
            raise

    def compile_contract(self, source: str, is_file_path: bool = False, solc_version: str = "0.8.20") -> Dict[str, Any]:
        """
        Compiles Solidity source code (file path or string) and returns ABI and bytecode.

        Args:
            source (str): Solidity file path or raw Solidity source code string.
            is_file_path (bool): If True, 'source' is treated as a file path; otherwise, as a raw string.
            solc_version (str): solc compiler version to use (default: "0.8.20").

        Returns:
            Dict[str, Any]: A dictionary containing the ABI and bytecode of the compiled contract.
                            {"abi": [...], "bytecode": "0x..."}

        Raises:
            FileNotFoundError: If is_file_path is True and the file is not found.
            SolcError: If an error occurs during Solidity compilation.
            Exception: For other unexpected errors.
        """
        print(f"🔄 Compiling Solidity code with solc {solc_version}...")
        try:
            # Check if the specified solc version is installed
            current_installed_solc = get_solc_version()
            if str(current_installed_solc) != solc_version:
                print(f"   → solc version {solc_version} not found or mismatch. Installing...")
                install_solc(solc_version)
                set_solc_version(solc_version)
                print(f"   → solc version set to {get_solc_version()}")
            else:
                print(f"   → Using already installed solc version {solc_version}")

            source_code = ""
            if is_file_path:
                if not os.path.exists(source):
                    raise FileNotFoundError(f"File '{source}' not found.")
                with open(source, 'r', encoding='utf-8') as f:
                    source_code = f.read()
            else:
                source_code = source # Use the provided string directly

            compiled_sol = compile_source(source_code, output_values=["abi", "bin"])

            if not compiled_sol:
                raise SolcError("No valid contract found in compilation result. Check your source code.")

            # Get the interface of the first contract (assuming a single contract)
            contract_name = list(compiled_sol.keys())[0]
            contract_interface = compiled_sol[contract_name]

            print(f"✅ Contract '{contract_name.split(':')[-1]}' compiled successfully.")
            return {"abi": contract_interface["abi"], "bytecode": "0x" + contract_interface["bin"]}
        except FileNotFoundError as e:
            print(f"❌ Compilation error: File not found - {e}")
            raise
        except SolcError as e:
            print(f"❌ Solidity compilation error: {e}")
            raise
        except Exception as e:
            print(f"❌ Unexpected error during contract compilation: {e}")
            raise

    def deploy_contract(self, abi: list, bytecode: str, constructor_args: Optional[list] = None,
                        gas_limit: int = 3_000_000, gas_price_multiplier: float = 1.0,
                        use_eip1559: bool = False, max_priority_fee_gwei: Optional[float] = None,
                        max_fee_gwei: Optional[float] = None) -> Dict[str, str]:
        """
        Deploys a compiled Solidity contract to the Ethereum network.
        Can use either legacy gas pricing (gasPrice) or EIP-1559 (maxFeePerGas, maxPriorityFeePerGas).

        Args:
            abi (list): The ABI (Application Binary Interface) of the contract.
            bytecode (str): The bytecode of the contract (with '0x' prefix).
            constructor_args (Optional[list]): List of arguments to pass to the contract constructor (default: None).
            gas_limit (int): Maximum gas limit for the transaction (default: 3,000,000 wei).
            gas_price_multiplier (float): Multiplier to apply to the gas price for legacy transactions (default: 1.0).
            use_eip1559 (bool): If True, uses EIP-1559 gas pricing. Requires max_priority_fee_gwei and max_fee_gwei.
            max_priority_fee_gwei (Optional[float]): Max priority fee for EIP-1559 (in Gwei).
            max_fee_gwei (Optional[float]): Max fee per gas for EIP-1559 (in Gwei).

        Returns:
            Dict[str, str]: A dictionary containing the deployed contract address and transaction hash.
                            {"contract_address": "0x...", "transaction_hash": "0x..."}

        Raises:
            TransactionNotFound: If transaction receipt is not found or times out.
            TimeExhausted: If waiting for transaction receipt exceeds timeout.
            RuntimeError: If the contract deployment transaction fails.
            AttributeError: If 'raw_transaction' attribute is not found.
            ValueError: If EIP-1559 is enabled but required fees are missing.
            ConnectionError: If the Web3 instance is not initialized.
            Exception: For other unexpected errors.
        """
        if self.w3 is None:
            raise ConnectionError("Web3 instance not initialized. Cannot deploy contract.")

        print("🚀 Starting contract deployment...")
        start_time = time.time()
        try:
            Contract = self.w3.eth.contract(abi=abi, bytecode=bytecode)
            nonce = self.w3.eth.get_transaction_count(self.account.address)

            tx_params = {
                "from": self.account.address,
                "nonce": nonce,
                "gas": gas_limit,
            }

            if use_eip1559:
                if max_priority_fee_gwei is None or max_fee_gwei is None:
                    raise ValueError("EIP-1559 requires 'max_priority_fee_gwei' and 'max_fee_gwei'.")
                
                # Convert Gwei to Wei
                tx_params["maxPriorityFeePerGas"] = self.w3.to_wei(max_priority_fee_gwei, 'gwei')
                tx_params["maxFeePerGas"] = self.w3.to_wei(max_fee_gwei, 'gwei')
                print(f"    → Using EIP-1559 gas: Max priority fee {max_priority_fee_gwei} Gwei, Max fee {max_fee_gwei} Gwei")
            else:
                current_gas_price = self.w3.eth.gas_price
                effective_gas_price = int(current_gas_price * gas_price_multiplier)
                tx_params["gasPrice"] = effective_gas_price
                print(f"    → Current gas price: {self.w3.from_wei(current_gas_price, 'gwei')} Gwei")
                print(f"    → Set gas price ({gas_price_multiplier}x): {self.w3.from_wei(effective_gas_price, 'gwei')} Gwei")

            # Calculate estimated transaction cost (gas limit * gas price)
            estimated_cost_wei = gas_limit * tx_params.get("gasPrice", tx_params.get("maxFeePerGas", 0))
            current_balance_wei = self.w3.eth.get_balance(self.account.address)

            print(f"    → Estimated transaction cost: {self.w3.from_wei(estimated_cost_wei, 'ether'):.6f} ETH")
            print(f"    → Current account balance: {self.w3.from_wei(current_balance_wei, 'ether'):.6f} ETH")

            if current_balance_wei < estimated_cost_wei:
                raise RuntimeError(
                    f"❌ Insufficient balance: Account balance ({self.w3.from_wei(current_balance_wei, 'ether'):.6f} ETH) is "
                    f"less than estimated transaction cost ({self.w3.from_wei(estimated_cost_wei, 'ether'):.6f} ETH). "
                    "Please top up your account from a faucet or reduce gas_limit."
                )

            if constructor_args:
                tx_builder = Contract.constructor(*constructor_args)
            else:
                tx_builder = Contract.constructor()

            tx = tx_builder.build_transaction(tx_params)

            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            raw_tx = getattr(signed_tx, "raw_transaction", None) or getattr(signed_tx, "rawTransaction", None)

            if raw_tx is None:
                raise AttributeError("❌ 'raw_transaction' attribute not found in web3 SignedTransaction object.")

            tx_hash = self.w3.eth.send_raw_transaction(raw_tx)
            print(f"    → Transaction sent. Hash: {tx_hash.hex()}")

            # Dynamically set poll_latency based on RPC URL.
            poll_latency = 0.1 if "127.0.0.1" in self.rpc_url or "localhost" in self.rpc_url else 5
            print(f"    → Waiting for receipt (polling every {poll_latency} seconds)...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300, poll_latency=poll_latency)

            if receipt.status != 1:
                raise RuntimeError(f"❌ Contract deployment failed.\n    → Receipt: {json.dumps(dict(receipt), indent=2, default=str)}")

            end_time = time.time()
            print(f"✅ Contract successfully deployed to address: {receipt.contractAddress}")
            print(f"⏱️ Deployment time: {end_time - start_time:.2f} seconds")
            return {"contract_address": receipt.contractAddress, "transaction_hash": tx_hash.hex()}

        except (TransactionNotFound, TimeExhausted) as e:
            print(f"❌ Transaction receipt waiting error: {e}")
            raise
        except Exception as e:
            print(f"❌ Error during contract deployment: {type(e).__name__}: {e}")
            raise

    def call_function(self, contract_address: str, abi: list, function_name: str, args: Optional[list] = None) -> Any:
        """
        Calls a read-only (view/pure) function of a deployed contract.

        Args:
            contract_address (str): The address of the contract.
            abi (list): The ABI of the contract.
            function_name (str): The name of the function to call.
            args (Optional[list]): List of arguments to pass to the function (default: None).

        Returns:
            Any: The result of the function call.

        Raises:
            ContractLogicError: If an error occurs in the contract's internal logic.
            ConnectionError: If the Web3 instance is not initialized.
            Exception: For other unexpected errors.
        """
        if self.w3 is None:
            raise ConnectionError("Web3 instance not initialized. Cannot call function.")

        print(f"🔄 Calling read-only function '{function_name}' on contract '{contract_address}'...")
        try:
            contract = self.w3.eth.contract(address=contract_address, abi=abi)
            if args:
                result = contract.functions[function_name](*args).call()
            else:
                result = contract.functions[function_name]().call()
            print(f"✅ Function '{function_name}' call successful. Result: {result}")
            return result
        except ContractLogicError as e:
            print(f"❌ Contract logic error occurred: {e}")
            raise
        except Exception as e:
            print(f"❌ Error calling function '{function_name}': {type(e).__name__}: {e}")
            raise

    def send_transaction(self, contract_address: str, abi: list, function_name: str, args: Optional[list] = None,
                         value: int = 0, gas_limit: int = 3_000_000, gas_price_multiplier: float = 1.0,
                         use_eip1559: bool = False, max_priority_fee_gwei: Optional[float] = None,
                         max_fee_gwei: Optional[float] = None) -> str:
        """
        Calls a state-changing function of a deployed contract and sends a transaction.
        Can use either legacy gas pricing (gasPrice) or EIP-1559 (maxFeePerGas, maxPriorityFeePerGas).

        Args:
            contract_address (str): The address of the contract.
            abi (list): The ABI of the contract.
            function_name (str): The name of the function to call.
            args (Optional[list]): List of arguments to pass to the function (default: None).
            value (int): Amount of Ether (in wei) to send with the function call.
            gas_limit (int): Maximum gas limit for the transaction (default: 3,000,000 wei).
            gas_price_multiplier (float): Multiplier to apply to the gas price for legacy transactions (default: 1.0).
            use_eip1559 (bool): If True, uses EIP-1559 gas pricing. Requires max_priority_fee_gwei and max_fee_gwei.
            max_priority_fee_gwei (Optional[float]): Max priority fee for EIP-1559 (in Gwei).
            max_fee_gwei (Optional[float]): Max fee per gas for EIP-1559 (in Gwei).

        Returns:
            str: The hash of the sent transaction (with '0x' prefix).

        Raises:
            TransactionNotFound: If transaction receipt is not found or times out.
            TimeExhausted: If waiting for transaction receipt exceeds timeout.
            ContractLogicError: If an error occurs in the contract's internal logic.
            RuntimeError: If the transaction sending fails.
            AttributeError: If 'raw_transaction' attribute is not found.
            ValueError: If EIP-1559 is enabled but required fees are missing.
            ConnectionError: If the Web3 instance is not initialized.
            Exception: For other unexpected errors.
        """
        if self.w3 is None:
            raise ConnectionError("Web3 instance not initialized. Cannot send transaction.")

        print(f"🔄 Sending transaction to state-changing function '{function_name}' on contract '{contract_address}'...")
        start_time = time.time()
        try:
            contract = self.w3.eth.contract(address=contract_address, abi=abi)
            nonce = self.w3.eth.get_transaction_count(self.account.address)

            tx_params = {
                "from": self.account.address,
                "nonce": nonce,
                "value": value,
                "gas": gas_limit,
            }

            if use_eip1559:
                if max_priority_fee_gwei is None or max_fee_gwei is None:
                    raise ValueError("EIP-1559 requires 'max_priority_fee_gwei' and 'max_fee_gwei'.")
                
                # Convert Gwei to Wei
                tx_params["maxPriorityFeePerGas"] = self.w3.to_wei(max_priority_fee_gwei, 'gwei')
                tx_params["maxFeePerGas"] = self.w3.to_wei(max_fee_gwei, 'gwei')
                print(f"    → Using EIP-1559 gas: Max priority fee {max_priority_fee_gwei} Gwei, Max fee {max_fee_gwei} Gwei")
            else:
                current_gas_price = self.w3.eth.gas_price
                effective_gas_price = int(current_gas_price * gas_price_multiplier)
                tx_params["gasPrice"] = effective_gas_price
                print(f"    → Current gas price: {self.w3.from_wei(current_gas_price, 'gwei')} Gwei")
                print(f"    → Set gas price ({gas_price_multiplier}x): {self.w3.from_wei(effective_gas_price, 'gwei')} Gwei")

            # Calculate estimated transaction cost (gas limit * gas price + value)
            estimated_cost_wei = gas_limit * tx_params.get("gasPrice", tx_params.get("maxFeePerGas", 0)) + value
            current_balance_wei = self.w3.eth.get_balance(self.account.address)

            print(f"    → Estimated transaction cost: {self.w3.from_wei(estimated_cost_wei, 'ether'):.6f} ETH")
            print(f"    → Current account balance: {self.w3.from_wei(current_balance_wei, 'ether'):.6f} ETH")

            if current_balance_wei < estimated_cost_wei:
                raise RuntimeError(
                    f"❌ Insufficient balance: Account balance ({self.w3.from_wei(current_balance_wei, 'ether'):.6f} ETH) is "
                    f"less than estimated transaction cost ({self.w3.from_wei(estimated_cost_wei, 'ether'):.6f} ETH). "
                    "Please top up your account from a faucet or reduce gas_limit."
                )

            if args:
                tx_builder = contract.functions[function_name](*args)
            else:
                tx_builder = contract.functions[function_name]()

            tx = tx_builder.build_transaction(tx_params)

            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            raw_tx = getattr(signed_tx, "raw_transaction", None) or getattr(signed_tx, "rawTransaction", None)

            if raw_tx is None:
                raise AttributeError("❌ 'raw_transaction' attribute not found in web3 SignedTransaction object.")

            tx_hash = self.w3.eth.send_raw_transaction(raw_tx)
            print(f"    → Transaction sent. Hash: {tx_hash.hex()}")

            poll_latency = 0.1 if "127.0.0.1" in self.rpc_url or "localhost" in self.rpc_url else 5
            print(f"    → Waiting for receipt (polling every {poll_latency} seconds)...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300, poll_latency=poll_latency)

            if receipt.status != 1:
                raise RuntimeError(f"❌ Transaction '{function_name}' failed.\n    → Receipt: {json.dumps(dict(receipt), indent=2, default=str)}")

            end_time = time.time()
            print(f"✅ Transaction '{function_name}' successful. Block number: {receipt.blockNumber}")
            print(f"⏱️ Transaction time: {end_time - start_time:.2f} seconds")
            return tx_hash.hex()

        except (TransactionNotFound, TimeExhausted) as e:
            print(f"❌ Transaction receipt waiting error: {e}")
            raise
        except ContractLogicError as e:
            print(f"❌ Contract logic error occurred: {e}")
            raise
        except Exception as e:
            print(f"❌ Unexpected error sending transaction to function '{function_name}': {type(e).__name__}: {e}")
            raise


def main():
    print("\n--- BlockchainTools Test Script Start ---")

    # --- 1. Write example Solidity Code ---
    simple_storage_code = """
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
    """

    # --- Minimal ERC20 Token Code ---
    erc20_token_code = """
pragma solidity ^0.8.0;

contract SimpleERC20 {
    string public name = "Test Token";
    string public symbol = "TTK";
    uint8 public decimals = 18;
    uint256 public totalSupply;

    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);

    constructor(uint256 initialSupply) {
        totalSupply = initialSupply;
        balanceOf[msg.sender] = initialSupply;
        emit Transfer(address(0), msg.sender, initialSupply);
    }

    function transfer(address to, uint256 value) public returns (bool) {
        require(balanceOf[msg.sender] >= value, "SimpleERC20: Not enough balance");
        balanceOf[msg.sender] -= value;
        balanceOf[to] += value;
        emit Transfer(msg.sender, to, value);
        return true;
    }

    function approve(address spender, uint256 value) public returns (bool) {
        allowance[msg.sender][spender] = value;
        emit Approval(msg.sender, spender, value);
        return true;
    }

    function transferFrom(address from, address to, uint256 value) public returns (bool) {
        require(balanceOf[from] >= value, "SimpleERC20: Not enough balance from");
        require(allowance[from][msg.sender] >= value, "SimpleERC20: Not approved or allowance too low");
        
        balanceOf[from] -= value;
        balanceOf[to] += value;
        allowance[from][msg.sender] -= value;
        emit Transfer(from, to, value);
        return true;
    }
}
    """

    # Define temporary file paths
    simple_storage_file_path = "SimpleStorage.sol"
    erc20_file_path = "MyERC20Token.sol" # Filename remains the same for consistency

    # --- 2. Anvil (Local Node) Test ---
    print("\n--- Anvil (Local Node) Deployment and Interaction Test ---")
    # Paste the RPC URL and private key from your Anvil output here.
    ANVIL_RPC_URL = "http://127.0.0.1:8545"
    ANVIL_PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80" # Example: First private key from Anvil

    # Initialize Anvil test variables
    anvil_tools = None
    compiled_simple = None
    deployed_simple = None
    compiled_erc20 = None
    deployed_erc20 = None

    try:
        # Create SimpleStorage file
        with open(simple_storage_file_path, "w", encoding='utf-8') as f:
            f.write(simple_storage_code)
        print(f"📝 Temporary contract file created: {simple_storage_file_path}")

        # Create ERC20 file
        with open(erc20_file_path, "w", encoding='utf-8') as f:
            f.write(erc20_token_code)
        print(f"📝 Temporary ERC20 contract file created: {erc20_file_path}")

        anvil_tools = BlockchainTools(rpc_url=ANVIL_RPC_URL, private_key=ANVIL_PRIVATE_KEY)

        # SimpleStorage Deployment and Interaction
        print("\n--- Anvil: SimpleStorage Contract Deployment and Interaction ---")
        compiled_simple = anvil_tools.compile_contract(simple_storage_file_path, is_file_path=True, solc_version="0.8.20")
        deployed_simple = anvil_tools.deploy_contract(compiled_simple["abi"], compiled_simple["bytecode"], gas_price_multiplier=1.0)

        current_data = anvil_tools.call_function(deployed_simple['contract_address'], compiled_simple['abi'], "get")
        print(f"    SimpleStorage initial storedData value: {current_data}")
        anvil_tools.send_transaction(deployed_simple['contract_address'], compiled_simple['abi'], "set", [9876], gas_price_multiplier=1.0)
        updated_data = anvil_tools.call_function(deployed_simple['contract_address'], compiled_simple['abi'], "get")
        print(f"    SimpleStorage updated storedData value: {updated_data}")

        # ERC20 Contract Deployment and Interaction
        print("\n--- Anvil: ERC20 Contract Deployment and Interaction ---")
        erc20_constructor_args = [1000 * (10**18)] # Initial Supply (1000 tokens, 18 decimals)
        compiled_erc20 = anvil_tools.compile_contract(erc20_file_path, is_file_path=True, solc_version="0.8.20")
        deployed_erc20 = anvil_tools.deploy_contract(
            compiled_erc20["abi"],
            compiled_erc20["bytecode"], # Anvil section already uses the correct variable
            constructor_args=erc20_constructor_args,
            gas_limit=25_000_000,
            gas_price_multiplier=1.0
        )

        owner_address = anvil_tools.account.address
        total_supply = anvil_tools.call_function(deployed_erc20['contract_address'], compiled_erc20['abi'], "totalSupply")
        owner_balance = anvil_tools.call_function(deployed_erc20['contract_address'], compiled_erc20['abi'], "balanceOf", [owner_address])
        print(f"    ERC20 Total Supply: {anvil_tools.w3.from_wei(total_supply, 'ether')} TTK")
        print(f"    Deployer ({owner_address}) balance: {anvil_tools.w3.from_wei(owner_balance, 'ether')} TTK")

        # Test ERC20 transfer (example)
        recipient_address = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266" # Anvil's second account
        transfer_amount = 100 * (10**18) # 100 TTK
        print(f"\n--- Anvil: ERC20 Token Transfer Test ---")
        anvil_tools.send_transaction(deployed_erc20['contract_address'], compiled_erc20['abi'], "transfer", [recipient_address, transfer_amount], gas_price_multiplier=1.0)
        recipient_balance = anvil_tools.call_function(deployed_erc20['contract_address'], compiled_erc20['abi'], "balanceOf", [recipient_address])
        print(f"    Recipient ({recipient_address}) balance: {anvil_tools.w3.from_wei(recipient_balance, 'ether')} TTK")


    except ConnectionError as e:
        print(f"❌ Anvil test skipped (connection error): {e}")
        print("    → Ensure Anvil (local node) is running at http://127.0.0.1:8545.")
    except Exception as e:
        print(f"❌ Error during Anvil test: {type(e).__name__}: {e}")
        try:
            # Attempt to check balance only if anvil_tools exists and is valid
            if anvil_tools and anvil_tools.w3 and anvil_tools.account:
                balance_wei = anvil_tools.w3.eth.get_balance(anvil_tools.account.address)
                balance_eth = anvil_tools.w3.from_wei(balance_wei, 'ether')
                print(f"    → Anvil account balance: {balance_eth} ETH ({balance_wei} wei)")
        except Exception as balance_err:
            print(f"    → Error checking Anvil account balance: {balance_err}")
    finally:
        # Delete temporary files after testing
        if os.path.exists(simple_storage_file_path):
            os.remove(simple_storage_file_path)
            print(f"\n🗑️ Temporary file deleted: {simple_storage_file_path}")
        if os.path.exists(erc20_file_path):
            os.remove(erc20_file_path)
            print(f"🗑️ Temporary file deleted: {erc20_file_path}")


    # --- 3. Ghostnet (Testnet) Test ---
    print("\n--- Ghostnet (Testnet) Deployment and Interaction Test ---")

    # Initialize Ghostnet test variables
    ghostnet_tools = None
    compiled_simple_ghost = None
    deployed_simple_ghost = None
    compiled_erc20_ghost = None
    deployed_erc20_ghost = None

    try:
        # For Ghostnet testing, 'PRIVATE_KEY' environment variable or Colab userdata must be set.
        # RPC URL defaults to 'https://node.ghostnet.etherlink.com'
        ghostnet_tools = BlockchainTools()

        # Create temporary files for Ghostnet compilation (if they were deleted by Anvil test's finally block)
        with open(simple_storage_file_path, "w", encoding='utf-8') as f:
            f.write(simple_storage_code)
        print(f"📝 Temporary contract file created (for Ghostnet): {simple_storage_file_path}")

        with open(erc20_file_path, "w", encoding='utf-8') as f:
            f.write(erc20_token_code)
        print(f"📝 Temporary ERC20 contract file created (for Ghostnet): {erc20_file_path}")


        print("\n--- Ghostnet: SimpleStorage Contract Deployment ---")
        # For Ghostnet, set gas price multiplier to 3.0 for higher priority
        compiled_simple_ghost = ghostnet_tools.compile_contract(simple_storage_file_path, is_file_path=True, solc_version="0.8.20")
        
        # Example of EIP-1559 deployment on Ghostnet (if supported by RPC)
        # You would need to estimate max_priority_fee_gwei and max_fee_gwei based on current network conditions
        # For a simple demo, sticking to gas_price_multiplier might be easier if EIP-1559 estimation is complex.
        deployed_simple_ghost = ghostnet_tools.deploy_contract(
            compiled_simple_ghost["abi"], 
            compiled_simple_ghost["bytecode"], 
            gas_price_multiplier=3.0, # Fallback for non-EIP-1559 or simpler demo
            # use_eip1559=True,
            # max_priority_fee_gwei=1.5, # Example value, adjust based on network
            # max_fee_gwei=30.0 # Example value, adjust based on network
        )
        print(f"🎉 Ghostnet SimpleStorage deployment address: {deployed_simple_ghost['contract_address']}")
        print(f"    Transaction hash: {deployed_simple_ghost['transaction_hash']}")

        print("\n--- Ghostnet: ERC20 Contract Deployment ---")
        erc20_constructor_args_ghost = [500 * (10**18)] # Initial Supply
        compiled_erc20_ghost = ghostnet_tools.compile_contract(erc20_file_path, is_file_path=True, solc_version="0.8.20")
        deployed_erc20_ghost = ghostnet_tools.deploy_contract(
            compiled_erc20_ghost["abi"], 
            compiled_erc20_ghost["bytecode"], # ✅ THIS WAS THE FIX: compiled_erc20 -> compiled_erc20_ghost
            constructor_args=erc20_constructor_args_ghost, 
            gas_limit=25_000_000, 
            gas_price_multiplier=3.0 
            # use_eip1559=True,
            # max_priority_fee_gwei=1.5, # Example value, adjust based on network
            # max_fee_gwei=30.0 # Example value, adjust based on network
        )
        print(f"🎉 Ghostnet ERC20 deployment address: {deployed_erc20_ghost['contract_address']}")
        print(f"    Transaction hash: {deployed_erc20_ghost['transaction_hash']}")


    except ValueError as e:
        print(f"❌ Ghostnet test skipped (PRIVATE_KEY error): {e}")
        print("    → You must set the PRIVATE_KEY environment variable to run Ghostnet tests.")
    except ConnectionError as e:
        print(f"❌ Ghostnet test skipped (connection error): {e}")
        print("    → Ensure the Ghostnet RPC URL is correct and accessible.")
    except Exception as e:
        print(f"❌ Error during Ghostnet test: {type(e).__name__}: {e}")
        try:
            # Attempt to check balance only if ghostnet_tools exists and is valid
            if ghostnet_tools and ghostnet_tools.w3 and ghostnet_tools.account:
                balance_wei = ghostnet_tools.w3.eth.get_balance(ghostnet_tools.account.address)
                balance_eth = ghostnet_tools.w3.from_wei(balance_wei, 'ether')
                print(f"    → Ghostnet account balance: {balance_eth} ETH ({balance_wei} wei)")
        except Exception as balance_err:
            print(f"    → Error checking Ghostnet account balance: {balance_err}")
    finally:
        # Ensure temporary files are cleaned up (even if Ghostnet test fails)
        if os.path.exists(simple_storage_file_path):
            os.remove(simple_storage_file_path)
            print(f"\n🗑️ Temporary file deleted: {simple_storage_file_path}")
        if os.path.exists(erc20_file_path):
            os.remove(erc20_file_path)
            print(f"🗑️ Temporary file deleted: {erc20_file_path}")

    print("\n--- BlockchainTools Test Script End ---")


if __name__ == "__main__":
    main()
