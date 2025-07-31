import sys # For sys.exit()
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# Backend modules import
# Assuming these are directly importable from the TrustFlow package root
# e.g., if TrustFlow is a package and these are modules within it.
from TrustFlow import (
    generate_contract, template_mapper, rule_checker,
    deploy_manager, dao_manager, zk_oracle_detector,
    ipfs_uploader, oneinch_api,
    lop_manager # ✅ lop_manager import
)

router = APIRouter()

# --- Global LOPManager Instance ---
# This instance will be initialized once when the FastAPI server starts
# due to its placement at the module level.
# With the updated lop_manager.py, it will now try to read environment variables first.
lop: Optional[lop_manager.LOPManager] = None

try:
    print("🚀 Attempting to initialize LOPManager in api.py...")
    lop = lop_manager.LOPManager()
    print("✅ LOPManager initialized successfully in api.py.")
except ValueError as e:
    # This catches errors from Web3Client if ENV variables are missing.
    # On Render, this means you forgot to set environment variables.
    print(f"🚨 FATAL ERROR: LOPManager initialization failed due to missing environment variable: {e}", file=sys.stderr)
    lop = None
    # In a production setup, if this is a critical dependency,
    # you might want to terminate the application startup here.
    # For a web server, letting it start but returning 503 on affected endpoints is also an option.
    # If using uvicorn/gunicorn, sys.exit(1) here would prevent the server from binding.
    # sys.exit(1) # Uncomment this if you want to hard-stop the app on startup failure.
except Exception as e:
    # Catch any other unexpected errors during initialization
    print(f"🚨 FATAL ERROR: An unexpected error occurred during LOPManager initialization: {e}", file=sys.stderr)
    lop = None
    # sys.exit(1) # Uncomment this if you want to hard-stop the app on startup failure.

# If lop is still None after the try-except, indicate that core functionality is unavailable
if lop is None:
    print("⚠️ Warning: LOPManager could not be initialized. On-chain related APIs will return 503 errors.", file=sys.stderr)


# --- Dependency for LOPManager (to be used by LOP endpoints) ---
async def get_lop_manager_instance():
    """
    Dependency injector for LOPManager.
    Raises HTTPException 503 if LOPManager failed to initialize.
    """
    if lop is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LOPManager is not initialized. Check server logs for details (missing ENV vars, Web3 connectivity)."
        )
    return lop


# ✅ 1. Deploy API --------------------------------------

class DeployRequest(BaseModel):
    prompt: str
    wallet_address: Optional[str] = None 

@router.post("/deploy/code", summary="AI Prompt -> Solidity Code Generation & Deployment")
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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Contract deployment failed: {e}")

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

@router.post("/dao/proposal", summary="Create DAO Proposal")
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

@router.post("/dao/vote", summary="Vote on DAO Proposal")
async def vote(req: VoteRequest):
    """
    Vote on DAO Proposal
    """
    result = dao_manager.vote(req.proposal_id, req.vote, wallet=req.wallet_address)
    return {"status": "ok", "vote_result": result}

# ✅ 3. ZK Oracle Detector ---------------------------

class ZKDetectRequest(BaseModel):
    solidity_code: str

@router.post("/zk-detect", summary="Detect ZK/Oracle/KYC in Solidity Code (Mock)")
async def zk_detect(req: ZKDetectRequest):
    """
    Detect ZK/Oracle/KYC in Solidity Code
    """
    result = zk_oracle_detector.analyze(req.solidity_code)
    return {"issues": result}

# ✅ 4. IPFS Report Upload ---------------------------

@router.post("/ipfs", summary="Upload Report File to IPFS (Mock)")
async def upload_report(file: UploadFile = File(...)):
    """
    Upload Report File to IPFS
    """
    try:
        ipfs_hash = ipfs_uploader.upload_file(file)
        return {"status": "uploaded", "ipfs_hash": ipfs_hash}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"IPFS upload failed: {e}")

# ✅ 5. 1inch API Integration -------------------------------

class SwapRequest(BaseModel):
    from_token: str
    to_token: str
    amount: float
    wallet_address: Optional[str] = None

@router.post("/1inch/swap", summary="Call 1inch Swap API (Mock)")
async def oneinch_swap(req: SwapRequest):
    """
    Call 1inch Swap API
    """
    try:
        swap_result = oneinch_api.swap(req.from_token, req.to_token, req.amount, req.wallet_address)
        return {"status": "ok", "swap": swap_result}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"1inch swap failed: {e}")

@router.get("/1inch/quote", summary="Call 1inch Quote API (Mock)")
async def oneinch_quote(from_token: str, to_token: str, amount: float):
    """
    Call 1inch Quote API
    """
    try:
        quote_result = oneinch_api.get_quote(from_token, to_token, amount)
        return {"status": "ok", "quote": quote_result}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"1inch quote failed: {e}")


# ✅ 6. LOPManager API -------------------------------

from fastapi import Depends # Import Depends for dependency injection

class LimitOrderRequest(BaseModel):
    prompt: str
    from_token: str
    to_token: str
    amount: float
    price: float

class OrderIdRequest(BaseModel): # New Pydantic model for single order_id argument
    order_id: int

@router.post("/lop/create", summary="Create LOP Limit Order & Execute ERC20 Approval Transaction")
async def create_limit_order_api(
    req: LimitOrderRequest,
    current_lop: lop_manager.LOPManager = Depends(get_lop_manager_instance) # Inject the lop_manager instance
):
    """Create LOP Limit Order + Execute ERC20 Approval Transaction"""
    try:
        order = current_lop.create_limit_order(req.prompt, req.from_token, req.to_token, req.amount, req.price)
        return {"status": "ok", "order": order}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create limit order: {e}")

@router.post("/lop/dao-approve", summary="Simulate DAO Pre-Approval for LOP Order")
async def dao_approve_api(
    req: OrderIdRequest,
    current_lop: lop_manager.LOPManager = Depends(get_lop_manager_instance)
):
    """Simulate DAO Pre-Approval"""
    try:
        result = current_lop.initiate_dao_pre_approval(req.order_id)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order {req.order_id} not found.")
        return {"status": "ok", "dao": result}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to initiate DAO approval: {e}")

@router.post("/lop/submit", summary="On-chain LOP Order Submission and Execution Simulation")
async def submit_order_api(
    req: OrderIdRequest,
    current_lop: lop_manager.LOPManager = Depends(get_lop_manager_instance)
):
    """On-chain Order Submission and Execution Simulation"""
    try:
        result = current_lop.submit_order_on_chain_and_simulate_execution(req.order_id)
        if not result or "status" not in result:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order {req.order_id} not found or submission failed to return result.")
        if result.get("status") == "FAILED_ONCHAIN":
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"On-chain submission failed for order {req.order_id}: {result.get('error', 'Unknown error')}")
        return {"status": "ok", "execution": result}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to submit order on-chain: {e}")

@router.get("/lop/orders", response_model=Dict[str, Any], summary="Retrieve all LOP Orders") # Using Dict[str, Any] for flexibility
async def list_orders_api(
    current_lop: lop_manager.LOPManager = Depends(get_lop_manager_instance)
):
    """Retrieve all LOP Orders"""
    try:
        orders = current_lop.list_all_orders()
        return {"status": "ok", "orders": orders}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to list orders: {e}")

@router.post("/lop/cancel", summary="Cancel LOP Order")
async def cancel_order_api(
    req: OrderIdRequest,
    current_lop: lop_manager.LOPManager = Depends(get_lop_manager_instance)
):
    """Cancel LOP Order"""
    try:
        result = current_lop.cancel_order(req.order_id)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order {req.order_id} not found.")
        return {"status": "ok", "canceled": result}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to cancel order: {e}")
