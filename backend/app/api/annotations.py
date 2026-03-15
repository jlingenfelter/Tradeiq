import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.tier_gate import require_pro
from app.core.exceptions import NotFoundError
from app.models.user import User
from app.models.annotation import NetWorthAnnotation

router = APIRouter(prefix="/annotations", tags=["annotations"])


class AnnotationCreateRequest(BaseModel):
    annotation_date: str
    label: str
    description: str | None = None
    emoji: str = "\U0001f4cc"


# ── GET /annotations ────────────────────────────────────────────────────
@router.get("")
def list_annotations(
    current_user: User = Depends(require_pro),
    db: Session = Depends(get_db),
):
    """List all net worth annotations for the user."""
    annotations = db.query(NetWorthAnnotation).filter(
        NetWorthAnnotation.user_id == current_user.id,
    ).order_by(NetWorthAnnotation.annotation_date.desc()).all()

    return [
        {
            "id": str(a.id),
            "annotation_date": a.annotation_date.isoformat() if a.annotation_date else None,
            "label": a.label,
            "description": a.description,
            "emoji": a.emoji,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in annotations
    ]


# ── POST /annotations ───────────────────────────────────────────────────
@router.post("")
def create_annotation(
    body: AnnotationCreateRequest,
    current_user: User = Depends(require_pro),
    db: Session = Depends(get_db),
):
    """Create a new annotation on the net worth timeline."""
    annotation = NetWorthAnnotation(
        user_id=current_user.id,
        annotation_date=body.annotation_date,
        label=body.label,
        description=body.description,
        emoji=body.emoji,
    )
    db.add(annotation)
    db.commit()
    db.refresh(annotation)

    return {
        "id": str(annotation.id),
        "annotation_date": annotation.annotation_date.isoformat() if annotation.annotation_date else None,
        "label": annotation.label,
        "description": annotation.description,
        "emoji": annotation.emoji,
    }


# ── DELETE /annotations/{id} ────────────────────────────────────────────
@router.delete("/{annotation_id}")
def delete_annotation(
    annotation_id: uuid.UUID,
    current_user: User = Depends(require_pro),
    db: Session = Depends(get_db),
):
    """Delete a net worth annotation."""
    annotation = db.query(NetWorthAnnotation).filter(
        NetWorthAnnotation.id == annotation_id,
        NetWorthAnnotation.user_id == current_user.id,
    ).first()
    if not annotation:
        raise NotFoundError("Annotation not found")

    db.delete(annotation)
    db.commit()
    return {"message": "Annotation deleted"}
