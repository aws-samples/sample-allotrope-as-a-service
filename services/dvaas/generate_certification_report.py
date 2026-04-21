# Copyright 2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Licensed under the Apache License, Version 2.0 (the "License").
# You may not use this file except in compliance with the License.
# A copy of the License is located at http://aws.amazon.com/apache2.0/
# This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND.
"""
Certification Report Generator
Generates professional PDF certification reports for ASM validation
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import io


def generate_certification_report(validation_result, asm_file_name=None):
    """
    Generate PDF certification report from validation results
    
    Args:
        validation_result: Dict with validation results from DVaaS
        asm_file_name: Optional filename being validated
        
    Returns:
        bytes: PDF document as bytes
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    styles = getSampleStyleSheet()
    story = []
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a5490'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1a5490'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6
    )
    
    # Header
    story.append(Paragraph("ASM VALIDATION CERTIFICATION REPORT", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Certificate status box
    is_valid = validation_result.get('valid', False)
    cert_info = validation_result.get('certification', {})
    
    if is_valid and cert_info:
        status_text = f"<b>STATUS: CERTIFIED ✓</b>"
        status_color = colors.green
    elif is_valid:
        status_text = f"<b>STATUS: VALID</b>"
        status_color = colors.blue
    else:
        status_text = f"<b>STATUS: FAILED ✗</b>"
        status_color = colors.red
    
    status_table = Table([[Paragraph(status_text, body_style)]], colWidths=[6*inch])
    status_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), status_color),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 16),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(status_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Certificate Information
    if cert_info:
        story.append(Paragraph("Certificate Information", heading_style))
        cert_data = [
            ['Certificate ID:', cert_info.get('certificate_id', 'N/A')],
            ['Issued At:', cert_info.get('issued_at', 'N/A')],
            ['Validator:', cert_info.get('validator', 'N/A')],
            ['Status:', cert_info.get('status', 'N/A')]
        ]
        cert_table = Table(cert_data, colWidths=[2*inch, 4*inch])
        cert_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(cert_table)
        story.append(Spacer(1, 0.2*inch))
    
    # File Information
    story.append(Paragraph("File Information", heading_style))
    file_data = [
        ['File Name:', asm_file_name or 'N/A'],
        ['Validation Level:', validation_result.get('validation_level', 'N/A')],
        ['Validation Time:', validation_result.get('timestamp', 'N/A')],
        ['Validator:', validation_result.get('validator', 'N/A')]
    ]
    file_table = Table(file_data, colWidths=[2*inch, 4*inch])
    file_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(file_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Validation Metrics
    metrics = validation_result.get('metrics', {})
    if metrics:
        story.append(Paragraph("Validation Metrics", heading_style))
        metrics_data = [[k.replace('_', ' ').title(), str(v)] for k, v in metrics.items()]
        metrics_table = Table(metrics_data, colWidths=[3*inch, 3*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(metrics_table)
        story.append(Spacer(1, 0.2*inch))
    
    # Errors
    errors = validation_result.get('errors', [])
    if errors:
        story.append(Paragraph("Errors", heading_style))
        for error in errors:
            story.append(Paragraph(f"• {error}", body_style))
        story.append(Spacer(1, 0.1*inch))
    
    # Warnings
    warnings = validation_result.get('warnings', [])
    if warnings:
        story.append(Paragraph("Warnings", heading_style))
        for warning in warnings[:10]:  # Limit to 10 warnings
            story.append(Paragraph(f"• {warning}", body_style))
        if len(warnings) > 10:
            story.append(Paragraph(f"... and {len(warnings) - 10} more warnings", body_style))
        story.append(Spacer(1, 0.1*inch))
    
    # Info
    info = validation_result.get('info', [])
    if info:
        story.append(Paragraph("Validation Details", heading_style))
        for info_item in info[:10]:  # Limit to 10 info items
            story.append(Paragraph(f"• {info_item}", body_style))
        if len(info) > 10:
            story.append(Paragraph(f"... and {len(info) - 10} more details", body_style))
        story.append(Spacer(1, 0.1*inch))
    
    # Summary
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("Summary", heading_style))
    
    if is_valid:
        if warnings:
            summary = f"This ASM file has passed validation with {len(warnings)} warning(s). The file conforms to Allotrope standards and is suitable for regulatory submission."
        else:
            summary = "This ASM file has passed validation with no issues. The file fully conforms to Allotrope standards and is suitable for regulatory submission."
    else:
        summary = f"This ASM file has failed validation with {len(errors)} error(s). Please review and correct the errors before resubmitting."
    
    story.append(Paragraph(summary, body_style))
    
    # Footer
    story.append(Spacer(1, 0.5*inch))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    story.append(Paragraph("This certification report was generated by ASM Transformation Service", footer_style))
    story.append(Paragraph(f"Report generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC", footer_style))
    story.append(Paragraph("For questions or support, contact: support@asm-transformation.com", footer_style))
    
    # Build PDF
    doc.build(story)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes


def save_certification_report(validation_result, output_path, asm_file_name=None):
    """
    Generate and save certification report to file
    
    Args:
        validation_result: Dict with validation results
        output_path: Path to save PDF file
        asm_file_name: Optional filename being validated
    """
    pdf_bytes = generate_certification_report(validation_result, asm_file_name)
    
    with open(output_path, 'wb') as f:
        f.write(pdf_bytes)
    
    return output_path
