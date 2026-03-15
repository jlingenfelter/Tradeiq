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
from app.services.ai_service import answer_portfolio_question, generate_portfolio_summary

router = APIRouter(tags=["chat"])


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


@router.get("/portfolios/{portfolio_id}/chat/sessions", response_model=list[ChatSessionResponse])
def list_chat_sessions(
    portfolio_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    portfolio = get_portfolio(db, portfolio_id, current_user)
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.portfolio_id == portfolio.id, ChatSession.user_id == current_user.id)
        .order_by(ChatSession.updated_at.desc())
        .limit(20)
        .all()
    )
    return [ChatSessionResponse(
        id=str(s.id), portfolio_id=str(s.portfolio_id),
        created_at=s.created_at, updated_at=s.updated_at,
    ) for s in sessions]


@router.get("/chat/sessions/{session_id}", response_model=ChatSessionResponse)
def get_chat_session(
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
        id=str(session.id), portfolio_id=str(session.portfolio_id),
        created_at=session.created_at, updated_at=session.updated_at,
        messages=messages,
    )


@router.post("/portfolios/{portfolio_id}/ai-summary")
def get_ai_summary(
    portfolio_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    portfolio = get_portfolio(db, portfolio_id, current_user)
    summary = generate_portfolio_summary(db, str(portfolio.id), current_user.id)
    return {"summary": summary}
