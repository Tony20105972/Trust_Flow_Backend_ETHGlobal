import requests
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime
import hashlib # For generating a consistent "dummy" hash

# Import userdata only in Colab environment.
try:
    from google.colab import userdata
except ImportError:
    # Print a warning only if not in Colab environment.
    print("⚠️ Could not import 'google.colab.userdata'. User data will not be available.")
    class UserDataMock:
        def get(self, key: str) -> Optional[str]:
            return None
    userdata = UserDataMock()

class IPFSUploader:
    """
    A class to upload JSON data or files to IPFS and return the CID (Content Identifier).
    It leverages the Pinata service for IPFS pinning.
    Includes a dummy mode for hackathon demonstrations when API keys are not set.
    """
    PINATA_JSON_UPLOAD_URL = "https://api.pinata.cloud/pinning/pinJSONToIPFS"
    PINATA_FILE_UPLOAD_URL = "https://api.pinata.cloud/pinning/pinFileToIPFS"
    REQUEST_TIMEOUT = 15 # Seconds to wait for a response

    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        """
        Initializes the IPFSUploader instance for Pinata.
        Pinata API key and secret are retrieved from:
        1. Directly passed arguments (`api_key`, `api_secret`).
        2. Google Colab secrets via `userdata.get('PINATA_API_KEY')` and `userdata.get('PINATA_SECRET_API_KEY')`.
        3. System environment variables via `os.getenv("PINATA_API_KEY")` and `os.getenv("PINATA_SECRET_API_KEY')`.
        If keys are not found, the uploader operates in a dummy mode.

        Args:
            api_key (Optional[str]): Pinata API Key.
            api_secret (Optional[str]): Pinata Secret API Key.
        """
        print("🛠️ Initializing IPFSUploader...")
        # Prioritize passed arguments, then Colab secrets, then OS environment variables.
        self.api_key: str = api_key or userdata.get('PINATA_API_KEY') or os.getenv("PINATA_API_KEY")
        self.api_secret: str = api_secret or userdata.get('PINATA_SECRET_API_KEY') or os.getenv("PINATA_SECRET_API_KEY")

        self.is_dummy_mode = False
        if not self.api_key or not self.api_secret:
            self.is_dummy_mode = True
            print("⚠️ No Pinata API Key or Secret found. Operating in DUMMY MODE for hackathon demo.")
            print("   → IPFS uploads will return mock CIDs. Set PINATA_API_KEY and PINATA_SECRET_API_KEY for real uploads.")
            self.headers = {} # No real headers needed in dummy mode
        else:
            self.headers = {
                "pinata_api_key": self.api_key,
                "pinata_secret_api_key": self.api_secret,
            }
            print("✅ IPFSUploader initialization complete (real mode).")

    def _generate_dummy_cid(self, data_content: str) -> str:
        """Generates a consistent mock IPFS CID based on the input data."""
        # IPFS CIDs usually start with 'Qm'. This simulates a common length.
        return "QmDUMMY" + hashlib.sha256(data_content.encode('utf-8')).hexdigest()[:37]

    def upload_json(self, data: Dict[str, Any], pin_name: Optional[str] = None) -> str:
        """
        Uploads JSON data to IPFS via Pinata and returns the CID (IpfsHash).
        In dummy mode, it returns a mock CID.

        Args:
            data (Dict[str, Any]): The JSON data dictionary to upload to IPFS.
            pin_name (Optional[str]): An optional name for the pin in Pinata's dashboard.

        Returns:
            str: The IPFS CID (IpfsHash) of the uploaded data.

        Raises:
            Exception: If an error occurs during the IPFS upload API call in real mode.
        """
        if self.is_dummy_mode:
            dummy_cid = self._generate_dummy_cid(json.dumps(data, sort_keys=True))
            print(f"✅ DUMMY MODE: JSON data simulated upload successful. Mock CID: {dummy_cid}")
            return dummy_cid
        
        print("🔄 Uploading JSON data to IPFS via Pinata...")
        try:
            payload = {
                "pinataContent": data
            }
            if pin_name:
                payload["pinataMetadata"] = {"name": pin_name}

            # Pinata JSON upload requires explicit Content-Type header
            json_headers = self.headers.copy()
            json_headers["Content-Type"] = "application/json"

            response = requests.post(self.PINATA_JSON_UPLOAD_URL, json=payload, headers=json_headers, timeout=self.REQUEST_TIMEOUT)
            response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)

            result = response.json()
            ipfs_hash = result.get("IpfsHash") # Pinata returns 'IpfsHash'

            if not ipfs_hash:
                raise Exception(f"Pinata JSON upload successful but 'IpfsHash' not found in response: {result}")

            print(f"✅ JSON data IPFS upload successful via Pinata. CID: {ipfs_hash}")
            return ipfs_hash
        except requests.exceptions.Timeout:
            print(f"❌ IPFS upload request timed out after {self.REQUEST_TIMEOUT} seconds.")
            raise Exception(f"IPFS upload request timed out.")
        except requests.exceptions.RequestException as e:
            print(f"❌ IPFS upload request failed: {e}")
            if e.response:
                print(f"   → Response status: {e.response.status_code}, message: {e.response.text}")
            raise Exception(f"IPFS upload request failed: {e}")
        except json.JSONDecodeError:
            print(f"❌ Failed to decode IPFS response JSON. Response: {response.text}")
            raise Exception("Failed to decode IPFS response JSON.")
        except Exception as e:
            print(f"❌ An unexpected error occurred during IPFS JSON upload: {type(e).__name__}: {e}")
            raise

    def upload_file(self, file_path: str, pin_name: Optional[str] = None) -> str:
        """
        Uploads a file to IPFS via Pinata and returns the CID.
        In dummy mode, it returns a mock CID.

        Args:
            file_path (str): The path to the file to upload.
            pin_name (Optional[str]): An optional name for the pin in Pinata's dashboard.<br>

        Returns:
            str: The IPFS CID (IpfsHash) of the uploaded file.<br>

        Raises:
            FileNotFoundError: If the specified file path does not exist.<br>
            Exception: If an error occurs during the IPFS file upload.
        """
        if self.is_dummy_mode:
            try:
                # Attempt to read file for dummy hash, but fallback to path if binary
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    file_content = f.read()
            except Exception:
                file_content = file_path # Use path if file cannot be read as text
            dummy_cid = self._generate_dummy_cid(file_content)
            print(f"✅ DUMMY MODE: File '{file_path}' simulated upload successful. Mock CID: {dummy_cid}")
            return dummy_cid

        print(f"🔄 Uploading file '{file_path}' to IPFS via Pinata...")
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found at: '{file_path}'")

            with open(file_path, 'rb') as f:
                # Pinata file upload uses multipart/form-data.
                files = {'file': (os.path.basename(file_path), f, 'application/octet-stream')}

                # Pinata allows adding metadata for file uploads via the options JSON.
                options = {}
                if pin_name:
                    options['pinataMetadata'] = {'name': pin_name}
                
                # Convert options to JSON string if not empty, for 'pinataOptions' form field
                data_fields = {'pinataOptions': json.dumps(options)} if options else {}

                # For file uploads, Content-Type is multipart/form-data and managed by requests.
                # We only need the API keys in headers, which self.headers already contains.
                response = requests.post(self.PINATA_FILE_UPLOAD_URL, files=files, data=data_fields, headers=self.headers, timeout=self.REQUEST_TIMEOUT)
                response.raise_for_status()
                result = response.json()
                ipfs_hash = result.get("IpfsHash")

                if not ipfs_hash:
                    raise Exception(f"Pinata file upload successful but 'IpfsHash' not found in response: {result}")

                print(f"✅ File IPFS upload successful via Pinata. CID: {ipfs_hash}")
                return ipfs_hash
        except FileNotFoundError as e:
            print(f"❌ File not found error: {e}")
            raise
        except requests.exceptions.Timeout:
            print(f"❌ IPFS file upload request timed out after {self.REQUEST_TIMEOUT} seconds.")
            raise Exception(f"IPFS file upload request timed out.")
        except requests.exceptions.RequestException as e:
            print(f"❌ IPFS file upload request failed: {e}")
            if e.response:
                print(f"   → Response status: {e.response.status_code}, message: {e.response.text}")
            raise Exception(f"IPFS file upload request failed: {e}")
        except Exception as e:
            print(f"❌ An unexpected error occurred during IPFS file upload: {type(e).__name__}: {e}")
            raise


# --- Integrated Test Code ---
if __name__ == "__main__":
    print("\n--- IPFSUploader Test Script Start (Pinata) ---")

    # To run this script in REAL MODE, you need a free Pinata API Key and Secret.
    # 1. Visit https://www.pinata.cloud/ and sign up/log in.
    # 2. Go to "API Keys" in your dashboard.
    # 3. Create a new key. You will get both an API Key and a Secret API Key. Copy them.
    # 4. Set them as environment variables or Colab secrets.
    #    Example for environment variables (Bash/Zsh):
    #    export PINATA_API_KEY="YOUR_ACTUAL_PINATA_API_KEY_HERE"<br>
    #    export PINATA_SECRET_API_KEY="YOUR_ACTUAL_PINATA_SECRET_API_KEY_HERE"
    #    Then run your script from the same terminal.
    #    For Windows (PowerShell):
    #    $env:PINATA_API_KEY="YOUR_ACTUAL_PINATA_API_KEY_HERE"<br>
    #    $env:PINATA_SECRET_API_KEY="YOUR_ACTUAL_PINATA_SECRET_API_KEY_HERE"
    #    For Google Colab: Go to the "Secrets" tab (key icon) on the left sidebar
    #    and add two new secrets:
    #    - Name: 'PINATA_API_KEY', Value: 'YOUR_ACTUAL_PINATA_API_KEY'
    #    - Name: 'PINATA_SECRET_API_KEY', Value: 'YOUR_ACTUAL_PINATA_SECRET_API_KEY'
    #    Make sure "Notebook access" is enabled for both secrets.

    try:
        uploader_test = IPFSUploader() # Use a different name for test instance

        # Test JSON data for contract report
        test_contract_report_data = {
            "name": "Hackathon Contract Report",
            "description": "This is an automated report for a smart contract deployed during the ETHGlobal Seoul hackathon.",
            "attributes": [
                {"trait_type": "Contract Type", "value": "ERC20"},
                {"trait_type": "Deployment Chain", "value": "Etherlink Ghostnet"},
                {"trait_type": "AI Generated", "value": "True"}
            ],
            "report_id": "mock_report_12345",
            "timestamp": datetime.utcnow().isoformat()
        }

        print("\n[Test: JSON Data Upload for Contract Report]")
        # pin_name helps identify the pin in Pinata's web UI.
        ipfs_cid_contract_report = uploader_test.upload_json(test_contract_report_data, pin_name="ContractReport-ETHGlobalSeoul")
        print(f"Generated IPFS CID (Contract Report JSON): {ipfs_cid_contract_report}")
        # Pinata's general gateway link
        print(f"Pinata Gateway Link (Contract Report): https://gateway.pinata.cloud/ipfs/{ipfs_cid_contract_report}")

        # Test JSON data for NFT metadata
        nft_metadata = {
            "name": "Deployment Proof NFT",
            "description": "This NFT serves as a verifiable proof of a smart contract deployment, linked to an on-chain report.",
            "image": "ipfs://QmbnK6mR4S3L9w3Y1N7j2G1f5Q2X3E4C5D6F7G8H9I0J1", # Placeholder for actual image CID
            "external_url": f"https://gateway.pinata.cloud/ipfs/{ipfs_cid_contract_report}", # Link to the uploaded contract report
            "attributes": [
                {"trait_type": "Report CID", "value": ipfs_cid_contract_report},
                {"trait_type": "Contract Address", "value": "0xABC..."}, # Placeholder for actual contract address
                {"trait_type": "Deployed By", "value": "Samantha OS AI"}
            ]
        }
        print("\n[Test: NFT Metadata Upload]")
        ipfs_cid_nft_metadata = uploader_test.upload_json(nft_metadata, pin_name="NFTMetadata-DeploymentProof")
        print(f"Generated IPFS CID (NFT Metadata): {ipfs_cid_nft_metadata}")
        print(f"Pinata Gateway Link (NFT Metadata): https://gateway.pinata.cloud/ipfs/{ipfs_cid_nft_metadata}")
        print("✅ IPFS JSON uploads test successful.")

        # --- Test: File Upload ---
        print("\n[Test: File Upload]")
        # Create a temporary text file for testing
        temp_file_path = "test_document_for_pinata.txt"
        with open(temp_file_path, "w") as f:
            f.write("This is a test document uploaded via Pinata.\n")
            f.write(f"Upload timestamp: {datetime.now().isoformat()}\n")
        try:
            file_cid = uploader_test.upload_file(temp_file_path, pin_name="MyTestDocument")
            print(f"Generated File CID: {file_cid}")
            print(f"Pinata Gateway Link (File): https://gateway.pinata.cloud/ipfs/{file_cid}")
            print("✅ IPFS File upload test successful.")
        except Exception as e:
            print(f"❌ IPFS File upload test failed: {e}")
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path) # Clean up the temporary file

    except Exception as e: # Catching general Exception to make the dummy mode message clearer
        # If the ValueError from __init__ happens, it will be caught here
        # and print a clear message.<br>
        print(f"❌ An unexpected error occurred during IPFSUploader test: {e}")
        if "Pinata API KEY or SECRET is not set" in str(e):
            print("   → The script might be in an environment where API keys are expected but not found.")

    print("\n--- IPFSUploader Test Script End (Pinata) ---")

# ✅ 전역으로 Uploader 인스턴스 생성 (api.py에서 사용할 인스턴스)
ipfs_uploader_instance = IPFSUploader()

def upload_to_ipfs(file_content: str, file_name: str) -> str:
    """
    Dummy IPFS upload function for Hackathon demo.
    It calls the upload_json method of the global IPFSUploader instance.
    """
    # 현재 file_content는 문자열로 가정하고, JSON 데이터로 처리하여 업로드합니다.
    # 실제 파일 업로드 시에는 `ipfs_uploader_instance.upload_file`을 사용해야 합니다.
    # 여기서는 간단한 더미 JSON으로 변환하여 `upload_json`을 호출합니다.
    dummy_data = {
        "fileName": file_name,
        "contentSnippet": file_content[:100] + "..." if len(file_content) > 100 else file_content,
        "timestamp": datetime.utcnow().isoformat(),
        "type": "dummy_upload_from_api_endpoint"
    }
    
    print(f"📦 [IPFS] Request to upload {file_name}. Calling upload_json with dummy data.")
    return ipfs_uploader_instance.upload_json(dummy_data, pin_name=f"API_Upload-{file_name}")
