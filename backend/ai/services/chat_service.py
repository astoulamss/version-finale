import json
import os
import re
from pathlib import Path
from sqlalchemy.orm import Session
from models.user import User, RoleEnum
from models.employees import Employee
from models.features import Contract, Document, DocumentStatusEnum, DocumentType, DocumentTemplate
from ai.utils.llm_client import call_llm_with_tools, semantic_filter
from ai.utils.context_builder import build_full_context
from ai.services.document_generator import TOOLS, execute_tool, generate_work_certificate_pdf, generate_report_pdf, generate_leave_certificate_pdf
from ai.schemas.chat import ChatDocumentInfo
from ai.services.knowledge_service import search_documents, format_context, needs_reindex, index_all_docs
from ai.utils.llm_client import input_guardrail


SYSTEM_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "hr_assistant.txt")

_ERROR_MSG = "Je ne peux pas traiter votre demande pour le moment. Veuillez réessayer plus tard."


def _load_system_prompt() -> str:
    try:
        with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "You are HR Assistant. Answer HR questions using the provided context directly and concisely."


def _role_scope(user: User) -> str:
    return {
        "admin": "You have FULL ACCESS to all company data.",
        "rh": "You have access to all employee records and HR operational data.",
        "manager": "You have access to your own data and your direct reports' data only.",
        "direction": "You have access to strategic overviews only. You CANNOT see individual employee personal data.",
        "collaborateur": "You have access to YOUR OWN data only. You CANNOT see any other employee's information.",
        "medecine_travail": "You have EXCLUSIVE ACCESS to health status, sickness reasons, and medical data for ALL employees.",
        "responsable_qvt": "You have access to YOUR OWN data only.",
    }.get(user.role.value, "You have access to your own data only.")


def _build_messages(
    query: str,
    user: User,
    db: Session,
    history: list | None = None,
    conversation_id: int | None = None,
) -> tuple[list[dict], list]:
    system_prompt = _load_system_prompt()
    context_data = build_full_context(user, db)

    # Dynamic specific employee context injection
    emp_tuple = _find_employee(query, db)
    if emp_tuple and user.role in [RoleEnum.RH, RoleEnum.ADMIN, RoleEnum.MANAGER, RoleEnum.MEDECINE_TRAVAIL]:
        emp, emp_user = emp_tuple
        from sqlalchemy import text
        # Fetch up to 100 leaves for this specific employee
        leaves_result = db.execute(
            text("SELECT lt.name as leave_type, l.start_date, l.end_date, l.status "
                 "FROM leaves l JOIN leave_types lt ON l.leave_type_id = lt.id WHERE l.employee_id = :eid ORDER BY l.start_date DESC LIMIT 100"),
            {"eid": emp_user.id}
        ).fetchall()
        
        absences_result = db.execute(
            text("SELECT absence_type, start_date, end_date, status FROM absences WHERE employee_id = :eid ORDER BY start_date DESC LIMIT 100"),
            {"eid": emp_user.id}
        ).fetchall()
        
        contract_result = db.execute(
            text("SELECT id, contract_type, position, salary, start_date, end_date FROM contracts WHERE user_id = :uid ORDER BY start_date DESC LIMIT 1"),
            {"uid": emp_user.id}
        ).first()
        
        context_data += f"\n\n=== EXPLICIT DATA FOR EMPLOYEE {emp_user.prenom} {emp_user.nom} ===\n"
        
        if contract_result:
            context_data += "--- CURRENT CONTRACT ---\n"
            context_data += f"- Type: {contract_result.contract_type} | Position: {contract_result.position} | Salary: {contract_result.salary or 'N/A'} | Start: {contract_result.start_date} | End: {contract_result.end_date or 'N/A'}\n"
        else:
            context_data += "--- CURRENT CONTRACT ---\n"
            context_data += "No contract found.\n\n"

        if leaves_result:
            context_data += "--- LEAVES HISTORY ---\n"
            for l in leaves_result:
                context_data += f"- {l.leave_type} | {l.start_date} to {l.end_date} | Status: {l.status}\n"
        else:
            context_data += "No leaves found.\n"
            
        if absences_result:
            context_data += "\n--- ABSENCES HISTORY ---\n"
            for a in absences_result:
                context_data += f"- Type: {a.absence_type} | {a.start_date} to {a.end_date} | Status: {a.status}\n"
        else:
            context_data += "\nNo absences found.\n"

    role_text = _role_scope(user)

    if needs_reindex():
        try:
            index_all_docs()
        except Exception:
            pass

    doc_chunks = search_documents(query, n_results=2)
    doc_context = ""
    if doc_chunks:
        doc_context = f"\n\n---POLICY DOCUMENTS---\n{format_context(doc_chunks)}"

    full_system = (
        f"{system_prompt}\n\n"
        f"Current user role: {user.role.value}\n"
        f"Current user: {user.prenom} {user.nom}\n\n"
        f"---ACCESS SCOPE---\n{role_text}\n\n"
        f"---DATABASE CONTEXT---\n{context_data}\n"
        f"{doc_context}"
    )

    messages = [{"role": "system", "content": full_system}]

    # Load from DB if conversation_id is provided
    if conversation_id:
        from models.chatbot import ChatbotMessage
        db_history = db.query(ChatbotMessage).filter(
            ChatbotMessage.conversation_id == conversation_id
        ).order_by(ChatbotMessage.created_at.asc()).all()
        # Keep last 10 messages (5 turns)
        for msg in db_history[-10:]:
            role = "user" if msg.sender == "user" else "assistant"
            messages.append({"role": role, "content": msg.message})
    elif history:
        for h in history[-6:]:
            messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})

    messages.append({"role": "user", "content": query})
    return messages, doc_chunks



def _is_document_request(query: str) -> bool:
    q = query.lower()
    doc_keywords = [
        "attestation", "certificate", "attestation de travail",
        "work certificate", "employment certificate",
        "generate", "create.*pdf", "create.*document",
        "salary report", "rapport.*salaire", "rapport", "pdf",
        "liste.*employe", "liste.*employee", "contrat", "contract",
        "autorisat", "authorization", "certificat",
    ]
    return any(re.search(k, q) for k in doc_keywords)


def _extract_employee_name(query: str) -> str | None:
    patterns = [
        r"(?:pour|for)\s+([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)+)",
        r"(?:de\s+)([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)+)",
        r"(?:concernant\s+)([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)+)",
        r"([A-Za-zÀ-ÿ]+\s+[A-Za-zÀ-ÿ]+)",
    ]
    ignore_words = {"generate an", "generate a", "create a", "create an", "pdf for", "pdf of", "of my"}
    for p in patterns:
        m = re.search(p, query)
        if m:
            name = m.group(1).strip()
            if name.lower() in ignore_words:
                continue
            if len(name) > 3:
                return name
    return None


def _build_salary_report_content(db: Session) -> str:
    lines = ["RAPPORT DES SALAIRES", ""]
    employees = db.query(Employee).all()
    total = 0.0
    for emp in employees:
        try:
            user = emp.user
            dept = emp.department.name if emp.department else "N/A"
            pos = emp.position.title if emp.position else "N/A"
            sal = float(emp.salary) if emp.salary else 0.0
            total += sal
            lines.append(f"{user.prenom} {user.nom} | {pos} | {dept} | {sal:.2f} EUR")
        except Exception:
            continue
    lines.append("")
    lines.append(f"Total masse salariale : {total:.2f} EUR")
    lines.append(f"Nombre d'employes : {len(employees)}")
    return "\n".join(lines)


def _find_employee(query: str, db: Session) -> tuple | None:
    """Find an employee matching a name in the query. Returns (Employee, User) or None."""
    name = _extract_employee_name(query)
    if not name:
        return None
    employees = db.query(Employee).all()
    name_lower = name.lower()
    for emp in employees:
        try:
            full = f"{emp.user.prenom} {emp.user.nom}".lower()
            if name_lower == full or name_lower in full or full in name_lower:
                return emp, emp.user
            parts = name_lower.split()
            emp_parts = set(full.split())
            if len(parts) >= 2 and len(emp_parts.intersection(parts)) == len(parts):
                return emp, emp.user
        except Exception:
            continue
    return None


def _get_my_employee(user: User, db: Session) -> tuple | None:
    emp = db.query(Employee).filter(Employee.user_id == user.id).first()
    if not emp:
        return None
    return emp, user


def _save_chat_log(query: str, response_text: str, user: User, db: Session, conv_id: int | None = None) -> int | None:
    from models.chatbot import ChatbotConversation, ChatbotMessage, ChatbotLog
    from datetime import datetime, timezone
    from utils.notifications import notify_role
    from models.user import RoleEnum
    
    # Check for unauthorized access
    unauth_keywords = ["permissions nécessaires pour accéder", "n'avez pas les permissions", "n'avez pas l'autorisation"]
    is_unauthorized = any(kw in response_text.lower() for kw in unauth_keywords)
    
    risk_level = "Normal"
    if is_unauthorized:
        risk_level = "Dangereux"
    elif "❌" in response_text:
        risk_level = "Signalé"
        
    try:
        if conv_id is None:
            conv = ChatbotConversation(user_id=user.id, title=query[:100], started_at=datetime.now(timezone.utc))
            db.add(conv)
            db.flush()
            conv_id = conv.id
            
        db.add(ChatbotMessage(conversation_id=conv_id, user_id=user.id, sender="user", message=query))
        db.add(ChatbotMessage(conversation_id=conv_id, user_id=user.id, sender="bot", message=response_text[:1000]))
        
        log_entry = ChatbotLog(
            user_id=user.id, 
            conversation_id=conv_id, 
            query=query, 
            response=response_text[:2000],
            response_status="error" if is_unauthorized or "❌" in response_text else "success",
            risk_level=risk_level
        )
        db.add(log_entry)
        
        if is_unauthorized:
            msg = f"Alerte Sécurité: {user.prenom} {user.nom} a tenté d'accéder à des informations non autorisées via le chatbot. Requête: '{query[:50]}...'"
            notify_role(db, RoleEnum.RH, msg)
            notify_role(db, RoleEnum.ADMIN, msg)
            
        db.commit()
        return conv_id
    except Exception:
        import traceback
        traceback.print_exc()
        try:
            db.rollback()
        except Exception:
            pass
        return None


def _save_doc_to_db(
    requesting_user: User,
    target_user_id: int,
    title: str,
    content: str,
    doc_type: str,
    file_url: str,
    db: Session,
) -> int | None:
    """Save a generated document record to the database, ensuring DocumentType and DocumentTemplate exist."""
    try:
        type_record = db.query(DocumentType).filter(DocumentType.name == doc_type).first()
        if not type_record:
            type_record = DocumentType(
                name=doc_type,
                description=f"Type de document généré par IA : {doc_type}"
            )
            db.add(type_record)
            db.flush()

        template_name = f"Template {doc_type.replace('_', ' ').capitalize()}"
        template_record = db.query(DocumentTemplate).filter(DocumentTemplate.name == template_name).first()
        if not template_record:
            template_record = DocumentTemplate(
                name=template_name,
                content=content,
                description=f"Modèle automatique généré par l'IA pour {doc_type}"
            )
            db.add(template_record)
            db.flush()

        doc_record = Document(
            employee_id=target_user_id,
            template_id=template_record.id,
            document_type=doc_type,
            title=title,
            content=content,
            generated_by_ai=True,
            status=DocumentStatusEnum.FINAL,
            created_by=requesting_user.id,
            file_url=file_url,
            is_sent=False,  # Visible par le RH, invisible par l'employé tant que non validé
        )

        db.add(doc_record)
        db.flush()
        db.commit()
        return doc_record.id
    except Exception as e:
        import traceback
        traceback.print_exc()
        try:
            db.rollback()
        except Exception:
            pass
        return None


def _build_certificate(
    emp: Employee,
    target_user: User,
    requesting_user: User,
    db: Session,
    cert_type: str,
) -> tuple[str, str, str]:
    """Build a work certificate PDF. Returns (title, file_url, response_text)."""
    contract = db.query(Contract).filter(Contract.user_id == target_user.id).first()
    emp_name = f"{target_user.prenom} {target_user.nom}"
    job_title = emp.position.title if emp.position else "Employé"
    department = emp.department.name if emp.department else "Général"
    start_date = str(contract.start_date) if contract and contract.start_date else "01/01/2024"

    ct = contract.contract_type if contract else "CDI"
    file_url = generate_work_certificate_pdf(
        employee_name=emp_name, job_title=job_title, department=department,
        contract_type=ct, start_date=start_date, city="Casablanca",
    )
    title = f"Attestation de travail - {emp_name}"
    text = f"✅ Attestation de travail générée pour **{emp_name}** — Poste : **{job_title}**, Département : **{department}**"

    doc_content = f"{title}\nEmployé: {emp_name}\nPoste: {job_title}\nDépartement: {department}"
    _save_doc_to_db(
        requesting_user=requesting_user,
        target_user_id=target_user.id,
        title=title,
        content=doc_content,
        doc_type="attestation_travail",
        file_url=file_url,
        db=db,
    )

    return title, file_url, text


def _fallback_document(query: str, user: User, db: Session) -> tuple[str, ChatDocumentInfo | None]:
    q = query.lower()

    is_report_request = any(kw in q for kw in [
        "rapport", "report", "liste", "list", "masse salariale",
        "table", "tableau", "all", "tous", "everyone", "all employees",
        "tous les employes", "ensemble", "global", "summary", "overview",
    ])
    is_work_cert_request = any(kw in q for kw in [
        "attestation", "certificat de travail", "work certificate",
        "employment certificate", "attestation de travail",
    ])

    is_leave_cert_request = any(kw in q for kw in [
        "congé", "conge", "leave certificate", "certificat de congé",
        "certificat de conge", "certificat congé",
    ])

    is_contract_request = any(kw in q for kw in [
        "contrat", "contract",
    ])

    is_mine_words = any(w in q.split() for w in ["mon", "my", "ma", "mes"])
    is_mine = is_mine_words and not _find_employee(query, db)

    cert_type = "work" if is_work_cert_request else None

    # Report request — redirect to chart
    if is_report_request:
        return "Je peux générer un graphique pour visualiser ces données. Dites-moi ce que vous voulez voir (ex: 'affiche un graphique des effectifs par département').", None

    # Individual work certificate
    if cert_type:
        result = _get_my_employee(user, db) if is_mine else _find_employee(query, db)
        if not result:
            return (
                "❌ Employé introuvable. Précisez le nom complet "
                "(ex: 'attestation de travail pour Jean Dupont')",
                None,
            )

        emp, target_user = result
        try:
            title, file_url, text = _build_certificate(emp, target_user, user, db, "work")
            key = file_url.split("/", 1)[-1]
            doc_info = ChatDocumentInfo(
                id=0, title=title, document_type="attestation_travail",
                pdf_url=f"/api/ai/documents/minio/{key}", status="final",
            )
            return text, doc_info
        except Exception as e:
            return f"❌ Erreur lors de la génération du document : {str(e)}", None

    # Leave certificate request
    if is_leave_cert_request:
        result = _get_my_employee(user, db) if is_mine else _find_employee(query, db)
        if not result:
            return "Employe introuvable. Precisez le nom complet.", None
        emp, target_user = result
        from sqlalchemy import text
        row = db.execute(
            text("SELECT lt.name as leave_type, l.status, l.start_date, l.end_date FROM leaves l JOIN leave_types lt ON l.leave_type_id = lt.id WHERE l.employee_id = :eid ORDER BY l.created_at DESC LIMIT 1"),
            {"eid": target_user.id}
        ).first()
        if not row:
            return f"{target_user.prenom} {target_user.nom} n'a aucun conge enregistre. Impossible de generer un certificat de conge.", None
        contract = db.query(Contract).filter(Contract.user_id == target_user.id).first()
        lv_type_raw = row[0] if row[0] else "N/A"
        lv_status_raw = row[1] if row[1] else "N/A"
        lv_start = row[2].strftime("%d/%m/%Y") if row[2] else "N/A"
        lv_end = row[3].strftime("%d/%m/%Y") if row[3] else "N/A"
        type_map = {"vacation": "Congé annuel", "sick": "Congé maladie", "maternity": "Congé maternité", "personal": "Congé personnel", "unpaid": "Congé sans solde"}
        status_map = {"pending": "En attente", "approved": "Approuvé", "rejected": "Rejeté", "cancelled": "Annulé"}
        lv_type = type_map.get(lv_type_raw, str(lv_type_raw)) if lv_type_raw != "N/A" else "N/A"
        lv_status = status_map.get(lv_status_raw, str(lv_status_raw)) if lv_status_raw != "N/A" else "N/A"
        if row[2] and row[3]:
            lv_days = str((row[3] - row[2]).days + 1)
        else:
            lv_days = "N/A"
        emp_name = f"{target_user.prenom} {target_user.nom}"
        job_title = emp.position.title if emp.position else "Employé"
        department = emp.department.name if emp.department else "Général"
        ct = contract.contract_type if contract else "CDI"
        c_start = str(contract.start_date) if contract and contract.start_date else "N/A"
        hr_name = f"{user.prenom} {user.nom}"
        file_url = generate_leave_certificate_pdf(
            employee_name=emp_name, employee_id=str(target_user.id),
            job_title=job_title, department=department, contract_type=ct,
            contract_start_date=c_start, leave_type=lv_type, start_date=lv_start,
            end_date=lv_end, num_days=lv_days, status=lv_status,
            city="Casablanca", hr_manager_name=hr_name,
        )
        title = f"Certificat de congé - {emp_name}"
        key = file_url.split("/", 1)[-1]
        doc_info = ChatDocumentInfo(
            id=0, title=title, document_type="leave_certificate",
            pdf_url=f"/api/ai/documents/minio/{key}", status="final",
        )
        return f"✅ Certificat de congé généré pour **{emp_name}** — {lv_type} du {lv_start} au {lv_end}.", doc_info

    # Contract request
    if is_contract_request:
        result = _get_my_employee(user, db) if is_mine else _find_employee(query, db)
        if not result:
            return "❌ Employé introuvable. Précisez le nom complet.", None
        emp, target_user = result
        contract = db.query(Contract).filter(Contract.user_id == target_user.id).first()
        if not contract:
            return f"❌ {target_user.prenom} {target_user.nom} n'a pas de contrat enregistré.", None
        
        try:
            from api.contracts import get_contract_html
            from ai.utils.pdf_generator import generate_pdf
            from ai.services.document_generator import _upload_pdf_bytes

            content = get_contract_html(contract, target_user, db)
            contract_type = (contract.contract_type or "CDI").upper()
            title = f"Contrat {contract_type} - {target_user.prenom} {target_user.nom}"
            
            pdf_bytes = generate_pdf(
                title=title,
                content=content,
                document_type="contrat",
                sig_left_label="Le Salarié",
                sig_left_name=f"{target_user.prenom} {target_user.nom}"
            )
            
            safe_title = re.sub(r'[^\w\s-]', '', title).strip().lower()[:80] or "contrat"
            file_url = _upload_pdf_bytes(pdf_bytes, safe_title)
            
            key = file_url.split("/", 1)[-1]
            doc_info = ChatDocumentInfo(
                id=0, title=title, document_type="contrat",
                pdf_url=f"/api/ai/documents/minio/{key}", status="final",
            )
            
            # Save the document to DB so it appears in the documents list
            _save_doc_to_db(
                requesting_user=user,
                target_user_id=target_user.id,
                title=title,
                content=title,
                doc_type="contrat",
                file_url=file_url,
                db=db,
            )
            
            return f"✅ Contrat de travail ({contract_type}) généré pour **{target_user.prenom} {target_user.nom}**.", doc_info
        except Exception as e:
            return f"❌ Erreur lors de la génération du contrat : {str(e)}", None

    # Generic fallback: try work certificate
    result = _get_my_employee(user, db) if is_mine else _find_employee(query, db)
    if not result:
        return (
            "❌ Employé introuvable dans la base. Veuillez préciser le nom complet "
            "(ex: 'attestation de travail pour Jean Dupont')",
            None,
        )

    emp, target_user = result
    try:
        title, file_url, text = _build_certificate(emp, target_user, user, db, "work")
        key = file_url.split("/", 1)[-1]
        doc_info = ChatDocumentInfo(
            id=0, title=title, document_type="attestation_travail",
            pdf_url=f"/api/ai/documents/minio/{key}", status="final",
        )
        return text, doc_info
    except Exception as e:
        return f"❌ Erreur lors de la génération du document : {str(e)}", None


def _detect_lang(q: str) -> str:
    """Return 'fr' if the query appears to be French, else 'en'."""
    fr_words = {"bonjour", "bonsoir", "comment", "quel", "quelle", "quels", "quelles",
                "combien", "liste", "tous", "employes", "employés", "mon", "ma", "mes",
                "je", "tu", "vous", "nous", "est", "sont", "suis", "avez", "avons",
                "qui", "suis", "rôle", "role", "merci", "salut"}
    words = set(q.lower().split())
    return "fr" if words & fr_words else "en"


def _simple_query(q_lower: str, user: User, db: Session) -> str | None:
    q = q_lower.strip().rstrip("?.!")
    lang = _detect_lang(q)

    # Employee count
    count_fr = {"nombre d'employés", "combien d'employés", "combien d employes", "total employés", "total employes"}
    count_en = {"how many employees", "employee count", "total employees", "how many employees do we have", "how many people work here"}
    if q in count_fr | count_en:
        from models.employees import Employee
        cnt = db.query(Employee).count()
        if lang == "fr" or q in count_fr:
            return f"Nous avons actuellement **{cnt} employés** dans l'entreprise."
        return f"We currently have **{cnt} employees** in the company."

    # Role / identity
    role_fr = {"quel est mon rôle", "quel est mon role", "mon rôle", "mon role", "qui suis je", "qui suis-je"}
    role_en = {"what is my role", "what's my role", "who am i", "what am i", "my role"}
    if q in role_fr | role_en:
        if lang == "fr" or q in role_fr:
            return f"Vous êtes **{user.prenom} {user.nom}** avec le rôle **{user.role.value}**."
        return f"You are **{user.prenom} {user.nom}** with the role **{user.role.value}**."

    # Greeting
    greet_fr = {"bonjour", "bonsoir", "salut", "coucou"}
    greet_en = {"hello", "hi", "hey", "good morning", "good afternoon", "good evening"}
    if q in greet_fr:
        return f"Bonjour **{user.prenom} {user.nom}**. Comment puis-je vous aider aujourd'hui ?"
    if q in greet_en:
        return f"Hello **{user.prenom} {user.nom}**! How can I help you today?"

    # Employee list
    list_fr = {"liste des employés", "liste des employes", "tous les employés", "tous les employes"}
    list_en = {"list employees", "show all employees", "all employees", "list all employees"}
    if q in list_fr | list_en:
        from models.employees import Employee
        emps = db.query(Employee).order_by(Employee.id).all()
        if lang == "fr" or q in list_fr:
            if not emps:
                return "Aucun employé trouvé."
            lines = []
            for e in emps:
                u = db.query(User).filter(User.id == e.user_id).first()
                name = f"{u.prenom} {u.nom}" if u else f"#{e.user_id}"
                dept = e.department.name if e.department else "N/A"
                lines.append(f"- {name} ({dept})")
            return f"**Liste des employés ({len(emps)}) :**\n" + "\n".join(lines)
        else:
            if not emps:
                return "No employees found."
            lines = []
            for e in emps:
                u = db.query(User).filter(User.id == e.user_id).first()
                name = f"{u.prenom} {u.nom}" if u else f"#{e.user_id}"
                dept = e.department.name if e.department else "N/A"
                lines.append(f"- {name} ({dept})")
            return f"**Employees ({len(emps)}) :**\n" + "\n".join(lines)
    return None


def chat(
    query: str,
    user: User,
    db: Session,
    history: list | None = None,
    conversation_id: int | None = None,
) -> tuple[str, ChatDocumentInfo | None, list | None, str | None, int | None]:
    conv_id = conversation_id
    try:
        guard_block = input_guardrail(query)
        if guard_block:
            conv_id = _save_chat_log(query, guard_block, user, db, conv_id)
            return guard_block, None, None, None, conv_id

        simple = _simple_query(query.lower(), user, db)
        if simple:
            conv_id = _save_chat_log(query, simple, user, db, conv_id)
            return simple, None, None, None, conv_id

        messages, doc_chunks = _build_messages(query, user, db, history, conv_id)

        # ── Intercept document generation requests before LLM to avoid hallucinations ──
        if _is_document_request(query):
            if user.role.value == "rh":
                fallback_text, doc_info = _fallback_document(query, user, db)
                if doc_info is not None:  # A document was actually generated
                    conv_id = _save_chat_log(query, fallback_text, user, db, conv_id)
                    return fallback_text, doc_info, None, None, conv_id
            else:
                from utils.notifications import notify_role
                msg = f"⚠️ Alerte Sécurité IA : {user.prenom} {user.nom} (Rôle: {user.role.value}) a tenté de faire générer un document par l'assistant IA sans autorisation."
                try:
                    notify_role(db, RoleEnum.ADMIN, msg)
                    notify_role(db, RoleEnum.RH, msg)
                except Exception as e:
                    print("Erreur notification accès refusé chat:", e)
                
                refusal_msg = "vous n'avez pas le droit de générer des documents, seul le RH peut le faire. Veuillez le signaler au service RH"
                conv_id = _save_chat_log(query, refusal_msg, user, db, conv_id)
                return refusal_msg, None, None, None, conv_id

        response_msg = call_llm_with_tools(messages, tools=TOOLS, tool_choice="auto")


        chart_b64 = None
        if response_msg and response_msg.get("tool_calls"):
            messages.append(response_msg)
            
            for tool_call in response_msg["tool_calls"]:
                result = execute_tool(tool_call, db=db, user=user)
                if isinstance(result, dict) and result.get("chart"):
                    chart_b64 = result["chart"]
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "name": tool_call["function"]["name"],
                    "content": json.dumps(result, ensure_ascii=False),
                })
                
            messages.append({
                "role": "system",
                "content": "Inform the user about what happened based on the tool results using natural language. YOU MUST RESPOND IN FRENCH. If success, confirm clearly. If error, explain why."
            })

            final_msg = call_llm_with_tools(messages, tools=TOOLS, tool_choice="none")
            response_text = final_msg.get("content", "").strip() if final_msg else ""
            if not response_text:
                response_text = "Opération terminée."
            response_text = semantic_filter(response_text)
            conv_id = _save_chat_log(query, response_text, user, db, conv_id)
            return response_text, None, None, chart_b64, conv_id

        response_text = response_msg.get("content", "").strip() if response_msg else ""
        if response_text:
            response_text = semantic_filter(response_text)

        if not response_text:
            fallback = _simple_query(query.lower(), user, db)
            if fallback:
                conv_id = _save_chat_log(query, fallback, user, db, conv_id)
                return fallback, None, None, None, conv_id
            lang = _detect_lang(query.lower())
            if lang == "fr":
                err = "Je suis désolé, je ne peux pas répondre à cette question pour le moment. Veuillez réessayer."
            else:
                err = "Je suis désolé, je ne peux pas répondre à cette question pour le moment. Veuillez réessayer."
            conv_id = _save_chat_log(query, err, user, db, conv_id)
            return err, None, None, None, conv_id

        sources = [
            {
                "title": chunk["source"].replace(".pdf", "").replace("_", " ").title(),
                "page": chunk["page"],
                "snippet": chunk["text"][:200],
            }
            for chunk in doc_chunks
        ]
        conv_id = _save_chat_log(query, response_text, user, db, conv_id)
        return response_text, None, sources if sources else None, None, conv_id

    except Exception as e:
        import traceback
        traceback.print_exc()
        error_msg = str(e)
        # return the error in the chat
        response_text = f"❌ Une erreur s'est produite lors du traitement de votre demande :\n{error_msg}"
        doc_info = None
        conv_id = _save_chat_log(query, response_text, user, db, conv_id)
        return response_text, doc_info, None, None, conv_id


def chat_stream(
    query: str,
    user: User,
    db: Session,
    history: list | None = None,
    conversation_id: int | None = None,
):
    from ai.utils.llm_client import call_llm_stream
    conv_id = conversation_id
    try:
        guard_block = input_guardrail(query)
        if guard_block:
            conv_id = _save_chat_log(query, guard_block, user, db, conv_id)
            import json
            yield f"data: {{\"content\": \"{guard_block}\", \"conversation_id\": {conv_id}}}\n\n"
            yield "data: [DONE]\n\n"
            return

        simple = _simple_query(query.lower(), user, db)
        if simple:
            conv_id = _save_chat_log(query, simple, user, db, conv_id)
            import json
            yield f"data: {{\"content\": \"{simple}\", \"conversation_id\": {conv_id}}}\n\n"
            yield "data: [DONE]\n\n"
            return

        messages, doc_chunks = _build_messages(query, user, db, history, conv_id)
        
        full_text = ""
        for chunk in call_llm_stream(messages):
            if chunk.startswith('data: {"content":'):
                import json
                try:
                    data = json.loads(chunk[6:])
                    full_text += data.get("content", "")
                except:
                    pass
            yield chunk
            
        conv_id = _save_chat_log(query, full_text, user, db, conv_id)
        yield f"data: {{\"conversation_id\": {conv_id}}}\n\n"
        yield "data: [DONE]\n\n"

    except Exception as e:
        import json
        yield f"data: {{\"error\": \"Une erreur s'est produite : {str(e)}\"}}\n\n"

