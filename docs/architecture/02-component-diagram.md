# Hermes Agent 组件图

## 版本信息
- **创建日期**: 2026-04-22
- **文档类型**: 架构决策记录 (ADR-001)

## 1. 核心组件关系图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Hermes Agent 系统                                │
│                                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │   CLI 界面    │    │  Gateway 网关 │    │   TUI 界面   │              │
│  │  (cli.py)    │    │ (gateway/)   │    │ (ui-tui/)    │              │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘              │
│         │                   │                   │                       │
│         └───────────────────┼───────────────────┘                       │
│                             │                                           │
│                    ┌────────▼────────┐                                  │
│                    │   AIAgent 核心   │                                  │
│                    │ (run_agent.py)  │                                  │
│                    └────────┬────────┘                                  │
│                             │                                           │
│         ┌───────────────────┼───────────────────┐                       │
│         │                   │                   │                       │
│  ┌──────▼───────┐  ┌───────▼────────┐  ┌──────▼───────┐                │
│  │ 模型工具层    │  │  工具注册中心   │  │  会话数据库   │                │
│  │(model_tools) │  │(tools/registry)│  │(hermes_state)│                │
│  └──────────────┘  └───────┬────────┘  └──────────────┘                │
│                            │                                            │
│         ┌──────────────────┼──────────────────┐                         │
│         │                  │                  │                         │
│  ┌──────▼─────┐   ┌───────▼──────┐   ┌──────▼─────┐                    │
│  │ 终端工具    │   │  文件工具     │   │  Web 工具   │                    │
│  │(terminal)  │   │(read/patch)  │   │(search/web)│                    │
│  └────────────┘   └──────────────┘   └────────────┘                    │
│                                                                         │
│  ┌──────┬─────┐   ┌───────┬──────┐   ┌──────┬─────┐                    │
│  │浏览器 │代码  │   │ 委托  │  MCP  │   │ 技能 │ 记忆 │                    │
│  │工具   │执行  │   │ 工具  │ 工具  │   │ 工具 │ 工具 │                    │
│  └──────┴─────┘   └───────┴──────┘   └──────┴─────┘                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   外部服务层     │
                    ├─────────────────┤
                    │ • LLM APIs      │
                    │ • 浏览器服务     │
                    │ • 文件系统       │
                    │ • 网络 API       │
                    │ • MCP 服务器     │
                    └─────────────────┘
```

## 2. 组件职责说明

### 2.1 用户界面层

| 组件 | 文件位置 | 职责 |
|------|----------|------|
| CLI 界面 | `cli.py`, `hermes_cli/` | 交互式命令行，slash 命令，配置管理 |
| Gateway 网关 | `gateway/` | 多平台消息适配 (Telegram/Discord/Slack) |
| TUI 界面 | `ui-tui/`, `tui_gateway/` | React/Ink 终端 UI，JSON-RPC 通信 |

### 2.2 核心引擎层

| 组件 | 文件位置 | 职责 |
|------|----------|------|
| AIAgent 核心 | `run_agent.py` | 对话循环，API 调用，工具调度 |
| 模型工具层 | `model_tools.py` | 工具发现，调用处理，schema 生成 |
| 工具注册中心 | `tools/registry.py` | 工具注册，可用性检查，错误包装 |
| 会话数据库 | `hermes_state.py` | SQLite 存储，FTS5 搜索，会话恢复 |

### 2.3 工具实现层

| 工具集 | 文件位置 | 功能 |
|--------|----------|------|
| 终端工具 | `tools/terminal_tool.py` | 命令执行，进程管理 |
| 文件工具 | `tools/file_tools.py` | 读写/搜索/补丁文件 |
| Web 工具 | `tools/web_tools.py` | 搜索/抓取/提取 |
| 浏览器工具 | `tools/browser_tool.py` | 网页自动化 |
| 代码执行 | `tools/code_execution_tool.py` | Python 沙箱执行 |
| 委托工具 | `tools/delegate_tool.py` | 子智能体创建 |
| MCP 工具 | `tools/mcp_tool.py` | MCP 协议客户端 |
| 技能工具 | `agent/skill_commands.py` | 技能加载和管理 |
| 记忆工具 | `memory.py` | 持久化记忆存储 |

### 2.4 支持系统

| 组件 | 文件位置 | 职责 |
|------|----------|------|
| 配置系统 | `hermes_cli/config.py` | 默认配置，迁移，环境变量 |
| 显示系统 | `agent/display.py` | 动画 spinner，工具预览 |
| 皮肤引擎 | `hermes_cli/skin_engine.py` | 主题定制，颜色配置 |
| 定时任务 | `cron/` | 调度器，任务管理 |
| 环境管理 | `environments/` | 本地/Docker/SSH/云端终端后端 |

## 3. 组件交互模式

### 3.1 同步调用链
```
用户输入 → CLI.parse() → AIAgent.chat() → LLM API → handle_function_call() 
→ registry.dispatch() → tool.execute() → JSON 结果 → messages.append() 
→ 下一轮 LLM 调用 → 最终响应
```

### 3.2 异步事件流
```
Gateway 接收消息 → 会话查找/创建 → AIAgent 实例化 → 异步处理 → 
流式输出 → 平台 API 发送 → 用户接收
```

### 3.3 工具注册流程
```
Python 导入 → tools/*.py 执行 → registry.register() 调用 → 
schema 收集 → 可用性检查 → 工具集构建 → AIAgent 加载
```

## 4. 依赖关系矩阵

| 组件 | 依赖 | 被依赖 |
|------|------|--------|
| registry.py | 无 | 所有工具文件 |
| tools/*.py | registry.py | model_tools.py |
| model_tools.py | tools/registry | run_agent.py, cli.py |
| run_agent.py | model_tools.py | cli.py, gateway/, batch_runner.py |
| cli.py | run_agent.py | 用户直接交互 |

## 5. 扩展点设计

### 5.1 工具扩展
- 在 `tools/` 目录创建新文件
- 调用 `registry.register()` 注册
- 自动被 `model_tools.discover_builtin_tools()` 发现

### 5.2 平台扩展
- 在 `gateway/platforms/` 创建适配器
- 实现 `PlatformAdapter` 接口
- 注册到网关主循环

### 5.3 环境扩展
- 在 `environments/` 创建新后端
- 实现 `Environment` 基类方法
- 支持新的终端执行环境

## 6. 架构约束

### 6.1 硬约束
- 工具文件必须返回 JSON 字符串
- 所有路径必须使用 `get_hermes_home()` 而非硬编码
- 测试必须隔离 HERMES_HOME 到临时目录
- 禁止在 schema 中硬编码跨工具引用

### 6.2 软约束
- 优先使用现有工具而非创建新工具
- 工具调用应幂等和可重试
- 错误应包装并提供上下文信息
- 配置变更需要版本迁移

---

*本文档自动生成，最后更新：2026-04-22 11:30:30*
