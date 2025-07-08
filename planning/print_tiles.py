#!/usr/bin/env python3
"""
Script to convert tile data from tiles.py into a clean, formatted markdown file.
"""

import sys
import os
from datetime import datetime

# Add the parent directory to sys.path to import from game_service_api
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'game_service_api'))

from constants.tiles import world1_tiles, world2_tiles, world3_tiles, world4_tiles

def format_tile_section(tiles, section_name):
    """Format a section of tiles (world_tiles, key_tiles, or boss_tile) as markdown."""
    if not tiles:
        return ""
    
    markdown = f"### {section_name}\n\n"
    
    if section_name == "Boss Tile" and isinstance(tiles, dict):
        # Boss tile is a single tile, not a list
        tiles = [tiles]
    
    markdown += "| ID | Tile Name | Description | Required Count | Wiki Link |\n"
    markdown += "|----|-----------| ------------|---------------|----------|\n"
    
    for tile in tiles:
        tile_id = tile.get('id', 'N/A')
        tile_name = tile.get('tile_name', 'Unknown').replace('\n', ' ')
        description = tile.get('description', '').replace('\n', ' ')
        completion_counter = tile.get('completion_counter', 1)
        wiki_url = tile.get('wiki_url', '')
        
        # Create wiki link if URL exists
        wiki_link = f"[Wiki]({wiki_url})" if wiki_url else "N/A"
        
        # Escape pipe characters in cell content
        tile_name = tile_name.replace('|', '\\|')
        description = description.replace('|', '\\|')
        
        markdown += f"| {tile_id} | {tile_name} | {description} | {completion_counter} | {wiki_link} |\n"
    
    markdown += "\n"
    return markdown

def format_world_tiles(world_data, world_name):
    """Format all tiles for a specific world."""
    markdown = f"## {world_name}\n\n"
    
    # Format world tiles
    if 'world_tiles' in world_data:
        markdown += format_tile_section(world_data['world_tiles'], "World Tiles")
    
    # Format key tiles
    if 'key_tiles' in world_data:
        markdown += format_tile_section(world_data['key_tiles'], "Key Tiles")
    
    # Format boss tile
    if 'boss_tile' in world_data:
        markdown += format_tile_section(world_data['boss_tile'], "Boss Tile")
    
    return markdown

def generate_markdown():
    """Generate the complete markdown document."""
    markdown = "# Summer Bingo Tile List\n\n"
    markdown += f"*Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}*\n\n"
    markdown += "---\n\n"
    
    # Add table of contents
    markdown += "## Table of Contents\n\n"
    markdown += "- [World 1](#world-1)\n"
    markdown += "- [World 2](#world-2)\n"
    markdown += "- [World 3](#world-3)\n"
    markdown += "- [World 4](#world-4)\n\n"
    markdown += "---\n\n"
    
    # Format each world
    worlds = [
        (world1_tiles, "World 1"),
        (world2_tiles, "World 2"),
        (world3_tiles, "World 3"),
        (world4_tiles, "World 4")
    ]
    
    for world_data, world_name in worlds:
        markdown += format_world_tiles(world_data, world_name)
        markdown += "---\n\n"
    
    # Add footer
    markdown += "## Notes\n\n"
    markdown += "- **Required Count**: The number of items needed to complete the tile\n"
    markdown += "- **Wiki Link**: Link to the Old School RuneScape Wiki for more information\n"
    markdown += "- Some tiles may have multiple ways to complete them (indicated by 'OR' in the description)\n\n"
    
    return markdown

def main():
    """Main function to generate and save the markdown file."""
    try:
        # Generate markdown content
        markdown_content = generate_markdown()
        
        # Save to file
        output_file = os.path.join(os.path.dirname(__file__), 'tile_list.md')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"✅ Markdown file generated successfully: {output_file}")
        print(f"📄 Total characters: {len(markdown_content):,}")
        
        # Count total tiles
        total_world_tiles = sum(len(world['world_tiles']) for world in [world1_tiles, world2_tiles, world3_tiles, world4_tiles])
        total_key_tiles = sum(len(world['key_tiles']) for world in [world1_tiles, world2_tiles, world3_tiles, world4_tiles])
        total_boss_tiles = 4  # One boss tile per world
        
        print(f"📊 Tile counts:")
        print(f"   - World tiles: {total_world_tiles}")
        print(f"   - Key tiles: {total_key_tiles}")
        print(f"   - Boss tiles: {total_boss_tiles}")
        print(f"   - Total: {total_world_tiles + total_key_tiles + total_boss_tiles}")
        
    except Exception as e:
        print(f"❌ Error generating markdown file: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())