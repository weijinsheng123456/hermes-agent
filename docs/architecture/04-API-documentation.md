# Hermes Agent API 文档

## 版本信息
- **API 版本**: v1.0
- **最后更新**: 2026-04-22

## 1. AIAgent 类 API

### 1.1 初始化

```python
from run_agent import AIAgent

agent = AIAgent(
    model: str = "deepseek/deepseek-chat",
    max_iterations: int = 90,
    enabled_toolsets: list = None,
    disabled_toolsets: list = None,
    quiet_mode: bool = False,
    save_trajectories: bool = False,
    platform: str = None,
    session_id: str = None,
    skip_context_files: bool = False,
    skip_memory: bool = False
)
```

### 1.2 简单对话

```python
response = agent.chat("你好，请帮我分析这个 Python 文件")
print(response)  # 字符串
```

### 1.3 完整对话

```python
result = agent.run_conversation(
    user_message="分析这个项目",
    system_message=None,
    conversation_history=None,
    task_id=None
)
print(result["final_response"])  # 最终响应
print(result["messages"])        # 完整消息历史
```

## 2. 工具注册 API

### 2.1 注册新工具

```python
from tools.registry import registry

def my_tool(param: str, task_id: str = None) -> str:
    return json.dumps({"success": True, "data": "..."})

registry.register(
    name="my_tool",
    toolset="custom",
    schema={
        "name": "my_tool",
        "description": "我的自定义工具",
        "parameters": {
            "type": "object",
            "properties": {
                "param": {"type": "string", "description": "参数描述"}
            },
            "required": ["param"]
        }
    },
    handler=lambda args, **kw: my_tool(param=args.get("param"), task_id=kw.get("task_id")),
    check_fn=lambda: True,  # 可用性检查
    requires_env=["MY_API_KEY"]
)
```

### 2.2 工具处理函数签名

工具处理函数必须返回 JSON 字符串

**参数:**
- args: LLM 传递的参数 dict
- task_id: 任务 ID（用于追踪）

**返回值:**
- JSON 字符串，格式：
  - 成功：{"success": True, "data": ...}
  - 失败：{"error": "错误信息", "details": {...}}

## 3. CLI API

### 3.1 命令行入口

```bash
hermes                    # 启动交互式 CLI
hermes --tui             # 启动 TUI 界面
hermes --quiet           # 安静模式
hermes --model <model>   # 指定模型
```

### 3.2 Slash 命令

```bash
/help                    # 显示帮助
/model <model>           # 切换模型
/tools                   # 查看可用工具
/skills                  # 浏览技能
/sessions                # 管理会话
/config                  # 查看配置
/quit                    # 退出
```

## 4. Gateway API

### 4.1 启动网关

```bash
hermes gateway start     # 启动网关服务
hermes gateway status    # 查看状态
hermes gateway stop      # 停止服务
```

### 4.2 平台配置

```yaml
# ~/.hermes/config.yaml
gateway:
  telegram:
    enabled: true
    bot_token: "${TELEGRAM_BOT_TOKEN}"
  discord:
    enabled: false
    bot_token: "${DISCORD_BOT_TOKEN}"
```

## 5. 定时任务 API

### 5.1 创建任务

```bash
hermes cron create --prompt "每天早上 8 点发送新闻摘要" --schedule "0 8 * * *"
```

### 5.2 管理任务

```bash
hermes cron list         # 列出所有任务
hermes cron pause <id>   # 暂停任务
hermes cron resume <id>  # 恢复任务
hermes cron remove <id>  # 删除任务
hermes cron run <id>     # 手动运行任务
```

## 6. 技能系统 API

### 6.1 技能结构

```
~/.hermes/skills/<skill-name>/
├── SKILL.md          # 技能描述和使用说明
├── references/       # 参考文档
├── templates/        # 模板文件
└── scripts/          # 辅助脚本
```

### 6.2 技能加载

```python
from skill_view import skill_view

skill = skill_view("my-skill")
print(skill["content"])  # SKILL.md 内容
print(skill["linked_files"])  # 链接文件
```

## 7. 记忆系统 API

### 7.1 保存记忆

```python
from memory_tool import memory

memory(
    action="add",
    target="memory",  # 或 "user"
    content="重要信息内容"
)
```

### 7.2 更新记忆

```python
memory(
    action="replace",
    target="memory",
    old_text="要替换的原文",
    new_text="新的内容"
)
```

### 7.3 删除记忆

```python
memory(
    action="remove",
    target="memory",
    old_text="要删除的内容"
)
```

## 8. 会话管理 API

### 8.1 SessionDB 类

```python
from hermes_state import SessionDB

db = SessionDB()

# 保存消息
db.save_message(session_id, role, content, metadata)

# 加载会话
messages = db.load_messages(session_id)

# 搜索会话
results = db.search(query, limit=10)

# 删除会话
db.delete_session(session_id)
```

## 9. 错误处理

### 9.1 标准错误格式

```json
{
  "error": "错误类型",
  "message": "人类可读的错误信息",
  "details": {
    "tool": "工具名称",
    "args": {...},
    "traceback": "..."
  }
}
```

### 9.2 错误类型

| 错误类型 | 说明 | 处理建议 |
|----------|------|----------|
| ToolUnavailable | 工具不可用 | 检查 API key 和环境变量 |
| ToolExecutionError | 工具执行失败 | 检查参数和依赖 |
| ApprovalRequired | 需要审批 | 等待用户确认 |
| TimeoutError | 超时 | 增加 timeout 或优化查询 |
| RateLimitError | 频率限制 | 实现退避重试 |

## 10. 性能最佳实践

### 10.1 减少 API 调用
- 使用 `/model` 选择合适大小的模型
- 启用提示缓存（Anthropic）
- 限制 `max_iterations`
- 使用 `quiet_mode` 减少输出

### 10.2 优化工具调用
- 批量操作而非多次调用
- 使用 `search_files` 而非 `terminal("grep ...")`
- 使用 `read_file` 而非 `terminal("cat ...")`
- 使用 `patch` 而非 `terminal("sed ...")`

### 10.3 会话管理
- 定期清理旧会话
- 使用会话搜索而非加载全部历史
- 启用自动压缩

---

*本文档自动生成，最后更新：2026-04-22 11:33:12*
