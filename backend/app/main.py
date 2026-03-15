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
from app.api.connections import router as connections_router
from app.api.trading212 import router as trading212_router
from app.api.alpaca import router as alpaca_router
from app.api.ibkr import router as ibkr_router
from app.api.ig import router as ig_router
from app.api.tradier import router as tradier_router
from app.api.crypto_wallet import router as crypto_wallet_router
from app.api.moneybox import router as moneybox_router
from app.api.kraken import router as kraken_router
from app.api.goals import router as goals_router
from app.api.recap import router as recap_router
from app.api.insights import router as insights_router
from app.api.smart_alerts import router as smart_alerts_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    # Add new columns to existing tables (create_all doesn't alter tables)
    from sqlalchemy import text, inspect
    with engine.connect() as conn:
        inspector = inspect(engine)
        existing_cols = [c["name"] for c in inspector.get_columns("accounts")]
        migrations = {
            "encrypted_credentials": "ALTER TABLE accounts ADD COLUMN encrypted_credentials TEXT",
            "environment": "ALTER TABLE accounts ADD COLUMN environment VARCHAR(20)",
            "auto_sync": "ALTER TABLE accounts ADD COLUMN auto_sync BOOLEAN DEFAULT false NOT NULL",
            "last_synced_at": "ALTER TABLE accounts ADD COLUMN last_synced_at TIMESTAMP WITH TIME ZONE",
            "sync_error": "ALTER TABLE accounts ADD COLUMN sync_error TEXT",
        }
        for col_name, sql in migrations.items():
            if col_name not in existing_cols:
                try:
                    conn.execute(text(sql))
                except Exception:
                    pass
        conn.commit()
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

# Broker integrations & connections
app.include_router(connections_router)
app.include_router(trading212_router)
app.include_router(alpaca_router)
app.include_router(ibkr_router)
app.include_router(ig_router)
app.include_router(tradier_router)
app.include_router(crypto_wallet_router)
app.include_router(moneybox_router)
app.include_router(kraken_router)

# Goals & gamification
app.include_router(goals_router)
app.include_router(recap_router)
app.include_router(insights_router)
app.include_router(smart_alerts_router)

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
