"""Main API router combining all routes."""

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from config import get_settings

from api.auth import router as auth_router
from api.user import router as user_router
from api.activity import router as activity_router
from api.rewards import router as rewards_router
from api.public import router as public_router
from api.agent import router as agent_router
from api.ai_routes import router as ai_routes_router
from api.agent import router as agent_router

# Create main app
app = FastAPI(
    title="DRP API",
    description="Decentralized Rights Protocol API",
    version="1.0.0"
)

# CORS middleware
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api", tags=["Authentication"])
app.include_router(user_router, prefix="/api", tags=["Users"])
app.include_router(activity_router, prefix="/api", tags=["Activities"])
app.include_router(rewards_router, prefix="/api", tags=["Rewards"])
app.include_router(public_router, tags=["Public API"])
app.include_router(agent_router, tags=["AI Agents"])
app.include_router(ai_routes_router, tags=["AI ElderCore"])

# Agent endpoints (no additional prefix so paths match spec, e.g. /get_user_status)
app.include_router(agent_router, tags=["Agents"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "DRP API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}

