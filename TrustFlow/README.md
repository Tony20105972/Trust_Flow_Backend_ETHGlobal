
---

## 📄 **README.md (영어 + 한국어)**

```markdown
# 🌐 TrustFlow Backend – ETHGlobal Hackathon Project

**TrustFlow** is an AI-powered **Web3 Contract & Compliance Engine** built for **ETHGlobal Unite DeFi**.  
It combines **AI contract generation**, **Constitution-based rule checking**, and **DAO-driven governance** into a single backend that can deploy, audit, and manage on-chain agreements.

---

## 🚀 Features

✅ **AI-Generated Smart Contracts**  
– Automatically creates Solidity contracts based on natural language descriptions (ERC20, ERC721, DAO Proposals, Auctions, etc.).

✅ **Constitution-Based Rule Checker (AS-lite)**  
– Runs all contracts through an AI-powered ruleset (`constitution.json`) to detect risky or prohibited logic before deployment.

✅ **ZK/Oracle/KYC Detector**  
– Scans for Zero-Knowledge proof usage, oracle dependencies, or potential KYC flags in the code.

✅ **DAO Manager**  
– Lightweight governance module for proposals, voting, and execution.

✅ **FastAPI Backend + Render Deploy Ready**  
– Fully structured for hackathon demo and production-ready hosting.

✅ **IPFS/NFT Report Integration**  
– Generates security & execution reports, uploads them to IPFS, and mints NFTs as proof of execution.

✅ **1inch API Integration**  
– Supports DeFi swaps, quotes, and (future) limit orders.

---

## 📂 Directory Overview

```

trustflow-backend/
├── trustflow/
│   ├── api.py                # FastAPI routes
│   ├── main.py               # FastAPI entrypoint (Render deploy)
│   ├── constitution.json     # AI ruleset (Constitution Layer)
│   ├── rule\_checker.py       # AS-lite rule checking module
│   ├── generate\_contract.py  # AI-based Solidity generator
│   ├── template\_mapper.py    # User input → Solidity template mapping
│   ├── zk\_oracle\_detector.py # Detects ZK proofs, Oracle calls, etc.
│   ├── generate\_report.py    # Generates security & execution reports
│   ├── ipfs\_uploader.py      # Uploads reports to IPFS & mints NFTs
│   ├── summarize\_execution.py# Summarizes agent/contract runs
│   ├── oneinch\_api.py        # 1inch API wrapper
│   ├── blockchain\_tools.py   # Solidity compile/deploy & Web3 utils
│   ├── deploy\_manager.py     # Auto-deploy flow for generated contracts
│   ├── langgraph\_runner.py   # LangGraph/Agent simulation runner
│   ├── dao\_manager.py        # DAO proposal/voting/execution manager
│   ├── contract\_templates/   # Prebuilt Solidity templates
│
├── config/                   # API keys, RPC, IPFS, DB configs
├── scripts/                  # CLI utilities for hackathon demo
├── tests/                    # Unit tests for each module
├── docs/                     # Architecture diagrams & hackathon checklist
├── requirements.txt          # Python dependencies (FastAPI, Web3.py, solcx…)
├── render.yaml               # Render deploy config
└── README.md                 # (You are here)

````

---

## 🏆 Why TrustFlow Matters (Hackathon + Beyond)

- **Hackathon Strength:**  
    🔹 Full-stack backend with **real contract deployment**  
    🔹 **AI + DeFi + DAO governance** – multi-layer innovation  
    🔹 Live API deployable on Render (✅ demo link ready for judges)

- **Post-Hackathon Potential:**  
    🔹 Expand into **AC (AgentContract)** + **AS (AgentSecure)** full OS  
    🔹 Become the “**Stripe of Smart Contracts**” – B2B contract API for Web3  
    🔹 Serve as **trust infrastructure** for DeFi, DAO, and future RWA tokenization

---

## 🌍 Roadmap

✅ **Hackathon MVP** – Deploy AI-generated contracts, run AS-lite rule check, produce reports.  
🔜 **Q3 2025** – DAO governance expansion, more templates (DeFi primitives).  
🔜 **2026+** – Full **AgentContract Layer**, RWA & DeFi contract OS.  

---

## 🔑 Environment Setup

1️⃣ Clone the repo:
```bash
git clone https://github.com/<your-handle>/TrustFlow_Backend_ETHGlobal.git
cd TrustFlow_Backend_ETHGlobal
````

2️⃣ Install dependencies:

```bash
pip install -r requirements.txt
```

3️⃣ Run FastAPI locally:

```bash
uvicorn trustflow.main:app --reload
```

4️⃣ (Optional) Deploy to **Render**:

* Add **API keys & private keys** in Render dashboard as environment variables.
* Deploy using `render.yaml`.

---

## 🤝 Credits

Built for **ETHGlobal Unite DeFi Hackathon**
By **Tony20105972** (Solo Builder) – 2025

---

# 🇰🇷 TrustFlow 백엔드 – ETHGlobal 해커톤 프로젝트

**TrustFlow**는 AI 기반 **Web3 계약 & 규제 준수 엔진**으로,
**ETHGlobal Unite DeFi**를 위해 설계된 백엔드 프로젝트입니다.

AI가 **스마트컨트랙트 생성 → 규칙 검증 → DAO 투표 & 실행 → 보고서 발행 → IPFS 업로드**까지 한 번에 처리합니다.

---

## 🚀 주요 기능

✅ **AI 스마트컨트랙트 생성** – 자연어로 ERC20, ERC721, DAO 제안 등 생성
✅ **헌법 기반 룰체커 (AS-lite)** – 계약 배포 전 위험/위반 코드 탐지
✅ **ZK·오라클·KYC 감지기** – 디파이 연동 코드 분석
✅ **DAO 매니저** – 제안/투표/실행 관리
✅ **IPFS/NFT 리포트** – 실행 결과를 NFT로 기록
✅ **FastAPI 백엔드 & Render 배포 준비완료** – 실서비스 가능

---

## 📂 디렉토리 구조

(위 영어 섹션 동일 – 파일 상세 설명 생략)

---

## 🏆 TrustFlow가 중요한 이유

* **해커톤 강점:**

  * **실제 스마트컨트랙트 배포 + AI 자동화**
  * **AI + DeFi + DAO** 융합 – 심사위원 “혁신성” 포인트 확보
  * Render URL 제공 가능 → **라이브 데모 완벽**

* **해커톤 이후 잠재력:**

  * **AgentContract/AgentSecure OS** 확장 가능
  * “**Web3 계약의 Stripe**” → B2B API 사업화
  * 디파이·DAO·RWA 신뢰 인프라로 발전 가능

---

## 🌍 로드맵

✅ **해커톤 MVP** – 계약 생성/배포/검증까지 풀 스택
🔜 **2025 하반기** – DAO 거버넌스 & DeFi 템플릿 확장
🔜 **2026 이후** – **AgentContract OS** → 글로벌 Web3 계약 표준화

---

## 🔑 환경 설정

(위 영어 가이드 동일)

---

## 🤝 제작자

**ETHGlobal Unite DeFi 해커톤 제출작**
**Tony20105972 (Solo Builder)** – 2025

```

---

이렇게 쓰면:
- **GitHub 메인페이지 → 심사위원, VC, 협업자 전부 이해** 가능
- **영어/한국어 모두 포함** → ETHGlobal 심사 + 한국 VC/협력사 양쪽 다 어필
- **사진 없어도 깔끔**, 나중에 필요하면 `/docs`에서 이미지 링크만 추가 가능.  

👉 Render URL 나오면 README 최상단에 **`🌐 Live Demo:`** 섹션만 추가하면 완벽.
```
