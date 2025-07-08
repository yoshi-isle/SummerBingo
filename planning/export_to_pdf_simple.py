#!/usr/bin/env python3
"""
Alternative script to convert the tile_list.md file to PDF using reportlab.
This is more reliable on macOS and doesn't require system libraries.
"""

import os
import sys
import re
from datetime import datetime

def install_dependencies():
    """Install required packages."""
    import subprocess
    
    required_packages = ['reportlab', 'markdown']
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

def parse_markdown_to_data(markdown_file_path):
    """Parse the markdown file and extract structured data."""
    try:
        with open(markdown_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        worlds = []
        current_world = None
        current_section = None
        
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # World headers (## World X)
            if line.startswith('## World'):
                if current_world:
                    worlds.append(current_world)
                current_world = {
                    'name': line.replace('## ', ''),
                    'world_tiles': [],
                    'key_tiles': [],
                    'boss_tile': []
                }
                current_section = None
            
            # Section headers (### World Tiles, etc.)
            elif line.startswith('### '):
                section_name = line.replace('### ', '')
                if 'World Tiles' in section_name:
                    current_section = 'world_tiles'
                elif 'Key Tiles' in section_name:
                    current_section = 'key_tiles'
                elif 'Boss Tile' in section_name:
                    current_section = 'boss_tile'
            
            # Table rows (starts with |)
            elif line.startswith('| ') and '|' in line and current_section and current_world:
                # Skip header and separator rows
                if 'ID' in line or '----' in line:
                    continue
                
                # Parse table row
                columns = [col.strip() for col in line.split('|')[1:-1]]
                if len(columns) >= 4:
                    tile_data = {
                        'id': columns[0],
                        'name': columns[1],
                        'description': columns[2],
                        'count': columns[3],
                        'wiki': columns[4] if len(columns) > 4 else 'N/A'
                    }
                    current_world[current_section].append(tile_data)
        
        # Add the last world
        if current_world:
            worlds.append(current_world)
        
        return worlds
        
    except FileNotFoundError:
        print(f"❌ Error: Could not find markdown file at {markdown_file_path}")
        return None
    except Exception as e:
        print(f"❌ Error parsing markdown file: {e}")
        return None

def create_pdf(worlds_data, output_path):
    """Create PDF from the parsed world data."""
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    
    # Create document
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    # Container for the 'Flowable' objects
    story = []
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue
    )
    
    world_style = ParagraphStyle(
        'WorldTitle',
        parent=styles['Heading2'],
        fontSize=18,
        spaceAfter=20,
        spaceBefore=20,
        textColor=colors.darkgreen
    )
    
    section_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading3'],
        fontSize=14,
        spaceAfter=12,
        spaceBefore=16,
        textColor=colors.darkred
    )
    
    # Title
    story.append(Paragraph("Summer Bingo Tile List", title_style))
    story.append(Paragraph(f"<i>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</i>", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Process each world
    for world_idx, world in enumerate(worlds_data):
        if world_idx > 0:
            story.append(PageBreak())
        
        # World title
        story.append(Paragraph(world['name'], world_style))
        
        # Process each section
        sections = [
            ('world_tiles', 'World Tiles'),
            ('key_tiles', 'Key Tiles'),
            ('boss_tile', 'Boss Tile')
        ]
        
        for section_key, section_title in sections:
            if world[section_key]:
                story.append(Paragraph(section_title, section_style))
                
                # Create table data
                table_data = [['ID', 'Tile Name', 'Description', 'Required', 'Wiki']]
                
                for tile in world[section_key]:
                    # Clean up wiki link
                    wiki_text = 'Wiki' if 'oldschool.runescape.wiki' in tile['wiki'] else 'N/A'
                    
                    # Wrap long descriptions
                    description = tile['description']
                    if len(description) > 60:
                        description = description[:57] + "..."
                    
                    table_data.append([
                        tile['id'],
                        tile['name'],
                        description,
                        tile['count'],
                        wiki_text
                    ])
                
                # Create table
                table = Table(table_data, colWidths=[0.8*inch, 2.2*inch, 3.0*inch, 0.8*inch, 0.8*inch])
                table.setStyle(TableStyle([
                    # Header row styling
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    
                    # Data rows styling
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                ]))
                
                story.append(table)
                story.append(Spacer(1, 20))
    
    # Add notes
    story.append(PageBreak())
    story.append(Paragraph("Notes", world_style))
    notes = [
        "• <b>Required Count</b>: The number of items needed to complete the tile",
        "• <b>Wiki Link</b>: Link to the Old School RuneScape Wiki for more information",
        "• Some tiles may have multiple ways to complete them (indicated by 'OR' in the description)"
    ]
    
    for note in notes:
        story.append(Paragraph(note, styles['Normal']))
        story.append(Spacer(1, 6))
    
    # Build PDF
    doc.build(story)
    return True

def main():
    """Main function."""
    print("🔄 Starting PDF export process...")
    
    # Install dependencies
    if not install_dependencies():
        return 1
    
    # Define file paths
    script_dir = os.path.dirname(__file__)
    markdown_file = os.path.join(script_dir, 'tile_list.md')
    pdf_file = os.path.join(script_dir, 'tile_list_simple.pdf')
    
    # Check if markdown file exists
    if not os.path.exists(markdown_file):
        print(f"❌ Markdown file not found: {markdown_file}")
        print("💡 Make sure to run the print_tiles.py script first to generate the markdown file.")
        return 1
    
    # Parse markdown
    print("📝 Parsing markdown file...")
    worlds_data = parse_markdown_to_data(markdown_file)
    if not worlds_data:
        return 1
    
    print(f"📊 Found {len(worlds_data)} worlds with tile data")
    
    # Create PDF
    print("🖨️  Creating PDF...")
    try:
        if create_pdf(worlds_data, pdf_file):
            print(f"✅ PDF generated successfully: {pdf_file}")
            
            # Get file size
            file_size = os.path.getsize(pdf_file)
            file_size_mb = file_size / (1024 * 1024)
            
            print(f"📄 File size: {file_size_mb:.2f} MB")
            print(f"📂 Location: {os.path.abspath(pdf_file)}")
            
            return 0
        else:
            return 1
    except Exception as e:
        print(f"❌ Error creating PDF: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
