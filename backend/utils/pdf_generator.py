from fpdf import FPDF
from datetime import date
import re

def clean_text_for_pdf(text: str) -> str:
    """
    Nettoie le texte pour éviter les erreurs d'encodage avec les polices standards FPDF (latin-1).
    Remplace les caractères spéciaux Unicode non supportés par des équivalents proches.
    """
    if not text:
        return ""
    
    replacements = {
        '—': '-',
        '–': '-',
        '’': "'",
        '‘': "'",
        '“': '"',
        '”': '"',
        '«': '"',
        '»': '"',
        'œ': 'oe',
        'Œ': 'OE',
        '€': ' EUR',
        '\u202f': ' ', # Narrow no-break space
        '\xa0': ' ',   # No-break space
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
        
    return text.encode('latin-1', errors='replace').decode('latin-1')


def parse_document_content(content: str):
    """
    Parse the document content into structured elements:
    - sections: list of dicts:
        - type: 'header' | 'table' | 'highlight' | 'paragraph'
        - title: str
        - rows: list of (key, value)
        - text: str
    - date_place: str
    - signatures: dict with keys 'left' and 'right' (tuples of (title, name/details))
    """
    lines = content.split('\n')
    sections = []
    current_table = []
    current_highlight = []
    
    date_place = None
    signatures = {}
    
    for line in lines:
        cleaned = line.strip()
        if not cleaned:
            continue
            
        # Detect signatures
        if cleaned.startswith("Bénéficiaire :") or cleaned.startswith("Demandeur :") or cleaned.startswith("Bénéficiaire:") or cleaned.startswith("Demandeur:"):
            parts = cleaned.split(':', 1)
            title = parts[0].strip()
            name = parts[1].strip()
            signatures["left"] = (title, name)
            continue
            
        if cleaned.startswith("Pour la Direction Générale :") or cleaned.startswith("Pour la Direction Générale:"):
            parts = cleaned.split(':', 1)
            title = parts[0].strip()
            details = parts[1].strip()
            signatures["right"] = (title, details)
            continue

        # Detect Fait à
        if cleaned.startswith("Fait à") or cleaned.startswith("Fait a"):
            date_place = cleaned
            continue
            
        # Detect Section Headers (e.g. "1. INFORMATIONS DE L'EMPLOYÉ")
        header_match = re.match(r'^\d+\.\s+(.*)$', cleaned)
        if header_match:
            if current_table:
                sections.append({"type": "table", "rows": current_table})
                current_table = []
            if current_highlight:
                sections.append({"type": "highlight", "text": "\n".join(current_highlight)})
                current_highlight = []
                
            sections.append({"type": "header", "title": cleaned})
            continue
            
        # Detect Key-Value pair for Table
        if ":" in cleaned and not cleaned.startswith("http") and not cleaned.startswith("mailto"):
            parts = cleaned.split(':', 1)
            key = parts[0].strip()
            val = parts[1].strip()
            # If key is relatively short, treat it as a table row
            if len(key) < 30 and len(val) > 0:
                if current_highlight:
                    sections.append({"type": "highlight", "text": "\n".join(current_highlight)})
                    current_highlight = []
                current_table.append((key, val))
                continue
                
        # Flush table if we were building one
        if current_table:
            sections.append({"type": "table", "rows": current_table})
            current_table = []
            
        # Check if we are in highlight section
        is_highlight_section = False
        last_header = None
        for s in reversed(sections):
            if s["type"] == "header":
                last_header = s["title"].upper()
                break
        if last_header and ("ATTRIBUTION" in last_header or "VALIDATION" in last_header or "3." in last_header):
            is_highlight_section = True
            
        if is_highlight_section:
            current_highlight.append(cleaned)
        else:
            sections.append({"type": "paragraph", "text": cleaned})
            
    # Flush remaining
    if current_table:
        sections.append({"type": "table", "rows": current_table})
    if current_highlight:
        sections.append({"type": "highlight", "text": "\n".join(current_highlight)})
        
    return sections, date_place, signatures


def generate_pdf(title: str, content: str, document_type: str = None, document_id: int = None) -> bytes:
    """
    Génère un PDF propre et mis en forme à partir du contenu d'un document.
    Format professionnel de type "SMART RH".
    """

    class DocumentPDF(FPDF):
        def header(self):
            # En-tête de page NEXCORE RH
            self.set_font('Helvetica', 'B', 12)
            self.set_text_color(31, 41, 55) # Off-black
            self.cell(0, 5, clean_text_for_pdf("NEXCORE RH"), ln=True)
            
            self.set_font('Helvetica', '', 8.5)
            self.set_text_color(107, 114, 128) # Grey
            self.cell(0, 4, clean_text_for_pdf("SmartRH - Plateforme Intelligente de Gestion RH"), ln=True)
            self.cell(0, 4, clean_text_for_pdf("123 Avenue Hassan II, 20000 Casablanca, Maroc"), ln=True)
            self.cell(0, 4, clean_text_for_pdf("Tél : +212 522 12 34 56 | Email : contact@smartrh.com"), ln=True)
            
            # Ligne de séparation bleue
            self.ln(2)
            self.set_draw_color(30, 64, 175) # Blue
            self.set_line_width(0.7)
            self.line(15, self.get_y(), 195, self.get_y())
            self.set_line_width(0.2) # Reset
            self.ln(6)

        def footer(self):
            self.set_y(-15)
            self.set_font('Helvetica', 'I', 8)
            self.set_text_color(156, 163, 175)
            today_str = date.today().strftime("%d/%m/%Y")
            footer_text = f"Document généré le {today_str} - Confidentiel - Page {self.page_no()}"
            self.cell(0, 5, clean_text_for_pdf(footer_text), align='C')

    pdf = DocumentPDF()
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # Nettoyage et formatage du Titre
    safe_title = clean_text_for_pdf(title)
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(30, 64, 175)
    pdf.cell(0, 8, safe_title.upper(), ln=True, align='C')

    # Génération et affichage de la Référence
    ref_date = date.today().strftime("%d%m%Y")
    doc_num = f"{1000 + document_id}" if document_id else "9999"
    if "CONGÉ" in safe_title.upper() or "ABSENCE" in safe_title.upper():
        ref_text = f"Réf : CERT-{ref_date}-{doc_num}"
    else:
        ref_text = f"Réf : {ref_date}-{doc_num}"
        
    pdf.set_font('Helvetica', '', 8.5)
    pdf.set_text_color(156, 163, 175)
    pdf.cell(0, 5, ref_text, ln=True, align='C')
    pdf.set_text_color(0, 0, 0)
    pdf.ln(6)

    # Parser le contenu
    sections, date_place, signatures = parse_document_content(content)

    for section in sections:
        if section["type"] == "header":
            pdf.ln(3)
            pdf.set_font('Helvetica', 'B', 10.5)
            pdf.set_text_color(30, 64, 175)
            pdf.cell(0, 6, clean_text_for_pdf(section["title"]), ln=True)
            pdf.ln(2.5)
            
        elif section["type"] == "table":
            pdf.set_draw_color(229, 231, 235) # Light grey borders
            for key, val in section["rows"]:
                # Exclure le champ "Objet" d'un format tableau et le traiter plus tard
                if key.lower() == "objet":
                    pdf.ln(1)
                    pdf.set_font('Helvetica', 'B', 10)
                    pdf.set_text_color(31, 41, 55)
                    pdf.write(6, "Objet : ")
                    pdf.set_font('Helvetica', '', 10)
                    pdf.write(6, clean_text_for_pdf(val) + "\n")
                    pdf.ln(2)
                    continue
                    
                # Rendu d'une ligne de tableau standard
                pdf.set_font('Helvetica', 'B', 9)
                pdf.set_text_color(55, 65, 81)
                pdf.set_fill_color(249, 250, 251) # Grey bg for key
                pdf.cell(50, 8.5, clean_text_for_pdf(key), border=1, fill=True)
                
                pdf.set_font('Helvetica', '', 9)
                pdf.set_text_color(31, 41, 55)
                pdf.set_fill_color(255, 255, 255) # White bg for value
                
                val_clean = val.strip()
                if val_clean in ["Approuvé", "Approuve", "approved"]:
                    pdf.cell(130, 8.5, "", border=1, fill=True)
                    # Dessiner le badge vert
                    x = pdf.get_x() - 130 + 4
                    y = pdf.get_y() + 1.7
                    pdf.set_fill_color(209, 250, 229)
                    pdf.rect(x, y, 20, 5, 'F')
                    pdf.set_text_color(6, 95, 70)
                    pdf.set_font('Helvetica', 'B', 7.5)
                    pdf.text(x + 2.5, y + 3.8, "Approuve")
                elif val_clean in ["En attente", "pending"]:
                    pdf.cell(130, 8.5, "", border=1, fill=True)
                    # Dessiner le badge orange
                    x = pdf.get_x() - 130 + 4
                    y = pdf.get_y() + 1.7
                    pdf.set_fill_color(254, 243, 199)
                    pdf.rect(x, y, 20, 5, 'F')
                    pdf.set_text_color(146, 64, 14)
                    pdf.set_font('Helvetica', 'B', 7.5)
                    pdf.text(x + 2.5, y + 3.8, "En attente")
                else:
                    pdf.cell(130, 8.5, clean_text_for_pdf(val), border=1, fill=True)
                    
                pdf.ln(8.5)
            pdf.ln(2.5)
            
        elif section["type"] == "highlight":
            start_y = pdf.get_y()
            pdf.set_fill_color(248, 250, 252) # Soft light bg
            pdf.set_font('Helvetica', '', 9.5)
            pdf.set_text_color(31, 41, 55)
            
            # Décaler le X de 3mm pour laisser de la place à la barre
            pdf.set_x(18)
            pdf.multi_cell(172, 5.5, clean_text_for_pdf(section["text"]), border=0, fill=True)
            end_y = pdf.get_y()
            
            # Dessiner la ligne verticale bleue
            pdf.set_draw_color(30, 64, 175)
            pdf.set_line_width(1.0)
            pdf.line(15, start_y, 15, end_y)
            pdf.set_line_width(0.2) # Reset line width
            pdf.ln(4)
            
        elif section["type"] == "paragraph":
            txt = section["text"].strip()
            if txt.startswith("Objet :") or txt.startswith("Objet:"):
                parts = txt.split(':', 1)
                pdf.set_font('Helvetica', 'B', 10)
                pdf.set_text_color(31, 41, 55)
                pdf.write(6, "Objet : ")
                pdf.set_font('Helvetica', '', 10)
                pdf.write(6, clean_text_for_pdf(parts[1].strip()) + "\n")
                pdf.ln(2)
            else:
                pdf.set_font('Helvetica', '', 10)
                pdf.set_text_color(31, 41, 55)
                pdf.multi_cell(0, 6, clean_text_for_pdf(txt))
                pdf.ln(2)

    # Date et Lieu
    if date_place:
        pdf.ln(4)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_text_color(31, 41, 55)
        pdf.cell(0, 6, clean_text_for_pdf(date_place), ln=True, align='C')
        pdf.ln(4)

    # Signatures
    if signatures:
        start_y = pdf.get_y()
        if start_y > 235:
            pdf.add_page()
            start_y = pdf.get_y()
            
        # Colonne Gauche (Bénéficiaire / Demandeur)
        if "left" in signatures:
            pdf.set_xy(15, start_y)
            title, name = signatures["left"]
            pdf.set_font('Helvetica', 'B', 10)
            pdf.set_text_color(31, 41, 55)
            pdf.cell(85, 5, clean_text_for_pdf(title), ln=True, align='C')
            pdf.set_font('Helvetica', '', 9.5)
            pdf.set_text_color(75, 85, 99)
            pdf.cell(85, 5, clean_text_for_pdf(name), ln=True, align='C')
            pdf.ln(12)
            pdf.set_draw_color(156, 163, 175)
            pdf.set_line_width(0.3)
            pdf.line(25, pdf.get_y(), 90, pdf.get_y())
            
        # Colonne Droite (Direction Générale / Directeur des RH)
        if "right" in signatures:
            pdf.set_xy(110, start_y)
            title, details = signatures["right"]
            pdf.set_font('Helvetica', 'B', 10)
            pdf.set_text_color(31, 41, 55)
            pdf.cell(85, 5, clean_text_for_pdf(title), ln=True, align='C')
            
            # Parsing des détails (Directeur et Cachet)
            pdf.set_text_color(75, 85, 99)
            parts = details.split('[')
            for part in parts:
                if not part:
                    continue
                if part.endswith(']'):
                    pdf.set_font('Helvetica', 'I', 8.5)
                    pdf.cell(85, 4.5, clean_text_for_pdf('[' + part), ln=True, align='C')
                else:
                    pdf.set_font('Helvetica', '', 9.5)
                    pdf.cell(85, 4.5, clean_text_for_pdf(part.strip()), ln=True, align='C')
                    
            pdf.ln(12)
            pdf.set_draw_color(156, 163, 175)
            pdf.set_line_width(0.3)
            pdf.line(120, pdf.get_y(), 185, pdf.get_y())

    return bytes(pdf.output())
