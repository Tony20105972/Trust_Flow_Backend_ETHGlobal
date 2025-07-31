import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# TrustFlow 패키지 내 상대 경로 임포트
# 모든 모듈이 TrustFlow/ 바로 아래에 있다고 가정합니다.
# 예를 들어, TrustFlow/api.py와 TrustFlow/dao_manager.py가 같은 폴더에 있는 경우
try:
    from .dao_manager import DAOManager
    from .rule_checker import check_code # check_code 래퍼 함수는 RuleChecker 인스턴스를 사용합니다.
    from .lop_manager import LOPManager  # <-- 수정됨: LopManager -> LOPManager
    from .deploy_manager import DeploymentManager
    from .zk_oracle_detector import analyze_zk_oracle # TrustFlow/utils가 아닌 TrustFlow/ 바로 아래로 수정
    from .ipfs_uploader import upload_to_ipfs       # TrustFlow/utils가 아닌 TrustFlow/ 바로 아래로 수정
    from .oneinch_api import oneinch_swap, oneinch_get_quote # TrustFlow/utils가 아닌 TrustFlow/ 바로 아래로 수정

except ImportError as e:
    print(f"모듈 임포트 오류: {e}")
    print("Python 경로가 올바르게 구성되어 있는지 확인하거나 임포트 문을 조정하십시오.")
    print("예시: TrustFlow/ (상위 디렉토리)에서 실행하는 경우, TrustFlow/가 PYTHONPATH에 포함되어 있는지 확인하십시오.")
    raise

app = FastAPI()

# 글로벌 매니저 인스턴스
try:
    dao_manager_instance = DAOManager()
    lop_manager_instance = LOPManager()  # <-- 수정됨: LopManager() -> LOPManager()
    deploy_manager_instance = DeploymentManager()
except Exception as e:
    print(f"매니저 인스턴스 초기화 실패: {e}")
    raise


# Pydantic 모델
class CodeCheckRequest(BaseModel):
    code: str
    code_type: Optional[str] = "smart_contract" # RuleChecker의 check_code 기본값과 일치
    target_lang: Optional[str] = "solidity"     # RuleChecker의 check_code 기본값과 일치

class ProposalCreateRequest(BaseModel):
    title: str
    description: str
    proposer_address: str
    initial_status: str = "pending"
    code_hash: Optional[str] = None

class ProposalVoteRequest(BaseModel):
    proposal_id: str
    voter_address: str
    vote_type: str # 'for', 'against', 'abstain'

class DeployCodeRequest(BaseModel):
    solidity_code: str
    constructor_args: Optional[List[Any]] = None
    solc_version: str = "0.8.20"
    gas_price_multiplier: float = 2.0

class DeployTemplateRequest(BaseModel):
    template_name: str
    variables: Dict[str, Any]
    solc_version: str = "0.8.20"
    gas_price_multiplier: float = 2.0

class CallContractFunctionRequest(BaseModel):
    contract_address: str
    abi: List[Dict[str, Any]]
    function_name: str
    args: Optional[List[Any]] = None

class SendContractTransactionRequest(BaseModel):
    contract_address: str
    abi: List[Dict[str, Any]]
    function_name: str
    args: Optional[List[Any]] = None
    value: int = 0
    gas_limit: int = 5_000_000 # Increased gas limit
    gas_price_multiplier: float = 1.5
    timeout_seconds: int = 300


@app.get("/")
async def read_root():
    return {"message": "Samantha OS API is running!"}

# --- Core API Endpoints ---

@app.post("/code/check")
async def check_code_endpoint(request: CodeCheckRequest):
    """
    제공된 코드를 보안 취약점, 규칙 위반 및 모범 사례에 대해 분석합니다.
    """
    try:
        # RuleChecker의 check_code 함수에 기본값이 있으므로, Pydantic 모델에서 제공되지 않으면 기본값이 사용됩니다.
        analysis_result = check_code(
            request.code,
            code_type=request.code_type,
            target_lang=request.target_lang
        )
        return {"status": "success", "analysis_result": analysis_result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"코드 분석 실패: {e}")

@app.post("/proposals/create")
async def create_proposal_endpoint(request: ProposalCreateRequest):
    """
    새로운 DAO 제안을 생성합니다.
    """
    try:
        proposal_data = {
            "title": request.title,
            "description": request.description,
            "proposer_address": request.proposer_address,
            "initial_status": request.initial_status,
            "code_hash": request.code_hash
        }
        proposal_id = dao_manager_instance.create_proposal(proposal_data)
        return {"status": "success", "proposal_id": proposal_id, "message": "제안이 성공적으로 생성되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"제안 생성 실패: {e}")

@app.post("/proposals/vote")
async def vote_proposal_endpoint(request: ProposalVoteRequest):
    """
    특정 DAO 제안에 대한 투표를 기록합니다.
    """
    try:
        dao_manager_instance.vote(request.proposal_id, request.voter_address, request.vote_type)
        return {"status": "success", "message": f"제안 {request.proposal_id}에 대한 투표가 {request.voter_address}에 의해 기록되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"투표 기록 실패: {e}")

@app.get("/proposals/{proposal_id}")
async def get_proposal_endpoint(proposal_id: str):
    """
    특정 DAO 제안의 상세 정보를 검색합니다.
    """
    try:
        proposal = dao_manager_instance.get_proposal(proposal_id)
        if not proposal:
            raise HTTPException(status_code=404, detail="제안을 찾을 수 없습니다.")
        return {"status": "success", "proposal": proposal}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"제안 검색 실패: {e}")

@app.post("/deploy/code")
async def deploy_code_endpoint(request: DeployCodeRequest):
    """
    Solidity 코드를 직접 사용하여 스마트 컨트랙트를 배포합니다.
    """
    try:
        deployment_result = deploy_manager_instance.deploy_from_code(
            request.solidity_code,
            request.constructor_args,
            request.solc_version,
            request.gas_price_multiplier
        )
        return {"status": "success", "deployment": deployment_result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"코드로부터 컨트랙트 배포 실패: {e}")

@app.post("/deploy/template")
async def deploy_template_endpoint(request: DeployTemplateRequest):
    """
    사전 정의된 템플릿으로부터 스마트 컨트랙트를 배포합니다.
    """
    try:
        deployment_result = deploy_manager_instance.deploy_from_template(
            request.template_name,
            request.variables,
            request.solc_version,
            request.gas_price_multiplier
        )
        return {"status": "success", "deployment": deployment_result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"템플릿으로부터 컨트랙트 배포 실패: {e}")

@app.post("/contract/call")
async def call_contract_function_endpoint(request: CallContractFunctionRequest):
    """
    배포된 스마트 컨트랙트의 읽기 전용 (view/pure) 함수를 호출합니다.
    """
    try:
        result = deploy_manager_instance.call_contract_function(
            request.contract_address,
            request.abi,
            request.function_name,
            request.args
        )
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"컨트랙트 함수 호출 실패: {e}")

@app.post("/contract/send_transaction")
async def send_contract_transaction_endpoint(request: SendContractTransactionRequest):
    """
    배포된 스마트 컨트랙트의 상태 변경 함수로 트랜잭션을 전송합니다.
    """
    try:
        tx_hash = deploy_manager_instance.send_contract_transaction(
            request.contract_address,
            request.abi,
            request.function_name,
            request.args,
            request.value,
            request.gas_limit,
            request.gas_price_multiplier,
            request.timeout_seconds
        )
        return {"status": "success", "transaction_hash": tx_hash}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"컨트랙트 트랜잭션 전송 실패: {e}")

@app.post("/lop/analyze")
async def analyze_lop_endpoint(code: str):
    """
    LOP (Language of Power) 코드를 분석합니다.
    """
    try:
        analysis_result = lop_manager_instance.analyze_lop(code)
        return {"status": "success", "analysis_result": analysis_result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LOP 분석 실패: {e}")

@app.post("/zk_oracle/analyze")
async def zk_oracle_analyze_endpoint(data: Dict[str, Any]):
    """
    Zero-Knowledge Oracle을 위한 데이터를 분석합니다.
    """
    try:
        # analyze_zk_oracle은 독립형 함수로 가정합니다.
        analysis_result = analyze_zk_oracle(data)
        return {"status": "success", "analysis_result": analysis_result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ZK 오라클 분석 실패: {e}")

@app.post("/ipfs/upload")
async def ipfs_upload_endpoint(file_content: str, file_name: str):
    """
    IPFS에 콘텐츠를 업로드합니다.
    """
    try:
        # upload_to_ipfs는 독립형 함수로 가정합니다.
        cid = upload_to_ipfs(file_content, file_name)
        return {"status": "success", "cid": cid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"IPFS 업로드 실패: {e}")

@app.post("/oneinch/swap")
async def oneinch_swap_endpoint(
    src_token: str,
    dst_token: str,
    amount: str,
    from_address: str,
    slippage: float = 1,
    disable_estimate: bool = False,
    allow_partial_fill: bool = False
):
    """
    1inch API를 사용하여 토큰 스왑을 수행합니다.
    """
    try:
        # oneinch_swap은 독립형 함수로 가정합니다.
        swap_data = oneinch_swap(src_token, dst_token, amount, from_address, slippage, disable_estimate, allow_partial_fill)
        return {"status": "success", "swap_data": swap_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"1inch 스왑 실패: {e}")

@app.get("/oneinch/quote")
async def oneinch_quote_endpoint(
    src_token: str,
    dst_token: str,
    amount: str
):
    """
    1inch API로부터 토큰 스왑 견적을 받습니다.
    """
    try:
        # oneinch_get_quote는 독립형 함수로 가정합니다.
        quote_data = oneinch_get_quote(src_token, dst_token, amount)
        return {"status": "success", "quote_data": quote_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"1inch 견적 실패: {e}")
