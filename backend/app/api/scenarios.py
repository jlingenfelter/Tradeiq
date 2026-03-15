from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.tier_gate import require_pro
from app.core.exceptions import BadRequestError
from app.models.user import User
from app.services.scenario_service import (
    run_mortgage_payoff,
    run_savings_projection,
    run_asset_change,
    run_debt_snowball,
)

router = APIRouter(prefix="/scenarios", tags=["scenarios"])

SCENARIO_RUNNERS = {
    "mortgage_payoff": run_mortgage_payoff,
    "savings_projection": run_savings_projection,
    "asset_change": run_asset_change,
    "debt_snowball": run_debt_snowball,
}


class ScenarioRunRequest(BaseModel):
    scenario_type: str
    params: dict


# ── POST /scenarios/run ─────────────────────────────────────────────────
@router.post("/run")
def post_run_scenario(
    body: ScenarioRunRequest,
    current_user: User = Depends(require_pro),
    db: Session = Depends(get_db),
):
    """Run a what-if scenario and return projections."""
    runner = SCENARIO_RUNNERS.get(body.scenario_type)
    if not runner:
        raise BadRequestError(
            f"Unknown scenario type '{body.scenario_type}'. "
            f"Available: {', '.join(SCENARIO_RUNNERS.keys())}"
        )

    try:
        result = runner(**body.params)
    except TypeError as e:
        raise BadRequestError(f"Invalid params for '{body.scenario_type}': {e}")

    return result
