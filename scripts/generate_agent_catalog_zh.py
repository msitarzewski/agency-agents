#!/usr/bin/env python3
"""
Regenerate docs/智能体全目录与组合流程.md with per-agent **中文阐释** (machine-translated).
Requires: pip install deep-translator

Usage:
  python3 scripts/generate_agent_catalog_zh.py

Cache: docs/.agent-catalog-zh-cache.json (skipped entries refreshed when source mtime changes)
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

try:
    from deep_translator import GoogleTranslator
except ImportError:
    raise SystemExit("Install deep-translator: pip install deep-translator") from None

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "智能体全目录与组合流程.md"
CACHE = ROOT / "docs" / ".agent-catalog-zh-cache.json"

CATEGORIES = [
    ("academic", "学术分部（Academic）"),
    ("design", "设计分部（Design）"),
    ("engineering", "工程分部（Engineering）"),
    ("game-development", "游戏开发分部（Game Development）"),
    ("marketing", "营销分部（Marketing）"),
    ("paid-media", "付费媒体分部（Paid Media）"),
    ("product", "产品分部（Product）"),
    ("project-management", "项目管理分部（Project Management）"),
    ("sales", "销售分部（Sales）"),
    ("testing", "测试分部（Testing）"),
    ("support", "支持分部（Support）"),
    ("spatial-computing", "空间计算分部（Spatial Computing）"),
    ("specialized", "专项分部（Specialized）"),
]


def load_cache() -> dict:
    if CACHE.is_file():
        try:
            return json.loads(CACHE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def save_cache(c: dict) -> None:
    CACHE.write_text(json.dumps(c, ensure_ascii=False, indent=0), encoding="utf-8")


def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm = text[3:end].strip()
    body = text[end + 4 :].lstrip("\n")
    meta: dict = {}
    for line in fm.splitlines():
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if m:
            k, v = m.group(1), m.group(2).strip()
            if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                v = v[1:-1]
            meta[k] = v
    return meta, body


def clean_snippet_line(ln: str) -> str:
    ln = ln.strip()
    ln = re.sub(r"^#{1,6}\s*", "", ln)
    ln = re.sub(r"^\*\*([^*]+)\*\*\s*", r"\1: ", ln)
    ln = re.sub(r"^[-*]\s*", "", ln)
    return ln.strip()


def extract_mission_snippet(body: str, max_chars: int = 520) -> str:
    patterns = [
        r"##\s*🎯[^\n]*\n([\s\S]*?)(?=\n##\s|$)",
        r"##\s*Your Core Mission[^\n]*\n([\s\S]*?)(?=\n##\s|$)",
        r"##\s*Core Mission[^\n]*\n([\s\S]*?)(?=\n##\s|$)",
    ]
    for pat in patterns:
        m = re.search(pat, body, re.I)
        if m:
            chunk = m.group(1).strip()
            lines: list[str] = []
            for ln in chunk.splitlines():
                t = ln.strip()
                if not t or t.startswith("```"):
                    continue
                if t.startswith("|") and "---" in t:
                    continue
                cl = clean_snippet_line(t)
                if not cl or cl.startswith("!["):
                    continue
                if len(cl) > 220:
                    cl = cl[:217] + "…"
                lines.append(cl)
                if len(lines) >= 14:
                    break
            s = " ".join(lines)
            s = re.sub(r"\s+", " ", s).strip()
            if len(s) > max_chars:
                s = s[: max_chars - 1] + "…"
            return s
    paras: list[str] = []
    for block in body.split("\n\n"):
        b = block.strip()
        if b.startswith("#") or b.startswith("```"):
            continue
        if b.startswith("|") and "---" in b:
            continue
        line = re.sub(r"\s+", " ", b.replace("\n", " "))
        if len(line) > 35:
            paras.append(line)
        if len(paras) >= 4:
            break
    s = " ".join(paras)
    if len(s) > max_chars:
        s = s[: max_chars - 1] + "…"
    return s


def strip_default_requirement_tail(snippet: str) -> str:
    """Avoid mid-sentence cut at 'Default requirement' after translation + truncate."""
    m = re.search(r"\*\*Default requirement\*\*:", snippet, re.I)
    if m:
        snippet = snippet[: m.start()].strip()
    return snippet


def translate_block(translator: GoogleTranslator, text: str, retries: int = 3) -> str:
    text = text.strip()
    if not text:
        return ""
    for attempt in range(retries):
        try:
            return translator.translate(text[:4500])
        except Exception:
            time.sleep(1.5 * (attempt + 1))
    return text


def main() -> None:
    if not OUT.is_file():
        raise SystemExit(f"Missing {OUT}")

    existing = OUT.read_text(encoding="utf-8")
    idx = existing.find("## 组合流程推荐")
    if idx == -1:
        raise SystemExit("Could not find ## 组合流程推荐 in existing doc")
    workflows = existing[idx:]

    translator = GoogleTranslator(source="en", target="zh-CN")
    cache = load_cache()
    parts: list[str] = []
    parts.append("# The Agency 智能体全目录（按分类）与组合流程推荐\n\n")
    parts.append(
        "> 本文档按仓库内源文件目录归类，逐个列出智能体：**名称**（与 frontmatter `name` 一致）、**一句话定位**（`description`）、"
        "**中文阐释**（基于英文描述与职责要点经机器翻译并略作整理，便于中文读者理解；**以英文源文件为权威**）、"
        "**职责摘要**（英文压缩摘录）、**源文件路径**。\n\n"
    )
    parts.append("---\n\n")

    total = 0
    for slug, title_zh in CATEGORIES:
        d = ROOT / slug
        if not d.is_dir():
            continue
        files = sorted(d.rglob("*.md"))
        if not files:
            continue
        parts.append(f"## {title_zh}（`{slug}/`）\n\n")
        parts.append(f"本类共 **{len(files)}** 个智能体。\n\n")
        for fp in files:
            total += 1
            rel = fp.relative_to(ROOT).as_posix()
            mtime = fp.stat().st_mtime
            text = fp.read_text(encoding="utf-8", errors="replace")
            meta, body = parse_frontmatter(text)
            name = meta.get("name", fp.stem.replace("-", " ").title())
            desc = meta.get("description", "—")
            emoji = (meta.get("emoji") or "").strip()
            color = (meta.get("color") or "").strip()
            snippet = extract_mission_snippet(body)
            if not snippet:
                snippet = "See source file for mission, rules, deliverables, and workflows."

            # Bump suffix when translation layout changes (invalidates stale cache entries).
            cache_key = f"{rel}#v4"
            entry = cache.get(cache_key, {})
            zh_block = entry.get("zh") if entry.get("mtime") == mtime else None

            if not zh_block:
                # Two-pass translation reads more naturally in Chinese than one blob with English labels.
                zh_desc = translate_block(translator, desc[:2000]).replace("\n", " ").strip()
                time.sleep(0.15)
                focus = strip_default_requirement_tail(snippet)[:450] if snippet else ""
                zh_focus = (
                    translate_block(translator, focus).replace("\n", " ").strip() if focus else ""
                )
                time.sleep(0.15)
                if zh_focus:
                    zh_block = f"{zh_desc} 在具体任务中，通常侧重：{zh_focus}"
                else:
                    zh_block = zh_desc
                if len(zh_block) > 2000:
                    zh_block = zh_block[:1997] + "…"
                cache[cache_key] = {"mtime": mtime, "zh": zh_block}
                save_cache(cache)

            head = f"{emoji} **{name}**" if emoji else f"**{name}**"
            parts.append(f"### {total}. {head}\n\n")
            if color:
                parts.append(f"- 主题色：`{color}`\n\n")
            parts.append(f"- **一句话定位**：{desc}\n\n")
            parts.append(f"- **中文阐释**：{zh_block}\n\n")
            parts.append(f"- **职责摘要**：{snippet}\n\n")
            parts.append(f"- **源文件**：[{rel}](../{rel})\n\n")
        parts.append("\n")

    parts.append("---\n\n")
    parts.append(
        f"## 文档统计\n\n"
        f"- 归类智能体总数：**{total}**（不含 `strategy/`、`examples/`、`docs/`、`integrations/` 等目录）\n\n"
    )
    parts.append(workflows)

    OUT.write_text("".join(parts), encoding="utf-8")
    print(f"Wrote {OUT} ({total} agents). Cache: {CACHE}")


if __name__ == "__main__":
    main()
