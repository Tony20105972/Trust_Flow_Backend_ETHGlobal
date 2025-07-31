from fastapi import FastAPI
from TrustFlow.api import router as api_router # Ensure this import path is correct
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="TrustFlow API",
    description="Backend API for TrustFlow dApp with AI Contract Generation, DAO, ZK, IPFS, 1inch, and LOP features.",
    version="0.1.0",
)

# Add CORS settings (essential for frontend connection)
# For production, it's a good security practice to restrict `allow_origins` to your frontend's specific domain(s).
origins = [
    "http://localhost",
    "http://localhost:3000", # React development server address
    "http://localhost:8000", # FastAPI development server address
    # "https://your-frontend-domain.com", # Actual frontend deployment domain
    # "https://your-render-backend-url.onrender.com" # If the backend needs to call itself
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the API router from TrustFlow/api.py
app.include_router(api_router)

@app.get("/")
async def root():
    """Root endpoint for basic health check."""
    return {"message": "TrustFlow API is running! Access /docs for API documentation."}
