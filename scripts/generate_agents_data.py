#!/usr/bin/env python3
import re
import yaml
import os

with open('AGENTS_LIST.md', 'r') as f:
    en_content = f.read()
with open('AGENTS_LIST_CN.md', 'r') as f:
    zh_content = f.read()

category_map = {'Engineering': 'engineering', '设计': 'design', 'Game Development': 'game-development', '游戏开发': 'game-development', 'Marketing': 'marketing', '营销': 'marketing', 'Paid Media': 'paid-media', '付费媒体': 'paid-media', 'Product': 'product', '产品': 'product', 'Project Management': 'project-management', '项目管理': 'project-management', 'Sales': 'sales', '销售': 'sales', 'Specialized': 'specialized', '专业化': 'specialized', 'Spatial Computing': 'spatial-computing', '空间计算': 'spatial-computing', 'Support': 'support', '支持': 'support', 'Testing': 'testing', '测试': 'testing'}

category_colors = {'engineering': '#3b82f6', 'design': '#ec4899', 'game-development': '#8b5cf6', 'marketing': '#f59e0b', 'paid-media': '#ef4444', 'product': '#06b6d4', 'project-management': '#84cc16', 'sales': '#14b8a6', 'specialized': '#6366f1', 'spatial-computing': '#f97316', 'support': '#22c55e', 'testing': '#a855f7'}

category_emojis = {'engineering': '⚙️', 'design': '🎨', 'game-development': '🎮', 'marketing': '📢', 'paid-media': '💰', 'product': '📦', 'project-management': '📋', 'sales': '💼', 'specialized': '🔧', 'spatial-computing': '🌐', 'support': '🎧', 'testing': '🧪'}

def slugify(name):
    slug = name.lower()
    slug = slug.replace(' & ', '-').replace('&', '').replace(' ', '-').replace('(', '').replace(')', '')
    while '--' in slug: slug = slug.replace('--', '-')
    return slug

def find_agent_file(agent_name, category):
    folder_map = {'engineering': 'engineering', 'design': 'design', 'game-development': 'game-development', 'marketing': 'marketing', 'paid-media': 'paid-media', 'product': 'product', 'project-management': 'project-management', 'sales': 'sales', 'specialized': 'specialized', 'spatial-computing': 'spatial-computing', 'support': 'support', 'testing': 'testing'}
    folder = folder_map.get(category, category)
    slug = slugify(agent_name)
    baseurl = '/agency-agents'
    if os.path.exists(folder):
        files = [f[:-3] for f in os.listdir(folder) if f.endswith('.md')]
        for f in files:
            if f == slug: return f"{baseurl}/{folder}/{f}.html"
        for f in files:
            if slug in f or f in slug: return f"{baseurl}/{folder}/{f}.html"
        for f in files:
            slug_parts = slug.split('-')
            if any(part in f.split('-') for part in slug_parts if len(part) > 3): return f"{baseurl}/{folder}/{f}.html"
    return None

def parse_agents(content, is_english=True):
    agents, current_category, current_category_name = [], None, None
    for line in content.split('\n'):
        cat_match = re.match(r'^##\s+(.+)\s+\((\d+)\)$', line)
        if cat_match:
            cat_name = cat_match.group(1).strip()
            current_category = category_map.get(cat_name, cat_name.lower().replace(' ', '-'))
            current_category_name = cat_name
            continue
        row_match = re.match(r'^\|\s*(.+?)\s*\|\s*(.+?)\s*\|$', line)
        if row_match and current_category and '---' not in line:
            name, description = row_match.group(1).strip(), row_match.group(2).strip()
            if name and description and name not in ['Name', '名称']:
                agents.append({'name': name, 'description_en' if is_english else 'description_zh': description, 'category': current_category, 'category_name': current_category_name})
    return agents

en_agents, zh_agents = parse_agents(en_content, True), parse_agents(zh_content, False)
agents_dict = {a['name']: a for a in en_agents}
for a in zh_agents:
    if a['name'] in agents_dict: agents_dict[a['name']]['description_zh'] = a['description_zh']
    else: agents_dict[a['name']] = a

for name, agent in agents_dict.items():
    cat = agent['category']
    agent['color'], agent['emoji'] = category_colors.get(cat, '#6b7280'), category_emojis.get(cat, '🤖')
    url = find_agent_file(name, cat)
    baseurl = '/agency-agents'
    agent['url'] = url if url else f"{baseurl}/{cat}/{slugify(name)}.html"

agents_list = sorted(agents_dict.values(), key=lambda x: x['name'])
print(yaml.dump(agents_list, allow_unicode=True, default_flow_style=False, sort_keys=False))
