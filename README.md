# 🎯 Onion Skill Hub

> Onion CLI 的社区技能市场 —— 可复用的 AI Prompt 技能库

[![CI](https://github.com/onion-ai/skill-hub/actions/workflows/ci.yml/badge.svg)](https://github.com/onion-ai/skill-hub/actions)
[![Skills](https://img.shields.io/badge/dynamic/json?url=https://raw.githubusercontent.com/onion-ai/skill-hub/main/index.json&query=$.total&label=skills&color=green)](./index.json)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)

## 什么是技能？

技能（Skill）= **预设 Prompt 模板 + 参数定义**，是可复用的 AI 操作单元。

```yaml
# skills/basic/translate.yaml
name: translate
description: 将文本翻译为指定语言
template: |
  请将以下文本翻译为{lang}：
  {input}
params:
  - name: input
    required: true
  - name: lang
    default: "英文"
```

## 快速使用

```bash
# 浏览市场
onion skill hub list

# 搜索技能
onion skill hub search translate

# 安装技能
onion skill install translate

# 安装整个仓库
onion skill install onion-ai/skill-hub

# 执行技能
onion skill run translate -p lang=英文 -i "Hello World"
```

## 技能分类

| 分类 | 描述 | 技能数 |
|------|------|--------|
| [basic](./skills/basic/) | 基础通用技能（翻译、总结、解释、润色） | 4 |
| [dev](./skills/dev/) | 开发技能（代码审查、文档、调试、测试） | 6 |
| [writing](./skills/writing/) | 写作技能（改写、大纲、校对） | 3 |
| [data](./skills/data/) | 数据技能（分析、图表描述） | 2 |

## 贡献技能

欢迎提交你的技能！请阅读 [CONTRIBUTING.md](./CONTRIBUTING.md)。

```bash
# 1. Fork 本仓库
# 2. 添加技能文件
cp my-skill.yaml skills/<category>/
# 3. 校验格式
python scripts/validate.py
# 4. 提交 PR
```

## 技能文件格式

详见 [CONTRIBUTING.md](./CONTRIBUTING.md#技能文件格式)。

## License

MIT © [onion-ai](https://github.com/onion-ai)