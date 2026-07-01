import os
from sqlalchemy.orm import Session
from models.user import User, RoleEnum
from models.features import Document, DocumentStatusEnum, DocumentType, DocumentTemplate, Contract
from models.employees import Employee
from ai.utils.llm_client import call_llm
from ai.utils.pdf_generator import generate_pdf as make_pdf
from datetime import date


DOCUMENT_PROMPTS = {
    "employment_certificate": (
        "Agissez en tant que gestionnaire RH expert et rédacteur de documents juridiques d'entreprise pour NexcoreRH.\n"
        "Rédigez une attestation de travail professionnelle, moderne, et conforme à la législation en vigueur, adaptée à des fins administratives, bancaires, de visa ou d'emploi.\n\n"
        "Directives :\n"
        "- Utilisez un français formel et une terminologie RH rigoureuse.\n"
        "- Intégrez l'en-tête de l'entreprise : NexcoreRH, 123 Avenue Hassan II, 20000 Casablanca, Maroc, Tél : +212 522 12 34 56, Fax : +212 522 12 34 57, Email : contact@Nexcorerh.com, www.Nexcorerh.com.\n"
        "- Indiquez clairement la date et le lieu (Casablanca, le [Date]).\n"
        "- Présentez les informations de l'employé dans un format structuré (Nom, Prénom, Poste occupé, Département, Type de contrat, Date d'entrée).\n"
        "- Formulez le texte de manière à confirmer explicitement que l'employé est actuellement en poste au sein de l'entreprise et que son contrat est toujours en vigueur à ce jour.\n"
        "- Conservez un ton neutre, officiel et solennel.\n"
        "- Supprimez tout placeholder si l'information est absente ; sinon remplacez-le par les données fournies.\n"
        "- Incluez un bloc de signature en bas à droite : 'Pour la Direction générale, Le Directeur des Ressources Humaines'.\n"
        "- Rédigez uniquement le document final en français. N'utilisez pas de caractères de balisage markdown comme '**', '*' ou '#', écrivez en texte brut direct."
    ),
    "leave_certificate": (
        "Agissez en tant que gestionnaire RH expert pour NexcoreRH.\n"
        "Rédigez un certificat de congé professionnel, clair et juridiquement conforme en français.\n\n"
        "Directives :\n"
        "- Utilisez un français formel, neutre et officiel.\n"
        "- Précisez l'objet du document : 'Attestation de Congé'.\n"
        "- Présentez les informations de l'employé : nom complet, poste, département, type de contrat, date d'entrée.\n"
        "- Indiquez clairement : le type de congé, les dates de début et fin, le nombre de jours ouvrés/calendaires, le statut de validation.\n"
        "- Confirmez que la demande a été dûment enregistrée et validée par le service RH.\n"
        "- Précisez que le document est délivré à la demande de l'intéressé(e) pour servir et valoir ce que de droit.\n"
        "- Incluez un bloc de signature en bas à droite : 'Pour la Direction générale, Le Directeur des Ressources Humaines'.\n"
        "- N'utilisez aucun symbole de balisage ('**', '*', '#'). Rédigez en texte brut uniquement."
    ),
    "admin_request": (
        "Agissez en tant que rédacteur administratif expert pour NexcoreRH.\n"
        "Rédigez une lettre de demande administrative professionnelle, claire et formelle en français.\n\n"
        "Directives :\n"
        "- Utilisez un français administratif formel et poli.\n"
        "- Structurez le document avec : en-tête NexcoreRH, date, objet de la demande, corps de la lettre, formule de politesse.\n"
        "- Précisez clairement l'objet de la demande, le contexte, la justification et la requête expresse.\n"
        "- Terminez avec une formule de politesse professionnelle et un bloc de signature : 'Pour la Direction générale, Le Directeur des Ressources Humaines'.\n"
        "- N'utilisez aucun symbole de balisage ('**', '*', '#'). Rédigez en texte brut uniquement."
    ),
    "hr_summary": (
        "Agissez en tant qu'analyste RH senior pour NexcoreRH.\n"
        "Rédigez une fiche de synthèse RH très concise tenant sur UNE SEULE PAGE, professionnelle et confidentielle en français.\n\n"
        "Directives :\n"
        "- Soyez extrêmement concis — chaque section doit faire 1 à 2 lignes maximum.\n"
        "- Organisez la fiche en sections claires avec des titres en MAJUSCULES : PROFIL EMPLOYE, INFORMATIONS CONTRACTUELLES, HISTORIQUE DES CONGES, EVALUATION, OBSERVATIONS.\n"
        "- Présentez les données sous forme de lignes : 'Champ : Valeur'.\n"
        "- Incluez UNIQUEMENT : nom, poste, département, contrat, date entrée, statut, salaire, congés récents (1 ligne max).\n"
        "- Section OBSERVATIONS : une phrase courte uniquement.\n"
        "- Précisez que le document est confidentiel et destiné à usage interne uniquement.\n"
        "- N'utilisez aucun symbole de balisage ('**', '*', '#'). Rédigez en texte brut uniquement.\n"
        "- IMPORTANT : LE DOCUMENT COMPLET NE DOIT PAS DÉPASSER UNE PAGE A4."
    ),
}



import re


def _extract_field(text: str, pattern: str) -> str:
    m = re.search(pattern, text)
    return m.group(1) if m else "N/A"


def _extract_leave_type(text: str) -> str:
    leave_keywords = {
        "congé annuel": "Congé annuel",
        "conge annuel": "Congé annuel",
        "congé maladie": "Congé maladie",
        "conge maladie": "Congé maladie",
        "congé maternité": "Congé maternité",
        "conge maternite": "Congé maternité",
        "congé paternité": "Congé paternité",
        "conge paternite": "Congé paternité",
        "congé sans solde": "Congé sans solde",
        "conge sans solde": "Congé sans solde",
    }
    text_lower = text.lower()
    for key, val in leave_keywords.items():
        if key in text_lower:
            return val
    return "Congé"


def _get_leave_data(employee_id: int, db: Session) -> str:
    from sqlalchemy import text
    rows = db.execute(
        text("SELECT leave_type, start_date, end_date, status FROM leaves WHERE employee_id = :eid ORDER BY created_at DESC LIMIT 5"),
        {"eid": employee_id}
    ).fetchall()
    if not rows:
        return "No leave records."
    lines = ["Recent leave history:"]
    for row in rows:
        lines.append(f"- {row[0]}: {row[1]} to {row[2]} ({row[3]})")
    return "\n".join(lines)


def generate_document(
    employee_id: int,
    document_type: str,
    user: User,
    db: Session,
    extra_context: str | None = None,
    save_to_db: bool = True,
    generate_pdf: bool = True,
) -> dict:
    if user.role not in (RoleEnum.ADMIN, RoleEnum.RH):
        return {"error": "Access denied"}

    target_user = db.query(User).filter(User.id == employee_id).first()
    if not target_user:
        return {"error": "Employee not found"}

    employee = db.query(Employee).filter(Employee.user_id == employee_id).first()
    contract = db.query(Contract).filter(Contract.user_id == employee_id).first()

    info_parts = [
        f"Employee: {target_user.prenom} {target_user.nom}",
        f"Email: {target_user.email}",
        f"Role: {target_user.role.value}",
    ]
    if employee:
        info_parts.append(f"Department: {employee.department.name if employee.department else 'N/A'}")
        info_parts.append(f"Position: {employee.position.title if employee.position else 'N/A'}")
    if contract:
        info_parts.append(f"Contract: {contract.contract_type}")
        info_parts.append(f"Position: {contract.position}")
        info_parts.append(f"Start date: {contract.start_date}")
        if contract.salary:
            info_parts.append(f"Salaire: {contract.salary}")
    if document_type in ("leave_certificate",):
        from sqlalchemy import text
        row = db.execute(text("SELECT id FROM leaves WHERE employee_id = :eid LIMIT 1"), {"eid": employee_id}).first()
        if not row:
            return {"error": f"{target_user.prenom} {target_user.nom} n'a aucun congé enregistré dans la base de données. Impossible de générer un certificat de congé."}
        info_parts.append(_get_leave_data(employee_id, db))

    if extra_context:
        info_parts.append(f"Extra context: {extra_context}")

    employee_info = "\n".join(info_parts)

    prompt_template = DOCUMENT_PROMPTS.get(
        document_type,
        "Generate a professional HR document in French based on the employee data below."
    )

    system = (
        "You are SmartRH Document Generator by NexcoreRH. Generate professional HR documents in French. "
        "Use the employee data provided. Generate with proper date, subject, body, and signature.\n\n"
        "CRITICAL: NEVER use placeholder text in brackets like [Nom], [Date], [Responsable RH], "
        "[Ville], etc. You MUST replace every placeholder with the actual data from the context. "
        "If a piece of information is not available, simply omit it rather than using brackets.\n\n"
        f"This document is generated by: {user.prenom} {user.nom} ({user.role.value}). "
        "Use this name for the signature/signatory if needed."
    )

    response = call_llm(system, f"{prompt_template}\n\nEmployee Data:\n{employee_info}")
    if not response:
        response = f"Document could not be generated for {target_user.prenom} {target_user.nom}."

    document_type_labels = {
        "employment_certificate": "Attestation de Travail",
        "leave_certificate": "Certificat de Congé",
        "admin_request": "Demande Administrative",
        "hr_summary": "Fiche de Synthèse RH",
    }

    title = f"{document_type_labels.get(document_type, 'document')} - {target_user.prenom} {target_user.nom}"
    content = response

    result = {
        "title": title,
        "content": content,
        "document_type": document_type,
        "generated_by_ai": True,
        "id": None,
        "status": None,
        "pdf_url": None,
    }

    if save_to_db:
        type_name = document_type_labels.get(document_type, document_type)
        doc_type = db.query(DocumentType).filter(DocumentType.name == type_name).first()
        if not doc_type:
            doc_type = DocumentType(name=type_name, description=f"Documents de type {type_name}")
            db.add(doc_type)
            db.flush()

        doc_tmpl = db.query(DocumentTemplate).filter(DocumentTemplate.name == type_name).first()
        if not doc_tmpl:
            doc_tmpl = DocumentTemplate(
                name=type_name,
                content=f"Modèle standard pour {type_name}",
                description=f"Template généré automatiquement pour {type_name}"
            )
            db.add(doc_tmpl)
            db.flush()

        doc_record = Document(
            employee_id=employee_id,
            template_id=doc_tmpl.id,
            document_type=type_name,
            title=title,
            content=content,
            generated_by_ai=True,
            status=DocumentStatusEnum.DRAFT,
            created_by=user.id,
        )
        db.add(doc_record)
        db.flush()
        doc_id = doc_record.id
        result["id"] = doc_id
        result["status"] = DocumentStatusEnum.DRAFT.value

        if generate_pdf:
            pdf_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "generated_pdfs")
            os.makedirs(pdf_dir, exist_ok=True)
            pdf_path = os.path.join(pdf_dir, f"{doc_id}.pdf")

            if document_type == "leave_certificate" and employee and contract:
                from sqlalchemy import text
                lrow = db.execute(
                    text("SELECT leave_type, status, start_date, end_date FROM leaves WHERE employee_id = :eid ORDER BY created_at DESC LIMIT 1"),
                    {"eid": employee_id}
                ).first()
                if lrow:
                    type_map = {"vacation": "Congé annuel", "sick": "Congé maladie", "maternity": "Congé maternité", "personal": "Congé personnel", "unpaid": "Congé sans solde"}
                    status_map = {"pending": "En attente", "approved": "Approuvé", "rejected": "Rejeté", "cancelled": "Annulé"}
                    lv_type = type_map.get(lrow[0], str(lrow[0])) if lrow[0] else "N/A"
                    lv_start = lrow[2].strftime("%d/%m/%Y") if lrow[2] else "N/A"
                    lv_end = lrow[3].strftime("%d/%m/%Y") if lrow[3] else "N/A"
                    lv_days = str((lrow[3] - lrow[2]).days + 1) if lrow[2] and lrow[3] else "N/A"
                    lv_status = status_map.get(lrow[1], str(lrow[1])) if lrow[1] else "N/A"
                else:
                    lv_type = _extract_leave_type(content) if content else "N/A"
                    lv_start = _extract_field(content, r"(\d{1,2}/\d{1,2}/\d{4})")
                    lv_end = _extract_field(content, r"(?:\bau\b|Date de fin)[^0-9]*(\d{1,2}/\d{1,2}/\d{4})")
                    lv_days = _extract_field(content, r"(\d+)\s*jours")
                    lv_status = "Approuvé"
                from ai.services.document_generator import generate_leave_certificate_pdf
                file_url = generate_leave_certificate_pdf(
                    employee_name=f"{target_user.prenom} {target_user.nom}",
                    employee_id=str(employee_id),
                    job_title=employee.position.title if employee.position else "N/A",
                    department=employee.department.name if employee.department else "N/A",
                    contract_type=contract.contract_type if contract else "N/A",
                    contract_start_date=str(contract.start_date) if contract and contract.start_date else "N/A",
                    leave_type=lv_type,
                    start_date=lv_start,
                    end_date=lv_end,
                    num_days=lv_days,
                    status=lv_status,
                    city="Casablanca",
                    hr_manager_name=f"{user.prenom} {user.nom}",
                )
                doc_record.file_url = file_url
                key = file_url.split("/", 1)[-1]
                result["pdf_url"] = f"/api/ai/documents/minio/{key}"
            elif document_type == "employment_certificate" and employee and contract:
                from ai.services.document_generator import generate_work_certificate_pdf
                file_url = generate_work_certificate_pdf(
                    employee_name=f"{target_user.prenom} {target_user.nom}",
                    job_title=employee.position.title if employee.position else "N/A",
                    department=employee.department.name if employee.department else "N/A",
                    contract_type=contract.contract_type if contract else "N/A",
                    start_date=str(contract.start_date) if contract and contract.start_date else "N/A",
                    city="Casablanca",
                )
                doc_record.file_url = file_url
                key = file_url.split("/", 1)[-1]
                result["pdf_url"] = f"/api/ai/documents/minio/{key}"
            else:
                sig_label = None
                sig_name = None
                if document_type == "admin_request":
                    sig_label = "Demandeur"
                    sig_name = f"{target_user.prenom} {target_user.nom}"
                elif document_type == "hr_summary":
                    sig_label = "L'Administrateur RH"
                    sig_name = f"{user.prenom} {user.nom}"
                pdf_bytes = make_pdf(title, content, document_type, sig_left_label=sig_label, sig_left_name=sig_name)
                from ai.utils.minio_client import upload_pdf
                file_url = upload_pdf(pdf_bytes, title)
                doc_record.file_url = file_url
                key = file_url.split("/", 1)[-1]
                result["pdf_url"] = f"/api/ai/documents/minio/{key}"

        db.commit()

    return result
