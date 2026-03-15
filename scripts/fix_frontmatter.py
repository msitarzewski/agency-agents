#!/usr/bin/env python3
import os
import re

def fix_frontmatter(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if file has frontmatter
    if not content.startswith('---'):
        print(f"  Skipping (no frontmatter): {filepath}")
        return

    # Find the first frontmatter block
    parts = content.split('---', 2)
    if len(parts) < 3:
        print(f"  Skipping (invalid frontmatter): {filepath}")
        return

    first_frontmatter = parts[1]
    body = parts[2]

    # Check if title and layout are in the body (not in frontmatter)
    body_start = body.lstrip()
    if body_start.startswith('title:') or body_start.startswith('layout:'):
        # Need to fix - move title and layout to frontmatter
        # Extract title and layout from body
        title_match = re.search(r'^title:\s*(.+)$', body, re.MULTILINE)
        layout_match = re.search(r'^layout:\s*(.+)$', body, re.MULTILINE)

        new_frontmatter = first_frontmatter.rstrip('\n')

        if title_match:
            title_value = title_match.group(1).strip()
            if 'title:' not in first_frontmatter:
                new_frontmatter += f"\ntitle: {title_value}"
            body = re.sub(r'^title:\s*.+\$\n?', '', body, flags=re.MULTILINE)

        if layout_match:
            layout_value = layout_match.group(1).strip()
            if 'layout:' not in first_frontmatter:
                new_frontmatter += f"\nlayout: {layout_value}"
            body = re.sub(r'^layout:\s*.+\$\n?', '', body, flags=re.MULTILINE)

        # Reconstruct the file
        new_content = f"---\n{new_frontmatter}\n---\n{body.lstrip()}"

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"  Fixed: {filepath}")
    else:
        print(f"  OK: {filepath}")

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Find all markdown files in category directories
    categories = ['engineering', 'design', 'game-development', 'marketing', 'paid-media',
                 'product', 'project-management', 'sales', 'specialized', 'spatial-computing',
                 'support', 'testing']

    for category in categories:
        category_path = os.path.join(base_dir, category)
        if os.path.isdir(category_path):
            print(f"\nProcessing {category}/...")
            for filename in os.listdir(category_path):
                if filename.endswith('.md'):
                    filepath = os.path.join(category_path, filename)
                    fix_frontmatter(filepath)

if __name__ == '__main__':
    main()
