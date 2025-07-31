from fastapi import FastAPI
from TrustFlow.api import router as api_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="TrustFlow API",
    description="Backend API for TrustFlow dApp with AI Contract Generation, DAO, ZK, IPFS, 1inch, and LOP features.",
    version="0.1.0",
)

# ✅ 프론트엔드 링크(Lovable) 전용 CORS 허용
origins = [
    "https://trustflow-flow-builder.lovable.app",  # ✅ Lovable 프론트 URL (오타 수정: lovable.app)
    # 로컬 개발 환경에서 테스트할 경우 아래 주석을 풀어서 사용하세요.
    # "http://localhost",
    # "http://localhost:3000",
    # "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],    # OPTIONS, GET, POST 등 모두 허용
    allow_headers=["*"],    # Content-Type, Authorization 등 모두 허용
)

app.include_router(api_router)

@app.get("/")
async def root():
    return {"message": "TrustFlow API is running! Let's explore DeFi together 🚀"}
