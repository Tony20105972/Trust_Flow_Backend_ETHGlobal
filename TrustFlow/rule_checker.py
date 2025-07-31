import os
import json
from typing import Dict, Any, List

# Rule Checker (Constitution)
class RuleChecker:
    def __init__(self, constitution_path: str = "constitution.json"):
        # Corrected path: Assumes constitution.json is in the same directory as rule_checker.py
        # If rule_checker.py is in TrustFlow/ and constitution.json is also in TrustFlow/, this is correct.
        # If constitution.json is in TrustFlow/data/constitution.json, you need to adjust:
        # self.constitution_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "constitution.json")
        self.constitution_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), constitution_path)
        self.rules = self._load_constitution()
        print(f"✅ RuleChecker initialized. Constitution loaded from: {self.constitution_path}")

    def _load_constitution(self) -> Dict[str, Any]:
        """Loads rules from the constitution.json file."""
        if not os.path.exists(self.constitution_path):
            print(f"❌ Error: Constitution file not found at {self.constitution_path}")
            raise FileNotFoundError(f"Constitution file not found at {self.constitution_path}")
        with open(self.constitution_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
            # Ensure 'rules' key exists
            if "rules" not in content:
                raise ValueError("Constitution file must contain a 'rules' key.")
            return content

    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """
        Evaluates a condition string within a given context.
        Uses a restricted environment for security.
        """
        # Define allowed built-ins to restrict arbitrary code execution
        allowed_builtins = {
            'True': True, 'False': False, 'None': None,
            'all': all, 'any': any, 'len': len,
            'str': str, 'int': int, 'float': float,
            'list': list, 'dict': dict, 'set': set,
            'tuple': tuple
        }
        try:
            # Safely evaluate the condition string
            # 'context' provides variables like 'solidity_code', 'proposal', 'wallet', 'result'
            # '__builtins__' are restricted to prevent arbitrary code execution
            return bool(eval(condition, {"__builtins__": allowed_builtins}, context))
        except Exception as e:
            print(f"⚠️ Warning: Failed to evaluate condition '{condition}' with context {context}. Error: {e}")
            return False # Default to false if evaluation fails

    def check_proposal_adherence(self, proposal_data: Dict[str, Any]) -> List[str]:
        """
        Checks a DAO proposal against the loaded constitutional rules.
        Returns a list of violations.
        """
        violations = []
        context = {"proposal": proposal_data} # Context for evaluating proposal-related rules

        for rule in self.rules.get("rules", []):
            if "DAO proposals" in rule.get("description", "") or "proposal" in rule.get("condition", ""): # Heuristic to apply rules to proposals
                if not self._evaluate_condition(rule["condition"], context):
                    violations.append(rule["name"])

        print(f"📋 Proposal adherence check completed. Violations: {violations}")
        return violations

    def check_code_adherence(self, code: str, code_type: str, target_lang: str) -> List[str]:
        """
        Checks the provided code against defined coding standards and security rules.
        Returns a list of violations found in the code.
        """
        print(f"📋 Checking {code_type} code for adherence to rules (Language: {target_lang})...")
        violations = []
        context = {
            "solidity_code": code if target_lang.lower() == "solidity" else "",
            "code": code,
            "code_type": code_type,
            "target_lang": target_lang
        }

        for rule in self.rules.get("rules", []):
            # Apply rules relevant to code analysis
            # This heuristic could be improved with dedicated 'applies_to' field in constitution.json
            if "solidity_code" in rule.get("condition", "") or "code" in rule.get("condition", ""):
                 if not self._evaluate_condition(rule["condition"], context):
                    violations.append(rule["name"])
        
        print(f"📋 Code adherence check completed. Violations: {violations}")
        return violations

# Create a global instance of RuleChecker
try:
    # Ensure this path is correct relative to where rule_checker.py is located
    rule_checker_instance = RuleChecker(constitution_path="constitution.json")
except Exception as e:
    print(f"Failed to initialize RuleChecker: {e}")
    raise

# Wrapper function for check_code endpoint with default values
def check_code(code: str, code_type: str = "smart_contract", target_lang: str = "solidity") -> Dict[str, Any]:
    """
    Wrapper function to expose rule_checker_instance.check_code_adherence.
    Provides default values for code_type and target_lang.
    """
    violations = rule_checker_instance.check_code_adherence(code, code_type, target_lang)
    return {"violations": violations, "status": "analyzed"}
