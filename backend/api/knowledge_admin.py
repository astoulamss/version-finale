"""
Router d'administration des documents de connaissance IA.
Réservé à l'administrateur.
"""
import os
import shutil
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database.db import get_db
from models.user import User, RoleEnum
from models.knowledge_document import KnowledgeDocument
from core.security import get_current_user

router = APIRouter(prefix="/api/ai/knowledge-admin", tags=["Knowledge Admin"])

# Chemin vers le dossier de documents IA
DOCS_DIR = Path(__file__).parent.parent / "ai" / "docs"
DOCS_DIR.mkdir(parents=True, exist_ok=True)

DISPLAY_NAMES = {
    "benefits_guide.pdf": "Guide des avantages sociaux",
    "code_of_conduct.pdf": "Code de conduite",
    "company_presentation.pdf": "Présentation de l'entreprise",
    "employee_handbook.pdf": "Manuel de l'employé",
    "internal_mobility_policy.pdf": "Politique de mobilité interne",
    "internal_procedures_guide.pdf": "Guide des procédures internes",
    "it_security_policy.pdf": "Politique de sécurité IT",
    "leave_policy.pdf": "Politique de congés",
    "leave_process.pdf": "Processus de demande de congés",
    "onboarding_guide.pdf": "Guide d'intégration",
    "onboarding_offboarding_process.pdf": "Processus intégration & départs",
    "performance_review_policy.pdf": "Politique d'évaluation",
    "remote_work_policy.pdf": "Politique télétravail",
}


# ─── Schémas ────────────────────────────────────────────────────────────────

class KnowledgeDocResponse(BaseModel):
    id: int
    filename: str
    display_name: str
    description: Optional[str]
    is_active: bool
    file_size: Optional[int]
    chunk_count: int
    indexed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class EngineStatus(BaseModel):
    status: str
    total_chunks: int
    active_documents: int
    inactive_documents: int
    total_documents: int
    collection_name: str
    chroma_dir: str
    docs_dir: str


class UpdateDocRequest(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None


# ─── Helpers ────────────────────────────────────────────────────────────────

def _require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != RoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé à l'administrateur."
        )
    return current_user


def _get_chroma_collection():
    """Obtenir la collection ChromaDB."""
    from ai.services.knowledge_service import _get_collection
    return _get_collection()


def _get_chunks_for_file(filename: str) -> int:
    """Compter le nombre de chunks d'un fichier dans ChromaDB."""
    try:
        collection = _get_chroma_collection()
        count = collection.count()
        if count == 0:
            return 0
        results = collection.get(where={"source": filename})
        return len(results.get("ids", []))
    except Exception:
        return 0


def _delete_chunks_for_file(filename: str) -> int:
    """Supprimer tous les chunks d'un fichier de ChromaDB."""
    try:
        collection = _get_chroma_collection()
        results = collection.get(where={"source": filename})
        ids = results.get("ids", [])
        if ids:
            collection.delete(ids=ids)
        return len(ids)
    except Exception:
        return 0


def _index_file(filename: str) -> int:
    """Indexer un fichier PDF dans ChromaDB."""
    from ai.services.knowledge_service import index_pdf
    file_path = DOCS_DIR / filename
    if not file_path.exists():
        return 0
    return index_pdf(str(file_path))


def _sync_db_with_disk(db: Session):
    """Synchroniser la base avec les fichiers présents sur disque."""
    pdf_files = list(DOCS_DIR.glob("*.pdf"))
    existing_filenames = {doc.filename for doc in db.query(KnowledgeDocument).all()}

    for pdf_path in pdf_files:
        if pdf_path.name not in existing_filenames:
            chunk_count = _get_chunks_for_file(pdf_path.name)
            doc = KnowledgeDocument(
                filename=pdf_path.name,
                display_name=DISPLAY_NAMES.get(pdf_path.name, pdf_path.stem.replace("_", " ").title()),
                description=None,
                is_active=True,
                file_size=pdf_path.stat().st_size,
                chunk_count=chunk_count,
                indexed_at=datetime.now(timezone.utc) if chunk_count > 0 else None,
            )
            db.add(doc)

    db.commit()


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/engine-status", response_model=EngineStatus)
def get_engine_status(
    _: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """État du moteur documentaire ChromaDB."""
    from ai.services.knowledge_service import collection_stats, CHROMA_DIR, COLLECTION_NAME
    try:
        stats = collection_stats()
        total_chunks = stats.get("total_chunks", 0)
        engine_status = "online"
    except Exception as e:
        total_chunks = 0
        engine_status = f"error: {str(e)}"

    active = db.query(KnowledgeDocument).filter(KnowledgeDocument.is_active == True).count()
    inactive = db.query(KnowledgeDocument).filter(KnowledgeDocument.is_active == False).count()
    total = db.query(KnowledgeDocument).count()

    return EngineStatus(
        status=engine_status,
        total_chunks=total_chunks,
        active_documents=active,
        inactive_documents=inactive,
        total_documents=total,
        collection_name=COLLECTION_NAME,
        chroma_dir=str(CHROMA_DIR),
        docs_dir=str(DOCS_DIR),
    )


@router.post("/sync")
def sync_documents(
    _: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """Synchroniser le registre DB avec les fichiers sur disque."""
    _sync_db_with_disk(db)
    total = db.query(KnowledgeDocument).count()
    return {"message": f"Synchronisation terminée. {total} document(s) dans le registre."}


@router.get("/documents", response_model=List[KnowledgeDocResponse])
def list_documents(
    _: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """Lister tous les documents de connaissance."""
    _sync_db_with_disk(db)
    docs = db.query(KnowledgeDocument).order_by(KnowledgeDocument.display_name).all()
    return docs


@router.put("/documents/{doc_id}/toggle")
def toggle_document(
    doc_id: int,
    _: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """Activer ou désactiver un document (modifie l'index ChromaDB)."""
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document introuvable.")

    if doc.is_active:
        # Désactiver : supprimer les chunks de ChromaDB
        deleted = _delete_chunks_for_file(doc.filename)
        doc.is_active = False
        doc.chunk_count = 0
        doc.updated_at = datetime.now(timezone.utc)
        db.commit()
        return {"message": f"Document désactivé. {deleted} chunk(s) supprimés de ChromaDB.", "is_active": False}
    else:
        # Activer : ré-indexer dans ChromaDB
        count = _index_file(doc.filename)
        doc.is_active = True
        doc.chunk_count = count
        doc.indexed_at = datetime.now(timezone.utc)
        doc.updated_at = datetime.now(timezone.utc)
        db.commit()
        return {"message": f"Document activé. {count} chunk(s) ajoutés dans ChromaDB.", "is_active": True}


@router.post("/documents/{doc_id}/reindex")
def reindex_document(
    doc_id: int,
    _: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """Ré-indexer un document spécifique (même s'il est déjà actif)."""
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document introuvable.")
    if not doc.is_active:
        raise HTTPException(status_code=400, detail="Activez le document avant de le ré-indexer.")

    # Supprimer les anciens chunks
    _delete_chunks_for_file(doc.filename)
    # Ré-indexer
    count = _index_file(doc.filename)
    doc.chunk_count = count
    doc.indexed_at = datetime.now(timezone.utc)
    doc.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {"message": f"Document ré-indexé avec succès. {count} chunk(s).", "chunk_count": count}


@router.post("/reindex-all")
def reindex_all(
    _: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """Ré-indexer tous les documents actifs."""
    _sync_db_with_disk(db)
    active_docs = db.query(KnowledgeDocument).filter(KnowledgeDocument.is_active == True).all()
    total_chunks = 0
    results = []
    for doc in active_docs:
        _delete_chunks_for_file(doc.filename)
        count = _index_file(doc.filename)
        doc.chunk_count = count
        doc.indexed_at = datetime.now(timezone.utc)
        total_chunks += count
        results.append({"filename": doc.filename, "chunks": count})
    db.commit()
    return {
        "message": f"Ré-indexation terminée. {len(active_docs)} document(s), {total_chunks} chunk(s) au total.",
        "results": results,
    }


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    display_name: str = Form(""),
    description: str = Form(""),
    auto_index: bool = Form(True),
    current_user: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """Uploader un nouveau document PDF."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Seuls les fichiers PDF sont acceptés.")

    safe_filename = "".join(c for c in file.filename if c.isalnum() or c in "._- ").strip()
    safe_filename = safe_filename.replace(" ", "_")
    dest_path = DOCS_DIR / safe_filename

    # Lire et sauvegarder
    content = await file.read()
    if len(content) > 50 * 1024 * 1024:  # 50 MB max
        raise HTTPException(status_code=400, detail="Fichier trop volumineux (max 50 MB).")

    with open(dest_path, "wb") as f:
        f.write(content)

    # Créer ou mettre à jour l'entrée DB
    existing = db.query(KnowledgeDocument).filter(KnowledgeDocument.filename == safe_filename).first()
    chunk_count = 0

    if auto_index:
        chunk_count = _index_file(safe_filename)

    if existing:
        existing.display_name = display_name or existing.display_name
        existing.description = description or existing.description
        existing.file_size = len(content)
        existing.chunk_count = chunk_count
        existing.is_active = auto_index
        existing.indexed_at = datetime.now(timezone.utc) if auto_index else None
        db.commit()
        doc = existing
    else:
        doc = KnowledgeDocument(
            filename=safe_filename,
            display_name=display_name or safe_filename.replace("_", " ").replace(".pdf", "").title(),
            description=description or None,
            is_active=auto_index,
            file_size=len(content),
            chunk_count=chunk_count,
            indexed_at=datetime.now(timezone.utc) if auto_index else None,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

    return {
        "message": f"Document '{safe_filename}' importé avec succès.",
        "filename": safe_filename,
        "chunk_count": chunk_count,
        "auto_indexed": auto_index,
    }


@router.delete("/documents/{doc_id}", status_code=status.HTTP_200_OK)
def delete_document(
    doc_id: int,
    _: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """Supprimer définitivement un document (disque + ChromaDB + DB)."""
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document introuvable.")

    # Supprimer de ChromaDB
    deleted_chunks = _delete_chunks_for_file(doc.filename)

    # Supprimer du disque
    file_path = DOCS_DIR / doc.filename
    if file_path.exists():
        file_path.unlink()

    # Supprimer de la DB
    db.delete(doc)
    db.commit()

    return {
        "message": f"Document '{doc.filename}' supprimé définitivement. {deleted_chunks} chunk(s) retirés de ChromaDB."
    }


@router.put("/documents/{doc_id}")
def update_document(
    doc_id: int,
    data: UpdateDocRequest,
    _: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """Modifier le nom ou la description d'un document."""
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document introuvable.")
    if data.display_name:
        doc.display_name = data.display_name
    if data.description is not None:
        doc.description = data.description
    db.commit()
    return {"message": "Document mis à jour."}
