import uuid
import json
from datetime import datetime, timezone

import anthropic
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User
from app.models.wealth import Asset, Liability, WealthSnapshot, AllocationSnapshot
from app.models.analytics import AnalyticsSnapshot
from app.models.warning import Warning
from app.models.chat import ChatSession, ChatMessage
from app.services.audit_service import log_event

SYSTEM_PROMPT = """You are Wealth Copilot, an AI assistant that helps users understand their personal wealth and financial picture.

CRITICAL RULES:
1. You ONLY explain data that is provided to you in the structured context. Never invent assets, values, prices, weights, or any financial data.
2. You are a read-only monitoring tool. You do NOT execute trades, move money, rebalance portfolios, or act as a broker or financial adviser.
3. Use cautious, analytical language. Never guarantee outcomes or promise returns.
4. Do NOT give direct buy/sell/hold recommendations. Instead, highlight risks, exposures, concentrations, and areas to review.
5. Always cite actual values from the provided data when making claims.
6. If asked about something not in the data, say so clearly.

LANGUAGE GUIDELINES:
- Prefer: "monitor", "track", "analyze", "review", "highlight", "explain"
- Prefer: "This creates concentration risk", "Your exposure is notable", "Consider reviewing this allocation"
- Avoid: "You should buy/sell", "Guaranteed", "Best investment", "Beat the market"
- Avoid: certainty about future performance, unsupported predictions

RESPONSE STYLE:
- Start with a concise direct answer
- Follow with supporting evidence using actual numbers
- Keep responses focused and practical
- When describing an issue, explain why it matters and cite the provided figures
- If the user asks for direct financial advice, respond by highlighting the relevant area and suggest reviewing it"""


def _build_wealth_context(db: Session, user_id: uuid.UUID) -> dict:
    """Build the structured context packet for the AI from wealth data."""
    user = db.query(User).filter(User.id == user_id).first()

    # Get latest wealth snapshot
    ws = (
        db.query(WealthSnapshot)
        .filter(WealthSnapshot.user_id == user_id)
        .order_by(WealthSnapshot.snapshot_time.desc())
        .first()
    )

    # Get allocation snapshot
    alloc = None
    if ws:
        alloc = (
            db.query(AllocationSnapshot)
            .filter(AllocationSnapshot.wealth_snapshot_id == ws.id)
            .first()
        )

    # Get assets summary
    assets = db.query(Asset).filter(Asset.user_id == user_id).order_by(Asset.current_value.desc()).all()
    liabilities = db.query(Liability).filter(Liability.user_id == user_id).all()

    if not ws:
        return {"error": "No wealth data available"}

    return {
        "wealth_summary": {
            "base_currency": user.base_currency if user else "USD",
            "total_assets": ws.total_assets,
            "total_liabilities": ws.total_liabilities,
            "net_worth": ws.net_worth,
            "liquid_assets": ws.liquid_assets,
            "illiquid_assets": ws.illiquid_assets,
            "liquid_net_worth": ws.liquid_net_worth,
            "cash_value": ws.cash_value,
            "investment_value": ws.investment_value,
            "property_value": ws.property_value,
            "crypto_value": ws.crypto_value,
            "business_value": ws.business_value,
            "pension_value": ws.pension_value,
        },
        "allocation": alloc.asset_class_allocations_json if alloc else [],
        "liquidity_breakdown": alloc.liquidity_allocations_json if alloc else {},
        "top_concentrations": alloc.top_concentrations_json if alloc else [],
        "health_score": alloc.health_score if alloc else 0,
        "health_score_breakdown": alloc.health_score_breakdown_json if alloc else {},
        "warnings": alloc.warnings_json if alloc else [],
        "top_assets": [
            {"name": a.name, "class": a.asset_class, "value": a.current_value, "currency": a.currency}
            for a in assets[:15]
        ],
        "liabilities": [
            {"name": l.name, "type": l.liability_type, "balance": l.current_balance, "currency": l.currency}
            for l in liabilities
        ],
    }


def _build_portfolio_context(db: Session, portfolio_id: str) -> dict:
    """Build the structured context packet for portfolio-level AI."""
    snapshot = (
        db.query(AnalyticsSnapshot)
        .filter(AnalyticsSnapshot.portfolio_id == uuid.UUID(portfolio_id))
        .order_by(AnalyticsSnapshot.created_at.desc())
        .first()
    )
    if not snapshot:
        return {"error": "No analytics data available"}

    warnings = (
        db.query(Warning)
        .filter(Warning.analytics_snapshot_id == snapshot.id)
        .all()
    )

    total_value = snapshot.portfolio_snapshot.total_value if snapshot.portfolio_snapshot else 0

    return {
        "portfolio_summary": {
            "total_value": round(total_value, 2),
            "health_score": snapshot.health_score,
            "health_score_breakdown": snapshot.health_score_breakdown,
            "position_count": len(snapshot.holdings_detail or []),
            "top_holding_weight": round(snapshot.top_holding_weight, 2),
            "top_3_weight": round(snapshot.top_3_weight, 2),
            "diversification_score": round(snapshot.diversification_score, 2),
        },
        "holdings": [
            {
                "symbol": h.get("symbol"),
                "name": h.get("name"),
                "weight": h.get("weight"),
                "market_value": h.get("market_value"),
                "sector": h.get("sector"),
                "country": h.get("country"),
                "unrealized_pnl": h.get("unrealized_pnl"),
            }
            for h in (snapshot.holdings_detail or [])[:20]
        ],
        "sector_exposure": snapshot.sector_exposure or {},
        "country_exposure": snapshot.country_exposure or {},
        "stress_tests": snapshot.stress_tests or [],
        "warnings": [
            {
                "type": w.warning_type,
                "severity": w.severity,
                "title": w.title,
                "description": w.description,
            }
            for w in warnings
        ],
    }


def generate_wealth_summary(db: Session, user_id: uuid.UUID) -> str:
    """Generate a plain-English wealth summary using AI."""
    context = _build_wealth_context(db, user_id)

    if "error" in context:
        return "No wealth data available yet. Please add assets and liabilities to get started."

    prompt = f"""Based on the following wealth data, provide a concise executive summary (3-5 sentences) covering:
1. Overall financial position and net worth
2. Key strengths of the wealth profile
3. The most significant risk or concern (concentration, liquidity, leverage)
4. One notable observation about the overall allocation

Wealth Context:
{json.dumps(context, indent=2)}"""

    try:
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        summary = response.content[0].text

        log_event(db, user_id, "ai_wealth_summary_generated", {
            "model": "claude-sonnet-4-20250514",
        })

        return summary
    except Exception:
        return "Unable to generate AI summary at this time."


def generate_portfolio_summary(db: Session, portfolio_id: str, user_id: uuid.UUID) -> str:
    """Generate a plain-English portfolio summary using AI."""
    context = _build_portfolio_context(db, portfolio_id)

    if "error" in context:
        return "No analytics data available yet. Please add positions and refresh analytics."

    prompt = f"""Based on the following portfolio data, provide a concise executive summary (3-5 sentences) covering:
1. Overall portfolio health and key strength
2. The most significant risk or concern
3. One notable observation about diversification or exposure

Portfolio Context:
{json.dumps(context, indent=2)}"""

    try:
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        summary = response.content[0].text

        log_event(db, user_id, "ai_summary_generated", {
            "portfolio_id": portfolio_id,
            "model": "claude-sonnet-4-20250514",
        }, portfolio_id=uuid.UUID(portfolio_id))

        return summary
    except Exception:
        return "Unable to generate AI summary at this time."


def answer_wealth_question(
    db: Session,
    question: str,
    user_id: uuid.UUID,
    session_id: str | None = None,
) -> tuple[str, str]:
    """Answer a user's wealth question. Returns (answer, session_id)."""
    context = _build_wealth_context(db, user_id)

    # Get or create chat session
    if session_id:
        chat_session = db.query(ChatSession).filter(ChatSession.id == uuid.UUID(session_id)).first()
    else:
        chat_session = None

    if not chat_session:
        chat_session = ChatSession(user_id=user_id)
        db.add(chat_session)
        db.flush()

    # Save user message
    user_msg = ChatMessage(
        chat_session_id=chat_session.id,
        role="user",
        content=question,
    )
    db.add(user_msg)
    db.flush()

    # Build messages with history
    previous = (
        db.query(ChatMessage)
        .filter(ChatMessage.chat_session_id == chat_session.id)
        .order_by(ChatMessage.created_at)
        .all()
    )

    messages = []
    for msg in previous[:-1]:
        messages.append({"role": msg.role, "content": msg.content})

    user_content = f"""Wealth Context:
{json.dumps(context, indent=2)}

User Question: {question}"""

    messages.append({"role": "user", "content": user_content})

    try:
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=messages,
        )
        answer = response.content[0].text

        assistant_msg = ChatMessage(
            chat_session_id=chat_session.id,
            role="assistant",
            content=answer,
            structured_context_json=context,
            model_name="claude-sonnet-4-20250514",
        )
        db.add(assistant_msg)
        db.commit()

        log_event(db, user_id, "ai_chat_response", {
            "session_id": str(chat_session.id),
            "question_length": len(question),
        })

        return answer, str(chat_session.id)
    except Exception:
        db.rollback()
        return "I'm unable to process your question right now. Please try again.", str(chat_session.id)


def answer_portfolio_question(
    db: Session,
    portfolio_id: str,
    question: str,
    user_id: uuid.UUID,
    session_id: str | None = None,
) -> tuple[str, str]:
    """Answer a user's portfolio question. Returns (answer, session_id)."""
    context = _build_portfolio_context(db, portfolio_id)

    if session_id:
        chat_session = db.query(ChatSession).filter(ChatSession.id == uuid.UUID(session_id)).first()
    else:
        chat_session = None

    if not chat_session:
        chat_session = ChatSession(
            user_id=user_id,
            portfolio_id=uuid.UUID(portfolio_id),
        )
        db.add(chat_session)
        db.flush()

    user_msg = ChatMessage(
        chat_session_id=chat_session.id,
        role="user",
        content=question,
    )
    db.add(user_msg)
    db.flush()

    previous = (
        db.query(ChatMessage)
        .filter(ChatMessage.chat_session_id == chat_session.id)
        .order_by(ChatMessage.created_at)
        .all()
    )

    messages = []
    for msg in previous[:-1]:
        messages.append({"role": msg.role, "content": msg.content})

    user_content = f"""Portfolio Context:
{json.dumps(context, indent=2)}

User Question: {question}"""

    messages.append({"role": "user", "content": user_content})

    try:
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=messages,
        )
        answer = response.content[0].text

        assistant_msg = ChatMessage(
            chat_session_id=chat_session.id,
            role="assistant",
            content=answer,
            structured_context_json=context,
            model_name="claude-sonnet-4-20250514",
        )
        db.add(assistant_msg)
        db.commit()

        log_event(db, user_id, "ai_chat_response", {
            "portfolio_id": portfolio_id,
            "session_id": str(chat_session.id),
            "question_length": len(question),
        }, portfolio_id=uuid.UUID(portfolio_id))

        return answer, str(chat_session.id)
    except Exception:
        db.rollback()
        return "I'm unable to process your question right now. Please try again.", str(chat_session.id)
