"""Export service — CSV & PDF reports for net worth, monthly summaries, tax summaries."""

import io
import csv
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session

from app.models.wealth import WealthSnapshot, Asset, Liability
from app.models.user import User


RANGE_DAYS = {
    "90d": 90,
    "1y": 365,
    "5y": 365 * 5,
    "all": None,
}


def export_net_worth_csv(db: Session, user_id: uuid.UUID, days_limit: int | None = None) -> bytes:
    """Export net worth history as CSV."""
    q = db.query(WealthSnapshot).filter(WealthSnapshot.user_id == user_id)
    if days_limit:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_limit)
        q = q.filter(WealthSnapshot.snapshot_time >= cutoff)
    snapshots = q.order_by(WealthSnapshot.snapshot_time.asc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Date", "Total Assets", "Total Liabilities", "Net Worth",
        "Liquid Assets", "Illiquid Assets", "Cash", "Investments",
        "Property", "Crypto", "Business", "Pension", "Debt",
    ])
    for s in snapshots:
        writer.writerow([
            s.snapshot_time.strftime("%Y-%m-%d") if s.snapshot_time else "",
            round(s.total_assets, 2),
            round(s.total_liabilities, 2),
            round(s.net_worth, 2),
            round(s.liquid_assets, 2),
            round(s.illiquid_assets, 2),
            round(s.cash_value, 2),
            round(s.investment_value, 2),
            round(s.property_value, 2),
            round(s.crypto_value, 2),
            round(s.business_value, 2),
            round(s.pension_value, 2),
            round(s.debt_value, 2),
        ])

    return output.getvalue().encode("utf-8")


def export_net_worth_pdf(db: Session, user_id: uuid.UUID, days_limit: int | None = None) -> bytes:
    """Export net worth history as a simple PDF using reportlab."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet

    q = db.query(WealthSnapshot).filter(WealthSnapshot.user_id == user_id)
    if days_limit:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_limit)
        q = q.filter(WealthSnapshot.snapshot_time >= cutoff)
    snapshots = q.order_by(WealthSnapshot.snapshot_time.asc()).all()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Net Worth Report", styles["Title"]))
    elements.append(Spacer(1, 12))

    user = db.query(User).filter(User.id == user_id).first()
    if user:
        elements.append(Paragraph(f"User: {user.email}", styles["Normal"]))
    elements.append(Paragraph(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", styles["Normal"]))
    elements.append(Spacer(1, 20))

    # Summary table
    if snapshots:
        latest = snapshots[-1]
        summary_data = [
            ["Metric", "Value"],
            ["Total Assets", f"${latest.total_assets:,.2f}"],
            ["Total Liabilities", f"${latest.total_liabilities:,.2f}"],
            ["Net Worth", f"${latest.net_worth:,.2f}"],
            ["Liquid Net Worth", f"${latest.liquid_net_worth:,.2f}"],
        ]
        summary_table = Table(summary_data, colWidths=[200, 200])
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 20))

    # History table (last 30 entries max for readability)
    display_snapshots = snapshots[-30:] if len(snapshots) > 30 else snapshots
    if display_snapshots:
        history_data = [["Date", "Assets", "Liabilities", "Net Worth"]]
        for s in display_snapshots:
            history_data.append([
                s.snapshot_time.strftime("%Y-%m-%d") if s.snapshot_time else "",
                f"${s.total_assets:,.2f}",
                f"${s.total_liabilities:,.2f}",
                f"${s.net_worth:,.2f}",
            ])
        history_table = Table(history_data, colWidths=[100, 130, 130, 130])
        history_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
        ]))
        elements.append(Paragraph("Net Worth History", styles["Heading2"]))
        elements.append(history_table)

    doc.build(elements)
    return buffer.getvalue()


def generate_monthly_report(db: Session, user_id: uuid.UUID, month: int, year: int) -> bytes:
    """Generate a monthly net worth PDF report."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet

    # Get snapshots for the given month
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    if month == 12:
        end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(year, month + 1, 1, tzinfo=timezone.utc)

    snapshots = db.query(WealthSnapshot).filter(
        WealthSnapshot.user_id == user_id,
        WealthSnapshot.snapshot_time >= start,
        WealthSnapshot.snapshot_time < end,
    ).order_by(WealthSnapshot.snapshot_time.asc()).all()

    # Also get the previous month's last snapshot for comparison
    prev_snapshot = db.query(WealthSnapshot).filter(
        WealthSnapshot.user_id == user_id,
        WealthSnapshot.snapshot_time < start,
    ).order_by(WealthSnapshot.snapshot_time.desc()).first()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    month_name = start.strftime("%B %Y")
    elements.append(Paragraph(f"Monthly Report: {month_name}", styles["Title"]))
    elements.append(Spacer(1, 20))

    if snapshots:
        latest = snapshots[-1]
        prev_nw = prev_snapshot.net_worth if prev_snapshot else 0.0
        change = latest.net_worth - prev_nw
        change_pct = (change / prev_nw * 100) if prev_nw != 0 else 0.0

        summary_data = [
            ["Metric", "Value"],
            ["Net Worth (End of Month)", f"${latest.net_worth:,.2f}"],
            ["Net Worth (Previous Month)", f"${prev_nw:,.2f}"],
            ["Change", f"${change:+,.2f} ({change_pct:+.1f}%)"],
            ["Total Assets", f"${latest.total_assets:,.2f}"],
            ["Total Liabilities", f"${latest.total_liabilities:,.2f}"],
        ]
        summary_table = Table(summary_data, colWidths=[220, 220])
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ]))
        elements.append(summary_table)
    else:
        elements.append(Paragraph("No snapshot data available for this month.", styles["Normal"]))

    doc.build(elements)
    return buffer.getvalue()


def generate_tax_summary(db: Session, user_id: uuid.UUID, year: int) -> bytes:
    """Generate a yearly tax summary PDF showing asset/liability breakdown."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet

    start = datetime(year, 1, 1, tzinfo=timezone.utc)
    end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)

    # Get start and end of year snapshots
    start_snapshot = db.query(WealthSnapshot).filter(
        WealthSnapshot.user_id == user_id,
        WealthSnapshot.snapshot_time >= start,
        WealthSnapshot.snapshot_time < end,
    ).order_by(WealthSnapshot.snapshot_time.asc()).first()

    end_snapshot = db.query(WealthSnapshot).filter(
        WealthSnapshot.user_id == user_id,
        WealthSnapshot.snapshot_time >= start,
        WealthSnapshot.snapshot_time < end,
    ).order_by(WealthSnapshot.snapshot_time.desc()).first()

    # Get current assets & liabilities for breakdown
    assets = db.query(Asset).filter(Asset.user_id == user_id).all()
    liabilities = db.query(Liability).filter(Liability.user_id == user_id).all()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"Tax Summary: {year}", styles["Title"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        styles["Normal"],
    ))
    elements.append(Spacer(1, 20))

    # Year-over-year summary
    if start_snapshot and end_snapshot:
        change = end_snapshot.net_worth - start_snapshot.net_worth
        summary_data = [
            ["Metric", "Value"],
            ["Net Worth (Start of Year)", f"${start_snapshot.net_worth:,.2f}"],
            ["Net Worth (End of Year)", f"${end_snapshot.net_worth:,.2f}"],
            ["Net Change", f"${change:+,.2f}"],
            ["Investment Growth", f"${end_snapshot.investment_value - start_snapshot.investment_value:+,.2f}"],
        ]
        summary_table = Table(summary_data, colWidths=[220, 220])
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ]))
        elements.append(Paragraph("Year Overview", styles["Heading2"]))
        elements.append(summary_table)
        elements.append(Spacer(1, 20))

    # Assets breakdown
    if assets:
        elements.append(Paragraph("Assets", styles["Heading2"]))
        asset_data = [["Name", "Class", "Value", "Cost Basis"]]
        for a in sorted(assets, key=lambda x: x.current_value, reverse=True):
            asset_data.append([
                a.name[:40],
                a.asset_class,
                f"${a.current_value:,.2f}",
                f"${a.cost_basis:,.2f}" if a.cost_basis else "N/A",
            ])
        asset_table = Table(asset_data, colWidths=[150, 80, 100, 100])
        asset_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
        ]))
        elements.append(asset_table)
        elements.append(Spacer(1, 20))

    # Liabilities breakdown
    if liabilities:
        elements.append(Paragraph("Liabilities", styles["Heading2"]))
        liab_data = [["Name", "Type", "Balance", "Interest Rate"]]
        for l in sorted(liabilities, key=lambda x: x.current_balance, reverse=True):
            liab_data.append([
                l.name[:40],
                l.liability_type,
                f"${l.current_balance:,.2f}",
                f"{l.interest_rate:.2f}%" if l.interest_rate else "N/A",
            ])
        liab_table = Table(liab_data, colWidths=[150, 80, 100, 100])
        liab_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
        ]))
        elements.append(liab_table)

    doc.build(elements)
    return buffer.getvalue()
