from fastapi import FastAPI
from TrustFlow.api import router as api_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="TrustFlow API",
    description="Backend API for TrustFlow dApp with AI Contract Generation, DAO, ZK, IPFS, 1inch, and LOP features.",
    version="0.1.0",
)

# ✅ CORS 설정 (CORS Middleware)
# 🚨 해커톤/데모 단계에서는 모든 출처를 허용하여 개발 편의성을 높입니다.
# 📌 프로덕션 배포 시에는 반드시 특정 프론트엔드 도메인으로 제한해야 합니다 (보안 중요!).
origins = [
    "*",  # 모든 출처(도메인) 허용 - Preflight 요청 포함
    # "http://localhost",         # 로컬 개발용 (필요하다면 유지)
    # "http://localhost:3000",    # 로컬 React 개발 서버 (필요하다면 유지)
    # "http://localhost:8000",    # 로컬 FastAPI 개발 서버 (필요하다면 유지)
    # "https://your-frontend-domain.com", # 실제 배포용 프론트엔드 도메인 (나중에 추가)
    # "https://your-render-backend-url.onrender.com" # 백엔드가 스스로를 호출할 경우 (나중에 추가)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],    # OPTIONS, GET, POST 등 모든 HTTP 메서드 허용
    allow_headers=["*"],    # Content-Type, Authorization 등 모든 요청 헤더 허용
)

app.include_router(api_router)

@app.get("/")
async def root():
    """Root endpoint for basic health check."""
    return {"message": "TrustFlow API is running! Access /docs for API documentation."}
