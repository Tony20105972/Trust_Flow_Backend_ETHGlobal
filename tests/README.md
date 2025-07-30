# ✅ Unit Tests

This directory contains all the unit tests for the backend services and blockchain interactions of our project. These tests ensure the reliability, correctness, and stability of our codebase, covering various modules from API integrations to smart contract interactions.

---

## **Purpose**

The primary goals of these unit tests are to:

* **Validate Functionality**: Ensure individual components and functions work as expected.
* **Prevent Regressions**: Catch bugs introduced by new changes or refactoring.
* **Facilitate Development**: Provide clear examples of how modules are intended to be used and make development more robust.
* **Enhance Code Quality**: Contribute to a stable and maintainable codebase.

---

## **Structure**

Tests are organized by the module or feature they cover:

* **`test_rules.py`**: Tests for the `RuleChecker` and other business logic rules.
* **`test_oneinch_api.py`**: Tests for integration with the 1inch API.
* **`test_blockchain_tools.py`**: Tests for core blockchain interactions, including contract deployment and transaction handling.
* **`test_ipfs_uploader.py`**: Tests for the IPFS upload functionality.
* **`test_generate_contract.py`**: Tests for AI-driven smart contract generation (if applicable).
* **`test_deploy_manager.py`**: Comprehensive tests for the end-to-end AI-generated code deployment flow.
* **`test_dao_manager.py`**: Tests for Decentralized Autonomous Organization (DAO) related functionalities.
* **`test_zk_oracle_detector.py`**: Tests for detecting ZK and Oracle patterns within smart contract code (if applicable).

---

## **How to Run Tests**

We use **`pytest`** as our testing framework.

1.  **Install Dependencies**:
    Make sure you have all project dependencies installed, including `pytest`.
    ```bash
    pip install -r requirements.txt
    ```

2.  **Set Up Environment Variables**:
    Some tests (especially those involving blockchain or external APIs) require sensitive information like **private keys** or **API keys**. Ensure your `.env` file (in the project root) is correctly configured with these variables.
    * **`PRIVATE_KEY`**: Your Ethereum private key for test transactions.
    * **`GROQ_API_KEY`** or **`OPENAI_API_KEY`**: API key for LLM services.
    * **`IPFS_API_KEY`**: API key for your IPFS pinning service (e.g., Pinata, Infura).

    ***Note:*** *Do not commit your `.env` file to Git. It's excluded by `.gitignore` for security reasons.*

3.  **Run All Tests**:
    To run all tests in this directory, navigate to the **project root directory** in your terminal and execute:
    ```bash
    pytest tests/
    ```

4.  **Run Specific Test File**:
    To run tests from a specific file (e.g., `test_blockchain_tools.py`):
    ```bash
    pytest tests/test_blockchain_tools.py
    ```

5.  **Run Specific Test Function**:
    To run a single test function within a file (e.g., `test_contract_deployment` in `test_blockchain_tools.py`):
    ```bash
    pytest tests/test_blockchain_tools.py::test_contract_deployment
    ```

---

## **Writing New Tests**

When adding new features or fixing bugs, please ensure you add corresponding unit tests in the appropriate file within this directory. Follow the existing patterns for test functions and fixtures.

---
이제 `tests/` 폴더에 이 `README.md` 파일을 추가해 주시면 됩니다.

다음으로, `requirements.txt`에 `pytest`를 포함하여 필요한 Python 종속성들을 정의할 차례일까요?
