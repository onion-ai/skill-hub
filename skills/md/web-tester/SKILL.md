---
name: web-tester
description: 自动化测试网页应用，包括功能测试、UI 测试、性能测试和可访问性
  检查。当用户需要测试网站、验证页面功能、检查 UI 交互或生成测试报告时使用。
compatibility: 需要 Playwright 或 Puppeteer；Node.js 环境
---

# Web Tester

自动化网页测试专家，帮助用户编写和执行全面的 Web 测试。

## 测试类型

### 功能测试
- 表单提交和验证
- 导航和路由
- 用户认证流程
- API 接口调用

### UI/视觉测试
- 截图对比
- 响应式布局检查
- 跨浏览器兼容性

### 性能测试
- 页面加载时间（Core Web Vitals）
- 资源大小分析
- 渲染性能

### 可访问性测试
- WCAG 2.1 合规检查
- 键盘导航
- 屏幕阅读器兼容性

## 工作流程

1. 分析目标页面结构
2. 生成 Playwright/Puppeteer 测试脚本
3. 执行测试并收集结果
4. 生成测试报告（含截图、错误日志）
5. 提供修复建议

## 测试脚本模板

```javascript
import { test, expect } from '@playwright/test';

test('页面基础功能', async ({ page }) => {
  await page.goto('{url}');
  await expect(page).toHaveTitle(/{title}/);
  // 更多断言...
});
```