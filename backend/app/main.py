import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import engine, Base
import app.models  # noqa: F401 — register all models with Base.metadata
from app.api.auth import router as auth_router
from app.api.portfolios import router as portfolios_router
from app.api.positions import router as positions_router
from app.api.ingestion import router as ingestion_router
from app.api.analytics import router as analytics_router
from app.api.warnings import router as warnings_router
from app.api.dashboard import router as dashboard_router
from app.api.chat import router as chat_router
from app.api.alerts import router as alerts_router
from app.api.containers import router as containers_router
from app.api.assets import router as assets_router
from app.api.liabilities import router as liabilities_router
from app.api.wealth_dashboard import router as wealth_dashboard_router
from app.api.trading212 import router as trading212_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Wealth Copilot",
    description="AI-powered wealth tracking and portfolio monitoring platform",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth
app.include_router(auth_router)

# Wealth tracking
app.include_router(containers_router)
app.include_router(assets_router)
app.include_router(liabilities_router)
app.include_router(wealth_dashboard_router)

# Portfolio (investment submodule)
app.include_router(portfolios_router)
app.include_router(positions_router)
app.include_router(ingestion_router)
app.include_router(analytics_router)
app.include_router(warnings_router)
app.include_router(dashboard_router)

# AI & chat
app.include_router(chat_router)

# Broker integrations
app.include_router(trading212_router)

# Alerts
app.include_router(alerts_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    print(f"Unhandled error: {exc}\n{tb}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        },
    )


@app.get("/health")
def health_check():
    return {"status": "ok"}
