# TrustFlow/main.py
# 이 파일은 FastAPI 애플리케이션의 진입점 역할을 합니다.
# uvicorn trustflow.main:app --reload 와 같이 실행될 때,
# 'trustflow' 패키지 내의 'main' 모듈에서 'app' 객체를 찾습니다.

from .api import app
from fastapi.middleware.cors import CORSMiddleware
import os

# --- CORS 설정 추가 (프론트엔드 연결 문제 해결용) ---
# 개발 환경과 프로덕션 환경에 따라 allow_origins를 동적으로 설정
allowed_origins_env = os.getenv("CORS_ORIGINS")
origins = allowed_origins_env.split(',') if allowed_origins_env else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# main.py는 api.py에서 정의된 'app' FastAPI 인스턴스를 노출합니다.
# 추가적인 초기화 로직이나 미들웨어 설정이 필요하면 여기에 추가할 수 있습니다.

# 예시: 애플리케이션 시작 시 메시지 출력
@app.on_event("startup")
async def startup_event():
    print("TrustFlow API is running! Let's explore DeFi together 🚀")
    print(f"CORS origins configured: {origins}")

@app.on_event("shutdown")
async def shutdown_event():
    print("👋 The TrustFlow FastAPI application shuts down.")
