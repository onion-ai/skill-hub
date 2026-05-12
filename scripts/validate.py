"""
validate.py - 校验 skills/ 目录下所有技能文件格式

支持两种格式:
  - YAML 格式    (.yaml)         轻量 Prompt 模板
  - SKILL.md 格式 (<name>/SKILL.md)  完整指令文档（兼容 Anthropic 官方）

用法:
  python scripts/validate.py              # 校验全部
  python scripts/validate.py skills/dev/  # 校验指定目录
  python scripts/validate.py --strict     # 严格模式（警告也报错）
  python scripts/validate.py --yaml-only  # 只校验 YAML 格式
  python scripts/validate.py --md-only    # 只校验 SKILL.md 格式
"""

import re
import sys
import argparse
from pathlib import Path

import yaml  # type: ignore


SKILLS_DIR = Path(__file__).parent.parent / "skills"

# ── YAML 格式规则 ─────────────────────────────────────────────
REQUIRED_FIELDS     = {"name", "description", "template"}
RECOMMENDED_FIELDS  = {"tags", "params", "author", "version"}
PARAM_FIELDS        = {"name", "description", "required", "default"}

# ── SKILL.md 格式规则 ─────────────────────────────────────────
MD_REQUIRED_FM      = {"name", "description"}          # frontmatter 必填
MD_RECOMMENDED_FM   = {"author", "version"}            # frontmatter 推荐（strict）
MD_BODY_WARN_LINES  = 500                              # 正文行数警告阈值
MD_VALID_RESOURCE_DIRS = {"scripts", "references", "assets"}  # 合法资源子目录


# ══════════════════════════════════════════════════════════════
# YAML 格式校验
# ══════════════════════════════════════════════════════════════

def validate_yaml_skill(path: Path, strict: bool = False) -> list[str]:
    """
    校验单个 YAML 技能文件
    返回错误列表（空列表表示通过）
    """
    errors = []

    # 1. 解析 YAML
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return [f"YAML 解析失败: {e}"]

    if not isinstance(data, dict):
        return ["根节点必须是 dict"]

    # 2. 必填字段
    for field in REQUIRED_FIELDS:
        if field not in data or not data[field]:
            errors.append(f"缺少必填字段: {field}")

    # 3. 推荐字段（strict 模式）
    if strict:
        for field in RECOMMENDED_FIELDS:
            if field not in data:
                errors.append(f"[WARN] 缺少推荐字段: {field}")

    # 4. name 格式（小写字母、数字、连字符）
    name = data.get("name", "")
    if name and not re.fullmatch(r"[a-z0-9][a-z0-9\-]*", name):
        errors.append(
            f"name 格式错误: '{name}'（只允许小写字母、数字、连字符，且不以连字符开头）"
        )

    # 5. 文件名与 name 一致
    expected_name = path.stem
    if name and name != expected_name:
        errors.append(
            f"name 与文件名不一致: name='{name}', 文件名='{expected_name}'"
        )

    # 6. params 格式校验
    params = data.get("params", [])
    if params is not None:
        if not isinstance(params, list):
            errors.append("params 必须是列表")
        else:
            for i, p in enumerate(params):
                if not isinstance(p, dict):
                    errors.append(f"params[{i}] 必须是 dict")
                    continue
                if "name" not in p:
                    errors.append(f"params[{i}] 缺少 name 字段")
                if "required" not in p:
                    errors.append(f"params[{i}] 缺少 required 字段")

    # 7. template 占位符与 params 一致
    template     = data.get("template", "")
    placeholders = set(re.findall(r'\{(\w+)\}', str(template)))
    param_names  = {
        p["name"] for p in (params or [])
        if isinstance(p, dict) and "name" in p
    }

    undefined = placeholders - param_names
    unused    = param_names - placeholders

    if undefined:
        errors.append(f"template 中有未定义的占位符: {sorted(undefined)}")
    if unused and strict:
        errors.append(f"[WARN] params 中有未使用的参数: {sorted(unused)}")

    # 8. tags 格式
    tags = data.get("tags", [])
    if tags and not isinstance(tags, list):
        errors.append("tags 必须是列表")

    # 9. version 格式（如果有）
    version = data.get("version", "")
    if version and not re.fullmatch(r"\d+\.\d+\.\d+", str(version)):
        errors.append(f"[WARN] version 格式建议为 x.y.z，当前: '{version}'")

    return errors


# ══════════════════════════════════════════════════════════════
# SKILL.md 格式校验
# ══════════════════════════════════════════════════════════════

def validate_skillmd(path: Path, strict: bool = False) -> list[str]:
    """
    校验单个 SKILL.md 文件
    path 应为 <skill-dir>/SKILL.md

    校验项:
      1. 文件可读
      2. 存在 YAML frontmatter
      3. frontmatter 解析成功
      4. 必填字段: name / description
      5. name 格式（小写字母+连字符）
      6. 目录名与 name 一致
      7. 正文（body）不为空
      8. 正文行数 < MD_BODY_WARN_LINES（strict: 超出报警告）
      9. compatibility 字段类型（如果存在）
     10. 附带资源目录合法（只允许 scripts/references/assets）
     11. scripts/ 下文件 shebang 检查（strict）
    """
    errors = []

    # 1. 文件可读
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        return [f"文件读取失败: {e}"]

    # 2. 检测 YAML frontmatter
    import re as _re
    fm_match = _re.match(r'^---\s*\n(.*?)\n---\s*\n', content, _re.DOTALL)
    if not fm_match:
        errors.append(
            "缺少 YAML frontmatter（文件应以 '---' 开头，格式: ---\\nname: ...\\n---）"
        )
        return errors  # 无 frontmatter 则后续无法继续

    # 3. frontmatter 解析
    try:
        fm = yaml.safe_load(fm_match.group(1))
    except yaml.YAMLError as e:
        errors.append(f"frontmatter YAML 解析失败: {e}")
        return errors

    if not isinstance(fm, dict):
        errors.append("frontmatter 必须是 key-value 格式")
        return errors

    # 4. 必填字段
    for field in MD_REQUIRED_FM:
        if field not in fm or not str(fm[field]).strip():
            errors.append(f"frontmatter 缺少必填字段: {field}")

    # 5. 推荐字段（strict）
    if strict:
        for field in MD_RECOMMENDED_FM:
            if field not in fm:
                errors.append(f"[WARN] frontmatter 缺少推荐字段: {field}")

    # 6. name 格式
    name = str(fm.get("name", "")).strip()
    if name and not _re.fullmatch(r"[a-z0-9][a-z0-9\-]*", name):
        errors.append(
            f"name 格式错误: '{name}'（只允许小写字母、数字、连字符）"
        )

    # 7. 目录名与 name 一致
    dir_name = path.parent.name
    if name and name != dir_name:
        errors.append(
            f"name 与目录名不一致: name='{name}', 目录名='{dir_name}'"
        )

    # 8. 正文不为空
    body = content[fm_match.end():].strip()
    if not body:
        errors.append("SKILL.md 正文（frontmatter 之后）不能为空")
    else:
        # 9. 正文行数检查
        body_lines = body.count("\n") + 1
        if body_lines > MD_BODY_WARN_LINES:
            msg = (
                f"[WARN] 正文较长: {body_lines} 行（建议 < {MD_BODY_WARN_LINES} 行）"
                "，考虑将部分内容移至 references/ 目录"
            )
            if strict:
                errors.append(msg)
            else:
                # 非 strict 模式只打印提示，不计入错误
                _warn(f"{path.parent.name}/SKILL.md: {msg}")

    # 10. compatibility 字段类型
    compat = fm.get("compatibility")
    if compat is not None and not isinstance(compat, str):
        errors.append(
            f"compatibility 字段必须是字符串，当前类型: {type(compat).__name__}"
        )

    # 11. version 格式（如果有）
    version = fm.get("version", "")
    if version and not _re.fullmatch(r"\d+\.\d+\.\d+", str(version)):
        errors.append(f"[WARN] version 格式建议为 x.y.z，当前: '{version}'")

    # 12. 附带资源目录校验
    skill_dir = path.parent
    for sub in skill_dir.iterdir():
        if not sub.is_dir():
            continue
        if sub.name.startswith("."):
            continue
        if sub.name not in MD_VALID_RESOURCE_DIRS:
            errors.append(
                f"未知的资源子目录: '{sub.name}'（合法目录: "
                f"{', '.join(sorted(MD_VALID_RESOURCE_DIRS))}）"
            )

    # 13. scripts/ 下文件 shebang 检查（strict）
    scripts_dir = skill_dir / "scripts"
    if strict and scripts_dir.exists():
        for script in scripts_dir.iterdir():
            if not script.is_file() or script.name.startswith("."):
                continue
            # 跳过非文本文件
            if script.suffix in {".png", ".jpg", ".gif", ".bin"}:
                continue
            try:
                first_line = script.read_text(encoding="utf-8", errors="ignore"
                                              ).splitlines()[0] if script.stat().st_size else ""
                if script.suffix in {".py", ".sh", ".js", ".ts"} and not first_line.startswith("#!"):
                    errors.append(
                        f"[WARN] scripts/{script.name} 缺少 shebang（如 #!/usr/bin/env python3）"
                    )
            except Exception:
                pass

    return errors


# ══════════════════════════════════════════════════════════════
# 统一校验入口
# ══════════════════════════════════════════════════════════════

def validate_all(
    target_dir: Path,
    strict:     bool = False,
    yaml_only:  bool = False,
    md_only:    bool = False,
) -> tuple[int, int]:
    """
    校验目录下所有技能文件（YAML + SKILL.md）
    返回 (通过数, 失败数)
    """
    passed = 0
    failed = 0

    # ── 收集待校验文件 ────────────────────────────────────────
    tasks: list[tuple[Path, str]] = []   # (文件路径, 格式标识)

    if not md_only:
        for p in sorted(target_dir.rglob("*.yaml")):
            if not p.name.startswith("."):
                tasks.append((p, "yaml"))

    if not yaml_only:
        for p in sorted(target_dir.rglob("SKILL.md")):
            tasks.append((p, "skillmd"))

    if not tasks:
        print(f"⚠️  目录 {target_dir} 中没有找到技能文件")
        return 0, 0

    # ── 按目录分组展示 ────────────────────────────────────────
    current_category = None

    for path, fmt in tasks:
        # 打印分类标题
        try:
            category = path.relative_to(target_dir).parts[0]
        except ValueError:
            category = ""
        if category != current_category:
            current_category = category
            print(f"\n📁 {category}/")

        errors = (
            validate_skillmd(path, strict=strict)
            if fmt == "skillmd"
            else validate_yaml_skill(path, strict=strict)
        )

        fmt_label = "📄 SKILL.md" if fmt == "skillmd" else "📋 YAML   "
        rel       = _rel_path(path, target_dir)

        if errors:
            failed += 1
            print(f"  ❌ [{fmt_label}] {rel}")
            for e in errors:
                indent = "           " if e.startswith("[WARN]") else "       "
                print(f"{indent}{e}")
        else:
            passed += 1
            print(f"  ✅ [{fmt_label}] {rel}")

    return passed, failed


# ══════════════════════════════════════════════════════════════
# 辅助函数
# ══════════════════════════════════════════════════════════════

def _rel_path(path: Path, base: Path) -> str:
    """安全地获取相对路径字符串"""
    try:
        return str(path.relative_to(base.parent))
    except ValueError:
        return str(path)


def _warn(msg: str):
    """打印非错误警告（黄色前缀）"""
    print(f"  ⚠️  {msg}")


# ══════════════════════════════════════════════════════════════
# main
# ══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="校验 skill-hub 技能文件格式（支持 YAML 和 SKILL.md）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python scripts/validate.py                      # 校验全部
  python scripts/validate.py skills/dev/          # 校验指定目录
  python scripts/validate.py skills/dev/translate.yaml  # 校验单个 YAML
  python scripts/validate.py skills/anthropic/skill-creator/SKILL.md  # 校验单个 SKILL.md
  python scripts/validate.py --strict             # 严格模式（警告也报错）
  python scripts/validate.py --yaml-only          # 只校验 YAML 格式
  python scripts/validate.py --md-only            # 只校验 SKILL.md 格式
        """,
    )
    parser.add_argument(
        "target", nargs="?", default=str(SKILLS_DIR),
        help="校验目录或文件（默认: skills/）",
    )
    parser.add_argument("--strict",    action="store_true", help="严格模式（警告也视为错误）")
    parser.add_argument("--yaml-only", action="store_true", help="只校验 YAML 格式技能")
    parser.add_argument("--md-only",   action="store_true", help="只校验 SKILL.md 格式技能")
    args = parser.parse_args()

    target = Path(args.target)

    # ── 校验单个文件 ──────────────────────────────────────────
    if target.is_file():
        fmt = "skillmd" if target.name == "SKILL.md" else "yaml"
        print(f"🔍 校验文件: {target}  [{fmt}]\n")

        errors = (
            validate_skillmd(target, strict=args.strict)
            if fmt == "skillmd"
            else validate_yaml_skill(target, strict=args.strict)
        )

        if errors:
            for e in errors:
                print(f"  ❌ {e}")
            sys.exit(1)
        else:
            print("  ✅ 校验通过")
            sys.exit(0)

    # ── 校验目录 ──────────────────────────────────────────────
    if not target.exists():
        print(f"❌ 目录不存在: {target}")
        sys.exit(1)

    mode_label = ""
    if args.yaml_only:
        mode_label = "  [仅 YAML]"
    elif args.md_only:
        mode_label = "  [仅 SKILL.md]"
    if args.strict:
        mode_label += "  [严格模式]"

    print(f"🔍 校验目录: {target}{mode_label}\n")

    passed, failed = validate_all(
        target,
        strict=args.strict,
        yaml_only=args.yaml_only,
        md_only=args.md_only,
    )

    total = passed + failed
    print(f"\n{'─' * 44}")
    print(f"  📋 YAML + 📄 SKILL.md  |  通过: {passed}  失败: {failed}  共: {total}")

    if failed > 0:
        print("\n❌ 校验未通过，请修复以上错误")
        sys.exit(1)
    else:
        print("\n✅ 全部校验通过！")
        sys.exit(0)


if __name__ == "__main__":
    main()