
import re
import random
from datetime import date, datetime
from pathlib import Path
try:
    from weasyprint import HTML
except (ImportError, OSError):
    class HTML:
        def __init__(self, string=None, **kwargs):
            self.string = string
        def write_pdf(self):
            return b"%PDF-1.4 Mocked PDF for Windows"

# Corporate Executive Palette Constants
NAVY = "#2b6cb0"
DARK_NAVY = "#1a365d"
SLATE = "#718096"
DARK_TEXT = "#2d3748"
BORDER = "#e2e8f0"
BG_SOFT = "#f7fafc"
BG_TABLE = "#edf2f7"
FOOTER_CLR = "#a0aec0"
WHITE = "#ffffff"


def _safe(text: str) -> str:
    if not text:
        return ""
    text = text.replace('\u2014', '--').replace('\u2013', '-')
    text = text.replace('\u2019', "'").replace('\u2018', "'")
    text = text.replace('\u201c', '"').replace('\u201d', '"')
    text = text.replace('\u00ab', '"').replace('\u00bb', '"')
    text = text.replace('\u0153', 'oe').replace('\u0152', 'OE')
    text = text.replace('\u20ac', ' EUR')
    text = text.replace('\u202f', ' ').replace('\u00a0', ' ')
    text = re.sub(r'\*{1,3}(.+?)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,2}(.+?)_{1,2}', r'\1', text)
    text = re.sub(r'#+\s*', '', text)
    text = re.sub(r'`+', '', text)
    return text


def _format_date_fr(date_val) -> str:
    if not date_val:
        return ""
    if isinstance(date_val, str):
        date_str = date_val.strip()
        try:
            if "-" in date_str:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
            elif "/" in date_str:
                dt = datetime.strptime(date_str, "%d/%m/%Y")
            else:
                return date_str
        except Exception:
            return date_str
    elif isinstance(date_val, (date, datetime)):
        dt = date_val
    else:
        return str(date_val)
    months = {
        1: "janvier", 2: "février", 3: "mars", 4: "avril", 5: "mai", 6: "juin",
        7: "juillet", 8: "août", 9: "septembre", 10: "octobre", 11: "novembre", 12: "décembre"
    }
    day_str = "1er" if dt.day == 1 else str(dt.day)
    return f"{day_str} {months[dt.month]} {dt.year}"


def _make_header_html() -> str:
    """Generates the modern executive header block used consistently across documents."""
    return f"""
    <div class="header-emp">
        <div class="header-company">NexcoreRH</div>
        <div class="header-subtitle">SmartRH — Plateforme Intelligente de Gestion RH</div>
        <div class="header-meta">
            123 Avenue Hassan II, 20000 Casablanca, Maroc<br>
            Tél : +212 522 12 34 56 | Email : contact@nexcorerh.com
        </div>
    </div>
    """


def _make_title_block(title_label: str, ref: str) -> str:
    """Generates a clean title display with an embedded reference tracking code."""
    return f"""
    <div class="title-block">
        <div class="title-main">{_safe(title_label)}</div>
        <div class="title-ref">{_safe(ref)}</div>
    </div>
    """


def _make_signature_block(city: str, today_fr: str, left_label: str = None, left_name: str = None) -> str:
    """Generates a signature segment protected against layout page splits."""
    if left_label and left_name:
        left_html = f"<p><strong>{_safe(left_label)}</strong></p><p>{_safe(left_name)}</p>"
    else:
        left_html = '<p><strong>Pour l\'Employé(e)</strong></p><p class="sig-subtext">(Signature précédée de la mention "Lu et approuvé")</p>'
        
    return f"""
    <p class="date-location">Fait à {_safe(city)}, le {today_fr}</p>
    <div class="signature-container clearfix">
        <div class="sig-box sig-left">
            {left_html}
            <div class="sig-line">_______________________</div>
        </div>
        <div class="sig-box sig-right">
            <p><strong>Pour la Direction Générale</strong></p>
            <p>Le Directeur des RH</p>
            <p class="sig-subtext">[Cachet NexcoreRH]</p>
            <div class="sig-line">_______________________</div>
        </div>
    </div>
    """


def _base_template(body_html: str, doc_type: str = "default") -> str:
    """
    Applies the defensive CSS blueprint rules directly inside the execution template.
    Enforces page sizing limitations to isolate layouts perfectly onto 1 page.
    """
    today_short = date.today().strftime("%d/%m/%Y")
    
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<style>
    @page {{
        size: A4;
        margin: 15mm 15mm 15mm 15mm;
        @bottom-center {{
            content: "NexcoreRH (SmartRH) — Document Confidentiel — Extraction Système Unique du {today_short}";
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            font-size: 7.5pt;
            color: {FOOTER_CLR};
            border-top: 1px solid {BORDER};
            width: 100%;
            padding-top: 5px;
        }}
    }}
    
    *, *::before, *::after {{ box-sizing: border-box; }}
    html, body {{ margin: 0; padding: 0; background-color: {WHITE}; }}
    
    body {{
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        color: {DARK_TEXT}; 
        line-height: 1.4;
        font-size: 9.5pt;
    }}
    
    .page-content {{ display: block; }}
    
    /* Header Component Styles */
    .header-emp {{ border-bottom: 2px solid {NAVY}; margin-bottom: 20px; padding-bottom: 8px; }}
    .header-company {{ font-size: 12pt; font-weight: bold; color: {DARK_TEXT}; }}
    .header-subtitle {{ font-size: 9.5pt; color: {SLATE}; margin-top: 1px; }}
    .header-meta {{ font-size: 9pt; color: {SLATE}; margin-top: 2px; line-height: 1.3; }}
    
    /* Title Component Styles */
    .title-block {{ background: none; border: none; padding: 0; margin: 0 0 15px 0; text-align: center; }}
    .title-main {{ font-size: 16pt; font-weight: bold; color: {DARK_NAVY}; letter-spacing: 1px; text-transform: uppercase; }}
    .title-ref {{ font-size: 8pt; color: {FOOTER_CLR}; margin-top: 2px; }}
    
    /* Document Section Headings */
    .section {{ font-size: 11pt; font-weight: bold; color: {NAVY}; text-transform: uppercase; margin: 15px 0 8px 0; }}
    
    /* Table Metrics Sizing & Layout */
    table.info {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; page-break-inside: avoid; }}
    table.info th {{ background-color: {BG_TABLE}; color: #4a5568; font-weight: 600; padding: 8px 12px; font-size: 9.5pt; border: 1px solid {BORDER}; text-align: left; width: 30%; }}
    table.info td {{ padding: 8px 12px; border: 1px solid {BORDER}; font-size: 9.5pt; color: {DARK_TEXT}; background-color: {WHITE}; width: 70%; }}
    
    /* Narrative Callout Components */
    .callout {{ background-color: {BG_SOFT}; border-left: 4px solid {NAVY}; padding: 12px 15px; text-align: justify; font-size: 9.5pt; color: #4a5568; margin-bottom: 15px; }}
    
    /* Status Capsule Badges — green / yellow / red */
    .status-green {{ background-color: #c6f6d5; color: #22543d; padding: 2px 8px; border-radius: 4px; font-size: 8pt; font-weight: bold; display: inline-block; }}
    .status-yellow {{ background-color: #fefcbf; color: #744210; padding: 2px 8px; border-radius: 4px; font-size: 8pt; font-weight: bold; display: inline-block; }}
    .status-red {{ background-color: #fed7d7; color: #9b2c2c; padding: 2px 8px; border-radius: 4px; font-size: 8pt; font-weight: bold; display: inline-block; }}
    
    /* Signature Block Layout Components */
    .date-location {{ text-align: center; margin: 25px 0 5px 0; font-size: 9.5pt; font-weight: bold; }}
    .signature-container {{ margin-top: 15px; page-break-inside: avoid; }}
    .sig-box {{ width: 45%; text-align: center; }}
    .sig-left {{ float: left; }}
    .sig-right {{ float: right; }}
    .sig-box p {{ margin: 2px 0; font-size: 9.5pt; }}
    .sig-subtext {{ font-size: 8.5pt; color: {SLATE}; }}
    .sig-line {{ margin-top: 15px; color: {SLATE}; }}
    
    /* Utility Layout Fixes */
    .spacer {{ height: 5px; }}
    .bottom-section {{ margin-top: 20px; page-break-inside: avoid; }}
    .clearfix::after {{ content: ""; clear: both; display: table; }}
</style>
</head>
<body class="doc-{doc_type}">
<div class="page-content">
    {body_html}
</div>
</body>
</html>"""


def _make_info_table(rows: list) -> str:
    """Builds structural metadata tables matching the design guide proportions."""
    trs = ""
    for label, value in rows:
        val_str = str(value)
        vlow = val_str.lower().strip()
        if vlow in ["actif", "approuvé", "approuve", "conforme aux attentes", "approved"]:
            val_str = f"<span class='status-green'>{val_str}</span>"
        elif vlow in ["en attente", "en_cours", "pending", "soumis"]:
            val_str = f"<span class='status-yellow'>{val_str}</span>"
        elif vlow in ["rejeté", "rejete", "refusé", "refuse", "rejected", "annulé", "annule", "cancelled"]:
            val_str = f"<span class='status-red'>{val_str}</span>"
        trs += f"<tr><th>{_safe(label)}</th><td>{val_str}</td></tr>\n"
    return f"<table class='info'>{trs}</table>"


def generate_work_certificate_html(
    employee_name: str, job_title: str, department: str,
    contract_type: str, start_date: str, city: str = "Casablanca"
) -> str:
    today_fr = _format_date_fr(date.today())
    ref = f"Réf : AT-{date.today().year}-{random.randint(1000, 9999):04d}"

    info = _make_info_table([
        ("Nom & Prénom :", employee_name),
        ("Poste Occupé :", job_title),
        ("Département :", department),
        ("Type de Contrat :", contract_type),
        ("Date d'Embauche :", _format_date_fr(start_date)),
        ("Statut Administratif :", "Actif"),
    ])

    cert_text = (
        f"La société <strong>NexcoreRH</strong>, dont le siège social est situé au "
        f"123 Avenue Hassan II, 20000 Casablanca, Maroc, certifie par la présente que l'employé(e) "
        f"désigné(e) ci-dessus est inscrit(e) au sein de nos effectifs. "
        f"<br><br>La direction des Ressources Humaines confirme que l'intéressé(e) "
        f"exerce ses fonctions de manière continue et permanente. Il/Elle est libre de tout engagement envers d'autres structures à "
        f"la date de délivrance de ce document. Cette attestation est délivrée à "
        f"l'intéressé(e) pour servir et valoir ce que de droit."
    )

    body = f"""
    {_make_header_html()}
    {_make_title_block("ATTESTATION DE TRAVAIL", ref)}
    <div class="section">INFORMATIONS SUR L'EMPLOYÉ</div>
    {info}
    <div class="section">DÉCLARATION DE CONFORMITÉ</div>
    <div class="callout">{cert_text}</div>
    <div class="bottom-section">
        {_make_signature_block(city, today_fr)}
    </div>
    """
    return _base_template(body, doc_type="employment_certificate")


def generate_leave_certificate_html(
    employee_name: str, employee_id: str, job_title: str, department: str,
    contract_type: str, contract_start_date: str, leave_type: str,
    start_date: str, end_date: str, num_days: str, status: str,
    city: str = "Casablanca", hr_manager_name: str = None
) -> str:
    today_fr = _format_date_fr(date.today())
    today_short = date.today().strftime("%d/%m/%Y")
    ref = f"Réf : CERT-{today_short.replace('/', '')}-{random.randint(1000, 9999):04d}"

    info = _make_info_table([
        ("Nom complet :", employee_name),
        ("Matricule :", employee_id),
        ("Poste Occupé :", job_title),
        ("Département :", department),
        ("Type de contrat :", contract_type),
        ("Date d'entrée :", _format_date_fr(contract_start_date)),
    ])

    leave_info = _make_info_table([
        ("Type de congé :", leave_type),
        ("Statut Demande :", status),
        ("Date de début :", start_date),
        ("Date de fin :", end_date),
        ("Nombre de jours :", f"{num_days} jours"),
    ])

    cert_text = (
        f"Nous certifions par la présente que <strong>{_safe(employee_name)}</strong>, "
        f"occupant le poste de <strong>{_safe(job_title)}</strong> au sein du département "
        f"<strong>{_safe(department)}</strong>, a bénéficié d'un congé de type "
        f"<strong>{_safe(leave_type)}</strong> du <strong>{start_date}</strong> au "
        f"<strong>{end_date}</strong>, soit un total de <strong>{num_days}</strong> jours."
        f"<br><br>Le présent certificat est délivré à la demande de l'intéressé(e) pour servir "
        f"et valoir ce que de droit auprès de toute autorité administrative de gestion de compétences."
    )

    body = f"""
    {_make_header_html()}
    {_make_title_block("CERTIFICAT DE CONGÉ", ref)}
    <div class="section">1. INFORMATIONS DE L'EMPLOYÉ</div>
    {info}
    <div class="section">2. DÉTAILS DE LA PÉRIODE DE CONGÉ</div>
    {leave_info}
    <div class="section">3. ATTRIBUTION & VALIDATION</div>
    <div class="callout">{cert_text}</div>
    <div class="bottom-section">
        {_make_signature_block(city, today_fr, left_label="Bénéficiaire", left_name=employee_name)}
    </div>
    """
    return _base_template(body, doc_type="leave_certificate")


def generate_report_html(title: str, content: str, document_type: str = None, sig_left_label: str = None, sig_left_name: str = None) -> str:
    """
    Unified fall-back parser engine. Decodes structure matrices into pure components 
    while embedding specific visual overrides based on requested targets.
    """
    city = "Casablanca"
    today_fr = _format_date_fr(date.today())
    today_short = date.today().strftime("%d/%m/%Y")

    doc_type_label = {
        "leave_certificate": "CERTIFICAT DE CONGÉ",
        "admin_request": "DEMANDE ADMINISTRATIVE",
        "hr_summary": "FICHE DE SYNTHÈSE RH",
        "employment_certificate": "ATTESTATION DE TRAVAIL",
    }.get(document_type or "", _safe(title).upper() if title else "DOCUMENT RH")

    ref = f"Réf : {today_short.replace('/', '')}-{random.randint(1000, 9999):04d}"

    safe_content = _safe(content)
    paragraphs_html = ""
    
    # Process inputs block-by-block to inject correct layout elements
    for para in safe_content.split("\n"):
        stripped = para.strip()
        if not stripped:
            paragraphs_html += '<div class="spacer"></div>'
            continue
        if "|" in stripped:
            cells = [c.strip() for c in stripped.split("|") if c.strip()]
            if len(cells) >= 2:
                first = cells[0]
                rest = cells[1:]
                val_str = "".join(f"{_safe(c)}" for c in rest)
                vlow2 = val_str.lower().strip()
                if vlow2 in ["actif", "approuvé", "approuve", "conforme aux attentes"]:
                    val_str = f"<span class='status-badge'>{val_str}</span>"
                elif vlow2 in ["en attente", "en_cours", "pending", "soumis"]:
                    val_str = f"<span class='status-pending'>{val_str}</span>"
                elif vlow2 in ["rejeté", "rejete", "refusé", "refuse", "rejected"]:
                    val_str = f"<span class='status-rejected'>{val_str}</span>"
                tr = f"<th>{_safe(first)}</th><td>{val_str}</td>"
                paragraphs_html += f"<table class='info'><tr>{tr}</tr></table>"
                continue
        if stripped.lower().startswith('objet'):
            paragraphs_html += f"<p style='margin:4px 0; text-align:justify; font-weight:bold;'>{stripped}</p>"
            continue
        if stripped.isupper() and len(stripped) > 3:
            paragraphs_html += f'<div class="section">{stripped}</div>'
        else:
            paragraphs_html += f"<p style='margin:4px 0; text-align:justify;'>{stripped}</p>"

    body = f"""
    {_make_header_html()}
    {_make_title_block(doc_type_label, ref)}
    {paragraphs_html}
    <div class="bottom-section">
        {_make_signature_block(city, today_fr, left_label=sig_left_label, left_name=sig_left_name)}
    </div>
    """
    return _base_template(body, doc_type=document_type)


def generate_pdf(title: str, content: str, document_type: str = None, sig_left_label: str = None, sig_left_name: str = None) -> bytes:
    html_str = generate_report_html(title, content, document_type, sig_left_label, sig_left_name)
    return HTML(string=html_str).write_pdf()


def html_to_pdf(html_str: str) -> bytes:
    return HTML(string=html_str).write_pdf()


