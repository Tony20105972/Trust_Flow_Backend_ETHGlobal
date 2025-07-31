import re
from typing import Dict, Any, List
import json

class ZKOracleDetector:
    """
    Detects ZK, Oracle, and KYC related patterns in Solidity smart contract code.
    Acts as an AS-lite (AgentSecure) role to pre-check for "risk flags" or advanced feature usage.
    """
    def __init__(self):
        # Regex patterns and descriptions for each category
        self.patterns = {
            "ZK_Features": {
                "keywords": [
                    r"zkSNARK", r"zk-SNARK", r"plonk", r"groth16", # ZK algorithm names
                    r"verifier", r"verifyProof", r"proof", r"publicInputs", # ZK proof-related terms
                    r"bellman", r"sapling" # ZK library/protocol related
                ],
                "description": "Potential use of ZK (Zero-Knowledge) proofs or related technologies detected. This may indicate features for privacy, scalability, or trust minimization."
            },
            "Oracle_Integration": {
                "keywords": [
                    r"chainlink", r"priceFeed", r"AggregatorV3Interface", # Chainlink Oracle
                    r"VRFConsumerBase", r"DataFeed", r"oracle", # General oracle interfaces/terms
                    r"i_coordinator", r"getRandomNumber" # Chainlink VRF
                ],
                "description": "Integration with external data oracles (e.g., Chainlink) detected. This can be used to bring off-chain information such as real-time price data or randomness onto the blockchain."
            },
            "KYC_AML_Compliance": {
                "keywords": [
                    r"KYC", r"AML", r"whitelist", r"blacklist", r"identity",
                    r"kycRequired", r"isVerified", r"restrictAccess"
                ],
                "description": "KYC (Know Your Customer), AML (Anti-Money Laundering), or other identity/regulatory compliance features detected. This may restrict or allow access to specific user groups."
            }
        }

    def scan_code(self, solidity_code: str) -> Dict[str, Any]:
        """
        Detects ZK, Oracle, and KYC related patterns in Solidity code and returns detailed results.

        Args:
            solidity_code (str): The Solidity code string to scan.

        Returns:
            Dict[str, Any]: A dictionary containing detection status and detailed descriptions for each category.
                            Example: {
                                "ZK_Features": {"detected": True, "reason": "Potential use of ZK (Zero-Knowledge) proofs..."},
                                "Oracle_Integration": {"detected": False, "reason": "Pattern not detected"},
                                "KYC_AML_Compliance": {"detected": False, "reason": "Pattern not detected"}
                            }
        """
        findings = {}
        for category, info in self.patterns.items():
            detected = False
            matched_keywords = []
            for pattern_str in info["keywords"]:
                # re.IGNORECASE: case-insensitive, re.MULTILINE: matches across multiple lines
                if re.search(pattern_str, solidity_code, re.IGNORECASE | re.MULTILINE):
                    detected = True
                    # Remove 'r"' from regex string for cleaner output
                    matched_keywords.append(pattern_str.strip('r"'))

            findings[category] = {
                "detected": detected,
                "reason": info["description"] if detected else "Pattern not detected in the code.",
                "matched_patterns": matched_keywords if detected else []
            }
        return findings

# --- Integrated Test Code ---
if __name__ == "__main__":
    print("\n--- ZKOracleDetector Test Script Start ---") # English translation

    detector_test = ZKOracleDetector() # Use a different name for test instance to avoid conflict

    # Test Case 1: Detect ZK patterns
    zk_code = """
    pragma solidity ^0.8.0;
    contract MyZKVerifier {
        function verifyProof(uint[] memory publicInputs, uint[] memory proof) public pure returns (bool) {
            // Some zkSNARK verification logic here
            return true;
        }
    }
    """
    print("\n[Test: ZK Pattern Detection]") # English translation
    zk_results = detector_test.scan_code(zk_code)
    # Ensure json.dumps outputs standard ASCII (no need for ensure_ascii=False for English)
    print(json.dumps(zk_results, indent=2))
    assert zk_results["ZK_Features"]["detected"] == True
    print("✅ ZK pattern detection test successful.") # English translation

    # Test Case 2: Detect Oracle patterns
    oracle_code = """
    pragma solidity ^0.8.0;
    import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";
    contract PriceConsumer {
        AggregatorV3Interface internal priceFeed;
        constructor() {
            priceFeed = AggregatorV3Interface(0x...); // Chainlink Goerli ETH/USD
        }
        function getLatestPrice() public view returns (int) {
            (uint80 roundID, int price, uint startedAt, uint timeStamp, uint80 answeredInRound) = priceFeed.latestRoundData();
            return price;
        }
    }
    """
    print("\n[Test: Oracle Pattern Detection]") # English translation
    oracle_results = detector_test.scan_code(oracle_code)
    print(json.dumps(oracle_results, indent=2))
    assert oracle_results["Oracle_Integration"]["detected"] == True
    print("✅ Oracle pattern detection test successful.") # English translation

    # Test Case 3: Detect KYC patterns
    kyc_code = """
    pragma solidity ^0.8.0;
    contract RestrictedAccess {
        mapping(address => bool) public whitelist;
        bool public kycRequired = true;

        modifier onlyWhitelisted() {
            require(whitelist[msg.sender] == true, "Not whitelisted.");
            _;
        }

        function addAddressToWhitelist(address _addr) public {
            whitelist[_addr] = true;
        }

        function doSomethingRestricted() public onlyWhitelisted {
            // ... sensitive operation
        }
    }
    """
    print("\n[Test: KYC Pattern Detection]") # English translation
    kyc_results = detector_test.scan_code(kyc_code)
    print(json.dumps(kyc_results, indent=2))
    assert kyc_results["KYC_AML_Compliance"]["detected"] == True
    print("✅ KYC pattern detection test successful.") # English translation

    # Test Case 4: No patterns
    clean_code = """
    pragma solidity ^0.8.0;
    contract SimpleCalc {
        function add(uint a, uint b) public pure returns (uint) {
            return a + b;
        }
    }
    """
    print("\n[Test: No Patterns]") # English translation
    clean_results = detector_test.scan_code(clean_code)
    print(json.dumps(clean_results, indent=2))
    assert clean_results["ZK_Features"]["detected"] == False
    assert clean_results["Oracle_Integration"]["detected"] == False
    assert clean_results["KYC_AML_Compliance"]["detected"] == False
    print("✅ No patterns test successful.") # English translation

    print("\n--- ZKOracleDetector Test Script End ---") # English translation


# ✅ 전역으로 감지기 인스턴스 생성 (api.py에서 사용할 인스턴스)
detector = ZKOracleDetector()

def analyze_zk_oracle(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Dummy analyze_zk_oracle function for API integration.
    Currently, it extracts 'code' from the input data and performs a scan
    using the ZKOracleDetector instance. Real ZK-SNARK specific analysis
    logic would be added here in a more advanced implementation.
    """
    code = data.get("code", "")
    if not code:
        return {
            "status": "error",
            "message": "No Solidity code provided for analysis in 'data' dictionary. Please include 'code' key."
        }

    results = detector.scan_code(code)
    return {
        "status": "success",
        "message": "ZK Oracle pattern scan completed.",
        "results": results
    }
