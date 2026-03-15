import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.tier_gate import require_family
from app.models.user import User
from app.models.document import Document
from app.services.storage_service import upload_file, get_presigned_url, delete_file

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("")
def list_documents(
    current_user: User = Depends(require_family),
    db: Session = Depends(get_db),
):
    """List all documents for the current user."""
    docs = db.query(Document).filter(
        Document.user_id == current_user.id,
    ).order_by(Document.created_at.desc()).all()

    return [_doc_to_dict(d) for d in docs]


@router.get("/asset/{asset_id}")
def list_documents_for_asset(
    asset_id: uuid.UUID,
    current_user: User = Depends(require_family),
    db: Session = Depends(get_db),
):
    """List documents attached to a specific asset."""
    docs = db.query(Document).filter(
        Document.user_id == current_user.id,
        Document.asset_id == asset_id,
    ).order_by(Document.created_at.desc()).all()

    return [_doc_to_dict(d) for d in docs]


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    asset_id: uuid.UUID | None = Form(None),
    liability_id: uuid.UUID | None = Form(None),
    description: str | None = Form(None),
    current_user: User = Depends(require_family),
    db: Session = Depends(get_db),
):
    """Upload a document (multipart file upload)."""
    file_bytes = await file.read()
    file_size = len(file_bytes)

    # 10 MB max
    if file_size > 10 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File too large (10 MB max)")

    file_key = upload_file(file_bytes, file.filename or "upload", current_user.id)

    doc = Document(
        user_id=current_user.id,
        asset_id=asset_id,
        liability_id=liability_id,
        filename=file.filename or "upload",
        file_key=file_key,
        file_size=file_size,
        mime_type=file.content_type or "application/octet-stream",
        description=description,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return _doc_to_dict(doc)


@router.get("/{id}/download")
def download_document(
    id: uuid.UUID,
    current_user: User = Depends(require_family),
    db: Session = Depends(get_db),
):
    """Get a temporary presigned download URL for a document."""
    doc = db.query(Document).filter(
        Document.id == id,
        Document.user_id == current_user.id,
    ).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    url = get_presigned_url(doc.file_key)
    return {"url": url}


@router.delete("/{id}")
def delete_document(
    id: uuid.UUID,
    current_user: User = Depends(require_family),
    db: Session = Depends(get_db),
):
    """Delete a document and its file from storage."""
    doc = db.query(Document).filter(
        Document.id == id,
        Document.user_id == current_user.id,
    ).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    delete_file(doc.file_key)
    db.delete(doc)
    db.commit()

    return {"deleted": True}


# ── Helpers ──────────────────────────────────────────────────────────────


def _doc_to_dict(doc: Document) -> dict:
    return {
        "id": str(doc.id),
        "filename": doc.filename,
        "file_size": doc.file_size,
        "mime_type": doc.mime_type,
        "description": doc.description,
        "asset_id": str(doc.asset_id) if doc.asset_id else None,
        "liability_id": str(doc.liability_id) if doc.liability_id else None,
        "created_at": doc.created_at.isoformat(),
    }
