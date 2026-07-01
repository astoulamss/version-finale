from pydantic import BaseModel
from typing import Optional


class AIDocumentRequest(BaseModel):
    employee_id: int
    document_type: str  # employment_certificate, leave_certificate, admin_request, hr_summary
    extra_context: Optional[str] = None
    save_to_db: bool = True
    generate_pdf: bool = True


class AIDocumentResponse(BaseModel):
    id: Optional[int] = None
    title: str
    content: str
    document_type: str
    generated_by_ai: bool
    status: Optional[str] = None
    pdf_url: Optional[str] = None
