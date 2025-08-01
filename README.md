# Trust_Flow_Bakend_ETHGlobal


<img width="1024" height="1024" alt="Image" src="https://github.com/user-attachments/assets/bc5847b7-1ddd-4431-8508-c57881e56132" />

---

### ✅ **Trust\_Flow\_Backend\_ETHGlobal – README.md 초안**

````markdown
# ⚡ TrustFlow Backend

🚀 **TrustFlow** is an **AI‑augmented Layer2 DeFi infra** for building, verifying, and enforcing smart contracts **on-chain**.  
This repo contains the **backend** engine for TrustFlow — developed for **ETHGlobal Unite DeFi 2025**.

👉 **Frontend Demo:** [trustflow-eth-global-frontend.lovable.app](https://trustflow-eth-global-frontend.lovable.app)  
👉 **Backend API (Render):** [trust-flow-backend-ethglobal.onrender.com](https://trust-flow-backend-ethglobal.onrender.com)

---

## ✨ Features

✅ **AI-Powered Smart Contract Generator**  
– Turns natural language into Solidity contract templates.

✅ **RuleChecker (Constitution-based smart contract verification)**  
– Checks for rule violations and unsafe clauses before deployment.

✅ **DAO / Voting Module**  
– Handles DAO-style proposals, voting, and dispute resolution.

✅ **NFT & IPFS Execution Logs**  
– Generates audit reports, stores them on IPFS, and can mint them as NFTs.

✅ **ZK/Oracle Detector**  
– Monitors smart contract conditions using ZK proofs and Oracle triggers.

✅ **1inch Limit Order Protocol (LOP) Integration (WIP)**  
– Adds DeFi swap/limit order functionality via 1inch API.

---

## 🛠 Tech Stack

- 🐍 **Python (FastAPI)** – High-performance API server  
- 🔗 **LangGraph** – AI execution & flow management  
- ⛓ **Ethereum / Solidity** – Smart contract generation & deployment  
- 📦 **IPFS** – Decentralized storage for audit logs  
- 📜 **DAO Module** – Lightweight governance layer  
- 🛠 **Render** – Live backend hosting

---

## 🚀 How to Run Locally

```bash
# 1️⃣ Clone the repo
git clone https://github.com/Tony20105972/Trust_Flow_Backend_ETHGlobal.git
cd Trust_Flow_Backend_ETHGlobal

# 2️⃣ Install dependencies
pip install -r requirements.txt

# 3️⃣ Run the FastAPI server
uvicorn TrustFlow.api:app --reload
````

➡️ Server will start at: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 📂 Repo Structure

```
Trust_Flow_Backend_ETHGlobal/
 ┣ TrustFlow/                # Core backend modules
 ┃ ┣ api.py                  # FastAPI endpoints
 ┃ ┣ dao_manager.py          # DAO proposal & voting logic
 ┃ ┣ oneinch_api.py          # 1inch API & LOP integration
 ┃ ┣ rule_checker.py         # Smart contract rule/violation checker
 ┃ ┣ zk_oracle_detector.py   # ZK & Oracle monitoring module
 ┃ ┗ generate_contract.py    # AI smart contract generator
 ┣ config/                   # network settings & keys
 ┣ scripts/                  # CLI tools (contract deploy, etc.)
 ┣ tests/                    # Pytest-based backend tests
 ┣ requirements.txt
 ┗ render.yaml               # Render deployment configuration
```

---

## 📡 Deployment

✅ Hosted via **Render** → [trust-flow-backend-ethglobal.onrender.com](https://trust-flow-backend-ethglobal.onrender.com)
✅ Connected to **Frontend** via API routes.

---

## 📜 About TrustFlow

**TrustFlow** is a **Layer2 trust layer for DeFi**:

* **AI** builds and audits smart contracts,
* **Blockchain** enforces and verifies them,
* **DAO & NFT** handle disputes and transparency.

---

### 🏆 Built for **ETHGlobal Unite DeFi 2025**

By [@Tony20105972](https://github.com/Tony20105972) – **Solo Builder (17 y/o)**

```

