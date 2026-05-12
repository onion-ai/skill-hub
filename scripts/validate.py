"""
validate.py - 校验 skills/ 目录下所有技能文件格式

用法:
  python scripts/validate.py              # 校验全部
  python scripts/validate.py skills/dev/  # 校验指定目录
  python scripts/validate.py --strict     # 严格模式（警告也报错）
"""

import sys
import argparse
from pathlib import Path

import yaml  # type: ignore


SKILLS_DIR = Path(__file__).parent.parent / "skills"

# 必填字段
REQUIRED_FIELDS = {"name", "description", "template"}
# 推荐字段（--strict 模式下缺少会报错）
RECOMMENDED_FIELDS = {"tags", "params", "author", "version"}
# 合法的 param 字段
PARAM_FIELDS = {"name", "description", "required", "default"}


def validate_skill(path: Path, strict: bool = False) -> list[str]:
    """
    校验单个技能文件
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
    if name and not all(c.isalnum() or c == "-" for c in name):
        errors.append(f"name 格式错误: '{name}'（只允许小写字母、数字、连字符）")

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

    # 7. template 中的占位符与 params 一致
    import re
    template     = data.get("template", "")
    placeholders = set(re.findall(r'\{(\w+)\}', template))
    param_names  = {p["name"] for p in params if isinstance(p, dict) and "name" in p}

    undefined = placeholders - param_names
    unused    = param_names - placeholders

    if undefined:
        errors.append(f"template 中有未定义的占位符: {undefined}")
    if unused and strict:
        errors.append(f"[WARN] params 中有未使用的参数: {unused}")

    # 8. tags 格式
    tags = data.get("tags", [])
    if tags and not isinstance(tags, list):
        errors.append("tags 必须是列表")

    return errors


def validate_all(
    target_dir: Path,
    strict:     bool = False,
) -> tuple[int, int]:
    """
    校验目录下所有技能文件
    返回 (通过数, 失败数)
    """
    passed = 0
    failed = 0

    yaml_files = sorted(target_dir.rglob("*.yaml"))
    if not yaml_files:
        print(f"⚠️  目录 {target_dir} 中没有找到 .yaml 文件")
        return 0, 0

    for path in yaml_files:
        if path.name.startswith("."):
            continue
        errors = validate_skill(path, strict=strict)
        rel    = path.relative_to(target_dir.parent)

        if errors:
            failed += 1
            print(f"  ❌ {rel}")
            for e in errors:
                print(f"       {e}")
        else:
            passed += 1
            print(f"  ✅ {rel}")

    return passed, failed


def main():
    parser = argparse.ArgumentParser(description="校验 skill-hub 技能文件格式")
    parser.add_argument(
        "target", nargs="?", default=str(SKILLS_DIR),
        help="校验目录或文件（默认: skills/）"
    )
    parser.add_argument("--strict", action="store_true", help="严格模式")
    args = parser.parse_args()

    target = Path(args.target)
    print(f"🔍 校验目录: {target}\n")

    if target.is_file():
        errors = validate_skill(target, strict=args.strict)
        if errors:
            for e in errors:
                print(f"  ❌ {e}")
            sys.exit(1)
        else:
            print("  ✅ 校验通过")
            sys.exit(0)

    passed, failed = validate_all(target, strict=args.strict)

    print(f"\n{'─'*40}")
    print(f"  通过: {passed}  失败: {failed}  共: {passed + failed}")

    if failed > 0:
        print("\n❌ 校验未通过，请修复以上错误")
        sys.exit(1)
    else:
        print("\n✅ 全部校验通过！")
        sys.exit(0)


if __name__ == "__main__":
    main()