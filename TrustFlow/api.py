# TrustFlow/api.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# Backend modules import
from TrustFlow import (
    generate_contract, template_mapper, rule_checker,
    deploy_manager, dao_manager, zk_oracle_detector,
    ipfs_uploader, oneinch_api,
    lop_manager # ✅ lop_manager import
)

router = APIRouter()

# ✅ LOPManager instance creation (global)
# This instance will be initialized once when the FastAPI server starts.
# With the updated lop_manager.py, it will now try to read environment variables first.
try:
    lop = lop_manager.LOPManager()
except Exception as e:
    print(f"⚠️ Warning: LOPManager initialization failed. Please ensure required environment variables (WEB3_RPC_URL_SEPOLIA, WALLET_PRIVATE_KEY, DUMMY_LOP_CONTRACT_ADDRESS) are set in your deployment environment (e.g., Render). Error: {e}")
    # In a production setup, you might want to raise an exception here
    # or handle this more gracefully, perhaps by disabling LOP endpoints.
    lop = None 

# ✅ 1. Deploy API --------------------------------------

class DeployRequest(BaseModel):
    prompt: str
    wallet_address: Optional[str] = None 

@router.post("/deploy/code")
async def deploy_code(data: DeployRequest):
    """
    1) AI Prompt -> Solidity Code Generation
    2) RuleChecker Execution
    3) Contract Deployment
    4) Return TX Hash & Address
    """
    # 1. AI-based Solidity code generation (Mock or actual LLM integration)
    solidity_code = generate_contract.create_contract_from_prompt(data.prompt)

    # 2. Constitution-based Rule Check
    issues = rule_checker.check_code(solidity_code)

    # 3. Contract deployment (depends on external deploy_manager module)
    try:
        deploy_result = deploy_manager.deploy_code(solidity_code, wallet=data.wallet_address)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Contract deployment failed: {e}")

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
    Create DAO Proposal
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
    Vote on DAO Proposal
    """
    result = dao_manager.vote(req.proposal_id, req.vote, wallet=req.wallet_address)
    return {"status": "ok", "vote_result": result}

# ✅ 3. ZK Oracle Detector ---------------------------

class ZKDetectRequest(BaseModel):
    solidity_code: str

@router.post("/zk-detect")
async def zk_detect(req: ZKDetectRequest):
    """
    Detect ZK/Oracle/KYC in Solidity Code
    """
    result = zk_oracle_detector.analyze(req.solidity_code)
    return {"issues": result}

# ✅ 4. IPFS Report Upload ---------------------------

@router.post("/ipfs")
async def upload_report(file: UploadFile = File(...)):
    """
    Upload Report File to IPFS
    """
    try:
        ipfs_hash = ipfs_uploader.upload_file(file)
        return {"status": "uploaded", "ipfs_hash": ipfs_hash}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"IPFS upload failed: {e}")

# ✅ 5. 1inch API Integration -------------------------------

class SwapRequest(BaseModel):
    from_token: str
    to_token: str
    amount: float
    wallet_address: Optional[str] = None

@router.post("/1inch/swap")
async def oneinch_swap(req: SwapRequest):
    """
    Call 1inch Swap API
    """
    try:
        swap_result = oneinch_api.swap(req.from_token, req.to_token, req.amount, req.wallet_address)
        return {"status": "ok", "swap": swap_result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"1inch swap failed: {e}")

@router.get("/1inch/quote")
async def oneinch_quote(from_token: str, to_token: str, amount: float):
    """
    Call 1inch Quote API
    """
    try:
        quote_result = oneinch_api.get_quote(from_token, to_token, amount)
        return {"status": "ok", "quote": quote_result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"1inch quote failed: {e}")


# ✅ 6. LOPManager API -------------------------------

class LimitOrderRequest(BaseModel):
    prompt: str
    from_token: str
    to_token: str
    amount: float
    price: float

class OrderIdRequest(BaseModel): # New Pydantic model for single order_id argument
    order_id: int

@router.post("/lop/create")
async def create_limit_order_api(req: LimitOrderRequest):
    """Create LOP Limit Order + Execute ERC20 Approval Transaction"""
    if lop is None:
        raise HTTPException(status_code=503, detail="LOPManager is not initialized. Please set required environment variables for deployment.")
    try:
        order = lop.create_limit_order(req.prompt, req.from_token, req.to_token, req.amount, req.price)
        return {"status": "ok", "order": order}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create limit order: {e}")

@router.post("/lop/dao-approve")
async def dao_approve_api(req: OrderIdRequest):
    """Simulate DAO Pre-Approval"""
    if lop is None:
        raise HTTPException(status_code=503, detail="LOPManager is not initialized. Please set required environment variables for deployment.")
    try:
        result = lop.initiate_dao_pre_approval(req.order_id)
        return {"status": "ok", "dao": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate DAO approval: {e}")

@router.post("/lop/submit")
async def submit_order_api(req: OrderIdRequest):
    """On-chain Order Submission and Execution Simulation"""
    if lop is None:
        raise HTTPException(status_code=503, detail="LOPManager is not initialized. Please set required environment variables for deployment.")
    try:
        result = lop.submit_order_on_chain_and_simulate_execution(req.order_id)
        return {"status": "ok", "execution": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit order on-chain: {e}")

@router.get("/lop/orders", response_model=Dict[str, List[Dict[str, Any]]]) # Explicit response model
async def list_orders_api():
    """Retrieve all LOP Orders"""
    if lop is None:
        raise HTTPException(status_code=503, detail="LOPManager is not initialized. Please set required environment variables for deployment.")
    try:
        orders = lop.list_all_orders()
        return {"status": "ok", "orders": orders}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list orders: {e}")

@router.post("/lop/cancel")
async def cancel_order_api(req: OrderIdRequest):
    """Cancel LOP Order"""
    if lop is None:
        raise HTTPException(status_code=503, detail="LOPManager is not initialized. Please set required environment variables for deployment.")
    try:
        result = lop.cancel_order(req.order_id)
        return {"status": "ok", "canceled": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel order: {e}")
