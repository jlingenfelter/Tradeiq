import csv
import io
import uuid
from typing import BinaryIO

from sqlalchemy.orm import Session

from app.models.portfolio import Account
from app.models.position import Position
from app.core.exceptions import BadRequestError
from app.services.name_resolver import resolve_stock_names

# In-memory store for CSV upload previews (use Redis in production)
_csv_uploads: dict[str, dict] = {}

KNOWN_COLUMN_ALIASES = {
    "symbol": ["symbol", "ticker", "stock", "sym"],
    "quantity": ["quantity", "shares", "qty", "amount", "no. of shares"],
    "cost_basis_per_share": ["avg_cost", "cost_basis", "cost_per_share", "avg_price", "purchase_price", "price / share"],
    "cost_basis_total": ["total_cost", "cost_basis_total", "total_cost_basis", "total"],
    "asset_name": ["name", "company", "company_name", "asset_name", "description"],
    "currency": ["currency", "ccy", "currency (price / share)"],
    "action": ["action"],
    "isin": ["isin"],
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


def _is_trading212_format(columns: list[str]) -> bool:
    lower_cols = {c.lower().strip() for c in columns}
    return "action" in lower_cols and "ticker" in lower_cols and "no. of shares" in lower_cols


def _aggregate_trading212_rows(rows: list[dict], columns: list[str]) -> list[dict]:
    """Aggregate Trading 212 transaction rows into net positions."""
    col_map = {c.lower().strip(): c for c in columns}
    action_col = col_map.get("action", "Action")
    ticker_col = col_map.get("ticker", "Ticker")
    name_col = col_map.get("name", "Name")
    shares_col = col_map.get("no. of shares", "No. of shares")
    price_col = col_map.get("price / share", "Price / share")
    currency_col = col_map.get("currency (price / share)", "Currency (Price / share)")

    positions: dict[str, dict] = {}
    for row in rows:
        action = row.get(action_col, "").strip()
        if action not in ("Market buy", "Limit buy", "Market sell", "Limit sell",
                          "Buy", "Sell", "Stop buy", "Stop sell"):
            continue

        ticker = row.get(ticker_col, "").strip()
        if not ticker:
            continue

        try:
            qty = float(row.get(shares_col, "0").strip().replace(",", ""))
        except ValueError:
            continue

        price_str = row.get(price_col, "").strip().replace(",", "").replace("$", "").replace("£", "").replace("€", "")
        try:
            price = float(price_str) if price_str else 0
        except ValueError:
            price = 0

        is_sell = "sell" in action.lower()

        if ticker not in positions:
            positions[ticker] = {
                "symbol": ticker,
                "name": row.get(name_col, ticker).strip(),
                "quantity": 0,
                "total_cost": 0,
                "currency": row.get(currency_col, "USD").strip() if currency_col in row else "USD",
            }

        if is_sell:
            positions[ticker]["quantity"] -= qty
        else:
            positions[ticker]["quantity"] += qty
            positions[ticker]["total_cost"] += qty * price

    # Convert to row format, filter out closed positions
    result = []
    for ticker, pos in positions.items():
        if pos["quantity"] > 0.0001:
            avg_price = pos["total_cost"] / pos["quantity"] if pos["quantity"] > 0 else 0
            result.append({
                "Ticker": pos["symbol"],
                "Name": pos["name"],
                "No. of shares": str(pos["quantity"]),
                "Price / share": f"{avg_price:.4f}",
                "Currency (Price / share)": pos["currency"],
            })
    return result


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

    columns = list(reader.fieldnames)
    is_t212 = _is_trading212_format(columns)

    if is_t212:
        # Aggregate transactions into net positions
        rows = _aggregate_trading212_rows(rows, columns)
        columns = ["Ticker", "Name", "No. of shares", "Price / share", "Currency (Price / share)"]

    upload_id = str(uuid.uuid4())
    _csv_uploads[upload_id] = {
        "rows": rows,
        "columns": columns,
        "filename": filename,
    }

    return {
        "preview": rows[:10],
        "columns": columns,
        "row_count": len(rows),
        "upload_id": upload_id,
        "suggested_mapping": auto_map_columns(columns),
        "detected_format": "trading212" if is_t212 else "generic",
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

    db.flush()

    # Resolve full names for positions that only have a symbol as name
    symbol_only_positions = [p for p in db.new if isinstance(p, Position) and p.asset_name == p.symbol]
    if symbol_only_positions:
        symbols_needing_names = [p.symbol for p in symbol_only_positions]
        name_map = resolve_stock_names(db, symbols_needing_names)
        for p in symbol_only_positions:
            resolved = name_map.get(p.symbol.upper(), p.symbol)
            if resolved != p.symbol:
                p.asset_name = resolved

    db.commit()
    return {"imported": imported, "skipped": skipped, "errors": errors[:20]}
