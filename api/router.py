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
from api.verification import router as verification_router  # NEW

settings = get_settings()

app = FastAPI(
    title="DRP API",
    description="Decentralized Rights Protocol — Human activity verification, PoAT, PoST, $DeRi rewards.",
    version="1.1.0",
    docs_url="/docs" if getattr(settings, "enable_swagger_ui", True) else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core routers
app.include_router(auth_router, prefix="/api", tags=["Authentication"])
app.include_router(user_router, prefix="/api", tags=["Users"])
app.include_router(activity_router, prefix="/api", tags=["Activities"])
app.include_router(rewards_router, prefix="/api", tags=["Rewards"])
app.include_router(public_router, tags=["Public API"])
app.include_router(agent_router, tags=["AI Agents"])
app.include_router(ai_routes_router, tags=["AI ElderCore"])
app.include_router(verification_router, tags=["Verification"])  # NEW


@app.get("/", tags=["Root"])
async def root():
    return {
        "name": "DRP API",
        "version": "1.1.0",
        "status": "running",
        "docs": "/docs",
        "protocol": "Decentralized Rights Protocol",
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy", "version": "1.1.0"}
