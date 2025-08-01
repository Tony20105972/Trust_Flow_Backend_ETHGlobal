import os
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# --- TrustFlow 내부 모듈 임포트 ---
try:
    from .dao_manager import DAOManager
    from .rule_checker import check_code
    from .lop_manager import LOPManager
    from .deploy_manager import DeploymentManager
    from .zk_oracle_detector import analyze_zk_oracle
    from .ipfs_uploader import ipfs_uploader_instance   # ✅ global instance 사용
    from .oneinch_api import oneinch_swap, oneinch_get_quote
except ImportError as e:
    print(f"모듈 임포트 오류: {e}")
    raise

# --- FastAPI App 초기화 ---
app = FastAPI()

# --- 매니저 인스턴스 생성 ---
dao_manager_instance = DAOManager()
lop_manager_instance = LOPManager()
deploy_manager_instance = DeploymentManager()

# --- ✅ Pydantic 모델 정의 ---
class CodeCheckRequest(BaseModel):
    code: str
    code_type: Optional[str] = "smart_contract"
    target_lang: Optional[str] = "solidity"

class ProposalCreateRequest(BaseModel):
    title: str
    description: str
    proposer_address: str

class ProposalVoteRequest(BaseModel):
    proposal_id: int
    voter_address: str
    vote_type: bool   # True(찬성), False(반대)

class DeployCodeRequest(BaseModel):
    solidity_code: str
    constructor_args: Optional[List[Any]] = None
    solc_version: str = "0.8.20"
    gas_price_multiplier: float = 2.0

class LopAnalyzeRequest(BaseModel):
    code: str

class SwapRequest(BaseModel):
    src_token: str
    dst_token: str
    amount: str
    from_address: str
    slippage: float = 1
    disable_estimate: bool = False
    allow_partial_fill: bool = False

# --- ✅ API Routes ---

@app.get("/")
async def read_root():
    return {"message": "Samantha OS API is running!"}

# ✅ 코드 보안 체크
@app.post("/code/check")
async def check_code_endpoint(request: CodeCheckRequest):
    try:
        analysis_result = check_code(request.code, code_type=request.code_type, target_lang=request.target_lang)
        return {"status": "success", "analysis_result": analysis_result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"코드 분석 실패: {e}")

# ✅ DAO 제안 생성
@app.post("/proposals/create")
async def create_proposal_endpoint(request: ProposalCreateRequest):
    try:
        proposal_id = dao_manager_instance.create_proposal(
            request.title,
            request.description,
            request.proposer_address
        )
        return {"status": "success", "proposal_id": proposal_id, "message": "DAO Proposal created successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DAO Proposal 생성 실패: {e}")

# ✅ DAO 투표
@app.post("/proposals/vote")
async def vote_proposal_endpoint(request: ProposalVoteRequest):
    try:
        dao_manager_instance.vote(request.proposal_id, request.voter_address, request.vote_type)
        return {"status": "success", "message": f"Vote recorded for proposal {request.proposal_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DAO Vote 실패: {e}")

# ✅ 스마트컨트랙트 직접 배포
@app.post("/deploy/code")
async def deploy_code_endpoint(request: DeployCodeRequest):
    try:
        deployment_result = deploy_manager_instance.deploy_from_code(
            request.solidity_code,
            request.constructor_args,
            request.solc_version,
            request.gas_price_multiplier
        )
        return {"status": "success", "deployment": deployment_result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"컨트랙트 배포 실패: {e}")

# ✅ LOP 코드 분석
@app.post("/lop/analyze")
async def analyze_lop_endpoint(request: LopAnalyzeRequest):
    try:
        analysis_result = lop_manager_instance.analyze_lop(request.code)
        return {"status": "success", "analysis_result": analysis_result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LOP 분석 실패: {e}")

# ✅ IPFS 업로드 (FormData 방식)
@app.post("/ipfs/upload")
async def ipfs_upload_endpoint(file: UploadFile = File(...)):
    try:
        file_bytes = await file.read()
        cid = ipfs_uploader_instance.upload_bytes(file_bytes, file.filename)
        return {"status": "success", "cid": cid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"IPFS 업로드 실패: {e}")

# ✅ 1inch 토큰 스왑
@app.post("/oneinch/swap")
async def oneinch_swap_endpoint(request: SwapRequest):
    try:
        swap_data = oneinch_swap(
            request.src_token,
            request.dst_token,
            request.amount,
            request.from_address,
            request.slippage,
            request.disable_estimate,
            request.allow_partial_fill
        )
        return {"status": "success", "swap_data": swap_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"1inch Swap 실패: {e}")

# ✅ 1inch Quote
@app.get("/oneinch/quote")
async def oneinch_quote_endpoint(src_token: str, dst_token: str, amount: str):
    try:
        quote_data = oneinch_get_quote(src_token, dst_token, amount)
        return {"status": "success", "quote_data": quote_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"1inch Quote 실패: {e}")
