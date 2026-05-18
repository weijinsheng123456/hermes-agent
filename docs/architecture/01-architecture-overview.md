# Hermes Agent 系统架构总览

## 版本信息
- **版本**: v0.10.0
- **最后更新**: 2026-04-22
- **维护者**: Hermes Team

## 1. 系统概述

Hermes Agent 是一个模块化、可扩展的 AI 智能体系统，支持多平台部署（CLI、Telegram、Discord、Slack 等），具备完整的工具调用、技能管理、定时任务和浏览器自动化能力。

### 核心特性
- **多模型支持**: 支持 Anthropic、OpenAI、Alibaba、DeepSeek 等多个 LLM 提供商
- **工具系统**: 统一的工具注册和调度机制，支持 20+ 内置工具
- **技能系统**: 可持久化的技能库，支持自定义工作流
- **多平台网关**: 统一的消息网关，支持 Telegram/Discord/Slack/WhatsApp 等
- **TUI 界面**: 基于 Ink (React) 的现代化终端 UI
- **定时任务**: 完整的 cron 调度系统
- **浏览器自动化**: 基于 Browserbase 的网页交互能力

## 2. 核心架构组件

### 2.1 AIAgent 核心引擎
位置：`run_agent.py`

职责：
- 管理对话循环和 API 调用
- 处理工具调用和消息格式化
- 维护会话状态和上下文
- 实现迭代预算和最大调用次数控制

### 2.2 工具注册中心
位置：`tools/registry.py`

职责：
- 统一注册所有工具
- 管理工具可用性检查
- 处理工具调用分发
- 包装工具错误和输出

### 2.3 CLI 引擎
位置：`cli.py`, `hermes_cli/`

职责：
- 交互式命令行界面
- Slash 命令解析和分发
- 配置管理和迁移
- 皮肤/主题引擎

### 2.4 网关系统
位置：`gateway/`

职责：
- 多平台消息适配
- 会话持久化
- 平台特定命令处理
- 消息路由和分发

### 2.5 TUI 系统
位置：`ui-tui/`, `tui_gateway/`

职责：
- React/Ink 终端 UI 渲染
- JSON-RPC 通信桥接
- 实时流式输出
- 交互式组件（会话选择器、审批提示等）

## 3. 数据流架构

### 3.1 用户请求处理流程
```
用户输入 → CLI/Gateway → AIAgent → LLM API → 工具调用 → 结果返回 → 响应输出
```

### 3.2 工具调用流程
```
LLM 返回 tool_calls → handle_function_call() → tools/registry 分发 → 具体工具执行 → JSON 结果返回 → 消息追加 → 下一轮 LLM 调用
```

### 3.3 会话持久化流程
```
对话消息 → SessionDB (SQLite) → FTS5 全文索引 → 会话搜索/恢复
```

## 4. 文件依赖链

```
tools/registry.py (无依赖 - 所有工具文件导入)
       ↑
tools/*.py (每个文件在导入时调用 registry.register())
       ↑
model_tools.py (导入 tools/registry + 触发工具发现)
       ↑
run_agent.py, cli.py, batch_runner.py, environments/
```

## 5. 配置系统

### 5.1 配置文件
- `~/.hermes/config.yaml` - 用户配置
- `~/.hermes/.env` - API 密钥和环境变量
- `hermes_cli/config.py` - 默认配置和迁移逻辑

### 5.2 配置层次
1. 硬编码默认值 (DEFAULT_CONFIG)
2. 用户配置 YAML (config.yaml)
3. 环境变量 (.env)
4. 运行时覆盖 (命令行参数)

## 6. 扩展点

### 6.1 添加新工具
1. 创建 `tools/your_tool.py`
2. 调用 `registry.register()` 注册
3. 添加到 `toolsets.py` 的工具集

### 6.2 添加 Slash 命令
1. 在 `COMMAND_REGISTRY` 添加 `CommandDef`
2. 在 `cli.py` 添加处理器
3. 在 `gateway/run.py` 添加网关支持（可选）

### 6.3 添加新平台
1. 在 `gateway/platforms/` 创建适配器
2. 实现平台特定的消息处理
3. 注册到网关主循环

## 7. 测试架构

### 7.1 测试套件
- 位置：`tests/`
- 规模：~3000 测试用例
- 运行器：`scripts/run_tests.sh`
- 并行：4 个 xdist 工作进程

### 7.2 测试隔离
- HERMES_HOME 重定向到临时目录
- API 密钥取消设置
- 时区设置为 UTC
- Locale 设置为 C.UTF-8

## 8. 部署架构

### 8.1 本地部署
- Python 虚拟环境
- 直接运行 `hermes` 命令
- 配置文件在 `~/.hermes/`

### 8.2 Docker 部署
- Dockerfile 包含完整依赖
- 卷挂载配置文件
- 环境变量注入 API 密钥

### 8.3 云端部署
- Modal 无服务器 GPU
- 支持 SSH 远程环境
- 支持 Daytona 云开发环境

## 9. 监控和日志

### 9.1 日志系统
- 工具调用日志
- API 调用追踪
- 错误和异常记录
- 会话轨迹保存（可选）

### 9.2 监控指标
- Token 使用统计
- API 调用次数
- 工具调用成功率
- 会话持续时间

## 10. 安全机制

### 10.1 危险命令检测
- 文件删除操作
- 系统命令执行
- 网络请求发送
- 用户确认提示

### 10.2 凭证管理
- 环境变量存储 API 密钥
- 配置文件不包含敏感信息
- 平台特定的密钥管理

---

*本文档自动生成，最后更新：2026-04-22 11:29:49*
