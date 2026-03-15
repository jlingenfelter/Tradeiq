import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage
from app.schemas.chat import ChatRequest, ChatResponse, ChatSessionResponse, ChatMessageResponse
from app.services.portfolio_service import get_portfolio
from app.services.ai_service import (
    answer_portfolio_question, generate_portfolio_summary,
    answer_wealth_question, generate_wealth_summary,
)

router = APIRouter(tags=["chat"])


# ── Wealth-level chat ──

@router.post("/ai/chat", response_model=ChatResponse)
def chat_about_wealth(
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    answer, session_id = answer_wealth_question(
        db, body.question, current_user.id, body.session_id,
    )
    return ChatResponse(answer=answer, session_id=session_id)


@router.post("/ai/summary")
def get_wealth_ai_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    summary = generate_wealth_summary(db, current_user.id)
    return {"summary": summary}


@router.get("/ai/chat/sessions", response_model=list[ChatSessionResponse])
def list_wealth_chat_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == current_user.id, ChatSession.portfolio_id.is_(None))
        .order_by(ChatSession.updated_at.desc())
        .limit(20)
        .all()
    )
    return [ChatSessionResponse(
        id=str(s.id), portfolio_id=str(s.portfolio_id) if s.portfolio_id else None,
        created_at=s.created_at, updated_at=s.updated_at,
    ) for s in sessions]


@router.get("/ai/chat/sessions/{session_id}", response_model=ChatSessionResponse)
def get_wealth_chat_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id, ChatSession.user_id == current_user.id
    ).first()
    if not session:
        raise NotFoundError("Chat session not found")

    messages = [ChatMessageResponse(
        id=str(m.id), role=m.role, content=m.content, created_at=m.created_at,
    ) for m in session.messages]

    return ChatSessionResponse(
        id=str(session.id), portfolio_id=str(session.portfolio_id) if session.portfolio_id else None,
        created_at=session.created_at, updated_at=session.updated_at,
        messages=messages,
    )


# ── Portfolio-level chat (backward compatible) ──

@router.post("/portfolios/{portfolio_id}/chat", response_model=ChatResponse)
def chat_with_portfolio(
    portfolio_id: uuid.UUID,
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    portfolio = get_portfolio(db, portfolio_id, current_user)
    answer, session_id = answer_portfolio_question(
        db, str(portfolio.id), body.question, current_user.id, body.session_id,
    )
    return ChatResponse(answer=answer, session_id=session_id)


@router.post("/portfolios/{portfolio_id}/ai-summary")
def get_portfolio_ai_summary(
    portfolio_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    portfolio = get_portfolio(db, portfolio_id, current_user)
    summary = generate_portfolio_summary(db, str(portfolio.id), current_user.id)
    return {"summary": summary}
