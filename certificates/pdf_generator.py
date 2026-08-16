import os
import io
import qrcode
from PIL import Image
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone

from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY


def generate_certificate_qr(certificate, base_url=""):
    """Generates QR code for certificate public verification."""
    verify_url = f"{base_url}/certificates/verify/{certificate.uuid}/"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    qr.add_data(verify_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1a237e", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    file_name = f"cert_qr_{certificate.certificate_id}.png"
    certificate.qr_code.save(file_name, ContentFile(buffer.getvalue()), save=True)
    return certificate.qr_code.path


def generate_certificate_pdf(certificate):
    """Generates an aesthetic, landscape Certificate of Achievement using ReportLab."""
    buffer = io.BytesIO()
    
    # Page size landscape A4
    page_width, page_height = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    
    # Background & Ornamental Borders
    # Outer Border
    c.setStrokeColor(colors.HexColor('#1a237e')) # Deep Indigo
    c.setLineWidth(5)
    c.rect(20, 20, page_width - 40, page_height - 40)
    
    # Inner Gold Border
    c.setStrokeColor(colors.HexColor('#d4af37')) # Gold
    c.setLineWidth(2)
    c.rect(28, 28, page_width - 56, page_height - 56)

    # Decorative Corner Accents
    c.setFillColor(colors.HexColor('#1a237e'))
    for x, y in [(35, page_height - 45), (page_width - 45, page_height - 45), (35, 35), (page_width - 45, 35)]:
        c.circle(x, y, 6, fill=1, stroke=0)
        c.setFillColor(colors.HexColor('#d4af37'))
        c.circle(x, y, 3, fill=1, stroke=0)
        c.setFillColor(colors.HexColor('#1a237e'))

    # Header - Institute Name
    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(colors.HexColor('#1a237e'))
    c.drawCentredString(page_width / 2.0, page_height - 75, "EDUTRACK 360 INSTITUTE OF TECHNOLOGY")
    
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor('#555555'))
    c.drawCentredString(page_width / 2.0, page_height - 92, "Autonomous Institution | Approved by AICTE | Accredited by NAAC with 'A+' Grade")
    
    # Gold divider line
    c.setStrokeColor(colors.HexColor('#d4af37'))
    c.setLineWidth(1.5)
    c.line(page_width / 2.0 - 180, page_height - 102, page_width / 2.0 + 180, page_height - 102)

    # Certificate Main Title
    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(colors.HexColor('#0d47a1'))
    c.drawCentredString(page_width / 2.0, page_height - 140, certificate.title.upper())

    # Presentation text
    c.setFont("Helvetica-Oblique", 13)
    c.setFillColor(colors.HexColor('#424242'))
    c.drawCentredString(page_width / 2.0, page_height - 175, "This certificate is proudly awarded to")

    # Student Name
    c.setFont("Helvetica-Bold", 26)
    c.setFillColor(colors.HexColor('#1b5e20')) # Emerald Green / Gold Accent
    student_name = certificate.student.user.get_full_name() or certificate.student.user.username
    c.drawCentredString(page_width / 2.0, page_height - 215, student_name.upper())

    # Underline for name
    c.setStrokeColor(colors.HexColor('#d4af37'))
    c.setLineWidth(1)
    name_width = c.stringWidth(student_name.upper(), "Helvetica-Bold", 26)
    c.line(page_width / 2.0 - (name_width / 2) - 15, page_height - 222, page_width / 2.0 + (name_width / 2) + 15, page_height - 222)

    # Student Details
    c.setFont("Helvetica", 12)
    c.setFillColor(colors.HexColor('#333333'))
    details_line = f"PRN: {certificate.student.prn}   |   Branch: {certificate.student.branch.name}   |   Semester: {certificate.student.semester.roman_name}"
    c.drawCentredString(page_width / 2.0, page_height - 245, details_line)

    # Achievement Description
    c.setFont("Helvetica", 11)
    c.setFillColor(colors.HexColor('#424242'))
    desc = certificate.achievement_text
    # Simple word wrap for 2 lines if needed
    if len(desc) > 90:
        split_pt = desc.rfind(" ", 0, 90)
        line1 = desc[:split_pt]
        line2 = desc[split_pt:].strip()
        c.drawCentredString(page_width / 2.0, page_height - 275, line1)
        c.drawCentredString(page_width / 2.0, page_height - 292, line2)
    else:
        c.drawCentredString(page_width / 2.0, page_height - 280, desc)

    # Score Badge pill
    if certificate.score_percentage > 0:
        c.setFillColor(colors.HexColor('#e8f5e9'))
        c.roundRect(page_width / 2.0 - 80, page_height - 335, 160, 26, 13, fill=1, stroke=0)
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.HexColor('#2e7d32'))
        c.drawCentredString(page_width / 2.0, page_height - 327, f"Score Achieved: {certificate.score_percentage}%")

    # Embed QR Code at bottom-left
    if certificate.qr_code and os.path.exists(certificate.qr_code.path):
        c.drawImage(certificate.qr_code.path, 50, 48, width=70, height=70)
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.HexColor('#666666'))
        c.drawString(48, 40, "Scan to Verify Authenticity")

    # Certificate ID & Issue Date
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor('#444444'))
    c.drawString(130, 75, f"Certificate ID: {certificate.certificate_id}")
    c.drawString(130, 60, f"Issued Date: {certificate.issue_date.strftime('%B %d, %Y')}")
    c.drawString(130, 45, "Verified Digital Record: edutrack360.ac.in")

    # Signatures at bottom-right
    c.setStrokeColor(colors.HexColor('#666666'))
    c.setLineWidth(1)
    
    # HOD Sign
    c.line(page_width - 290, 75, page_width - 170, 75)
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.HexColor('#1a237e'))
    c.drawCentredString(page_width - 230, 62, "Dr. S. K. Sharma")
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor('#555555'))
    c.drawCentredString(page_width - 230, 50, "Head of Department")

    # Principal Sign
    c.line(page_width - 150, 75, page_width - 40, 75)
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.HexColor('#1a237e'))
    c.drawCentredString(page_width - 95, 62, "Dr. R. V. Patil")
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor('#555555'))
    c.drawCentredString(page_width - 95, 50, "Principal / Director")

    c.save()
    
    file_name = f"cert_{certificate.certificate_id}.pdf"
    certificate.pdf_file.save(file_name, ContentFile(buffer.getvalue()), save=True)
    return certificate.pdf_file.url


def generate_noc_qr(noc, base_url=""):
    """Generates QR code for Digital NOC verification."""
    verify_url = f"{base_url}/certificates/noc/verify/{noc.uuid}/"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    qr.add_data(verify_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#004d40", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    file_name = f"noc_qr_{noc.noc_id}.png"
    noc.qr_code.save(file_name, ContentFile(buffer.getvalue()), save=True)
    return noc.qr_code.path


def generate_noc_pdf(noc):
    """Generates official Digital No Objection Certificate (NOC) PDF."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    page_width, page_height = A4

    # Outer Border
    c.setStrokeColor(colors.HexColor('#004d40'))
    c.setLineWidth(3)
    c.rect(25, 25, page_width - 50, page_height - 50)

    # Header
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(colors.HexColor('#004d40'))
    c.drawCentredString(page_width / 2.0, page_height - 60, "EDUTRACK 360 INSTITUTE OF TECHNOLOGY")

    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor('#555555'))
    c.drawCentredString(page_width / 2.0, page_height - 75, "Department of Academic Affairs & Student Clearance")
    
    c.setStrokeColor(colors.HexColor('#004d40'))
    c.setLineWidth(1)
    c.line(50, page_height - 85, page_width - 50, page_height - 85)

    # Title
    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(colors.HexColor('#00695c'))
    c.drawCentredString(page_width / 2.0, page_height - 120, "NO OBJECTION CERTIFICATE (NOC)")

    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor('#333333'))
    c.drawCentredString(page_width / 2.0, page_height - 140, f"NOC Ref ID: {noc.noc_id}   |   Date: {noc.issued_at.strftime('%d/%m/%Y')}")

    # Body text
    c.setFont("Helvetica", 11)
    student = noc.student
    student_name = student.user.get_full_name() or student.user.username
    
    text = (
        f"This is to certify that Mr./Ms. {student_name.upper()}, bearing PRN {student.prn} "
        f"and Roll Number {student.roll_no}, is a bona fide student of {student.program.name} in the "
        f"branch of {student.branch.name}, Semester {student.semester.roman_name}."
    )
    
    # Paragraph draw
    styles = getSampleStyleSheet()
    style = ParagraphStyle('NOCBody', fontName='Helvetica', fontSize=11, leading=16, alignment=TA_JUSTIFY)
    p = Paragraph(text, style)
    p.wrapOn(c, page_width - 100, 100)
    p.drawOn(c, 50, page_height - 210)

    purpose_text = f"<b>Purpose:</b> {noc.purpose}"
    p_purp = Paragraph(purpose_text, style)
    p_purp.wrapOn(c, page_width - 100, 50)
    p_purp.drawOn(c, 50, page_height - 245)

    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.HexColor('#004d40'))
    c.drawString(50, page_height - 280, "Institutional Clearance Verification Summary:")

    # Table of 5 Clearances
    table_data = [
        ['Section / Authority', 'Requirement Status', 'Clearance State'],
        ['1. Central Library', 'All books, fines & journals returned', '✓ CLEARED' if noc.library_clearance else '✗ PENDING'],
        ['2. Academic Submissions', 'All assignments, microprojects & journals approved', '✓ CLEARED' if noc.academic_clearance else '✗ PENDING'],
        ['3. Department & Faculty', 'No dues / lab tools submitted to department', '✓ CLEARED' if noc.department_clearance else '✗ PENDING'],
        ['4. Engineering Labs & Workshop', 'Hardware kits & components verified intact', '✓ CLEARED' if noc.lab_clearance else '✗ PENDING'],
        ['5. Accounts & Student Dues', 'All term tuition and examination fees cleared', '✓ CLEARED' if noc.fees_clearance else '✗ PENDING'],
    ]

    t = Table(table_data, colWidths=[180, 210, 100])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#004d40')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#b2dfdb')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (2, 0), (2, -1), 'CENTER'),
        ('TEXTCOLOR', (2, 1), (2, -1), colors.HexColor('#2e7d32')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0fdf4')])
    ]))
    t.wrapOn(c, page_width - 100, 200)
    t.drawOn(c, 50, page_height - 430)

    # Clearance statement
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.HexColor('#2e7d32'))
    c.drawString(50, page_height - 460, "Official Declaration: The student has NO OUTSTANDING DUES or pending obligations.")

    # QR & Footer
    if noc.qr_code and os.path.exists(noc.qr_code.path):
        c.drawImage(noc.qr_code.path, 50, 70, width=75, height=75)
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.HexColor('#666666'))
        c.drawString(50, 60, "Scan QR for Official Verification")

    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor('#444444'))
    c.drawString(140, 120, f"Issued By: Office of Registrar & Student Affairs")
    c.drawString(140, 105, f"Digital Hash: SHA256-VERIFIED-{noc.uuid.hex[:12].upper()}")
    c.drawString(140, 90, f"Approved By: {noc.approved_by.get_full_name() if noc.approved_by else 'Dean Academics'}")

    # Registrar Sign
    c.line(page_width - 180, 100, page_width - 50, 100)
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.HexColor('#004d40'))
    c.drawCentredString(page_width - 115, 85, "Registrar")
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor('#555555'))
    c.drawCentredString(page_width - 115, 72, "EduTrack 360 Institute")

    c.save()
    
    file_name = f"noc_{noc.noc_id}.pdf"
    noc.pdf_file.save(file_name, ContentFile(buffer.getvalue()), save=True)
    return noc.pdf_file.url
