import requests
import json
import os
import time
from typing import Dict, Any, Optional, Union
import hashlib

# Web3.py imports
from web3 import Web3
from web3.middleware.proof_of_authority import ExtraDataToPOAMiddleware
from web3.exceptions import TransactionNotFound, TimeExhausted

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
    BASE_URL = "https://api.1inch.dev/swap/v5.2"

    def __init__(self, api_key: Optional[str] = None, chain_id: int = 1):
        """
        Initializes the OneInchAPI instance.
        1inch.dev API key is set from environment variables or directly passed arguments.
        The default chain_id is set to 1 (Ethereum Mainnet) for the ETHGlobal demo.

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
        """
        params = {
            "fromTokenAddress": from_token_address,
            "toTokenAddress": to_token_address,
            "amount": str(amount_wei),
            "fromAddress": from_address,
            "slippage": slippage,
            "disableEstimate": False
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
        Creates a new Limit Order using the 1inch Limit Order Protocol (Placeholder).
        """
        print("🔄 Requesting 1inch Limit Order creation...")
        print("⚠️ Limit Order creation requires a separate 1inch Limit Order API endpoint.")
        print("    Currently, this returns a dummy response for concept demonstration. Refer to API docs for actual implementation.")
        return {"status": "success", "message": "Limit Order created (dummy)", "order_data": order_data}

# --- Utility function for Web3.py transaction signing and sending ---
def send_onchain_transaction(w3: Web3, private_key: str, tx_data: Dict[str, Any], timeout_seconds: int = 300) -> str:
    """
    Signs and sends a built transaction data to the blockchain using Web3.py.
    """
    print("🚀 Starting on-chain transaction signing and sending...")
    try:
        required_fields = ['from', 'to', 'data', 'value', 'gas', 'gasPrice']
        for field in required_fields:
            if field not in tx_data:
                raise ValueError(f"Required transaction field '{field}' is missing.")

        if 'nonce' not in tx_data:
            tx_data['nonce'] = w3.eth.get_transaction_count(tx_data['from'])

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

# --- Global Wrapper Functions for API endpoints (with Mock Fallback) ---
def oneinch_swap(src_token: str, dst_token: str, amount: Union[int, str], from_address: str,
                 slippage: float = 1.0, disable_estimate: bool = False, allow_partial_fill: bool = False) -> Dict[str, Any]:
    try:
        api = OneInchAPI()
        return api.build_swap_transaction(src_token, dst_token, amount, from_address, slippage)
    except Exception as e:
        print(f"❌ oneinch_swap failed: {e}")
        print("⚠️ Returning MOCK swap response instead.")
        return {
            "status": "mock",
            "message": "⚠️ This is a mock swap response (API call failed)",
            "timestamp": int(time.time()),
            "mock": True,
            "src_token": src_token,
            "dst_token": dst_token,
            "amount": str(amount),
            "from_address": from_address,
            "slippage": slippage,
            "tx": {
                "to": "0x1111111254EEB25477B68fb85Ed929f73A960582",  # 1inch Router (Mainnet)
                "data": "0x" + hashlib.sha256(str(time.time()).encode()).hexdigest()[:128],
                "value": "0"
            },
            "estimated_gas": "150000",
            "route": [
                {"protocol": "MockSwap", "part": "100%", "fromToken": "WETH", "toToken": "USDC"}
            ]
        }

def oneinch_get_quote(src_token: str, dst_token: str, amount: Union[int, str]) -> Dict[str, Any]:
    try:
        api = OneInchAPI()
        return api.get_quote(src_token, dst_token, amount)
    except Exception as e:
        print(f"❌ oneinch_get_quote failed: {e}")
        print("⚠️ Returning MOCK quote response instead.")
        return {
            "status": "mock",
            "message": "⚠️ This is a mock quote response (API call failed)",
            "timestamp": int(time.time()),
            "mock": True,
            "src_token": src_token,
            "dst_token": dst_token,
            "amount": str(amount),
            "estimated_amount": "9999999999999999",
            "gas": "50000",
            "gas_price": "10000000000"
        }
