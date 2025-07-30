# TrustFlow/api.py
from fastapi import APIRouter, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional

# 백엔드 모듈 임포트
from TrustFlow import (
    generate_contract, template_mapper, rule_checker,
    deploy_manager, dao_manager, zk_oracle_detector,
    ipfs_uploader, oneinch_api
)

router = APIRouter()

# ✅ 1. Deploy API --------------------------------------

class DeployRequest(BaseModel):
    prompt: str
    wallet_address: Optional[str] = None

@router.post("/deploy/code")
async def deploy_code(data: DeployRequest):
    """
    1) AI Prompt → Solidity 코드 생성
    2) RuleChecker 실행
    3) 컨트랙트 배포
    4) TX Hash & Address 반환
    """
    # 1. AI 기반 Solidity 코드 생성
    solidity_code = generate_contract.create_contract_from_prompt(data.prompt)

    # 2. 헌법 기반 Rule Check
    issues = rule_checker.check_code(solidity_code)

    # 3. 컨트랙트 배포
    deploy_result = deploy_manager.deploy_code(solidity_code, wallet=data.wallet_address)

    return {
        "prompt": data.prompt,
        "solidity_code": solidity_code,
        "rule_issues": issues,
        "deploy_result": deploy_result
    }

# ✅ 2. DAO API --------------------------------------

class ProposalRequest(BaseModel):
    title: str
    description: str
    wallet_address: Optional[str] = None

@router.post("/dao/proposal")
async def create_proposal(req: ProposalRequest):
    """
    DAO Proposal 생성
    """
    result = dao_manager.create_proposal(req.title, req.description, wallet=req.wallet_address)
    return {"status": "ok", "proposal": result}

class VoteRequest(BaseModel):
    proposal_id: int
    vote: str    # "for" or "against"
    wallet_address: Optional[str] = None

@router.post("/dao/vote")
async def vote(req: VoteRequest):
    """
    DAO Proposal 투표
    """
    result = dao_manager.vote(req.proposal_id, req.vote, wallet=req.wallet_address)
    return {"status": "ok", "vote_result": result}

# ✅ 3. ZK Oracle Detector ---------------------------

class ZKDetectRequest(BaseModel):
    solidity_code: str

@router.post("/zk-detect")
async def zk_detect(req: ZKDetectRequest):
    """
    Solidity 코드 → ZK/Oracle/KYC 감지
    """
    result = zk_oracle_detector.analyze(req.solidity_code)
    return {"issues": result}

# ✅ 4. IPFS Report Upload ---------------------------

@router.post("/ipfs")
async def upload_report(file: UploadFile = File(...)):
    """
    리포트 파일 IPFS 업로드
    """
    ipfs_hash = ipfs_uploader.upload_file(file)
    return {"status": "uploaded", "ipfs_hash": ipfs_hash}

# ✅ 5. 1inch API 연동 -------------------------------

class SwapRequest(BaseModel):
    from_token: str
    to_token: str
    amount: float
    wallet_address: Optional[str] = None

@router.post("/1inch/swap")
async def oneinch_swap(req: SwapRequest):
    """
    1inch Swap API 호출
    """
    swap_result = oneinch_api.swap(req.from_token, req.to_token, req.amount, req.wallet_address)
    return {"status": "ok", "swap": swap_result}

@router.get("/1inch/quote")
async def oneinch_quote(from_token: str, to_token: str, amount: float):
    """
    1inch Quote API 호출
    """
    quote_result = oneinch_api.get_quote(from_token, to_token, amount)
    return {"status": "ok", "quote": quote_result}
