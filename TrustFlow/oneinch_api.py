# oneinch_api.py
import requests
import json
import os
import time # For generating unique salt in limit order
from typing import Dict, Any, Optional, Union

# Web3.py imports for on-chain transaction sending
from web3 import Web3
from web3.middleware.proof_of_authority import ExtraDataToPOAMiddleware
from web3.exceptions import TransactionNotFound, TimeExhausted # Removed ContractLogicError
# Removed from web3.constants import MAX_UINT256

# Import userdata for Google Colab environment
try:
    from google.colab import userdata
except ImportError:
    class UserDataMock:
        def get(self, key: str) -> Optional[str]:
            print(f"⚠️ 'google.colab.userdata' could not be imported. User data for '{key}' is not available.")
            return None
    userdata = UserDataMock()

class OneInchAPI:
    """
    Wrapper class for interacting with the 1inch DeFi Aggregator API.
    Provides functionalities for token price quotes, building swap transactions,
    building ERC20 approval transactions, and creating limit orders.
    """
    # Base URL for 1inch Swap API v5.2
    # Note: For hackathon demo, you might use Ethereum Mainnet (chain_id=1) or a testnet like Sepolia.
    # Etherlink might not be directly supported by 1inch API yet.
    BASE_URL = "https://api.1inch.dev/swap/v5.2"

    def __init__(self, api_key: Optional[str] = None, chain_id: int = 1):
        """
        Initializes the OneInchAPI instance.
        1inch.dev API key is set from environment variables or directly passed arguments.

        Args:
            api_key (Optional[str]): 1inch.dev API Key.
            chain_id (int): The Chain ID of the blockchain network to use (e.g., Ethereum Mainnet: 1, Sepolia: 11155111).

        Raises:
            ValueError: If ONEINCH_API_KEY is not set.
        """
        print("🛠️ Initializing OneInchAPI...")
        self.api_key: str = api_key or userdata.get('ONEINCH_API_KEY') or os.getenv("ONEINCH_API_KEY")
        self.chain_id = chain_id

        if not self.api_key:
            raise ValueError(
                "❌ ONEINCH_API_KEY environment variable is not set. "
                "Please add your 1inch.dev API key to Colab secrets or system environment variables."
            )
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
        print(f"✅ OneInchAPI initialized successfully (Chain ID: {self.chain_id}).")

    def set_chain_id(self, new_chain_id: int) -> None:
        """
        Changes the Chain ID of the blockchain network to be used for API calls.
        This is useful for switching between different chains like Etherlink.

        Args:
            new_chain_id (int): The new Chain ID of the blockchain network.
        """
        self.chain_id = new_chain_id
        print(f"🔄 Chain ID changed to {self.chain_id}.")

    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None, method: str = "GET", data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Internal helper function: performs a request to the 1inch API."""
        url = f"{self.BASE_URL}/{self.chain_id}/{endpoint}"
        print(f"🔄 1inch API call: {method} {url} (params: {params}, data: {data})")
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers, params=params)
            elif method == "POST":
                # For POST requests, ensure headers include Content-Type: application/json if sending JSON body
                post_headers = self.headers.copy()
                post_headers["Content-Type"] = "application/json"
                response = requests.post(url, headers=post_headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ 1inch API request failed: {e}")
            if e.response is not None:
                print(f"    → Response Status: {e.response.status_code}, Message: {e.response.text}")
            raise Exception(f"1inch API request failed: {e}")
        except json.JSONDecodeError:
            print(f"❌ 1inch API response JSON decoding failed. Response: {response.text}")
            raise Exception("1inch API response JSON decoding failed.")
        except Exception as e:
            print(f"❌ Unexpected error during 1inch API call: {type(e).__name__}: {e}")
            raise

    def get_quote(self, from_token_address: str, to_token_address: str, amount_wei: Union[int, str]) -> Dict[str, Any]:
        """
        Retrieves a swap quote for a given token amount.

        Args:
            from_token_address (str): Contract address of the token to swap from.
            to_token_address (str): Contract address of the token to receive.
            amount_wei (Union[int, str]): Amount of `from_token` to swap (in Wei units).

        Returns:
            Dict[str, Any]: The quote response from the 1inch API.
        """
        params = {
            "fromTokenAddress": from_token_address,
            "toTokenAddress": to_token_address,
            "amount": str(amount_wei)
        }
        quote_data = self._make_request("quote", params)
        print(f"✅ 1inch Quote successful. Estimated '{to_token_address}' amount: {quote_data.get('toTokenAmount', 'N/A')}")
        return quote_data

    def build_swap_transaction(self, from_token_address: str, to_token_address: str,
                               amount_wei: Union[int, str], from_address: str, slippage: float = 1.0) -> Dict[str, Any]:
        """
        Builds the transaction data for an actual on-chain swap.

        Args:
            from_token_address (str): Contract address of the token to swap from.
            to_token_address (str): Contract address of the token to receive.
            amount_wei (Union[int, str]): Amount of `from_token` to swap (in Wei units).
            from_address (str): Wallet address performing the swap.
            slippage (float): Permissible slippage percentage (0.1 to 50.0). (Default: 1.0)

        Returns:
            Dict[str, Any]: Transaction data that can be signed and sent.
        """
        params = {
            "fromTokenAddress": from_token_address,
            "toTokenAddress": to_token_address,
            "amount": str(amount_wei),
            "fromAddress": from_address,
            "slippage": slippage,
            "disableEstimate": False # Whether to get gas estimates (true increases risk of failure)
        }
        swap_tx_data = self._make_request("swap", params)
        print(f"✅ 1inch Swap transaction build successful. Data: {swap_tx_data.get('tx', {}).get('data', 'N/A')[:50]}...")
        return swap_tx_data

    def get_approve_spender(self) -> Dict[str, str]:
        """
        Retrieves the spender address that the 1inch router needs to be approved to use tokens
        before an ERC20 swap.
        """
        spender_data = self._make_request("approve/spender")
        print(f"✅ 1inch Approve Spender address: {spender_data.get('address', 'N/A')}")
        return spender_data

    def build_approve_transaction(self, token_address: str, amount_wei: Union[int, str]) -> Dict[str, Any]:
        """
        Builds the transaction data for an ERC20 token approval.
        This transaction needs to be signed and sent to grant the 1inch router
        permission to use a specific amount of tokens.

        Args:
            token_address (str): Contract address of the ERC20 token to approve.
            amount_wei (Union[int, str]): Amount of tokens to approve (in Wei units).
                                         Use a very large number for unlimited approval.

        Returns:
            Dict[str, Any]: Transaction data that can be signed and sent for approval.
        """
        params = {
            "tokenAddress": token_address,
            "amount": str(amount_wei)
        }
        approve_tx_data = self._make_request("approve/transaction", params)
        print(f"✅ 1inch Approve transaction build successful. Data: {approve_tx_data.get('data', 'N/A')[:50]}...")
        return approve_tx_data

    def create_limit_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a new Limit Order using the 1inch Limit Order Protocol.
        This is an off-chain signed message, not an on-chain transaction.
        The created order needs to be submitted to the 1inch Limit Order Relay.

        Args:
            order_data (Dict[str, Any]): Order data in the format required by the 1inch Limit Order API.
                                         (e.g., makerAddress, takerAddress, makerAsset, takerAsset,
                                         makerAmount, takerAmount, salt, interaction, signature, etc.)

        Returns:
            Dict[str, Any]: Response to the Limit Order creation request.

        Note:
            The 1inch Limit Order API uses different endpoints and potentially different authentication
            compared to the Swap API. This function is a placeholder for demonstration.
            For actual implementation, refer to the 1inch.dev Limit Order documentation.
            (e.g., POST to /limit-order/v3/submit or similar).
        """
        print("🔄 Requesting 1inch Limit Order creation...")
        # Placeholder for actual Limit Order API endpoint.
        # This might be a POST request to a different base URL or endpoint.
        # For demonstration, we'll simulate a successful response.
        print("⚠️ Limit Order creation requires a separate 1inch Limit Order API endpoint.")
        print("    Currently, this returns a dummy response for concept demonstration. Refer to API docs for actual implementation.")
        # Example of how an actual call might look if a POST endpoint existed:
        # return self._make_request("limit-order/v3/submit", method="POST", data=order_data)
        return {"status": "success", "message": "Limit Order created (dummy)", "order_data": order_data}


# --- Utility function for Web3.py transaction signing and sending ---
# This function is general-purpose and could be moved to a separate blockchain_utils.py
# for better modularity in a larger project. It's included here for demonstration
# of sending 1inch-built transactions.
def send_onchain_transaction(w3: Web3, private_key: str, tx_data: Dict[str, Any], timeout_seconds: int = 300) -> str:
    """
    Signs and sends a built transaction data to the blockchain using Web3.py.

    Args:
        w3 (Web3): Initialized Web3 instance.
        private_key (str): Private key (with 0x prefix) to sign the transaction.
        tx_data (Dict[str, Any]): Dictionary of transaction data built by 1inch API or similar.
                                  (Expected to contain 'from', 'to', 'data', 'value', 'gas', 'gasPrice', 'nonce' (optional))
        timeout_seconds (int): Maximum time (in seconds) to wait for the transaction receipt.

    Returns:
        str: The transaction hash (with 0x prefix) of the sent transaction.

    Raises:
        ValueError: If required transaction fields are missing.
        AttributeError: If raw_transaction is not found in the signed transaction object.
        TransactionNotFound: If transaction receipt is not found or timed out.
        TimeExhausted: If waiting for transaction receipt exceeds the timeout.
        Exception: For any other unexpected errors.
    """
    print("🚀 Starting on-chain transaction signing and sending...")
    try:
        # Validate required transaction fields
        required_fields = ['from', 'to', 'data', 'value', 'gas', 'gasPrice']
        for field in required_fields:
            if field not in tx_data:
                raise ValueError(f"Required transaction field '{field}' is missing.")

        # If nonce is not provided, get the next nonce for the account
        if 'nonce' not in tx_data:
            tx_data['nonce'] = w3.eth.get_transaction_count(tx_data['from'])

        # Create Web3.py transaction object
        # Use the content of the 'tx' field returned by 1inch API directly.
        transaction = {
            'from': w3.to_checksum_address(tx_data['from']),
            'to': w3.to_checksum_address(tx_data['to']),
            'data': tx_data['data'],
            'value': int(tx_data['value']),
            'gas': int(tx_data['gas']),
            'gasPrice': int(tx_data['gasPrice']),
            'nonce': tx_data['nonce']
        }

        signed_tx = w3.eth.account.sign_transaction(transaction, private_key)
        raw_tx = getattr(signed_tx, "raw_transaction", None) or getattr(signed_tx, "rawTransaction", None)

        if raw_tx is None:
            raise AttributeError("❌ Could not find 'raw_transaction' or 'rawTransaction' attribute in web3 SignedTransaction object.")

        tx_hash = w3.eth.send_raw_transaction(raw_tx)
        print(f"    → Transaction sent. Hash: {tx_hash.hex()}")

        # Wait for receipt
        # Use a shorter poll_latency for local testing, longer for real networks
        poll_latency = 0.5 if "127.0.0.1" in w3.provider.endpoint_uri or "localhost" in w3.provider.endpoint_uri else 5
        print(f"    → Waiting for transaction receipt (max {timeout_seconds}s, polling every {poll_latency}s)...")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout_seconds, poll_latency=poll_latency)

        if receipt.status != 1:
            raise RuntimeError(f"❌ Transaction failed. Receipt:\n{json.dumps(dict(receipt), indent=2, default=str)}")

        print(f"✅ Transaction successful. Block Number: {receipt.blockNumber}")
        return tx_hash.hex()

    except (TransactionNotFound, TimeExhausted) as e:
        print(f"❌ Transaction receipt wait error: {e}")
        raise
    except Exception as e:
        print(f"❌ Unexpected error during on-chain transaction sending: {type(e).__name__}: {e}")
        raise


# --- Integrated Test Code ---
if __name__ == "__main__":
    print("\n--- OneInchAPI Test Script Start ---")

    # --- Configuration for testing ---
    # Set these environment variables or ensure they are in a .env file:
    # ONEINCH_API_KEY="YOUR_1INCH_DEV_API_KEY"
    # PRIVATE_KEY="0xYOUR_MUMBAI_TESTNET_PRIVATE_KEY"
    # MUMBAI_RPC_URL="https://polygon-mumbai.g.alchemy.com/v2/YOUR_ALCHEMY_KEY"
    # (or "https://rpc-mumbai.maticvigil.com" etc.)

    # Polygon Mumbai Testnet Token Addresses (Examples)
    WMATIC_MUMBAI = "0x9c3C9283D3e053f3B0289aE8462Bf39d1c68d032" # Wrapped MATIC
    USDC_MUMBAI = "0x0FA8781a83E4682d4Be494d27463a9e8D9d29ae7" # USDC (Note: Testnet addresses can change, verify!)

    # Etherlink Ghostnet (Tezos) Chain ID (Example, if supported by 1inch)
    # 1inch API might not directly support Etherlink. This is for concept demo.
    ETHERLINK_GHOSTNET_CHAIN_ID = 123123 # Placeholder for actual Etherlink Chain ID
    ETHERLINK_GHOSTNET_RPC_URL = "https://node.ghostnet.etherlink.com" # Placeholder RPC

    # --- Web3.py Initialization (for sending transactions) ---
    test_private_key = os.getenv("PRIVATE_KEY")
    test_rpc_url = os.getenv("MUMBAI_RPC_URL") # Or ETHERLINK_GHOSTNET_RPC_URL for Etherlink tests

    w3_instance: Optional[Web3] = None
    test_wallet_address: str = "0x0000000000000000000000000000000000000000"

    if not test_private_key or not test_rpc_url:
        print("❌ PRIVATE_KEY or MUMBAI_RPC_URL environment variables are not set. Skipping Web3 tests.")
        # Set dummy values for non-Web3 tests to proceed
        test_private_key = "0x0000000000000000000000000000000000000000000000000000000000000001"
        test_rpc_url = "http://127.0.0.1:8545" # Anvil local RPC
    else:
        try:
            w3_instance = Web3(Web3.HTTPProvider(test_rpc_url))
            # Inject PoA middleware for networks like Etherlink
            w3_instance.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
            if not w3_instance.is_connected():
                print(f"❌ Web3 RPC connection failed: {test_rpc_url}. Skipping Web3 tests.")
                w3_instance = None # Ensure it's None if connection fails
            else:
                test_wallet_address = w3_instance.eth.account.from_key(test_private_key).address
                print(f"✅ Web3 connected successfully. Test wallet address: {test_wallet_address}")
        except Exception as e:
            print(f"❌ Error initializing Web3: {e}. Skipping Web3 tests.")
            w3_instance = None


    try:
        # 1inch API instance creation (defaulting to Ethereum Mainnet if chain_id not specified)
        # For Polygon Mumbai, explicitly set chain_id=137
        oneinch_api = OneInchAPI(chain_id=137)

        # --- Test 1: get_quote (Price Quote) ---
        print("\n--- Test 1: get_quote (Price Quote) ---")
        amount_to_swap_wei = int(0.01 * (10**18)) # 0.01 WMATIC (18 decimals)
        try:
            quote_result = oneinch_api.get_quote(WMATIC_MUMBAI, USDC_MUMBAI, amount_to_swap_wei)
            print("Quote Result:")
            print(json.dumps(quote_result, indent=2))
            if "toTokenAmount" in quote_result:
                # USDC typically has 6 decimals
                print(f"    → Expected USDC for {amount_to_swap_wei / (10**18)} WMATIC: {int(quote_result['toTokenAmount']) / (10**6):.4f} USDC")
            print("✅ get_quote test successful.")
        except Exception as e:
            print(f"❌ get_quote test failed: {e}")

        # --- Test 2: set_chain_id (Change Chain) ---
        print("\n--- Test 2: set_chain_id (Change Chain) ---")
        oneinch_api.set_chain_id(ETHERLINK_GHOSTNET_CHAIN_ID)
        print(f"Current 1inch API Chain ID: {oneinch_api.chain_id}")
        # If Etherlink is supported, you could test quote/swap with Etherlink tokens here
        print("✅ set_chain_id test successful (Chain ID change confirmed).")
        # Change back to Mumbai for subsequent tests
        oneinch_api.set_chain_id(137)


        # --- Test 3: build_approve_transaction (Build Approve Transaction) ---
        print("\n--- Test 3: build_approve_transaction (Build Approve Transaction) ---")
        # Build an Approve transaction for WMATIC to allow 1inch router unlimited spending
        # Use a very large number for unlimited approval, or a specific amount
        amount_to_approve_wei = str(2**256 - 1) # Unlimited approval using a large integer
        # amount_to_approve_wei = int(1 * (10**18)) # 1 WMATIC approval
        approve_tx_data_built: Optional[Dict[str, Any]] = None
        try:
            approve_tx_data_built = oneinch_api.build_approve_transaction(WMATIC_MUMBAI, amount_to_approve_wei)
            print("Approve Transaction Data:")
            print(json.dumps(approve_tx_data_built, indent=2))
            print("✅ build_approve_transaction test successful.")
        except Exception as e:
            print(f"❌ build_approve_transaction test failed: {e}")


        # --- Test 4: build_swap_transaction (Build Swap Transaction) ---
        print("\n--- Test 4: build_swap_transaction (Build Swap Transaction) ---")
        swap_tx_data_built: Optional[Dict[str, Any]] = None
        try:
            swap_tx_data_built = oneinch_api.build_swap_transaction(
                WMATIC_MUMBAI,
                USDC_MUMBAI,
                amount_to_swap_wei,
                test_wallet_address, # Your wallet address
                slippage=1.0
            )
            print("Swap Transaction Data:")
            print(json.dumps(swap_tx_data_built, indent=2))
            print("✅ build_swap_transaction test successful.")
        except Exception as e:
            print(f"❌ build_swap_transaction test failed: {e}")


        # --- Test 5: send_onchain_transaction (Actual On-chain Send - Approve) ---
        # This test will consume gas and record a transaction on the blockchain.
        # Ensure your wallet has enough MATIC (or native token of the chain) before running.
        print("\n--- Test 5: send_onchain_transaction (Actual On-chain Send - Approve) ---")
        if w3_instance and test_private_key and approve_tx_data_built and test_wallet_address != "0x0000000000000000000000000000000000000000":
            try:
                print(f"    → Attempting to send Approve transaction from wallet ({test_wallet_address})...")
                # Use the 'tx' field from the built data
                approve_tx_hash = send_onchain_transaction(w3_instance, test_private_key, approve_tx_data_built['tx'])
                print(f"✅ Approve transaction sent successfully. Hash: {approve_tx_hash}")
            except Exception as e:
                print(f"❌ Approve transaction send failed: {e}")
                print("    → Check wallet balance, network connection, private key validity.")
        else:
            print("    → Skipping Approve transaction send test (Web3 not initialized or data missing).")


        # --- Test 6: send_onchain_transaction (Actual On-chain Send - Swap) ---
        # This test will consume gas and record a transaction on the blockchain.
        # Ensure your wallet has enough WMATIC and that approval is completed before running.
        print("\n--- Test 6: send_onchain_transaction (Actual On-chain Send - Swap) ---")
        if w3_instance and test_private_key and swap_tx_data_built and test_wallet_address != "0x0000000000000000000000000000000000000000":
            try:
                print(f"    → Attempting to send Swap transaction from wallet ({test_wallet_address})...")
                # Use the 'tx' field from the built data
                swap_tx_hash = send_onchain_transaction(w3_instance, test_private_key, swap_tx_data_built['tx'])
                print(f"✅ Swap transaction sent successfully. Hash: {swap_tx_hash}")
            except Exception as e:
                print(f"❌ Swap transaction send failed: {e}")
                print("    → Check wallet balance, network connection, private key validity, and token approval status.")
        else:
            print("    → Skipping Swap transaction send test (Web3 not initialized or data missing).")


        # --- Test 7: create_limit_order (Limit Order Creation - Concept Demo) ---
        print("\n--- Test 7: create_limit_order (Limit Order Creation - Concept Demo) ---")
        # Limit Orders are part of a separate 1inch protocol and require specific signing logic.
        # This is a concept demonstration using dummy data.
        mock_limit_order_data = {
            "makerAddress": test_wallet_address,
            "takerAddress": "0x0000000000000000000000000000000000000000", # Taker (0x0 for anyone)
            "makerAsset": WMATIC_MUMBAI,
            "takerAsset": USDC_MUMBAI,
            "makerAmount": str(int(0.005 * (10**18))), # 0.005 WMATIC
            "takerAmount": str(int(15 * (10**6))),      # 15 USDC
            "salt": str(Web3.to_int(Web3.keccak(text=str(time.time())).hex())), # Unique salt - PATCHED HERE
            "expiresIn": 3600, # Expires in 1 hour (seconds)
            # Actual Limit Orders require EIP-712 signature here.
            "signature": "0x..." # Placeholder for actual signature data
        }
        try:
            limit_order_result = oneinch_api.create_limit_order(mock_limit_order_data)
            print("Limit Order Creation Result:")
            print(json.dumps(limit_order_result, indent=2))
            print("✅ create_limit_order test successful (concept demonstration).")
            print("    💡 Note: Actual 1inch Limit Orders involve more complex signing and submission logic. Refer to 1inch.dev documentation.")
        except Exception as e:
            print(f"❌ create_limit_order test failed: {e}")


    except ValueError as e:
        print(f"❌ OneInchAPI initialization failed: {e}")
        print("    → Please ensure your 1inch.dev API key is correctly set.")
    except Exception as e:
        print(f"❌ Unexpected error during OneInchAPI test: {e}")

    print("\n--- OneInchAPI Test Script End ---")


# --- Global Wrapper Functions for API endpoints ---
def oneinch_swap(src_token: str, dst_token: str, amount: Union[int, str], from_address: str,
                 slippage: float = 1.0, disable_estimate: bool = False, allow_partial_fill: bool = False) -> Dict[str, Any]:
    """
    Wrapper for OneInchAPI.build_swap_transaction (Hackathon demo).
    Uses ONEINCH_API_KEY from environment.
    """
    try:
        api = OneInchAPI()
        return api.build_swap_transaction(src_token, dst_token, amount, from_address, slippage)
    except Exception as e:
        print(f"❌ oneinch_swap failed: {e}")
        return {"status": "error", "message": str(e)}

def oneinch_get_quote(src_token: str, dst_token: str, amount: Union[int, str]) -> Dict[str, Any]:
    """
    Wrapper for OneInchAPI.get_quote (Hackathon demo).
    Uses ONEINCH_API_KEY from environment.
    """
    try:
        api = OneInchAPI()
        return api.get_quote(src_token, dst_token, amount)
    except Exception as e:
        print(f"❌ oneinch_get_quote failed: {e}")
        return {"status": "error", "message": str(e)}
