from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import Response
from sqlalchemy.orm import Session
from database.db import get_db
from models.user import User, RoleEnum
from models.features import Document, DocumentTemplate, DocumentType, DocumentStatusEnum
from models.employees import Employee
from models.features import Contract
from schemas.features import (
    DocumentManualCreate, DocumentGenerateRequest, DocumentStatusUpdate, DocumentResponse,
    DocumentTypeCreate, DocumentTypeResponse,
    DocumentTemplateCreate, DocumentTemplateUpdate, DocumentTemplateResponse
)
from core.security import get_current_user, require_role
from utils.template_renderer import render_template, build_employee_variables
from utils.pdf_generator import generate_pdf
from utils.history import log_action
from utils.minio_client import upload_to_minio, download_from_minio, upload_raw_to_minio
from typing import List, Optional
import unicodedata
import re

def _upload_doc_to_minio_helper(document: Document, db: Session):
    try:
        # Generate the PDF bytes
        pdf_bytes = generate_pdf(
            title=document.title,
            content=document.content,
            document_type=document.document_type
        )
        # Nettoyer le titre pour en faire un nom de fichier valide
        safe_title = re.sub(r'[^\w\s-]', '', document.title)
        safe_title = re.sub(r'\s+', '_', safe_title.strip())
        filename = f"doc_{document.id}_{safe_title}.pdf"
        
        # Upload to MinIO
        file_url = upload_to_minio(filename, pdf_bytes)
        
        # Mettre à jour le lien dans la BD
        document.file_url = file_url
        db.commit()
        db.refresh(document)
    except Exception as e:
        print(f"MinIO upload error: {e}")

router = APIRouter(prefix="/api/documents", tags=["documents"])


# ────────────────────────────────────────────────────────────────────
# TEMPLATES DE DOCUMENTS  (Admin et RH uniquement)
# ────────────────────────────────────────────────────────────────────

@router.post("/templates", response_model=DocumentTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_document_template(
    template_data: DocumentTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.RH]))
):
    """Ajouter un nouveau modèle de document (Admin et RH seulement)"""
    existing = db.query(DocumentTemplate).filter(DocumentTemplate.name == template_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Le modèle '{template_data.name}' existe déjà."
        )
    template = DocumentTemplate(
        name=template_data.name,
        content=template_data.content,
        description=template_data.description
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.get("/templates", response_model=List[DocumentTemplateResponse])
def list_document_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.RH]))
):
    """Lister tous les modèles de documents (Admin et RH seulement)"""
    return db.query(DocumentTemplate).all()


@router.get("/templates/{template_id}", response_model=DocumentTemplateResponse)
def get_document_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.RH]))
):
    """Obtenir un modèle de document (Admin et RH seulement)"""
    template = db.query(DocumentTemplate).filter(DocumentTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Modèle introuvable.")
    return template


@router.put("/templates/{template_id}", response_model=DocumentTemplateResponse)
def update_document_template(
    template_id: int,
    template_data: DocumentTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.RH]))
):
    """Modifier un modèle de document (Admin et RH seulement)"""
    template = db.query(DocumentTemplate).filter(DocumentTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Modèle introuvable.")

    if template_data.name is not None:
        existing = db.query(DocumentTemplate).filter(
            DocumentTemplate.name == template_data.name,
            DocumentTemplate.id != template_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Le nom '{template_data.name}' est déjà utilisé."
            )
        template.name = template_data.name
    if template_data.content is not None:
        template.content = template_data.content
    if template_data.description is not None:
        template.description = template_data.description

    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN]))
):
    """Supprimer un modèle de document (Admin seulement)"""
    template = db.query(DocumentTemplate).filter(DocumentTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Modèle introuvable.")
    db.delete(template)
    db.commit()
    return None


# ────────────────────────────────────────────────────────────────────
# TYPES DE DOCUMENTS  (Admin et RH uniquement)
# ────────────────────────────────────────────────────────────────────

@router.post("/types", response_model=DocumentTypeResponse, status_code=status.HTTP_201_CREATED)
def create_document_type(
    doc_type_data: DocumentTypeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.RH]))
):
    """Ajouter un type de document (Admin et RH seulement)"""
    existing = db.query(DocumentType).filter(DocumentType.name == doc_type_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Le type '{doc_type_data.name}' existe déjà."
        )
    doc_type = DocumentType(name=doc_type_data.name, description=doc_type_data.description)
    db.add(doc_type)
    db.commit()
    db.refresh(doc_type)
    return doc_type


@router.get("/types", response_model=List[DocumentTypeResponse])
def list_document_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.RH]))
):
    """Lister tous les types de documents (Admin et RH seulement)"""
    return db.query(DocumentType).all()


# ────────────────────────────────────────────────────────────────────
# DOCUMENTS — LECTURE
# ────────────────────────────────────────────────────────────────────

@router.get("/my-documents", response_model=List[DocumentResponse])
def get_my_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    L'employé consulte ses propres documents.
    - Les documents uploadés par l'employé lui-même sont toujours visibles.
    - Les documents créés par le RH/Admin ne sont visibles que s'ils ont été explicitement envoyés (is_sent=True).
    """
    docs = db.query(Document).filter(Document.employee_id == current_user.id).all()
    result = []
    for doc in docs:
        # Si l'employé est l'auteur, il voit toujours son document
        if doc.created_by == current_user.id:
            result.append(doc)
        # Sinon (créé par RH/Admin), seulement si is_sent=True
        elif doc.is_sent:
            result.append(doc)
    return result


@router.get("/employee/{employee_id}", response_model=List[DocumentResponse])
def get_employee_documents(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.RH, RoleEnum.ADMIN, RoleEnum.MEDECINE_TRAVAIL]))
):
    """Voir tous les documents d'un employé"""
    target = db.query(User).filter(User.id == employee_id).first()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Utilisateur id={employee_id} introuvable.")
    query = db.query(Document).filter(Document.employee_id == employee_id)
    if current_user.role == RoleEnum.MEDECINE_TRAVAIL:
        query = query.filter(Document.document_type.in_(["certificat_medical", "arret_maladie", "inaptitude", "visite_medicale"]))
    return query.all()


@router.post("/{document_id}/send", response_model=DocumentResponse)
def send_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.RH, RoleEnum.ADMIN]))
):
    """Marque un document comme envoyé — le collaborateur pourra dès lors le voir dans son espace."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document introuvable.")
    document.is_sent = True
    db.commit()
    db.refresh(document)
    return document


@router.get("/all", response_model=List[DocumentResponse])
def get_all_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.RH, RoleEnum.ADMIN, RoleEnum.MEDECINE_TRAVAIL]))
):
    """Voir tous les documents du système"""
    query = db.query(Document)
    if current_user.role == RoleEnum.MEDECINE_TRAVAIL:
        query = query.filter(Document.document_type.in_(["certificat_medical", "arret_maladie", "inaptitude", "visite_medicale"]))
    return query.all()


@router.get("/{document_id}/download")
def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Télécharger un document en tant que fichier .pdf.
    - L'employé propriétaire peut télécharger ses propres documents.
    - RH et Admin peuvent télécharger n'importe quel document.
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document introuvable.")

    # Vérifier les permissions
    if (document.employee_id != current_user.id
            and current_user.role not in [RoleEnum.ADMIN, RoleEnum.RH, RoleEnum.MEDECINE_TRAVAIL]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé.")
        
    if current_user.role == RoleEnum.MEDECINE_TRAVAIL and document.employee_id != current_user.id and document.document_type not in ["certificat_medical", "arret_maladie", "inaptitude", "visite_medicale"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé. Document non médical.")

    # Nettoyer le titre pour en faire un nom de fichier valide
    safe_title = re.sub(r'[^\w\s-]', '', document.title)
    safe_title = re.sub(r'\s+', '_', safe_title.strip())
    filename = f"{safe_title}.pdf"

    # Récupérer ou générer le PDF
    try:
        if document.file_url:
            pdf_bytes = download_from_minio(document.file_url)
        else:
            pdf_bytes = generate_pdf(
                title=document.title,
                content=document.content,
                document_type=document.document_type
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération ou génération du PDF: {str(e)}"
        )

    # Enregistrer le téléchargement dans l'historique
    log_action(
        db=db,
        record_type="document",
        record_id=document.id,
        action="downloaded",
        performed_by=current_user.id,
        details=f"Document '{document.title}' (ID: {document.id}) téléchargé au format PDF par l'utilisateur id={current_user.id}."
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes))
        }
    )



@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Voir un document spécifique (propriétaire, RH ou Admin)"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document introuvable.")

    # Vérifier les permissions d'accès
    if (document.employee_id != current_user.id
            and current_user.role not in [RoleEnum.ADMIN, RoleEnum.RH, RoleEnum.MEDECINE_TRAVAIL]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé.")
        
    if current_user.role == RoleEnum.MEDECINE_TRAVAIL and document.employee_id != current_user.id and document.document_type not in ["certificat_medical", "arret_maladie", "inaptitude", "visite_medicale"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé. Document non médical.")

    return document


# ────────────────────────────────────────────────────────────────────
# DOCUMENTS — CRÉATION MANUELLE  (Admin et RH)
# ────────────────────────────────────────────────────────────────────

@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def create_document_manually(
    document_data: DocumentManualCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.RH]))
):
    """
    Créer manuellement un document pour un employé (Admin et RH seulement).
    Le contenu est saisi directement dans le champ 'content'.
    """
    # Vérifier que l'employé cible existe
    target = db.query(User).filter(User.id == document_data.employee_id).first()
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Utilisateur id={document_data.employee_id} introuvable."
        )

    document = Document(
        employee_id=document_data.employee_id,
        template_id=None,
        document_type=document_data.document_type,
        title=document_data.title,
        content=document_data.content,
        generated_by_ai=False,
        status=document_data.status,
        created_by=current_user.id
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # Upload to MinIO
    _upload_doc_to_minio_helper(document, db)
    return document

@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    title: str = Form(...),
    document_type: Optional[str] = Form(None),
    employee_id: Optional[int] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Permet à un collaborateur ou un RH d'uploader un document existant (ex: justificatif).
    RH/Admin peuvent spécifier un employee_id pour attribuer le document à quelqu'un d'autre.
    """
    file_bytes = await file.read()
    
    target_employee_id = current_user.id
    if employee_id is not None and current_user.role in [RoleEnum.ADMIN, RoleEnum.RH, RoleEnum.MEDECINE_TRAVAIL]:
        target_employee_id = employee_id
        
    if current_user.role == RoleEnum.MEDECINE_TRAVAIL and document_type not in ["certificat_medical", "arret_maladie", "inaptitude", "visite_medicale"]:
        document_type = "certificat_medical"
    
    document = Document(
        employee_id=target_employee_id,
        template_id=None,
        document_type=document_type or "Autre",
        title=title,
        content="Document importé manuellement",
        generated_by_ai=False,
        status=DocumentStatusEnum.FINAL,
        created_by=current_user.id
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    try:
        safe_title = re.sub(r'[^\w\s-]', '', document.title)
        safe_title = re.sub(r'\s+', '_', safe_title.strip())
        
        # Extract extension
        import os
        _, ext = os.path.splitext(file.filename)
        filename = f"doc_{document.id}_{safe_title}{ext}"
        
        file_url = upload_raw_to_minio(filename, file_bytes, file.content_type)
        
        document.file_url = file_url
        db.commit()
        db.refresh(document)
    except Exception as e:
        db.delete(document)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Erreur d'upload: {e}")

    return document


# ────────────────────────────────────────────────────────────────────
# DOCUMENTS — GÉNÉRATION IA DEPUIS UN TEMPLATE  (Admin et RH)
# ────────────────────────────────────────────────────────────────────

@router.post("/generate", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def generate_document_from_template(
    request: DocumentGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.RH]))
):
    """
    Générer automatiquement un document pour un employé à partir d'un template.
    Les variables {{placeholder}} sont remplacées par les données réelles de l'employé.
    Vous pouvez passer des variables supplémentaires via 'extra_vars'
    (ex: start_date, end_date, duration, manager_name).
    generated_by_ai est automatiquement mis à True.
    """
    # Vérifier que l'employé cible existe
    target_user = db.query(User).filter(User.id == request.employee_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Utilisateur id={request.employee_id} introuvable."
        )

    # Vérifier que le template existe
    template = db.query(DocumentTemplate).filter(DocumentTemplate.id == request.template_id).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template id={request.template_id} introuvable."
        )

    # Charger le profil employé (département, poste, manager)
    employee = db.query(Employee).filter(Employee.user_id == request.employee_id).first()

    # Charger le contrat pour avoir salaire et date d'embauche
    contract = db.query(Contract).filter(Contract.user_id == request.employee_id).first()

    # Si le document généré est de type "Contrat", on s'assure qu'un contrat existe en base
    doc_type_lower = (request.document_type or template.name).lower()
    if "contrat" in doc_type_lower:
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Impossible de générer ce document : aucun contrat n'est enregistré en base de données pour ce collaborateur. Veuillez d'abord créer la fiche du contrat."
            )

    # Construire les variables de remplacement
    variables = build_employee_variables(
        user=target_user,
        employee=employee,
        contract=contract,
        extra_vars=request.extra_vars
    )

    # Rendre le template (substitution des {{variables}})
    rendered_content = render_template(template.content, variables)

    # Créer le titre automatiquement si non fourni via extra_vars
    title = request.extra_vars.get("title") if request.extra_vars else None
    if not title:
        title = f"{template.name} — {target_user.prenom} {target_user.nom}"

    document = Document(
        employee_id=request.employee_id,
        template_id=request.template_id,
        document_type=request.document_type or template.name,
        title=title,
        content=rendered_content,
        generated_by_ai=True,
        status=request.status,
        created_by=current_user.id
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # Upload to MinIO
    _upload_doc_to_minio_helper(document, db)
    return document


# ────────────────────────────────────────────────────────────────────
# DOCUMENTS — MISE À JOUR DU STATUT  (Admin et RH)
# ────────────────────────────────────────────────────────────────────

@router.put("/{document_id}/status", response_model=DocumentResponse)
def update_document_status(
    document_id: int,
    update_data: DocumentStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.RH]))
):
    """Passer un document de 'draft' à 'final' (Admin et RH seulement)"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document introuvable.")

    document.status = update_data.status
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # Upload/update in MinIO
    _upload_doc_to_minio_helper(document, db)
    return document


# ────────────────────────────────────────────────────────────────────
# DOCUMENTS — SUPPRESSION  (Admin seulement)
# ────────────────────────────────────────────────────────────────────

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.RH]))
):
    """Supprimer un document (Admin seulement)"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document introuvable.")
    db.delete(document)
    db.commit()
    return None
