"""
Convert Press Release Markdown to PDF
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
import re

def markdown_to_pdf(md_file, pdf_file):
    """Convert markdown press release to professional PDF"""
    
    # Read markdown
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create PDF
    doc = SimpleDocTemplate(pdf_file, pagesize=letter,
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor='#000000',
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor='#000000',
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=12,
        textColor='#333333',
        spaceAfter=10,
        spaceBefore=10,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        textColor='#000000',
        spaceAfter=12,
        alignment=TA_JUSTIFY,
        fontName='Helvetica'
    )
    
    bold_style = ParagraphStyle(
        'CustomBold',
        parent=styles['BodyText'],
        fontSize=10,
        textColor='#000000',
        spaceAfter=12,
        fontName='Helvetica-Bold'
    )
    
    # Build story
    story = []
    
    # Parse markdown
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        
        if not line:
            story.append(Spacer(1, 0.1*inch))
            continue
        
        # Headers
        if line.startswith('# '):
            text = line[2:].strip()
            story.append(Paragraph(text, title_style))
        elif line.startswith('## '):
            text = line[3:].strip()
            story.append(Paragraph(text, heading_style))
        elif line.startswith('### '):
            text = line[4:].strip()
            story.append(Paragraph(text, subheading_style))
        
        # Bold text
        elif line.startswith('**') and line.endswith('**'):
            text = line[2:-2]
            story.append(Paragraph(text, bold_style))
        
        # Lists
        elif line.startswith('- '):
            text = '• ' + line[2:]
            story.append(Paragraph(text, body_style))
        
        # Horizontal rule
        elif line.startswith('---'):
            story.append(Spacer(1, 0.2*inch))
        
        # Regular text
        else:
            # Clean up markdown formatting - simple approach
            text = line
            # Remove markdown bold markers
            text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
            # Remove markdown italic markers
            text = re.sub(r'\*([^*]+)\*', r'<i>\1</i>', text)
            # Escape special characters
            text = text.replace('–', '-')
            story.append(Paragraph(text, body_style))
    
    # Build PDF
    doc.build(story)
    print(f"PDF created: {pdf_file}")

if __name__ == "__main__":
    try:
        markdown_to_pdf('PRESS-RELEASE.md', 'PRESS-RELEASE.pdf')
        print("Press release converted to PDF successfully!")
    except ImportError:
        print("Installing required package: reportlab")
        import subprocess
        subprocess.run(['pip', 'install', 'reportlab'], check=True)
        print("Please run the script again.")
    except Exception as e:
        print(f"Error: {e}")
