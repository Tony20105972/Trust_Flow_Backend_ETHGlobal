import os
import json
import time
from datetime import datetime
from web3 import Web3
from eth_account import Account
from typing import Optional, Dict, Any, List
# Removed getpass as it implies interactive input, which we are avoiding for core setup

# --- Configuration ---
TEST_WETH_ADDRESS_SEPOLIA = "0xfFf9976782d46CC05630D1f6eB9Bc98210fBfCc5" # Example Sepolia WETH
TEST_USDC_ADDRESS_SEPOLIA = "0x56aD9fB23C8A0B2C9030A9086A0F174a7D4E708E" # Example Dummy USDC (adjust if needed)

ERC20_ABI = json.loads('''
[
    {
        "constant": false,
        "inputs": [
            {
                "name": "_spender",
                "type": "address"
            },
            {
                "name": "_value",
                "type": "uint256"
            }
        ],
        "name": "approve",
        "outputs": [
            {
                "name": "",
                "type": "bool"
            }
        ],
        "payable": false,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [],
        "name": "name",
        "outputs": [
            {
                "name": "",
                "type": "string"
            }
        ],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [],
        "name": "symbol",
        "outputs": [
            {
                "name": "",
                "type": "string"
            }
        ],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [],
        "name": "decimals",
        "outputs": [
            {
                "name": "",
                "type": "uint8"
            }
        ],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    }
]
''')

DUMMY_LOP_ABI = json.loads('''
[
    {
        "inputs": [
            {"internalType": "address", "name": "fromToken", "type": "address"},
            {"internalType": "address", "name": "toToken", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
            {"internalType": "uint256", "name": "price", "type": "uint256"},
            {"internalType": "address", "name": "maker", "type": "address"}
        ],
        "name": "submitLimitOrder",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]
''')

TOKEN_METADATA = {
    Web3.to_checksum_address(TEST_WETH_ADDRESS_SEPOLIA): {"name": "Wrapped Ether", "symbol": "WETH", "decimals": 18},
    Web3.to_checksum_address(TEST_USDC_ADDRESS_SEPOLIA): {"name": "USD Coin", "symbol": "USDC", "decimals": 6},
}

class Web3Client:
    def __init__(self):
        self.w3: Optional[Web3] = None
        self.account: Optional[Account] = None
        self.lop_contract_address: Optional[str] = None
        self.current_nonce: Optional[int] = None

        # 1. Get RPC URL ONLY from environment variable
        rpc_url = os.getenv("WEB3_RPC_URL_SEPOLIA")
        if not rpc_url:
            raise ValueError("WEB3_RPC_URL_SEPOLIA environment variable is not set. This is required for Web3Client initialization.")
        print(f"✅ Web3 RPC URL loaded from ENV: {rpc_url}")

        try:
            self.w3 = Web3(Web3.HTTPProvider(rpc_url))
            if not self.w3.is_connected():
                raise ConnectionError(f"Failed to connect to Web3 RPC URL: {rpc_url}. Check URL and network connectivity.")
            print(f"✅ Web3 connected to {rpc_url}.")
        except Exception as e:
            print(f"❌ Critical error connecting to Web3 RPC URL {rpc_url}: {e}")
            raise

        # 2. Get wallet private key ONLY from environment variable
        private_key = os.getenv("WALLET_PRIVATE_KEY")
        if not private_key:
            raise ValueError("WALLET_PRIVATE_KEY environment variable is not set. This is required for signing transactions.")
        print(f"✅ Wallet private key loaded from ENV.")

        try:
            self.account = Account.from_key(private_key)
            self.w3.eth.default_account = self.account.address
            self.current_nonce = self.w3.eth.get_transaction_count(self.account.address)
            print(f"✅ Wallet {self.account.address} loaded and set for transaction signing. Current nonce: {self.current_nonce}")
        except ValueError as e:
            print(f"❌ Error loading private key: {e}. Ensure it is a valid hex string.")
            self.account = None
            raise # Re-raise to halt initialization if private key is invalid
        except Exception as e:
            print(f"❌ Unexpected error loading private key: {e}")
            self.account = None
            raise

        # 3. Get DUMMY LOP Contract Address ONLY from environment variable
        lop_address_input = os.getenv("DUMMY_LOP_CONTRACT_ADDRESS")
        if not lop_address_input:
            raise ValueError("DUMMY_LOP_CONTRACT_ADDRESS environment variable is not set. This is required for LOP contract interactions.")
        print(f"✅ LOP Contract Address loaded from ENV: {lop_address_input}")

        if Web3.is_address(lop_address_input):
            self.lop_contract_address = Web3.to_checksum_address(lop_address_input)
            print(f"✅ LOP contract address '{self.lop_contract_address}' set.")
        else:
            print(f"❌ Error: Environment variable DUMMY_LOP_CONTRACT_ADDRESS '{lop_address_input}' is not a valid Ethereum address.")
            print("❗❗ LOP contract interactions will fail. Please correct the environment variable.")
            self.lop_contract_address = Web3.to_checksum_address("0x000000000000000000000000000000000000dEaD") # Fallback to a dummy address


    def get_token_info(self, token_address: str) -> Dict[str, Any]:
        """Fetches token name, symbol, and decimals using hardcoded data or on-chain calls."""
        checksum_address = Web3.to_checksum_address(token_address)
        
        if checksum_address in TOKEN_METADATA:
            return TOKEN_METADATA[checksum_address]

        token_contract = self.w3.eth.contract(address=checksum_address, abi=ERC20_ABI)
        name = token_address
        symbol = token_address
        decimals = 18

        try:
            name = token_contract.functions.name().call()
            symbol = token_contract.functions.symbol().call()
            try:
                decimals = token_contract.functions.decimals().call()
            except Exception as e:
                print(f"⚠️ Could not fetch decimals for {token_address}: {e}. Using default 18.")
        except Exception as e:
            print(f"⚠️ Could not fetch name/symbol for {token_address}: {e}. Using address as fallback.")
            
        return {"name": name, "symbol": symbol, "decimals": decimals}

    def _get_gas_fees(self) -> Dict[str, int]:
        """Estimates EIP-1559 gas fees."""
        try:
            latest_block = self.w3.eth.get_block('latest')
            base_fee_per_gas = latest_block['baseFeePerGas']

            max_priority_fee_per_gas = self.w3.to_wei(1, 'gwei') 
            max_fee_per_gas = (base_fee_per_gas * 2) + max_priority_fee_per_gas

            return {
                'maxFeePerGas': max_fee_per_gas,
                'maxPriorityFeePerGas': max_priority_fee_per_gas
            }
        except Exception as e:
            print(f"❌ Error estimating EIP-1559 gas fees: {e}. Falling back to legacy gas price.")
            return {'gasPrice': self.w3.eth.gas_price} # Fallback to legacy

    def approve_erc20(self, token_address: str, amount: int) -> Optional[str]:
        """
        Approves a specific amount for a given token to the LOP contract address.
        The spender address uses self.lop_contract_address set during Web3Client initialization.
        """
        if not self.account:
            print("❌ ERC-20 Approval failed: Wallet not set for signing. Check private key error.")
            return None
        
        if not self.lop_contract_address or self.lop_contract_address == Web3.to_checksum_address("0x000000000000000000000000000000000000dEaD"):
            print(f"❌ ERC-20 Approval skipped: LOP contract address not validly set or is fallback address ({self.lop_contract_address}).")
            return None

        spender_checksum_address = self.lop_contract_address

        try:
            token_contract = self.w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=ERC20_ABI)

            token_info = self.get_token_info(token_address)
            token_name = token_info.get("name", token_address)

            print(f"Approving {self.w3.from_wei(amount, 'ether')} {token_name} to {spender_checksum_address}...")

            gas_fees = self._get_gas_fees()
            tx_params = {
                'from': self.account.address,
                'nonce': self.current_nonce,
                'gas': 200000,
                **gas_fees
            }

            tx = token_contract.functions.approve(
                spender_checksum_address,
                amount
            ).build_transaction(tx_params)

            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)

            self.current_nonce += 1

            print(f"✅ ERC-20 Approval transaction sent: {tx_hash.hex()}")
            print(f"Waiting for transaction receipt for {tx_hash.hex()}...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
            if receipt.status == 1:
                print(f"✅ ERC-20 Approval transaction confirmed in block {receipt.blockNumber}!")
                return tx_hash.hex()
            else:
                print(f"❌ ERC-20 Approval transaction failed on-chain. Receipt status: {receipt.status}")
                return None

        except Exception as e:
            print(f"❌ Unexpected error during ERC-20 approval: {e}")
            return None

    def submit_lop_order_on_chain(self, order_data: Dict[str, Any]) -> Optional[str]:
        """
        Submits an order to the LOP contract.
        The LOP contract address uses self.lop_contract_address set during Web3Client initialization.
        """
        if not self.account:
            print("❌ LOP Order submission failed: Wallet not set for signing. Check private key error.")
            return None

        if not self.lop_contract_address or self.lop_contract_address == Web3.to_checksum_address("0x000000000000000000000000000000000000dEaD"):
            print(f"❌ LOP Order submission skipped: LOP contract address not validly set or is fallback address ({self.lop_contract_address}).")
            return None
        
        lop_contract_checksum_address = self.lop_contract_address

        try:
            lop_contract = self.w3.eth.contract(
                address=lop_contract_checksum_address,
                abi=DUMMY_LOP_ABI
            )

            from_token_address = Web3.to_checksum_address(order_data['from_token_address'])
            to_token_address = Web3.to_checksum_address(order_data['to_token_address'])
            
            from_token_info = self.get_token_info(from_token_address)
            from_token_decimals = from_token_info.get("decimals", 18) 

            amount_for_contract = int(order_data['amount'] * (10**from_token_decimals)) 
            price_for_contract = int(order_data['price'] * (10**18)) # Price assumed to be 18 decimals like ETH

            print(f"Submitting Order {order_data['id']} (Sell {order_data['from_token']} → Buy {order_data['to_token']}) on-chain...")

            gas_fees = self._get_gas_fees()
            tx_params = {
                'from': self.account.address,
                'nonce': self.current_nonce,
                'gas': 500000,
                **gas_fees
            }

            tx = lop_contract.functions.submitLimitOrder(
                from_token_address,
                to_token_address,
                amount_for_contract,
                price_for_contract,
                Web3.to_checksum_address(self.account.address)
            ).build_transaction(tx_params)

            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            self.current_nonce += 1

            print(f"✅ LOP Order transaction sent: {tx_hash.hex()}")
            print(f"Waiting for transaction receipt for {tx_hash.hex()}...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
            if receipt.status == 1:
                print(f"✅ LOP Order transaction confirmed in block {receipt.blockNumber}!")
                return tx_hash.hex()
            else:
                print(f"❌ LOP Order transaction failed on-chain. Receipt status: {receipt.status}")
                return None

        except Exception as e:
            print(f"❌ Unexpected error during LOP order submission: {e}")
            return None


class DAOManager:
    def __init__(self):
        self.proposals = {}
        self.next_proposal_id = 1753926014868 

    def create_proposal(self, order_id: int, title: str, proposer_address: str) -> Dict[str, Any]:
        proposal_id = self.next_proposal_id
        self.next_proposal_id += 1
        proposal = {
            "id": proposal_id,
            "title": title,
            "status": "pending",
            "proposer": proposer_address
        }
        self.proposals[order_id] = proposal
        print(f"  [Mock] DAO: Proposal '{title}' created by {proposer_address}. ID: {proposal_id}")
        return proposal

    def get_proposal_status(self, proposal_id: int) -> Optional[str]:
        for order_id, proposal in self.proposals.items():
            if proposal["id"] == proposal_id:
                return proposal["status"]
        return None

    def simulate_approval(self, order_id: int):
        if order_id in self.proposals:
            self.proposals[order_id]["status"] = "approved"
            print(f"--- (Simulated) Order {order_id} status updated to DAO_APPROVED. ---")

class RuleChecker:
    def check_rules(self, solidity_code: str) -> List[Dict[str, Any]]:
        print("  [Mock] Running rule checks...")
        issues = []
        issues.append({"type": "info", "message": "No critical issues found (mock result)."})
        return issues

class LOPManager:
    def __init__(self):
        self.web3_client = Web3Client() 
        self.dao_manager = DAOManager()
        self.rule_checker = RuleChecker()
        self.orders: Dict[int, Dict[str, Any]] = {}
        self.next_order_id = 1
        print("💡 LOPManager initialized.")

    def create_limit_order(self, prompt: str, from_token: str, to_token: str, amount: float, price: float) -> Dict[str, Any]:
        order_id = self.next_order_id
        self.next_order_id += 1

        print(f"  [Mock] Generating contract for prompt: {prompt[:80]}...")
        solidity_code = f"pragma solidity ^0.8.0;\n\ncontract LimitOrderContract_{int(time.time())} {{\n    // Prompt-based generation: {prompt}\n    // ... (placeholder Solidity code)\n    function execute() public {{ /* ... */ }}\n    function cancel() public {{ /* ... */ }}\n}}\n"

        from_token_address = TEST_WETH_ADDRESS_SEPOLIA if from_token == "WETH" else TEST_USDC_ADDRESS_SEPOLIA
        to_token_address = TEST_USDC_ADDRESS_SEPOLIA if to_token == "USDC" else TEST_WETH_ADDRESS_SEPOLIA
        
        order_wallet_address = self.web3_client.account.address if self.web3_client.account else "0xYourTestWalletIfNoPrivateKeyLoaded"

        order = {
            "id": order_id,
            "from_token": from_token,
            "to_token": to_token,
            "amount": amount,
            "price": price,
            "wallet": order_wallet_address,
            "from_token_address": from_token_address,
            "to_token_address": to_token_address,
            "solidity_code": solidity_code,
            "status": "CREATED",
            "created_at": int(time.time()),
            "rule_issues": [],
            "dao_proposal_id": None,
            "onchain_approval_tx": None,
            "onchain_order_tx": None
        }
        self.orders[order_id] = order
        print(f"✅ [LOP] Limit Order {order_id} created: {amount} {from_token} → {to_token} @ {price:.4f}")

        print(f"🤝 [LOP] Attempting ERC-20 approval for {from_token} for Order {order_id}...")
        
        if self.web3_client.lop_contract_address and self.web3_client.account:
            if self.web3_client.lop_contract_address != Web3.to_checksum_address("0x000000000000000000000000000000000000dEaD"):
                token_info = self.web3_client.get_token_info(from_token_address)
                decimals = token_info.get("decimals", 18)
                
                approval_amount_wei = int(amount * (10**decimals))

                approval_tx_hash = self.web3_client.approve_erc20(
                    from_token_address,
                    approval_amount_wei
                )
                if approval_tx_hash:
                    order["onchain_approval_tx"] = approval_tx_hash
                else:
                    print(f"❌ [LOP] Failed to submit ERC-20 approval transaction for Order {order_id}.")
            else:
                print(f"❌ [LOP] Skipping ERC-20 approval as LOP contract address is fallback. Please ensure a valid address is set via ENV.")
        else:
            print(f"❌ [LOP] Skipping ERC-20 approval as LOP contract address or wallet is not set.")

        return order

    def initiate_dao_pre_approval(self, order_id: int) -> Dict[str, Any]:
        order = self.orders.get(order_id)
        if not order:
            print(f"❗ [LOP] Order {order_id} not found.")
            return {}

        proposal_title = f"Approve Limit Order #{order_id} ({order['amount']} {order['from_token']})"
        proposer_address = order['wallet']
        proposal = self.dao_manager.create_proposal(order_id, proposal_title, proposer_address)
        order["dao_proposal_id"] = proposal["id"]
        order["status"] = "DAO_PENDING"
        print(f"🗳 [LOP] DAO proposal created for Order {order_id} → Proposal ID: {proposal['id']}")

        self.dao_manager.simulate_approval(order_id)
        order["status"] = "DAO_APPROVED"
        
        return {"order_id": order_id, "proposal_info": proposal, "current_order_status": order["status"]}

    def get_order_audit_details(self, order_id: int) -> Dict[str, Any]:
        order = self.orders.get(order_id)
        if not order:
            print(f"❗ [LOP] Order {order_id} not found.")
            return {}
        
        rule_issues = self.rule_checker.check_rules(order["solidity_code"])
        order["rule_issues"] = rule_issues
        return {"order_id": order_id, "solidity_code": order["solidity_code"], "rule_issues": rule_issues}

    def submit_order_on_chain_and_simulate_execution(self, order_id: int) -> Dict[str, Any]:
        order = self.orders.get(order_id)
        if not order:
            print(f"❗ [LOP] Order {order_id} not found.")
            return {}
        
        print(f"✨ [LOP] Submitting Order {order_id} to on-chain LOP protocol...")
        
        onchain_tx_hash = self.web3_client.submit_lop_order_on_chain(order)
        
        if onchain_tx_hash:
            order["onchain_order_tx"] = onchain_tx_hash
            order["status"] = "ONCHAIN_SUBMITTED"
            print(f"✅ [LOP] Order {order_id} successfully submitted on-chain. TX: {onchain_tx_hash}")
            order["status"] = "EXECUTED"
            return {"order_id": order_id, "status": "EXECUTED", "tx_hash": onchain_tx_hash}
        else:
            order["status"] = "FAILED_ONCHAIN"
            print(f"❌ [LOP] Failed to submit Order {order_id} on-chain.")
            return {"order_id": order_id, "status": "FAILED_ONCHAIN", "error": "Failed to submit order to on-chain LOP protocol."}


    def list_all_orders(self) -> List[Dict[str, Any]]:
        return list(self.orders.values())

    def cancel_order(self, order_id: int) -> Dict[str, Any]:
        order = self.orders.get(order_id)
        if not order:
            print(f"❗ [LOP] Order {order_id} not found.")
            return {}
        
        print(f"❌ [LOP] Order {order_id} has been canceled.")
        order["status"] = "CANCELED"
        order["canceled_at"] = int(time.time())
        return {"order_id": order_id, "status": "CANCELED", "canceled_at": order["canceled_at"]}


# --- Main Test Flow (for local testing, not for API deployment) ---
if __name__ == "__main__":
    # This block will ONLY execute when lop_manager.py is run directly.
    # It includes interactive input for local development convenience.
    # FOR RENDER DEPLOYMENT, ENSURE ENVIRONMENT VARIABLES ARE SET.
    print("\n--- Web3 Integration LOPManager Flow Test (Stand-alone) ---")
    
    # Temporarily override os.getenv for local interactive test
    original_getenv = os.getenv
    def mock_getenv(key, default=None):
        val = original_getenv(key, default)
        if val is None:
            if key == "WEB3_RPC_URL_SEPOLIA":
                val = input("🔐 Enter your Web3 RPC URL (e.g., Infura/Alchemy Sepolia URL): ")
            elif key == "WALLET_PRIVATE_KEY":
                # Using standard input() for simplicity in this mock, getpass is not available here easily
                val = input("🔐 Enter your wallet private key (input will be visible in console): ") 
            elif key == "DUMMY_LOP_CONTRACT_ADDRESS":
                val = input("🔐 Enter DUMMY LOP Contract Address (Sepolia): ")
        return val

    os.getenv = mock_getenv

    try:
        lop_manager_instance = LOPManager()
    except ValueError as e:
        print(f"Initialization failed: {e}")
        print("Please set the required environment variables or provide valid inputs locally.")
        exit(1)
    except ConnectionError as e:
        print(f"Web3 connection failed: {e}")
        print("Please check your RPC URL and network connectivity.")
        exit(1)
    except Exception as e:
        print(f"An unexpected error occurred during LOPManager initialization: {e}")
        exit(1)

    # Restore original os.getenv after initialization to not affect other modules
    os.getenv = original_getenv

    # ==============================================================================
    # IMPORTANT: Before running the script, please ensure the following:
    # 1. Your connected wallet (e.g., 0x8603ce985427ED2A9A9F9a0399d33d2d4bdC2787) has sufficient Sepolia ETH for gas fees!
    #    'insufficient funds for gas * price + value' error means insufficient gas.
    # ==============================================================================

    # Step 1: Create Limit Order (including on-chain approval attempt)
    print("\n--- Step 1: Create Limit Order (including on-chain approval attempt) ---")
    order_1_prompt = "Generate a Solidity limit order smart contract that allows a user to sell 0.01 WETH (0xfFf9976782d46CC05630D1f6eB9Bc98210fBfCc5) for USDC (0x56aD9fB23C8A0B2C9030A9086A0F174a7D4E708E) at a specific price of 3500.0. The contract should include functions for order creation, cancellation by the creator (0xYourTestWalletIfNoPrivateKeyLoaded), and execution by another party when conditions are met. Ensure the contract safely handles ERC-20 token transfers and requires necessary approvals."
    order1 = lop_manager_instance.create_limit_order(order_1_prompt, "WETH", "USDC", 0.01, 3500.0)
    print("Created Order:", json.dumps(order1, indent=2))

    # Step 2: Initiate DAO Pre-Approval
    print("\n--- Step 2: Initiate DAO Pre-Approval ---")
    dao_info = lop_manager_instance.initiate_dao_pre_approval(order1["id"])
    print("DAO Proposal Info:", json.dumps(dao_info, indent=2))

    # Step 3: Get Order Audit Details
    print("\n--- Step 3: Get Order Audit Details ---")
    audit_result = lop_manager_instance.get_order_audit_details(order1["id"])
    print("Audit Result:", json.dumps(audit_result, indent=2))

    # Step 4: Simulate On-chain Order Submission and Execution
    print("\n--- Step 4: Simulate On-chain Order Submission and Execution ---")
    execution_result = lop_manager_instance.submit_order_on_chain_and_simulate_execution(order1["id"])
    print("Execution Result:", json.dumps(execution_result, indent=2))

    print("\n--- Step 5: List All Orders ---")
    all_orders = lop_manager_instance.list_all_orders()
    print("All Orders in LOPManager:", json.dumps(all_orders, indent=2))

    print("\n--- Step 6: Test Order Cancellation ---")
    order_2_prompt = "Generate a Solidity limit order smart contract that allows a user to sell 0.005 DAI (0x56aD9fB23C8A0B2C9030A9086A0F174a7D4E708E) for ETH (0xfFf9976782d46CC05630D1f6eB9Bc98210fBfCc5) at a specific price of 0.0003. The contract should include functions for order creation, cancellation by the creator (0xYourTestWalletIfNoPrivateKeyLoaded), and execution by another party when conditions are met. Ensure the contract safely handles ERC-20 token transfers and requires necessary approvals."
    order2 = lop_manager_instance.create_limit_order(order_2_prompt, "DAI", "ETH", 0.005, 0.0003)
    print("Order created for cancellation test:", json.dumps(order2, indent=2))
    
    cancellation_result = lop_manager_instance.cancel_order(order2["id"])
    print("Cancellation Result:", json.dumps(cancellation_result, indent=2))

    print("\n--- LOPManager Test Flow Finished ---")
