import csv
import io
import uuid
from typing import BinaryIO

from sqlalchemy.orm import Session

from app.models.portfolio import Account
from app.models.position import Position
from app.core.exceptions import BadRequestError

# In-memory store for CSV upload previews (use Redis in production)
_csv_uploads: dict[str, dict] = {}

KNOWN_COLUMN_ALIASES = {
    "symbol": ["symbol", "ticker", "stock", "sym"],
    "quantity": ["quantity", "shares", "qty", "amount"],
    "cost_basis_per_share": ["avg_cost", "cost_basis", "cost_per_share", "avg_price", "purchase_price"],
    "cost_basis_total": ["total_cost", "cost_basis_total", "total_cost_basis"],
    "asset_name": ["name", "company", "company_name", "asset_name", "description"],
    "currency": ["currency", "ccy"],
}


def auto_map_columns(csv_columns: list[str]) -> dict[str, str]:
    mapping = {}
    lower_cols = {c.lower().strip(): c for c in csv_columns}
    for field, aliases in KNOWN_COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in lower_cols:
                mapping[lower_cols[alias]] = field
                break
    return mapping


def parse_csv_upload(file: BinaryIO, filename: str) -> dict:
    try:
        content = file.read().decode("utf-8-sig")
    except UnicodeDecodeError:
        raise BadRequestError("File must be UTF-8 encoded CSV")

    reader = csv.DictReader(io.StringIO(content))
    if not reader.fieldnames:
        raise BadRequestError("CSV file has no headers")

    rows = []
    for i, row in enumerate(reader):
        if i >= 500:  # limit preview
            break
        rows.append(row)

    if not rows:
        raise BadRequestError("CSV file has no data rows")

    upload_id = str(uuid.uuid4())
    _csv_uploads[upload_id] = {
        "rows": rows,
        "columns": list(reader.fieldnames),
        "filename": filename,
    }

    return {
        "preview": rows[:10],
        "columns": list(reader.fieldnames),
        "row_count": len(rows),
        "upload_id": upload_id,
        "suggested_mapping": auto_map_columns(list(reader.fieldnames)),
    }


def confirm_csv_import(
    db: Session,
    upload_id: str,
    column_mapping: dict[str, str],
    account: Account,
) -> dict:
    upload_data = _csv_uploads.pop(upload_id, None)
    if not upload_data:
        raise BadRequestError("Upload not found or expired")

    rows = upload_data["rows"]
    imported = 0
    skipped = 0
    errors = []

    # Reverse mapping: field_name -> csv_column
    field_to_csv = {v: k for k, v in column_mapping.items()}

    if "symbol" not in field_to_csv:
        raise BadRequestError("Column mapping must include 'symbol'")
    if "quantity" not in field_to_csv:
        raise BadRequestError("Column mapping must include 'quantity'")

    for i, row in enumerate(rows):
        try:
            symbol = row.get(field_to_csv["symbol"], "").strip().upper()
            if not symbol:
                skipped += 1
                continue

            qty_str = row.get(field_to_csv["quantity"], "").strip()
            if not qty_str:
                skipped += 1
                continue
            quantity = float(qty_str.replace(",", ""))

            asset_name = symbol
            if "asset_name" in field_to_csv:
                asset_name = row.get(field_to_csv["asset_name"], symbol).strip() or symbol

            cost_basis_per_share = None
            if "cost_basis_per_share" in field_to_csv:
                val = row.get(field_to_csv["cost_basis_per_share"], "").strip().replace(",", "").replace("$", "")
                if val:
                    cost_basis_per_share = float(val)

            cost_basis_total = None
            if "cost_basis_total" in field_to_csv:
                val = row.get(field_to_csv["cost_basis_total"], "").strip().replace(",", "").replace("$", "")
                if val:
                    cost_basis_total = float(val)

            if cost_basis_per_share and not cost_basis_total:
                cost_basis_total = cost_basis_per_share * quantity

            currency = "USD"
            if "currency" in field_to_csv:
                currency = row.get(field_to_csv["currency"], "USD").strip().upper() or "USD"

            position = Position(
                account_id=account.id,
                symbol=symbol,
                asset_name=asset_name,
                asset_type="equity",
                quantity=quantity,
                cost_basis_total=cost_basis_total,
                cost_basis_per_share=cost_basis_per_share,
                currency=currency,
            )
            db.add(position)
            imported += 1
        except (ValueError, KeyError) as e:
            errors.append(f"Row {i + 1}: {str(e)}")
            skipped += 1

    db.commit()
    return {"imported": imported, "skipped": skipped, "errors": errors[:20]}
