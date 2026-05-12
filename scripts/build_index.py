"""
build_index.py - 扫描 skills/ 目录，自动生成 index.json

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
    """扫描 skills/ 目录，构建索引"""
    skills = []

    # 遍历所有分类目录
    for category_dir in sorted(SKILLS_DIR.iterdir()):
        if not category_dir.is_dir() or category_dir.name.startswith("."):
            continue
        category = category_dir.name

        for skill_file in sorted(category_dir.glob("*.yaml")):
            try:
                skill_entry = _parse_skill_file(skill_file, category, base_url)
                if skill_entry:
                    skills.append(skill_entry)
                    print(f"  ✅ {category}/{skill_file.name}")
            except Exception as e:
                print(f"  ❌ {skill_file.name}: {e}")

    index = {
        "version":    "1.0.0",
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total":      len(skills),
        "skills":     skills,
    }

    print(f"\n共索引 {len(skills)} 个技能")
    return index


def _parse_skill_file(path: Path, category: str, base_url: str) -> dict:
    """解析单个技能文件，提取索引所需字段"""
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError("文件格式错误：根节点必须是 dict")
    if "name" not in data:
        raise ValueError("缺少必填字段: name")
    if "template" not in data:
        raise ValueError("缺少必填字段: template")

    # 相对路径（用于构建 raw_url）
    rel_path = f"skills/{category}/{path.name}"
    raw_url  = f"{base_url}/{rel_path}"

    # 统计 params 数量
    params     = data.get("params", [])
    param_cnt  = len(params) if isinstance(params, list) else 0

    return {
        "name":         data["name"],
        "description":  data.get("description", ""),
        "version":      data.get("version", "1.0.0"),
        "author":       data.get("author", "community"),
        "tags":         data.get("tags", []) + [category],
        "category":     category,
        "param_count":  param_cnt,
        "stars":        data.get("stars", 0),      # 手动维护或通过 API 获取
        "updated_at":   _get_file_mtime(path),
        "raw_url":      raw_url,
        "download_url": raw_url,
    }


def _get_file_mtime(path: Path) -> str:
    """获取文件最后修改时间（ISO 格式）"""
    import os
    mtime = os.path.getmtime(path)
    return datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    parser = argparse.ArgumentParser(description="构建 skill-hub 索引")
    parser.add_argument("--output",   default=str(OUTPUT_FILE), help="输出文件路径")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Raw 文件基础 URL")
    parser.add_argument("--pretty",   action="store_true",      help="格式化输出 JSON")
    args = parser.parse_args()

    print(f"🔍 扫描目录: {SKILLS_DIR}\n")
    index = build_index(base_url=args.base_url)

    output_path = Path(args.output)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2 if args.pretty else None)

    print(f"✅ 索引已写入: {output_path}")
    print(f"   总计: {index['total']} 个技能")


if __name__ == "__main__":
    main()