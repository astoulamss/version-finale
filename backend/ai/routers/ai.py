import os
import re
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse, Response, StreamingResponse
from sqlalchemy.orm import Session
from ai.db import get_db
from core.security import get_current_user, require_role
from models.user import User, RoleEnum
from models.features import Document

from ai.schemas.chat import ChatRequest, ChatResponse
from ai.schemas.analytics import RiskAnalysisRequest, RiskAnalysisResponse
from ai.schemas.documents import AIDocumentRequest, AIDocumentResponse
from ai.schemas.onboarding import OnboardingRequest, OnboardingResponse, OffboardingRequest

from ai.services.chat_service import chat, chat_stream
from ai.services.document_service import generate_document
from models.features import OnboardingPlan, OffboardingPlan, OnboardingTask, OffboardingTask, OnboardingStep, OffboardingStep
from ai.services.document_generator import GENERATED_DIR, TOOL_REGISTRY
from ai.services.analytics_service import analyze_risk
from ai.services.onboarding_service import generate_onboarding, generate_offboarding

router = APIRouter(prefix="/api/ai", tags=["AI Intelligence"])


@router.get("/health")
def ai_health():
    return {
        "status": "ok",
        "module": "AI Intelligence",
        "version": "1.0.0",
        "llm_provider": "OpenRouter (free models)",
    }


@router.post("/chat", response_model=ChatResponse)
def ai_chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        response_text, doc_info, sources_raw, chart_b64, conv_id = chat(
            query=request.query,
            user=current_user,
            db=db,
            history=request.history,
            conversation_id=request.conversation_id,
        )
    except Exception as e:
        response_text = f"❌ An error occurred while processing your request (API level):\n{str(e)}"
        doc_info = None
        sources_raw = None
        chart_b64 = None
        conv_id = request.conversation_id
    sources = None
    if sources_raw:
        from ai.schemas.chat import SourceInfo
        sources = [SourceInfo(**s) for s in sources_raw]
    return ChatResponse(
        response=response_text,
        conversation_id=conv_id,
        sources=sources,
        chart_base64=chart_b64,
        document=doc_info,
    )


@router.post("/chat/stream")
def ai_chat_stream(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return StreamingResponse(
        chat_stream(
            query=request.query,
            user=current_user,
            db=db,
            history=request.history,
            conversation_id=request.conversation_id,
        ),
        media_type="text/event-stream"
    )


@router.post("/generate-document", response_model=AIDocumentResponse)
def ai_generate_document(
    request: AIDocumentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.RH])),
):
    result = generate_document(
        employee_id=request.employee_id,
        document_type=request.document_type,
        user=current_user,
        db=db,
        extra_context=request.extra_context,
        save_to_db=request.save_to_db,
        generate_pdf=request.generate_pdf,
    )
    if "error" in result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])

    return AIDocumentResponse(
        id=result.get("id"),
        title=result["title"],
        content=result["content"],
        document_type=result["document_type"],
        generated_by_ai=result["generated_by_ai"],
        status=result.get("status"),
        pdf_url=result.get("pdf_url"),
    )


@router.get("/documents/{doc_id}/pdf")
def get_generated_pdf(
    doc_id: int,
    db: Session = Depends(get_db),
):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.file_url:
        from ai.utils.minio_client import download_pdf as _dp
        pdf_bytes = _dp(doc.file_url)
        if pdf_bytes:
            safe_name = re.sub(r'[^\w\s-]', '', doc.title).strip() or f"document_{doc_id}"
            return Response(content=pdf_bytes, media_type="application/pdf",
                            headers={"Content-Disposition": f"inline; filename={safe_name}.pdf"})
    pdf_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "generated_pdfs")
    pdf_path = os.path.join(pdf_dir, f"{doc_id}.pdf")
    if os.path.exists(pdf_path):
        safe_name = re.sub(r'[^\w\s-]', '', doc.title).strip() or f"document_{doc_id}"
        return FileResponse(pdf_path, media_type="application/pdf", filename=f"{safe_name}.pdf")
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDF not found")



@router.get("/documents/tool-pdf/{file_name}")
def get_tool_generated_pdf(
    file_name: str,
):
    import re
    safe = re.sub(r'[^a-zA-Z0-9_\-. ]', '', file_name)
    pdf_path = GENERATED_DIR / safe
    if not pdf_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDF not found")
    return FileResponse(str(pdf_path), media_type="application/pdf", filename=safe)


@router.get("/documents/minio/{key}")
def get_minio_document(key: str):
    from ai.utils.minio_client import download_pdf as _dp
    pdf_bytes = _dp(key)
    if pdf_bytes is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found in MinIO")
    return Response(content=pdf_bytes, media_type="application/pdf",
                    headers={"Content-Disposition": f"inline; filename={key}"})


@router.post("/analyze-risk", response_model=RiskAnalysisResponse)
def ai_analyze_risk(
    request: RiskAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.RH, RoleEnum.DIRECTION])),
):
    result = analyze_risk(
        analysis_type=request.analysis_type,
        user=current_user,
        db=db,
        department_id=request.department_id,
        period_start=request.period_start,
        period_end=request.period_end,
    )
    return RiskAnalysisResponse(**result)


@router.post("/onboarding", response_model=OnboardingResponse)
def ai_onboarding(
    request: OnboardingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.RH])),
):
    result = generate_onboarding(
        employee_id=request.employee_id,
        user=current_user,
        db=db,
        plan_type=request.plan_type,
        start_date=request.start_date,
    )
    if result["employee_name"] == "Unknown":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return OnboardingResponse(**result)


@router.get("/onboarding-plans")
def list_onboarding_plans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plans = db.query(OnboardingPlan).order_by(OnboardingPlan.created_at.desc()).all()
    result = []
    for p in plans:
        u = db.query(User).filter(User.id == p.employee_id).first()
        name = f"{u.prenom} {u.nom}" if u else "N/A"
        steps = db.query(OnboardingStep).filter(OnboardingStep.onboarding_id == p.id).order_by(OnboardingStep.step_order).all()
        tasks = db.query(OnboardingTask).filter(OnboardingTask.plan_id == p.id).all()
        result.append({
            "id": p.id,
            "employee_name": name,
            "plan_type": p.plan_type.value,
            "start_date": str(p.start_date),
            "end_date": str(p.end_date),
            "status": p.status.value,
            "created_at": str(p.created_at),
            "steps": [{"id": s.id, "title": s.title, "order": s.step_order} for s in steps],
            "tasks": [{"id": t.id, "title": t.title, "status": t.status.value} for t in tasks],
        })
    return result


@router.get("/offboarding-plans")
def list_offboarding_plans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plans = db.query(OffboardingPlan).order_by(OffboardingPlan.created_at.desc()).all()
    result = []
    for p in plans:
        u = db.query(User).filter(User.id == p.employee_id).first()
        name = f"{u.prenom} {u.nom}" if u else "N/A"
        steps = db.query(OffboardingStep).filter(OffboardingStep.plan_id == p.id).order_by(OffboardingStep.step_order).all()
        tasks = db.query(OffboardingTask).filter(OffboardingTask.plan_id == p.id).all()
        result.append({
            "id": p.id,
            "employee_name": name,
            "departure_date": str(p.departure_date),
            "departure_reason": p.departure_reason,
            "status": p.status.value,
            "created_at": str(p.created_at),
            "steps": [{"id": s.id, "title": s.title, "order": s.step_order} for s in steps],
            "tasks": [{"id": t.id, "title": t.title, "status": t.status.value} for t in tasks],
        })
    return result


@router.post("/offboarding", response_model=OnboardingResponse)
def ai_offboarding(
    request: OffboardingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.RH])),
):
    result = generate_offboarding(
        employee_id=request.employee_id,
        user=current_user,
        db=db,
        departure_date=request.departure_date,
        departure_reason=request.departure_reason,
    )
    if result["employee_name"] == "Unknown":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return OnboardingResponse(**result)
