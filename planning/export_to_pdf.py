#!/usr/bin/env python3
"""
Script to convert the tile_list.md file to a nicely formatted PDF.
"""

import os
import sys
from datetime import datetime

# Try to import required packages, install if missing
try:
    import markdown
    import weasyprint
except ImportError:
    # Will be handled in install_dependencies function
    pass

def create_custom_css():
    """Create custom CSS for better PDF formatting."""
    return """
    @page {
        size: A4;
        margin: 2cm;
        @bottom-center {
            content: "Page " counter(page) " of " counter(pages);
            font-size: 10px;
            color: #666;
        }
    }
    
    body {
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 11px;
        line-height: 1.4;
        color: #333;
        margin: 0;
        padding: 0;
    }
    
    h1 {
        font-size: 24px;
        color: #2c3e50;
        text-align: center;
        margin-bottom: 10px;
        border-bottom: 3px solid #3498db;
        padding-bottom: 10px;
    }
    
    h2 {
        font-size: 18px;
        color: #34495e;
        margin-top: 30px;
        margin-bottom: 15px;
        border-bottom: 2px solid #ecf0f1;
        padding-bottom: 5px;
        page-break-before: always;
    }
    
    h2:first-of-type {
        page-break-before: auto;
    }
    
    h3 {
        font-size: 14px;
        color: #2980b9;
        margin-top: 20px;
        margin-bottom: 10px;
        background-color: #f8f9fa;
        padding: 8px 12px;
        border-left: 4px solid #3498db;
    }
    
    table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 20px;
        font-size: 10px;
        page-break-inside: avoid;
    }
    
    th {
        background-color: #3498db;
        color: white;
        padding: 8px 6px;
        text-align: left;
        font-weight: bold;
        border: 1px solid #2980b9;
    }
    
    td {
        padding: 6px;
        border: 1px solid #bdc3c7;
        vertical-align: top;
    }
    
    tr:nth-child(even) {
        background-color: #f8f9fa;
    }
    
    tr:hover {
        background-color: #e8f4f8;
    }
    
    /* Column widths */
    th:nth-child(1), td:nth-child(1) { width: 8%; }   /* ID */
    th:nth-child(2), td:nth-child(2) { width: 25%; }  /* Tile Name */
    th:nth-child(3), td:nth-child(3) { width: 42%; }  /* Description */
    th:nth-child(4), td:nth-child(4) { width: 12%; }  /* Required Count */
    th:nth-child(5), td:nth-child(5) { width: 13%; }  /* Wiki Link */
    
    a {
        color: #3498db;
        text-decoration: none;
    }
    
    a:hover {
        text-decoration: underline;
    }
    
    .table-of-contents {
        background-color: #ecf0f1;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    
    .table-of-contents ul {
        margin: 0;
        padding-left: 20px;
    }
    
    .table-of-contents li {
        margin-bottom: 5px;
    }
    
    hr {
        border: none;
        border-top: 2px solid #ecf0f1;
        margin: 25px 0;
    }
    
    em {
        color: #7f8c8d;
        font-style: italic;
        text-align: center;
        display: block;
        margin-bottom: 20px;
    }
    
    /* Notes section */
    .notes {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 15px;
        margin-top: 20px;
    }
    
    .notes h2 {
        color: #856404;
        margin-top: 0;
        border-bottom: 1px solid #ffeaa7;
    }
    
    .notes ul {
        margin-bottom: 0;
    }
    
    /* Ensure tables don't break across pages poorly */
    .world-section {
        page-break-inside: avoid;
    }
    
    /* Better handling of long descriptions */
    td:nth-child(3) {
        word-wrap: break-word;
        max-width: 200px;
    }
    """

def markdown_to_html(markdown_file_path):
    """Convert markdown file to HTML string."""
    try:
        with open(markdown_file_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        # Configure markdown with extensions for better table support
        md = markdown.Markdown(extensions=[
            'markdown.extensions.tables',
            'markdown.extensions.toc',
            'markdown.extensions.attr_list'
        ])
        
        html_content = md.convert(markdown_content)
        
        # Wrap in proper HTML structure
        html_template = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Summer Bingo Tile List</title>
            <style>
                {create_custom_css()}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        return html_template
        
    except FileNotFoundError:
        print(f"❌ Error: Could not find markdown file at {markdown_file_path}")
        return None
    except Exception as e:
        print(f"❌ Error reading markdown file: {e}")
        return None

def html_to_pdf(html_content, output_path):
    """Convert HTML string to PDF file."""
    try:
        # Create PDF from HTML
        html_doc = weasyprint.HTML(string=html_content)
        pdf_doc = html_doc.render()
        pdf_doc.write_pdf(output_path)
        return True
        
    except Exception as e:
        print(f"❌ Error converting to PDF: {e}")
        return False

def install_dependencies():
    """Check and install required dependencies."""
    import subprocess
    
    required_packages = [
        'markdown',
        'weasyprint'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"📦 Installing missing packages: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install'
            ] + missing_packages)
            print("✅ Dependencies installed successfully!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False
    
    return True

def main():
    """Main function to convert markdown to PDF."""
    print("🔄 Starting PDF export process...")
    
    # Check and install dependencies
    if not install_dependencies():
        print("❌ Failed to install required dependencies.")
        print("💡 Try running: pip install markdown weasyprint")
        return 1
    
    # Re-import after potential installation
    global markdown, weasyprint
    try:
        import markdown
        import weasyprint
    except ImportError as e:
        print(f"❌ Import error after installation: {e}")
        return 1
    
    # Define file paths
    script_dir = os.path.dirname(__file__)
    markdown_file = os.path.join(script_dir, 'tile_list.md')
    pdf_file = os.path.join(script_dir, 'tile_list.pdf')
    
    # Check if markdown file exists
    if not os.path.exists(markdown_file):
        print(f"❌ Markdown file not found: {markdown_file}")
        print("💡 Make sure to run the print_tiles.py script first to generate the markdown file.")
        return 1
    
    # Convert markdown to HTML
    print("📝 Converting markdown to HTML...")
    html_content = markdown_to_html(markdown_file)
    if not html_content:
        return 1
    
    # Convert HTML to PDF
    print("🖨️  Converting HTML to PDF...")
    if html_to_pdf(html_content, pdf_file):
        print(f"✅ PDF generated successfully: {pdf_file}")
        
        # Get file size
        file_size = os.path.getsize(pdf_file)
        file_size_mb = file_size / (1024 * 1024)
        
        print(f"📄 File size: {file_size_mb:.2f} MB")
        print(f"📂 Location: {os.path.abspath(pdf_file)}")
        
        return 0
    else:
        return 1

if __name__ == "__main__":
    exit(main())
