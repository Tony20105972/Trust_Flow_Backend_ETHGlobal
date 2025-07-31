# TrustFlow/main.py
# 이 파일은 FastAPI 애플리케이션의 진입점 역할을 합니다.
# uvicorn trustflow.main:app --reload 와 같이 실행될 때,
# 'trustflow' 패키지 내의 'main' 모듈에서 'app' 객체를 찾습니다.

from .api import app

# main.py는 api.py에서 정의된 'app' FastAPI 인스턴스를 노출합니다.
# 추가적인 초기화 로직이나 미들웨어 설정이 필요하면 여기에 추가할 수 있습니다.

# 예시: 애플리케이션 시작 시 메시지 출력
@app.on_event("startup")
async def startup_event():
    print(“TrustFlow API is running! Let's explore DeFi together 🚀”)

@app.on_event("shutdown")
async def shutdown_event():
    print("👋 The TrustFlow FastAPI application shuts down.”)

# 이 파일은 주로 uvicorn이 `app` 객체를 찾을 수 있도록 돕는 역할을 합니다.
# 실제 API 엔드포인트 로직은 api.py에 있습니다.
