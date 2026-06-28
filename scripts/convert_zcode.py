#!/usr/bin/env python3
"""
convert_zcode.py — Batch convert agency agents to ZCode skills format

Usage:
    python convert_zcode.py

Output: integrations/zcode/skills/<slug>/SKILL.md
"""

import os
import re
from pathlib import Path

REPO_ROOT = Path("F:/zcode/agency-agents")
OUT_DIR = REPO_ROOT / "integrations" / "zcode" / "skills"

AGENT_DIRS = [
    "academic", "design", "engineering", "finance", "game-development", "gis",
    "marketing", "paid-media", "product", "project-management", "sales",
    "security", "spatial-computing", "specialized", "support", "testing"
]

def get_field(content: str, field: str) -> str:
    """Extract a field value from YAML frontmatter."""
    # Match frontmatter between --- lines
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return ""
    
    frontmatter = match.group(1)
    # Find the field line
    pattern = rf'^{field}:\s*(.*?)$'
    for line in frontmatter.split('\n'):
        m = re.match(pattern, line)
        if m:
            return m.group(1).strip()
    return ""

def get_body(content: str) -> str:
    """Extract body content after frontmatter."""
    match = re.match(r'^---\n.*?\n---\n(.*)', content, re.DOTALL)
    if match:
        return match.group(1)
    return content

def slugify(name: str) -> str:
    """Convert name to kebab-case slug."""
    slug = name.lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')
    return slug

def main():
    """Main conversion function."""
    # Create output directory
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    count = 0
    
    for dir_name in AGENT_DIRS:
        dir_path = REPO_ROOT / dir_name
        if not dir_path.exists():
            print(f"SKIP {dir_name} - not found")
            continue
        
        # Find all .md files
        md_files = sorted(dir_path.glob("*.md"))
        print(f"Processing {dir_name}: {len(md_files)} files")
        
        for file_path in md_files:
            # Read file
            content = file_path.read_text(encoding='utf-8')
            
            # Check if it has frontmatter
            if not content.startswith('---'):
                print(f"  SKIP {file_path.name} - no frontmatter")
                continue
            
            # Extract name
            name = get_field(content, "name")
            if not name:
                print(f"  SKIP {file_path.name} - no name")
                continue
            
            # Extract description
            description = get_field(content, "description")
            
            # Extract body
            body = get_body(content)
            
            # Generate slug
            slug = slugify(name)
            
            # Create skill directory
            skill_dir = OUT_DIR / slug
            skill_dir.mkdir(parents=True, exist_ok=True)
            
            # Write SKILL.md
            output = f"""---
name: {slug}
description: {description}
---

{body}
"""
            
            skill_file = skill_dir / "SKILL.md"
            skill_file.write_text(output, encoding='utf-8')
            
            count += 1
            print(f"  [OK] {slug}")
    
    print()
    print(f"Done. Total conversions: {count}")

if __name__ == "__main__":
    main()
