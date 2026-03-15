import uuid
import secrets

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.tier_gate import require_pro
from app.models.user import User
from app.models.api_key import APIKey

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


class APIKeyCreateRequest(BaseModel):
    name: str


@router.get("")
def list_api_keys(
    current_user: User = Depends(require_pro),
    db: Session = Depends(get_db),
):
    """List all API keys (prefix + metadata only, never the full key)."""
    keys = db.query(APIKey).filter(
        APIKey.user_id == current_user.id,
        APIKey.is_active == True,
    ).order_by(APIKey.created_at.desc()).all()

    return [
        {
            "id": str(k.id),
            "name": k.name,
            "prefix": k.key_prefix,
            "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
            "created_at": k.created_at.isoformat(),
        }
        for k in keys
    ]


@router.post("")
def create_api_key(
    body: APIKeyCreateRequest,
    current_user: User = Depends(require_pro),
    db: Session = Depends(get_db),
):
    """Create a new API key. The full key is shown ONCE in the response."""
    raw_key = secrets.token_urlsafe(32)
    prefix = raw_key[:8]
    key_hash = bcrypt.hashpw(raw_key.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    api_key = APIKey(
        user_id=current_user.id,
        key_hash=key_hash,
        key_prefix=prefix,
        name=body.name,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    return {
        "id": str(api_key.id),
        "key": raw_key,
        "prefix": prefix,
        "name": api_key.name,
    }


@router.delete("/{id}")
def revoke_api_key(
    id: uuid.UUID,
    current_user: User = Depends(require_pro),
    db: Session = Depends(get_db),
):
    """Revoke (deactivate) an API key."""
    api_key = db.query(APIKey).filter(
        APIKey.id == id,
        APIKey.user_id == current_user.id,
    ).first()
    if not api_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    api_key.is_active = False
    db.commit()

    return {"revoked": True}
