"""
build_index.py - 扫描 skills/ 目录，自动生成 index.json

支持两种格式：
  1. <category>/<name>.yaml   —— onion YAML 格式
  2. <category>/<name>/SKILL.md —— Anthropic SKILL.md 格式

用法:
  python scripts/build_index.py
  python scripts/build_index.py --output index.json
  python scripts/build_index.py --base-url https://raw.githubusercontent.com/your/repo/main
"""

import json
import argparse
from datetime import datetime, timezone
from pathlib import Path

import yaml # type: ignore
import re


# ── 配置 ──────────────────────────────────────────────────────
REPO_OWNER   = "onion-ai"
REPO_NAME    = "skill-hub"
BRANCH       = "main"
SKILLS_DIR   = Path(__file__).parent.parent / "skills"
OUTPUT_FILE  = Path(__file__).parent.parent / "index.json"

DEFAULT_BASE_URL = (
    f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}"
)


def build_index(base_url: str = DEFAULT_BASE_URL) -> dict:
    skills = []

    for category_dir in sorted(SKILLS_DIR.iterdir()):
        if not category_dir.is_dir() or category_dir.name.startswith("."):
            continue
        category = category_dir.name

        # ── 1. 扫描 YAML 格式 ─────────────────────────────────
        for skill_file in sorted(category_dir.glob("*.yaml")):
            try:
                entry = _parse_yaml_skill(skill_file, category, base_url)
                if entry:
                    skills.append(entry)
                    print(f"  ✅ [yaml]    {category}/{skill_file.name}")
            except Exception as e:
                print(f"  ❌ [yaml]    {skill_file.name}: {e}")

        # ── 2. 扫描 SKILL.md 格式（子目录）────────────────────
        for sub_dir in sorted(category_dir.iterdir()):
            if not sub_dir.is_dir():
                continue
            skillmd = sub_dir / "SKILL.md"
            if skillmd.exists():
                try:
                    entry = _parse_skillmd(skillmd, category, base_url)
                    if entry:
                        skills.append(entry)
                        print(f"  ✅ [skillmd] {category}/{sub_dir.name}/SKILL.md")
                except Exception as e:
                    print(f"  ❌ [skillmd] {sub_dir.name}: {e}")

    index = {
        "version":    "1.0.0",
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total":      len(skills),
        "skills":     skills,
    }
    print(f"\n共索引 {len(skills)} 个技能")
    return index


def _parse_yaml_skill(path: Path, category: str, base_url: str) -> dict:
    """解析 onion YAML 格式技能"""
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict) or "name" not in data:
        raise ValueError("格式错误")

    rel_path = f"skills/{category}/{path.name}"
    return {
        "name":        data["name"],
        "description": data.get("description", ""),
        "version":     data.get("version", "1.0.0"),
        "author":      data.get("author", "community"),
        "tags":        list(set(data.get("tags", []) + [category])),
        "category":    category,
        "fmt":         "yaml",                        # ← 格式标识
        "param_count": len(data.get("params", [])),
        "stars":       data.get("stars", 0),
        "updated_at":  _mtime(path),
        "raw_url":     f"{base_url}/{rel_path}",
        "download_url":f"{base_url}/{rel_path}",
    }


def _parse_skillmd(path: Path, category: str, base_url: str) -> dict:
    """解析 Anthropic SKILL.md 格式技能"""
    content  = path.read_text(encoding="utf-8")
    fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not fm_match:
        raise ValueError("缺少 YAML frontmatter")

    fm   = yaml.safe_load(fm_match.group(1))
    name = fm.get("name", path.parent.name)
    desc = fm.get("description", "")

    # 自动推断标签
    tags = [category]
    kw_map = {
        "dev":     ["code", "debug", "test", "sql", "mcp", "api"],
        "writing": ["write", "document", "pdf", "pptx", "brand", "文案"],
        "data":    ["data", "chart", "analys", "数据"],
        "creative":["art", "music", "design", "creative", "算法"],
    }
    for tag, keywords in kw_map.items():
        if any(kw in desc.lower() for kw in keywords):
            tags.append(tag)
    tags.append("anthropic")

    # 检查是否有附带资源
    skill_dir = path.parent
    has_scripts    = (skill_dir / "scripts").exists()
    has_references = (skill_dir / "references").exists()
    has_assets     = (skill_dir / "assets").exists()

    rel_path = f"skills/{category}/{path.parent.name}/SKILL.md"
    return {
        "name":          name,
        "description":   desc,
        "version":       fm.get("version", "1.0.0"),
        "author":        fm.get("author", "anthropic"),
        "tags":          list(set(tags)),
        "category":      category,
        "fmt":           "skillmd",                   # ← 格式标识
        "param_count":   0,                           # SKILL.md 无显式参数
        "stars":         fm.get("stars", 0),
        "updated_at":    _mtime(path),
        "compatibility": fm.get("compatibility"),
        "has_scripts":   has_scripts,
        "has_references":has_references,
        "has_assets":    has_assets,
        "raw_url":       f"{base_url}/{rel_path}",
        "download_url":  f"{base_url}/{rel_path}",
    }


def _mtime(path: Path) -> str:
    import os
    mtime = os.path.getmtime(path)
    return datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    parser = argparse.ArgumentParser(description="构建 skill-hub 索引")
    parser.add_argument("--output",   default=str(OUTPUT_FILE))
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--pretty",   action="store_true")
    args = parser.parse_args()

    print(f"🔍 扫描目录: {SKILLS_DIR}\n")
    index = build_index(base_url=args.base_url)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2 if args.pretty else None)

    print(f"\n✅ 索引已写入: {args.output}  共 {index['total']} 个技能")


if __name__ == "__main__":
    main()