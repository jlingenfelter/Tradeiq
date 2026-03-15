import uuid
import json
from datetime import datetime, timezone

import anthropic
from sqlalchemy.orm import Session

from app.config import settings
from app.models.analytics import AnalyticsSnapshot
from app.models.warning import Warning
from app.models.chat import ChatSession, ChatMessage
from app.services.audit_service import log_event

SYSTEM_PROMPT = """You are Portfolio Copilot, an AI assistant that helps users understand their investment portfolio.

CRITICAL RULES:
1. You ONLY explain data that is provided to you in the structured context. Never invent holdings, prices, weights, or any portfolio data.
2. You are a read-only monitoring tool. You do NOT execute trades, rebalance portfolios, or act as a broker.
3. Use cautious, analytical language. Never guarantee outcomes or promise returns.
4. Do NOT give direct buy/sell/hold recommendations. Instead, highlight risks, exposures, and areas to review.
5. Always cite actual values from the provided data when making claims.
6. If asked about something not in the data, say so clearly.

LANGUAGE GUIDELINES:
- Prefer: "monitor", "analyze", "detect", "review", "highlight", "explain"
- Prefer: "This creates concentration risk", "Your exposure is higher than benchmarks", "Consider reviewing this exposure"
- Avoid: "You should buy/sell", "Guaranteed", "Best investment", "This stock will outperform"
- Avoid: certainty about future performance, unsupported macro predictions

RESPONSE STYLE:
- Start with a concise direct answer
- Follow with supporting evidence using actual numbers
- Keep responses focused and practical
- Do not ramble about general market conditions unless directly relevant"""


def _build_portfolio_context(db: Session, portfolio_id: str) -> dict:
    """Build the structured context packet that the AI receives."""
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
    except Exception as e:
        return f"Unable to generate AI summary at this time."


def answer_portfolio_question(
    db: Session,
    portfolio_id: str,
    question: str,
    user_id: uuid.UUID,
    session_id: str | None = None,
) -> tuple[str, str]:
    """Answer a user's portfolio question. Returns (answer, session_id)."""
    context = _build_portfolio_context(db, portfolio_id)

    # Get or create chat session
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
    for msg in previous[:-1]:  # Exclude the just-added user message (we'll add it fresh)
        messages.append({"role": msg.role, "content": msg.content})

    # Add current question with context
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

        # Save assistant message
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
    except Exception as e:
        db.rollback()
        return "I'm unable to process your question right now. Please try again.", str(chat_session.id)
