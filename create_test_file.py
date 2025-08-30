#!/usr/bin/env python3
"""
Create a simple test PDF file with financial data for API testing
"""

import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def create_simple_test_pdf():
    """Create a simple test PDF with financial data"""
    
    filename = "data/input/samples/test_financial_statement.pdf"
    
    # Create the PDF document
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    title = Paragraph("Sample Financial Statement", title_style)
    story.append(title)
    
    # Income Statement
    income_data = [
        ['Income Statement', '', ''],
        ['Revenue', '$1,250,000', ''],
        ['Cost of Goods Sold', '$750,000', ''],
        ['Gross Profit', '$500,000', ''],
        ['Operating Expenses', '', ''],
        ['  - Salaries', '$200,000', ''],
        ['  - Rent', '$50,000', ''],
        ['  - Utilities', '$25,000', ''],
        ['  - Marketing', '$75,000', ''],
        ['Total Operating Expenses', '$350,000', ''],
        ['Operating Income', '$150,000', ''],
        ['Interest Expense', '$10,000', ''],
        ['Net Income', '$140,000', '']
    ]
    
    income_table = Table(income_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
    income_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),  # Right align numbers
    ]))
    
    story.append(income_table)
    story.append(Paragraph("<br/><br/>", styles['Normal']))
    
    # Balance Sheet
    balance_data = [
        ['Balance Sheet', '', ''],
        ['Assets', '', ''],
        ['  Cash', '$100,000', ''],
        ['  Accounts Receivable', '$150,000', ''],
        ['  Inventory', '$200,000', ''],
        ['  Fixed Assets', '$500,000', ''],
        ['Total Assets', '$950,000', ''],
        ['', '', ''],
        ['Liabilities', '', ''],
        ['  Accounts Payable', '$100,000', ''],
        ['  Short-term Debt', '$200,000', ''],
        ['  Long-term Debt', '$300,000', ''],
        ['Total Liabilities', '$600,000', ''],
        ['', '', ''],
        ['Equity', '', ''],
        ['  Common Stock', '$200,000', ''],
        ['  Retained Earnings', '$150,000', ''],
        ['Total Equity', '$350,000', ''],
        ['Total Liabilities & Equity', '$950,000', '']
    ]
    
    balance_table = Table(balance_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
    balance_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),  # Right align numbers
    ]))
    
    story.append(balance_table)
    
    # Build the PDF
    doc.build(story)
    
    print(f"✅ Test PDF created: {filename}")
    print(f"📏 File size: {os.path.getsize(filename) / 1024:.1f} KB")
    return filename

def create_simple_test_image():
    """Create a simple test image with financial data"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a new image with white background
        width, height = 800, 600
        image = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(image)
        
        # Try to use a default font, fallback to basic if not available
        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except:
            font = ImageFont.load_default()
        
        # Draw financial data
        text_lines = [
            "Sample Financial Statement",
            "",
            "Revenue: $1,250,000",
            "Cost of Goods Sold: $750,000",
            "Gross Profit: $500,000",
            "",
            "Operating Expenses:",
            "  - Salaries: $200,000",
            "  - Rent: $50,000",
            "  - Utilities: $25,000",
            "  - Marketing: $75,000",
            "",
            "Net Income: $140,000"
        ]
        
        y_position = 50
        for line in text_lines:
            draw.text((50, y_position), line, fill='black', font=font)
            y_position += 30
        
        filename = "data/input/samples/test_financial_statement.png"
        image.save(filename)
        
        print(f"✅ Test image created: {filename}")
        print(f"📏 File size: {os.path.getsize(filename) / 1024:.1f} KB")
        return filename
        
    except ImportError:
        print("❌ PIL not available. Install with: pip install Pillow")
        return None

def main():
    """Create test files for API testing"""
    print("🧪 Creating Test Files for API Testing")
    print("=" * 50)
    
    # Create PDF test file
    pdf_file = create_simple_test_pdf()
    
    # Create image test file
    image_file = create_simple_test_image()
    
    print("\n📁 Test files created:")
    if pdf_file:
        print(f"  📄 {pdf_file}")
    if image_file:
        print(f"  🖼️  {image_file}")
    
    print("\n🚀 Now you can test the API:")
    print("1. Run: python test_file_upload.py")
    print("2. Or visit: http://localhost:8000/docs")
    print("3. Or use curl commands from API_TESTING_GUIDE.md")

if __name__ == "__main__":
    main() 