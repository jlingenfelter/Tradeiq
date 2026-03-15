import uuid

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.position import CsvUploadResponse, CsvConfirmRequest, CsvImportResult
from app.services.portfolio_service import get_portfolio, create_account
from app.services.ingestion_service import parse_csv_upload, confirm_csv_import
from app.services.audit_service import log_event

router = APIRouter(tags=["ingestion"])


@router.post("/portfolios/{portfolio_id}/import/csv", response_model=CsvUploadResponse)
async def upload_csv(
    portfolio_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_portfolio(db, portfolio_id, current_user)  # verify ownership

    if not file.filename or not file.filename.endswith(".csv"):
        from app.core.exceptions import BadRequestError
        raise BadRequestError("File must be a CSV")

    result = parse_csv_upload(file.file, file.filename)
    return CsvUploadResponse(
        preview=result["preview"],
        columns=result["columns"],
        row_count=result["row_count"],
        upload_id=result["upload_id"],
    )


@router.post("/portfolios/{portfolio_id}/import/csv/confirm", response_model=CsvImportResult)
def confirm_csv(
    portfolio_id: uuid.UUID,
    body: CsvConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    portfolio = get_portfolio(db, portfolio_id, current_user)
    account = create_account(db, portfolio, body.account_name, "csv")

    result = confirm_csv_import(db, body.upload_id, body.column_mapping, account)
    log_event(db, current_user.id, "csv_import", {
        "portfolio_id": str(portfolio_id),
        "imported": result["imported"],
        "skipped": result["skipped"],
    }, portfolio_id=portfolio_id)
    return CsvImportResult(**result)
