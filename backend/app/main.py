from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.auth import router as auth_router
from app.api.portfolios import router as portfolios_router
from app.api.positions import router as positions_router
from app.api.ingestion import router as ingestion_router

app = FastAPI(
    title="Portfolio Copilot",
    description="AI-powered portfolio monitoring platform",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(portfolios_router)
app.include_router(positions_router)
app.include_router(ingestion_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
