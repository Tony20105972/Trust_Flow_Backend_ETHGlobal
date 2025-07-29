# deploy_manager.py

import os
import json
import tempfile
import time
from typing import Dict, Any, Optional, List
from web3 import Web3
from web3.middleware.proof_of_authority import ExtraDataToPOAMiddleware
from solcx import compile_source, install_solc, set_solc_version
from solcx.exceptions import SolcError
from web3.exceptions import TransactionNotFound, TimeExhausted, ContractLogicError
from web3.types import TxReceipt

# Import userdata only in Google Colab environment.
# This avoids NameError when running in a local environment.
try:
    from google.colab import userdata
except ImportError:
    # If not in Colab, indicate that userdata is unavailable.
    # A dummy class is created to prevent errors and return None.
    class UserDataMock:
        def get(self, key: str) -> Optional[str]:
            print(f"⚠️ Could not import 'google.colab.userdata'. User data for '{key}' is not available.")
            return None
    userdata = UserDataMock()


# Mock TemplateMapper class (ERC20 템플릿에 Mock ERC20 코드 적용 - transfer 함수 제거)
class TemplateMapper:
    """
    Mock TemplateMapper for testing when the actual module is not available.
    Provides placeholder methods to avoid ModuleNotFoundError.
    """
    def map_to_template(self, template_name: str, variables: Dict[str, Any]) -> str:
        print(f"💡 Using mock TemplateMapper.map_to_template for '{template_name}' with variables: {variables}")
        if template_name == "SimpleStorage":
            return """
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
        elif template_name == "ERC20": # ERC20 템플릿에 Mock ERC20 코드 적용 - transfer 함수 제거
             return """
pragma solidity ^0.8.0;

contract SimpleERC20 {
    string public name;
    string public symbol;
    uint8 public decimals = 18;
    uint256 public totalSupply;

    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);

    constructor(string memory _name, string memory _symbol, uint256 initialSupply) {
        name = _name;
        symbol = _symbol;
        totalSupply = initialSupply;
        balanceOf[msg.sender] = initialSupply;
        emit Transfer(address(0), msg.sender, initialSupply);
    }

    // transfer 함수 제거
    // function transfer(address to, uint256 value) public returns (bool) {
    //     require(balanceOf[msg.sender] >= value, "Not enough balance");
    //     balanceOf[msg.sender] -= value;
    //     balanceOf[to] += value;
    //     emit Transfer(msg.sender, to, value);
    //     return true;
    // }

    function approve(address spender, uint256 value) public returns (bool) {
        allowance[msg.sender][spender] = value;
        emit Approval(msg.sender, spender, value);
        return true;
    }

    function transferFrom(address from, address to, uint256 value) public returns (bool) {
        require(balanceOf[from] >= value, "Not enough balance");
        require(allowance[from][msg.sender] >= value, "Not approved");
        balanceOf[from] -= value;
        balanceOf[to] += value;
        allowance[from][msg.sender] -= value;
        emit Transfer(from, to, value);
        return true;
    }
}
"""
        else:
            raise ValueError(f"Mock TemplateMapper does not support template: {template_name}")

    def get_constructor_args_for_template(self, template_name: str, variables: Dict[str, Any]) -> Optional[List[Any]]:
        print(f"💡 Using mock TemplateMapper.get_constructor_args_for_template for '{template_name}' with variables: {variables}")
        if template_name == "SimpleStorage":
            return None
        elif template_name == "ERC20": # ERC20 생성자 인자도 Mock ERC20에 맞춰 수정
            name = variables.get("TOKEN_NAME", "DefaultToken")
            symbol = variables.get("TOKEN_SYMBOL", "DEF")
            initial_supply = variables.get("initialSupply", 0)
            return [name, symbol, initial_supply]
        else:
             return None


class DeploymentManager:
    """
    This class acts as the core deployment control tower for Samantha OS.
    It manages the entire lifecycle of smart contracts (compilation, deployment,
    function calls, transaction sending). Internally, it uses Web3.py to interact
    with the blockchain.
    """

    def __init__(self, rpc_url: Optional[str] = None, private_key: Optional[str] = None):
        """
        Initializes the DeploymentManager instance.
        The RPC URL and private key are configured from environment variables
        or directly passed arguments. The private key is searched in Colab secrets
        then in OS environment variables.

        Args:
            rpc_url (Optional[str]): URL of the Ethereum RPC node.
                                     Defaults to ETH_RPC_URL environment variable or 'https://node.ghostnet.etherlink.com'.
            private_key (Optional[str]): Private key (including 0x prefix) to be used for signing transactions.

        Raises:
            ValueError: If PRIVATE_KEY is not set.
            ConnectionError: If the Web3 instance fails to connect to the RPC.
        """
        print("🛠️ Initializing DeploymentManager...")

        self.rpc_url: str = rpc_url or os.getenv("ETH_RPC_URL", "https://node.ghostnet.etherlink.com")

        self.private_key: Optional[str] = private_key or userdata.get('PRIVATE_KEY') or os.getenv("PRIVATE_KEY")

        if not self.private_key:
            raise ValueError(
                "❌ PRIVATE_KEY environment variable is not set. "
                "Please add your private key to Colab secrets or system environment variables."
                "\n   (e.g., export PRIVATE_KEY='0x...') or add it to the 'Secrets' tab in your Colab notebook)"
            )
        if not self.private_key.startswith('0x'):
            self.private_key = '0x' + self.private_key

        self.w3: Web3 = None
        self.account = None
        self._initialize_web3()

        self.template_mapper = TemplateMapper()
        print("✅ DeploymentManager initialization complete.")

    def _initialize_web3(self) -> None:
        """
        Initializes the Web3 instance and sets up network connection and account.
        This method is for internal use only.
        """
        print(f"🔄 Attempting to connect to RPC URL: {self.rpc_url}...")
        try:
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
            self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

            if not self.w3.is_connected():
                raise ConnectionError(f"Failed to connect to RPC: {self.rpc_url}")

            self.account = self.w3.eth.account.from_key(self.private_key)
            print(f"✅ Network connection successful: {self.rpc_url}")
            print(f"   → Using account address: {self.account.address}")
            print(f"   → Current account balance: {self.w3.from_wei(self.w3.eth.get_balance(self.account.address), 'ether'):.4f} ETH")

        except ConnectionError as e:
            print(f"❌ Connection error: {e}")
            raise
        except Exception as e:
            print(f"❌ Unexpected error during Web3 initialization: {type(e).__name__}: {e}")
            raise

    def _compile_contract(self, file_path: str, solc_version: str = "0.8.20") -> Dict[str, Any]:
        """
        Compiles a Solidity .sol file and returns its ABI and bytecode.
        This method is for internal use within DeploymentManager only.

        Args:
            file_path (str): The path to the Solidity file.
            solc_version (str): The solc compiler version to use (default: "0.8.20").

        Returns:
            Dict[str, Any]: A dictionary containing the ABI and bytecode of the compiled contract.
                            Example: {"abi": [...], "bytecode": "0x..."}

        Raises:
            FileNotFoundError: If the specified file path does not exist.
            SolcError: If an error occurs during Solidity compilation.
            Exception: For other unexpected errors.
        """
        print(f"🔄 Compiling '{file_path}' with solc {solc_version}...")
        try:
            install_solc(solc_version)
            set_solc_version(solc_version)

            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File '{file_path}' not found.")

            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()

            temp_file_dir = os.path.abspath(os.path.dirname(file_path))
            allow_paths = [temp_file_dir, "/content/node_modules"]

            colab_content_dir = "/content"
            potential_project_roots = [
                colab_content_dir,
                os.path.join(colab_content_dir, 'samantha-os-v5-backend')
            ]
            for root in potential_project_roots:
                node_modules_path = os.path.join(root, 'node_modules')
                if os.path.exists(node_modules_path):
                    allow_paths.append(node_modules_path)
            
            solcx_user_dir = os.path.join(os.path.expanduser('~'), '.solcx')
            solcx_node_modules = os.path.join(solcx_user_dir, 'node_modules')
            if os.path.exists(solcx_node_modules):
                 allow_paths.append(solcx_node_modules)

            allow_paths = sorted(list(set([p for p in allow_paths if os.path.exists(p)])))

            if not allow_paths:
                 print("   ⚠️ Warning: No valid allow_paths found for Solidity imports. External contracts might not be located.")
                 allow_paths = [temp_file_dir]

            print(f"   → Compiler allow_paths: {allow_paths}")

            compiled_sol = compile_source(
                source_code,
                output_values=["abi", "bin"],
                solc_version=solc_version,
                allow_paths=allow_paths
            )

            if not compiled_sol:
                raise SolcError("No valid contract found in compilation result. Please check your source code.")

            contract_name = max(compiled_sol, key=lambda x: len(compiled_sol[x]['bin']))
            contract_interface = compiled_sol[contract_name]

            print(f"✅ Contract '{contract_name.split(':')[-1]}' compiled successfully.")
            return {"abi": contract_interface["abi"], "bytecode": "0x" + contract_interface["bin"]}
        except FileNotFoundError as e:
            print(f"❌ Compilation error: File not found - {e}")
            raise
        except SolcError as e:
            error_message = f"Solidity compilation error: {e}"
            if hasattr(e, 'stderr') and e.stderr:
                decoded_stderr = e.stderr.decode('utf-8').strip()
                error_message += f"\n   (Error code: {e.return_code}, Message: {decoded_stderr})"
            print(f"❌ {error_message}")
            raise
        except Exception as e:
            print(f"❌ Unexpected error during contract compilation: {type(e).__name__}: {e}")
            raise

    def _deploy_contract_internal(
        self,
        abi: List[Dict[str, Any]],
        bytecode: str,
        constructor_args: Optional[List[Any]] = None,
        gas_limit: int = 25_000_000, # <<<<< GAS LIMIT INCREASED HERE
        gas_price_multiplier: float = 1.5,
        timeout_seconds: int = 300
    ) -> Dict[str, str]:
        """
        Deploys a compiled Solidity contract to the Ethereum network.
        This method is for internal use within DeploymentManager only.
        """
        print("🚀 Starting contract deployment...")
        start_time = time.time()
        try:
            Contract = self.w3.eth.contract(abi=abi, bytecode=bytecode)
            nonce = self.w3.eth.get_transaction_count(self.account.address)

            current_gas_price = self.w3.eth.gas_price
            effective_gas_price = int(current_gas_price * gas_price_multiplier)

            print(f"   → Current network gas price: {self.w3.from_wei(current_gas_price, 'gwei'):.2f} Gwei")
            print(f"   → Applied gas price ({gas_price_multiplier}x): {self.w3.from_wei(effective_gas_price, 'gwei'):.2f} Gwei (Wei: {effective_gas_price})")

            if constructor_args:
                tx_builder = Contract.constructor(*constructor_args)
            else:
                tx_builder = Contract.constructor()

            tx = tx_builder.build_transaction({
                "from": self.account.address,
                "nonce": nonce,
                "gas": gas_limit,
                "gasPrice": effective_gas_price
            })

            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            raw_tx = getattr(signed_tx, "raw_transaction", None) or getattr(signed_tx, "rawTransaction", None)

            if raw_tx is None:
                raise AttributeError("❌ Could not find 'raw_transaction' or 'rawTransaction' attribute in web3 SignedTransaction object.")

            tx_hash = self.w3.eth.send_raw_transaction(raw_tx)
            print(f"   → Transaction sent. Hash: {tx_hash.hex()}")

            poll_latency = 0.5 if "127.0.0.1" in self.rpc_url or "localhost" in self.rpc_url else 5
            print(f"   → Waiting for transaction receipt (max {timeout_seconds}s, polling every {poll_latency}s)...")
            receipt: TxReceipt = self.w3.eth.wait_for_transaction_receipt(
                tx_hash,
                timeout=timeout_seconds,
                poll_latency=poll_latency
            )

            if receipt.status != 1:
                raise RuntimeError(f"❌ Contract deployment failed. Transaction receipt:\n{json.dumps(dict(receipt), indent=2, default=str)}")

            end_time = time.time()
            print(f"✅ Contract successfully deployed to address: {receipt.contractAddress}")
            print(f"⏱️ Deployment time: {end_time - start_time:.2f} seconds")
            return {"contract_address": receipt.contractAddress, "transaction_hash": tx_hash.hex()}

        except (TransactionNotFound, TimeExhausted) as e:
            print(f"❌ Transaction receipt waiting error (timeout or not found): {e}")
            raise
        except Exception as e:
            print(f"❌ Unexpected error during contract deployment: {type(e).__name__}: {e}")
            raise

    def deploy_from_code(self, solidity_code: str, constructor_args: Optional[List[Any]] = None,
                         solc_version: str = "0.8.20", gas_price_multiplier: float = 2.0) -> Dict[str, Any]:
        """
        [Core Function] Compiles and deploys a given Solidity code string to the blockchain.
        Can be directly called by the FastAPI `/deploy/code` endpoint.
        """
        print(f"\n🚀 deploy_from_code: Starting contract deployment (direct Solidity code input)...")
        temp_file_path = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".sol", encoding='utf-8') as temp_sol_file:
                temp_sol_file.write(solidity_code)
                temp_file_path = temp_sol_file.name
            print(f"   → Solidity code saved to temporary file: {temp_file_path}")

            compiled_contract = self._compile_contract(temp_file_path, solc_version=solc_version)
            abi = compiled_contract["abi"]
            bytecode = compiled_contract["bytecode"]
            print("   → Contract compilation complete.")

            print("   → Calling internal deployment method for contract deployment...")
            # deploy_from_code는 _deploy_contract_internal의 gas_limit 기본값을 따름
            deployed_info = self._deploy_contract_internal(
                abi,
                bytecode,
                constructor_args=constructor_args,
                gas_price_multiplier=gas_price_multiplier
            )
            contract_address = deployed_info["contract_address"]
            transaction_hash = deployed_info["transaction_hash"]
            print(f"✅ Contract deployment successful! Address: {contract_address}, Hash: {transaction_hash}")

            return {
                "contract_address": contract_address,
                "transaction_hash": transaction_hash,
                "abi": abi
            }

        except Exception as e:
            print(f"❌ Error during deploy_from_code execution: {type(e).__name__}: {e}")
            raise
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                print(f"   → Temporary file deleted: {temp_file_path}")

    def deploy_from_template(self, template_name: str, variables: Dict[str, Any],
                             solc_version: str = "0.8.20", gas_price_multiplier: float = 2.0) -> Dict[str, Any]:
        """
        [Core Function] Deploys a contract based on a template by connecting with TemplateMapper.
        Can be directly called by the FastAPI `/deploy/template` endpoint.
        """
        print(f"\n🚀 deploy_from_template: Starting template-based contract deployment for '{template_name}'...")
        try:
            solidity_code = self.template_mapper.map_to_template(template_name, variables)
            print(f"   → Solidity code generated from template '{template_name}'.")

            constructor_args = self.template_mapper.get_constructor_args_for_template(template_name, variables)
            print(f"   → Contract constructor arguments: {constructor_args}")

            deploy_result = self.deploy_from_code(
                solidity_code,
                constructor_args=constructor_args,
                solc_version=solc_version,
                gas_price_multiplier=gas_price_multiplier
            )
            print(f"✅ Template-based contract deployment successful: {deploy_result['contract_address']}")
            return deploy_result

        except ValueError as e:
            print(f"❌ Template-based deployment error (variable/template issue): {e}")
            raise
        except Exception as e:
            print(f"❌ Unexpected error during template-based contract deployment: {type(e).__name__}: {e}")
            raise

    def call_contract_function(self, contract_address: str, abi: List[Dict[str, Any]],
                               function_name: str, args: Optional[List[Any]] = None) -> Any:
        """
        Calls a read-only (view/pure) function of a deployed contract.
        Does not change blockchain state and does not consume gas.
        """
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

    def send_contract_transaction(self, contract_address: str, abi: List[Dict[str, Any]], function_name: str,
                                  args: Optional[List[Any]] = None, value: int = 0, gas_limit: int = 5_000_000, # <<<<< GAS LIMIT INCREASED HERE
                                  gas_price_multiplier: float = 1.5, timeout_seconds: int = 300) -> str:
        """
        Calls a state-changing function of a deployed contract and sends a transaction.
        Changes blockchain state and consumes gas.
        The transaction priority can be increased by multiplying the gas price with `gas_price_multiplier`.
        """
        print(f"🔄 Sending transaction to state-changing function '{function_name}' on contract '{contract_address}'...")
        start_time = time.time()
        try:
            contract = self.w3.eth.contract(address=contract_address, abi=abi)
            nonce = self.w3.eth.get_transaction_count(self.account.address)

            current_gas_price = self.w3.eth.gas_price
            effective_gas_price = int(current_gas_price * gas_price_multiplier)
            print(f"   → Current network gas price: {self.w3.from_wei(current_gas_price, 'gwei'):.2f} Gwei")
            print(f"   → Applied gas price ({gas_price_multiplier}x): {self.w3.from_wei(effective_gas_price, 'gwei'):.2f} Gwei (Wei: {effective_gas_price})")

            if args:
                tx_builder = contract.functions[function_name](*args)
            else:
                tx_builder = contract.functions[function_name]()

            tx = tx_builder.build_transaction({
                "from": self.account.address,
                "nonce": nonce,
                "value": value,
                "gas": gas_limit,
                "gasPrice": effective_gas_price
            })

            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            raw_tx = getattr(signed_tx, "raw_transaction", None) or getattr(signed_tx, "rawTransaction", None)

            if raw_tx is None:
                raise AttributeError("❌ Could not find 'raw_transaction' or 'rawTransaction' attribute in web3 SignedTransaction object.")

            tx_hash = self.w3.eth.send_raw_transaction(raw_tx)
            print(f"   → Transaction sent. Hash: {tx_hash.hex()}")

            poll_latency = 0.5 if "127.0.0.1" in self.rpc_url or "localhost" in self.rpc_url else 5
            print(f"   → Waiting for transaction receipt (max {timeout_seconds}s, polling every {poll_latency}s)...")
            receipt: TxReceipt = self.w3.eth.wait_for_transaction_receipt(
                tx_hash,
                timeout=timeout_seconds,
                poll_latency=poll_latency
            )

            if receipt.status != 1:
                raise RuntimeError(f"❌ Transaction '{function_name}' failed.\n   → Receipt: {json.dumps(dict(receipt), indent=2, default=str)}")

            end_time = time.time()
            print(f"✅ Transaction '{function_name}' successful. Block number: {receipt.blockNumber}")
            print(f"⏱️ Transaction time: {end_time - start_time:.2f} seconds")
            return tx_hash.hex()

        except (TransactionNotFound, TimeExhausted) as e:
            print(f"❌ Transaction receipt waiting error (timeout or not found): {e}")
            raise
        except ContractLogicError as e:
            print(f"❌ Contract logic error occurred: {e}")
            raise
        except Exception as e:
            print(f"❌ Unexpected error sending transaction to function '{function_name}': {type(e).__name__}: {e}")
            raise


# --- DeploymentManager Integration Test Code (main function) ---
def main():
    print("\n--- DeploymentManager Integration Test Script Start ---")

    # --- 1. Example Solidity Code (SimpleStorage) ---
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

    # --- Anvil (Local Node) Test - Optional ---
    is_anvil_test_enabled = False
    ANVIL_RPC_URL = "http://127.0.0.1:8545"
    ANVIL_PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"

    if is_anvil_test_enabled:
        print("\n--- Anvil (Local Node) Deployment and Interaction Test Start ---")
        try:
            anvil_manager = DeploymentManager(rpc_url=ANVIL_RPC_URL, private_key=ANVIL_PRIVATE_KEY)

            print("\n--- Anvil: deploy_from_code (SimpleStorage) ---")
            anvil_deploy_result_code = anvil_manager.deploy_from_code(simple_storage_code, gas_price_multiplier=1.0)
            print(f"🎉 Anvil (Code) SimpleStorage deployment address: {anvil_deploy_result_code['contract_address']}")

            current_data = anvil_manager.call_contract_function(anvil_deploy_result_code['contract_address'], anvil_deploy_result_code['abi'], "get")
            print(f"   SimpleStorage initial storedData: {current_data}")
            anvil_manager.send_contract_transaction(anvil_deploy_result_code['contract_address'], anvil_deploy_result_code['abi'], "set", [12345], gas_price_multiplier=1.0)
            updated_data = anvil_manager.call_contract_function(anvil_deploy_result_code['contract_address'], anvil_deploy_result_code['abi'], "get")
            print(f"   SimpleStorage updated storedData: {updated_data}")

            print("\n--- Anvil: deploy_from_template (ERC20) ---")
            erc20_vars_anvil = {
                "TOKEN_NAME": "AnvilTestToken",
                "TOKEN_SYMBOL": "ATT",
                "initialSupply": 5000 * (10**18)
            }
            anvil_template_deploy_result_erc20 = anvil_manager.deploy_from_template("ERC20", erc20_vars_anvil, gas_price_multiplier=1.0)
            print(f"🎉 Anvil (Template-ERC20) deployment address: {anvil_template_deploy_result_erc20['contract_address']}")

            owner_address = anvil_manager.account.address
            erc20_abi = anvil_template_deploy_result_erc20['abi']
            erc20_address = anvil_template_deploy_result_erc20['contract_address']
            total_supply = anvil_manager.call_contract_function(erc20_address, erc20_abi, "totalSupply")
            owner_balance = anvil_manager.call_contract_function(erc20_address, erc20_abi, "balanceOf", [owner_address])
            print(f"   ERC20 Total Supply: {anvil_manager.w3.from_wei(total_supply, 'ether'):.2f} ATT")
            print(f"   Deployer ({anvil_manager.account.address}) balance: {anvil_manager.w3.from_wei(owner_balance, 'ether'):.2f} ATT")


        except Exception as e:
            print(f"❌ Error during Anvil test: {type(e).__name__}: {e}")
            if 'anvil_manager' in locals() and anvil_manager.w3 and anvil_manager.account:
                balance_wei = anvil_manager.w3.eth.get_balance(anvil_manager.account.address)
                balance_eth = anvil_manager.w3.from_wei(balance_wei, 'ether')
                print(f"   → Anvil account balance: {balance_eth:.4f} ETH ({balance_wei} wei)")
        print("\n--- Anvil (Local Node) Test End ---")

    # --- Ghostnet (Testnet) Test ---
    print("\n--- Ghostnet (Testnet) Deployment and Interaction Test Start ---")
    try:
        ghostnet_manager = DeploymentManager()

        print("\n--- Ghostnet: deploy_from_code (SimpleStorage) ---")
        ghostnet_deploy_result_code = ghostnet_manager.deploy_from_code(simple_storage_code, gas_price_multiplier=2.5)
        print(f"🎉 Ghostnet (Code) SimpleStorage deployment address: {ghostnet_deploy_result_code['contract_address']}")
        print(f"   Transaction hash: {ghostnet_deploy_result_code['transaction_hash']}")

        current_data_ghost = ghostnet_manager.call_contract_function(ghostnet_deploy_result_code['contract_address'], ghostnet_deploy_result_code['abi'], "get")
        print(f"   Ghostnet SimpleStorage initial storedData: {current_data_ghost}")
        ghostnet_manager.send_contract_transaction(ghostnet_deploy_result_code['contract_address'], ghostnet_deploy_result_code['abi'], "set", [777], gas_price_multiplier=2.5)
        updated_data_ghost = ghostnet_manager.call_contract_function(ghostnet_deploy_result_code['contract_address'], ghostnet_deploy_result_code['abi'], "get")
        print(f"   Ghostnet SimpleStorage updated storedData: {updated_data_ghost}")


        print("\n--- Ghostnet: deploy_from_template (ERC20) ---")
        erc20_vars_ghostnet = {
            "TOKEN_NAME": "GhostHackToken",
            "TOKEN_SYMBOL": "GHT",
            "initialSupply": 1000 * (10**18)
        }
        ghostnet_template_deploy_result_erc20 = ghostnet_manager.deploy_from_template("ERC20", erc20_vars_ghostnet, solc_version="0.8.20", gas_price_multiplier=2.5)
        print(f"🎉 Ghostnet (Template-ERC20) deployment address: {ghostnet_template_deploy_result_erc20['contract_address']}")
        print(f"   Transaction hash: {ghostnet_template_deploy_result_erc20['transaction_hash']}")

        owner_address_ghost = ghostnet_manager.account.address
        erc20_abi_ghost = ghostnet_template_deploy_result_erc20['abi']
        erc20_address_ghost = ghostnet_template_deploy_result_erc20['contract_address']
        
        total_supply_ghost = ghostnet_manager.call_contract_function(erc20_address_ghost, erc20_abi_ghost, "totalSupply")
        owner_balance_ghost = ghostnet_manager.call_contract_function(erc20_address_ghost, erc20_abi_ghost, "balanceOf", [owner_address_ghost])
        print(f"   ERC20 Total Supply: {ghostnet_manager.w3.from_wei(total_supply_ghost, 'ether'):.2f} GHT")
        print(f"   Deployer ({owner_address_ghost}) balance: {ghostnet_manager.w3.from_wei(owner_balance_ghost, 'ether'):.2f} GHT")

        # ERC20 Token Transfer Test는 transfer 함수가 없으므로 주석 처리하거나 제거해야 합니다.
        # recipient_address_ghost = "0x2F7962F7961A624231E2A3423fA7A2500dE41E22"
        # transfer_amount_ghost = 10 * (10**18)
        # print(f"\n--- Ghostnet: ERC20 Token Transfer Test ---")
        # ghostnet_manager.send_contract_transaction(erc20_address_ghost, erc20_abi_ghost, "transfer", [recipient_address_ghost, transfer_amount_ghost], gas_price_multiplier=2.5)
        # recipient_balance_ghost = ghostnet_manager.call_contract_function(erc20_address_ghost, erc20_abi_ghost, "balanceOf", [recipient_address_ghost])
        # print(f"   Recipient ({recipient_address_ghost}) balance: {ghostnet_manager.w3.from_wei(recipient_balance_ghost, 'ether'):.2f} GHT")


    except ValueError as e:
        print(f"❌ Ghostnet test skipped (PRIVATE_KEY error): {e}")
        print("    → You must set the PRIVATE_KEY environment variable to run Ghostnet tests.")
    except ConnectionError as e:
        print(f"❌ Ghostnet test skipped (connection error): {e}")
        print("    → Ensure the Ghostnet RPC URL is correct and accessible.")
    except Exception as e:
        print(f"❌ Error during Ghostnet test: {type(e).__name__}: {e}")
        try:
            if ghostnet_manager and ghostnet_manager.w3 and ghostnet_manager.account:
                balance_wei = ghostnet_manager.w3.eth.get_balance(ghostnet_manager.account.address)
                balance_eth = ghostnet_manager.w3.from_wei(balance_wei, 'ether')
                print(f"   → Ghostnet account balance: {balance_eth:.4f} ETH ({balance_wei} wei)")
        except Exception as balance_err:
            print(f"   → Error checking Ghostnet account balance: {balance_err}")

    print("\n--- DeploymentManager Integration Test Script End ---")


if __name__ == "__main__":
    main()
