from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io
from flask import Response

def export_user_data(user):
    output = io.StringIO()
    output.write(f'User Data Export\n')
    output.write(f'=============\n\n')
    output.write(f'Name: {user.full_name}\n')
    output.write(f'Email: {user.email}\n')
    output.write(f'Phone: {user.phone}\n')
    output.write(f'Organisation: {user.organisation}\n')
    output.write(f'Location: {user.location}\n')
    output.write(f'Age: {user.age}\n')
    output.write(f'Account Created: {user.created_at}\n')
    output.write(f'Email Verified: {user.email_verified}\n')
    return output.getvalue()

def export_to_pdf(incident, submissions, evidence, user):
    from flask import Response
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=0.75*inch, leftMargin=0.75*inch,
                            topMargin=0.75*inch, bottomMargin=0.75*inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Title'],
                                  fontSize=18, textColor=HexColor('#1a3a5c'))
    heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'],
                                    fontSize=14, textColor=HexColor('#1a3a5c'))
    normal_style = ParagraphStyle('CustomNormal', parent=styles['Normal'],
                                   fontSize=10, leading=14)

    elements = []
    elements.append(Paragraph('CyberShield Ghana - Report Copy', title_style))
    elements.append(Paragraph('Application-generated copy — not an official CSA case document.', normal_style))
    elements.append(Spacer(1, 0.3*inch))

    elements.append(Paragraph('Incident Information', heading_style))
    data = [
        ['Internal Report ID', incident.incident_id],
        ['Category', incident.category],
        ['Incident Date', str(incident.incident_date) if incident.incident_date else 'N/A'],
        ['Incident Time', incident.incident_time or 'N/A'],
        ['Platform', incident.platform or 'N/A'],
        ['Status', incident.status],
        ['Submission Channel', submissions[0].channel if submissions else 'N/A'],
        ['Submission Status', submissions[0].status if submissions else 'N/A'],
    ]
    t = Table(data, colWidths=[2.5*inch, 3.5*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), HexColor('#e8f0f8')),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 0.3*inch))

    elements.append(Paragraph('Reporter Information', heading_style))
    rep_data = [
        ['Name', user.full_name],
        ['Email', user.email],
        ['Phone', user.phone or 'N/A'],
        ['Organisation', user.organisation or 'N/A'],
        ['Location', user.location or 'N/A'],
    ]
    rt = Table(rep_data, colWidths=[2.5*inch, 3.5*inch])
    rt.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), HexColor('#e8f0f8')),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(rt)
    elements.append(Spacer(1, 0.3*inch))

    elements.append(Paragraph('Incident Description', heading_style))
    elements.append(Paragraph(incident.description or 'No description provided.', normal_style))

    if evidence:
        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph('Evidence Files', heading_style))
        ev_data = [['File Name', 'Type', 'Size']]
        for ev in evidence:
            size_kb = f"{ev.file_size / 1024:.1f} KB" if ev.file_size else 'N/A'
            ev_data.append([ev.file_name, ev.file_type or 'N/A', size_kb])
        et = Table(ev_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
        et.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1a3a5c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))
        elements.append(et)

    doc.build(elements)
    buffer.seek(0)

    return Response(
        buffer.getvalue(),
        mimetype='application/pdf',
        headers={
            'Content-Disposition': f'attachment; filename=CyberShield_Report_{incident.incident_id}.pdf'
        }
    )