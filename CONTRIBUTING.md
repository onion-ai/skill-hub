# 贡献指南

感谢你为 Onion Skill Hub 贡献技能！

## 技能文件格式

每个技能是一个 YAML 文件，放在 `skills/<category>/` 目录下：

```yaml
# 必填字段
name: skill-name            # 技能名（小写字母 + 数字 + 连字符）
description: 技能的简短描述  # 一句话描述，50字以内
template: |                 # Prompt 模板，用 {变量名} 作占位符
  请处理以下内容：
  {input}

# 推荐填写
version: "1.0.0"
author: your-github-username
tags:
  - 标签1
  - 标签2

# 参数定义（与 template 中的占位符对应）
params:
  - name: input           # 参数名（与模板占位符一致）
    description: 输入内容
    required: true
    default: ""
  - name: style
    description: 风格
    required: false
    default: "专业"

# 可选：使用示例
examples:
  - params:
      input: "示例输入"
      style: "简洁"
```

## 分类说明

| 目录 | 适合的技能类型 |
|------|--------------|
| `basic/` | 通用技能：翻译、总结、解释、润色等 |
| `dev/` | 开发相关：代码审查、文档生成、调试、测试等 |
| `writing/` | 写作相关：改写、大纲、校对、创作等 |
| `data/` | 数据相关：分析、SQL、图表、报告等 |

> 如果你的技能不属于以上分类，可以在 PR 中说明，我们会讨论新增分类。

## 命名规范

- 文件名 = `name` 字段值 + `.yaml`，例如 `code-review.yaml`
- `name` 只允许：小写字母、数字、连字符（`-`）
- `name` 要简洁且具描述性，例如 `translate`、`code-review`、`sql-gen`

## 提交流程

```bash
# 1. Fork 并克隆
git clone https://github.com/<your-name>/skill-hub
cd skill-hub

# 2. 安装依赖
pip install pyyaml

# 3. 添加技能文件
vim skills/<category>/my-skill.yaml

# 4. 本地校验
python scripts/validate.py skills/<category>/my-skill.yaml

# 5. 提交 PR
git checkout -b feat/add-my-skill
git add skills/<category>/my-skill.yaml
git commit -m "feat: add my-skill"
git push origin feat/add-my-skill
```

## PR 要求

- [ ] 技能文件通过 `validate.py` 校验
- [ ] `name` 与文件名一致
- [ ] `description` 清晰描述技能用途
- [ ] 所有 `required: true` 的参数在 `template` 中有对应占位符
- [ ] 无重复技能（先搜索确认）