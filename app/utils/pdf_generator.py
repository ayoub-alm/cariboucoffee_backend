from io import BytesIO
from fpdf import FPDF
from app.models.models import Audit
from datetime import datetime

import os

class AuditPDF(FPDF):
    def header(self):
        # Arial bold 18, dark brown color for Caribou Coffee theme
        self.set_font('Arial', 'B', 18)
        self.set_text_color(75, 56, 42)
        self.cell(0, 15, 'Rapport d\'Audit - Caribou Coffee', border=0, ln=1, align='C')
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'C')

def generate_audit_pdf(audit: Audit) -> bytes:
    pdf = AuditPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # -------- SCORE & HEADER --------
    score_val = audit.score if audit.score else 0.0
    if score_val >= 85:
        score_color = (40, 167, 69)  # Green
    elif score_val >= 70:
        score_color = (255, 193, 7)  # Yellow/Orange
    else:
        score_color = (220, 53, 69)  # Red

    # Audit info
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(100, 8, f"Cafe: {audit.coffee.name}", ln=0)
    
    # Score aligned to right
    pdf.set_font('Arial', 'B', 16)
    pdf.set_text_color(*score_color)
    pdf.cell(0, 8, f"Score Total: {score_val}%", ln=1, align='R')
    
    pdf.set_font('Arial', '', 11)
    pdf.set_text_color(80, 80, 80)
    
    date_str = audit.created_at.strftime('%d/%m/%Y %H:%M') if audit.created_at else ''
    auditor_name = audit.auditor.full_name or audit.auditor.email
    
    pdf.cell(100, 6, f"Auditeur: {auditor_name}", ln=0)
    pdf.cell(0, 6, f"Status: {audit.status}", ln=1, align='R')
    
    pdf.cell(100, 6, f"Date: {date_str}", ln=0)
    if audit.shift:
        pdf.cell(0, 6, f"Shift: {audit.shift}", ln=1, align='R')
    else:
        pdf.ln(6)
        
    if audit.staff_present:
        pdf.cell(0, 6, f"Personnel present: {audit.staff_present}", ln=1)
        
    pdf.ln(4)
    # Divider
    pdf.set_draw_color(220, 220, 220)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    # General Photo
    if audit.photo_url:
        img_path = audit.photo_url
        if img_path.startswith('/static/'):
            img_path = "app" + img_path
        if os.path.exists(img_path):
            pdf.ln(2)
            pdf.set_font('Arial', 'B', 12)
            pdf.set_text_color(50, 50, 50)
            pdf.cell(0, 8, "Photo Generale de l'Audit:", ln=1)
            try:
                # max width 90 to not take full page horizontally
                pdf.image(img_path, w=90)
                pdf.ln(5)
            except Exception as e:
                print(f"Error loading image {img_path}: {e}")

    # -------- ANSWERS BY CATEGORY --------
    categories = {}
    for answer in audit.answers:
        if not answer.question or not answer.question.category:
            continue
        cat_name = answer.question.category.name
        if cat_name not in categories:
            categories[cat_name] = []
        categories[cat_name].append(answer)
        
    for cat_name, answers in categories.items():
        pdf.ln(3)
        # Category Header
        pdf.set_font('Arial', 'B', 12)
        pdf.set_fill_color(240, 240, 240)
        pdf.set_text_color(30, 30, 30)
        
        # Calculate Category Score
        cat_obtained = sum((ans.value or 0) for ans in answers if ans.choice and ans.choice.lower() != 'n/a')
        cat_total = sum((ans.question.weight or 1) for ans in answers if ans.choice and ans.choice.lower() != 'n/a')
        cat_score_str = f" - ({cat_obtained}/{cat_total} pts)" if cat_total > 0 else " - (N/A)"
        
        safe_cat_name = cat_name.encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(0, 10, f" {safe_cat_name}{cat_score_str}", ln=1, fill=True, border=1)
        
        for ans in answers:
            pdf.set_font('Arial', '', 10)
            pdf.set_text_color(50, 50, 50)
            
            choice_str = ans.choice.capitalize() if ans.choice else "N/A"
            question_text = ans.question.text[:95] + "..." if len(ans.question.text) > 95 else ans.question.text
            question_text = question_text.encode('latin-1', 'replace').decode('latin-1')
            
            # Points string
            q_weight = ans.question.weight or 1
            ans_val = ans.value or 0
            pts_str = f"[{ans_val}/{q_weight}]" if choice_str.lower() != 'n/a' else "[N/A]"
            
            # Draw row
            pdf.cell(145, 8, f" {question_text}", border='LTB', align='L')
            
            # Color code choice
            if choice_str.lower() == 'oui':
                pdf.set_text_color(40, 167, 69) # Green
            elif choice_str.lower() == 'non':
                pdf.set_text_color(220, 53, 69) # Red
            else:
                pdf.set_text_color(150, 150, 150) # Gray
                
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(20, 8, choice_str, border='TB', align='C')
            
            # Points cell
            pdf.set_font('Arial', '', 9)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(25, 8, pts_str, border='RTB', align='C', ln=1)
            
            # Check for Comment and Photo
            if ans.comment or ans.photo_url:
                pdf.set_font('Arial', 'I', 9)
                pdf.set_text_color(80, 80, 80)
                
                if ans.comment:
                    safe_comment = ans.comment.encode('latin-1', 'replace').decode('latin-1')
                    pdf.cell(10, 6, "") # indent
                    pdf.multi_cell(0, 6, f"Remarque: {safe_comment}", border=0)
                
                if ans.photo_url:
                    img_path = ans.photo_url
                    if img_path.startswith('/static/'):
                        img_path = "app" + img_path
                    if os.path.exists(img_path):
                        # Calculate available space, create page break if needed
                        if pdf.h - pdf.get_y() < 70:
                            pdf.add_page()
                        pdf.ln(2)
                        try:
                            # Print image with left margin alignment
                            pdf.image(img_path, x=20, w=60)
                            pdf.ln(2)
                        except Exception as e:
                            print(f"Error loading image {img_path}: {e}")

    # -------- CONCLUSION & ACTIONS --------
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(50, 50, 50)
    pdf.set_fill_color(220, 230, 240)
    pdf.cell(0, 10, " Conclusion & Plan d'Action", ln=1, fill=True)
    pdf.ln(2)
    
    def print_section(title, text):
        if text:
            pdf.set_font('Arial', 'B', 11)
            pdf.set_text_color(30, 30, 30)
            pdf.cell(0, 8, title, ln=1)
            pdf.set_font('Arial', '', 10)
            pdf.set_text_color(70, 70, 70)
            safe_text = text.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 6, safe_text)
            pdf.ln(4)

    print_section("Actions Correctives:", audit.actions_correctives)
    print_section("Besoins en formation:", audit.training_needs)
    print_section("Achats recommandes:", audit.purchases)

    return pdf.output(dest='S')
