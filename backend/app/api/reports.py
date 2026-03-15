from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.tier_gate import require_pro
from app.core.exceptions import BadRequestError
from app.models.user import User
from app.services.export_service import (
    export_net_worth_csv,
    export_net_worth_pdf,
    generate_monthly_report,
    generate_tax_summary,
    RANGE_DAYS,
)

router = APIRouter(prefix="/reports", tags=["reports"])


# ── GET /reports/net-worth ──────────────────────────────────────────────
@router.get("/net-worth")
def get_net_worth_report(
    format: str = Query("csv", description="csv or pdf"),
    range: str = Query("all", description="90d, 1y, 5y, or all"),
    current_user: User = Depends(require_pro),
    db: Session = Depends(get_db),
):
    """Export net worth history as CSV or PDF."""
    if format not in ("csv", "pdf"):
        raise BadRequestError("Format must be 'csv' or 'pdf'")
    if range not in RANGE_DAYS:
        raise BadRequestError("Range must be one of: 90d, 1y, 5y, all")

    days_limit = RANGE_DAYS[range]

    if format == "csv":
        data = export_net_worth_csv(db, current_user.id, days_limit)
        return Response(
            content=data,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=net-worth-report.csv"},
        )
    else:
        data = export_net_worth_pdf(db, current_user.id, days_limit)
        return Response(
            content=data,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=net-worth-report.pdf"},
        )


# ── GET /reports/monthly ────────────────────────────────────────────────
@router.get("/monthly")
def get_monthly_report(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2020, le=2100),
    current_user: User = Depends(require_pro),
    db: Session = Depends(get_db),
):
    """Generate a monthly net worth PDF report."""
    data = generate_monthly_report(db, current_user.id, month, year)
    filename = f"monthly-report-{year}-{month:02d}.pdf"
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ── GET /reports/tax-summary ────────────────────────────────────────────
@router.get("/tax-summary")
def get_tax_summary(
    year: int = Query(..., ge=2020, le=2100),
    current_user: User = Depends(require_pro),
    db: Session = Depends(get_db),
):
    """Generate a tax summary PDF for a given year."""
    data = generate_tax_summary(db, current_user.id, year)
    filename = f"tax-summary-{year}.pdf"
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
