#!/usr/bin/env bash
# init_hub.sh - 一键初始化 skill-hub 仓库结构
# 用法: bash scripts/init_hub.sh

set -e

echo "🚀 初始化 skill-hub 仓库结构..."

# 创建目录
mkdir -p skills/basic skills/dev skills/writing skills/data
mkdir -p scripts .github/workflows

# 创建占位文件
for dir in basic dev writing data; do
    touch "skills/$dir/.gitkeep"
done

echo "✅ 目录结构已创建"
echo ""
echo "📋 下一步："
echo "  1. 将技能 YAML 文件放入 skills/<category>/ 目录"
echo "  2. 运行: python scripts/validate.py    # 校验格式"
echo "  3. 运行: python scripts/build_index.py # 生成索引"
echo "  4. git add . && git commit -m 'init skill-hub'"
echo "  5. git push → GitHub Actions 自动维护 index.json"