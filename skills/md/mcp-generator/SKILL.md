---
name: mcp-generator
description: 生成 MCP（Model Context Protocol）Server 代码。当用户需要创建
  MCP 服务、将现有 API 封装为 MCP 工具、或为 Claude 添加新能力时使用。
---

# MCP Server Generator

帮助用户快速生成符合 MCP 规范的 Server 代码。

## MCP 核心概念

- **Tools**：Claude 可调用的函数（有副作用）
- **Resources**：Claude 可读取的数据源（无副作用）
- **Prompts**：预定义的 Prompt 模板

## 生成流程

1. 了解用户想暴露的能力（API/数据库/文件系统/外部服务）
2. 设计 Tool/Resource 接口（名称、参数、返回值）
3. 生成 MCP Server 代码（Python SDK 或 TypeScript SDK）
4. 生成配置文件（claude_desktop_config.json）
5. 提供测试和部署说明

## 代码模板（Python）

```python
from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.types as types

server = Server("{server-name}")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="{tool-name}",
            description="{description}",
            inputSchema={
                "type": "object",
                "properties": {
                    "param": {"type": "string", "description": "..."}
                },
                "required": ["param"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    if name == "{tool-name}":
        # 实现逻辑
        return [types.TextContent(type="text", text="结果")]
```