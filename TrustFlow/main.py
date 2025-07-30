# TrustFlow/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from TrustFlow import api  # api.py 라우터 임포트

app = FastAPI(
    title="TrustFlow Backend",
    description="FastAPI backend for TrustFlow (Samantha OS) - AI → Smart Contract → Onchain Deployment",
    version="1.0.0",
)

# ✅ CORS 설정 (프론트엔드 연결용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # 해커톤 데모용, 배포시 특정 도메인으로 제한 가능
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ API 라우터 연결
app.include_router(api.router)

@app.get("/")
def root():
    return {"status": "ok", "message": "TrustFlow Backend is running 🚀"}

# ✅ Uvicorn 실행 (로컬 개발용)
# uvicorn trustflow.main:app --reload
