# Hermes Agent 自动启动与监控指南

## 📋 目录

- [功能概述](#功能概述)
- [架构说明](#架构说明)
- [快速开始](#快速开始)
- [手动控制](#手动控制)
- [微信告警配置](#微信告警配置)
- [故障排查](#故障排查)

---

## 功能概述

### ✅ 已实现功能

1. **WSL 自动启动** - WSL 启动时自动启动所有 Hermes 服务
2. **Windows 开机启动** - Windows 登录时自动触发 WSL 启动
3. **进程监控** - 60 秒间隔健康检查，异常自动重启
4. **微信告警** - 服务异常、资源不足时发送微信通知
5. **统一管理** - 一个命令控制所有服务

### 🎯 服务清单

| 服务 | 端口 | 说明 |
|------|------|------|
| Gateway | 8000 | Hermes 核心网关服务 |
| Dashboard | 9119 | 官方 Web 管理界面 |
| WebUI | 8080 | Web 用户界面 |
| Monitor | - | 健康监控服务 |

---

## 架构说明

```
Windows 开机
    ↓
任务计划程序 (配置 Hermes WSL Startup)
    ↓
启动 Hermes.bat (等待 15 秒)
    ↓
WSL 启动 (用户：xiaobai)
    ↓
.bashrc 检测
    ↓
wsl_auto_start.sh (延迟 3 秒)
    ↓
┌─────────────────────────────────────┐
│  1. 等待网络就绪 (最多 30 秒)        │
│  2. 激活虚拟环境                     │
│  3. 启动 Gateway (tmux 会话)          │
│  4. 启动 Dashboard (tmux 会话)        │
│  5. 启动 WebUI (tmux 会话)            │
│  6. 启动监控服务                     │
│  7. 发送微信通知                     │
└─────────────────────────────────────┘
    ↓
hermes_monitor.sh (后台运行)
    ↓
┌─────────────────────────────────────┐
│  每 60 秒执行健康检查：                │
│  • Gateway 进程检查                  │
│  • Dashboard 端口检查 (9119)          │
│  • WebUI 端口检查 (8080)              │
│  • 系统资源检查 (磁盘/内存)           │
│  • 异常自动重启 (最多 3 次)             │
│  • 微信告警通知                     │
└─────────────────────────────────────┘
```

---

## 快速开始

### 方式一：Windows 开机自动启动（推荐）

1. **以管理员身份运行配置脚本**：
   ```batch
   双击桌面上的 "配置 Hermes 开机启动.bat"
   ```

2. **验证配置**：
   - 打开"任务计划程序"
   - 导航到：任务计划程序库 > Hermes
   - 确认 "Hermes WSL Startup" 任务存在且已启用

3. **重启 Windows 测试**：
   ```powershell
   wsl --shutdown
   # 重新打开 WSL 终端，检查服务是否自动启动
   ```

### 方式二：手动启动

1. **双击桌面快捷方式**：
   ```batch
   双击 "启动 Hermes.bat"
   ```

2. **或在 WSL 中运行**：
   ```bash
   cd /home/xiaobai/hermes-agent/scripts
   ./hermes_manager.sh start
   ```

---

## 手动控制

### 使用 hermes_manager.sh

```bash
# 查看所有服务状态
./hermes_manager.sh status

# 启动所有服务
./hermes_manager.sh start

# 停止所有服务
./hermes_manager.sh stop

# 重启所有服务
./hermes_manager.sh restart

# 单独控制
./hermes_manager.sh start-gw      # 只启动 Gateway
./hermes_manager.sh stop-dash     # 只停止 Dashboard
./hermes_manager.sh start-mon     # 只启动监控服务
```

### 使用 hermes_monitor.sh

```bash
# 启动监控服务
./hermes_monitor.sh start

# 执行单次健康检查
./hermes_monitor.sh check

# 查看监控状态
./hermes_monitor.sh status

# 停止监控服务
./hermes_monitor.sh stop
```

### 使用 tmux 管理

```bash
# 查看所有 tmux 会话
tmux list-sessions

# 连接到 Gateway 会话
tmux attach -t hermes-gateway

# 连接到 Dashboard 会话
tmux attach -t hermes-dashboard

# 连接到 WebUI 会话
tmux attach -t hermes-webui

# 退出 tmux 会话（不关闭）
# 按 Ctrl+B，然后按 D
```

---

## 微信告警配置

### 前提条件

需要配置 WxPusher（微信推送服务）：

1. **获取 WxPusher 配置**：
   - 访问 https://wxpusher.zjiecode.com/
   - 注册并创建应用
   - 获取 `appToken`
   - 关注应用获取 `uid`

2. **编辑 .env 文件**：
   ```bash
   nano /home/xiaobai/.hermes/.env
   ```

3. **添加配置**：
   ```env
   WX_PUSHER_APP_TOKEN=你的 appToken
   WX_PUSHER_UID=你的 uid
   ```

### 告警触发条件

| 告警类型 | 触发条件 | 告警级别 |
|---------|---------|---------|
| 服务异常 | 检测到服务进程消失 | WARNING |
| 重启失败 | 重启次数达到 3 次 | ERROR |
| 磁盘不足 | 使用率 ≥ 90% | WARNING |
| 磁盘严重不足 | 使用率 ≥ 95% | ERROR |
| 内存不足 | 使用率 ≥ 90% | WARNING |
| 内存严重不足 | 使用率 ≥ 95% | ERROR |

### 测试微信通知

```bash
# 发送测试消息
python3 /home/xiaobai/.hermes/scripts/wxpusher.py send "测试标题" "测试内容" --level INFO
```

---

## 故障排查

### 1. WSL 启动后服务未自动启动

**检查日志**：
```bash
cat /home/xiaobai/.hermes/logs/wsl_auto_start.log
```

**常见原因**：
- 虚拟环境不存在：检查 `/home/xiaobai/hermes-agent/.venv`
- 网络未就绪：查看日志中的网络等待部分
- 锁文件未清理：`rm -f /tmp/hermes_auto_start.lock`

### 2. Gateway 启动失败

**检查 Gateway 日志**：
```bash
tail -100 /home/xiaobai/.hermes/logs/gateway.log
```

**检查 tmux 会话**：
```bash
tmux list-sessions | grep hermes-gateway
```

**手动启动测试**：
```bash
cd /home/xiaobai/hermes-agent
source .venv/bin/activate
python gateway/run.py
```

### 3. 监控服务未运行

**检查进程**：
```bash
pgrep -f "hermes_monitor.sh"
```

**查看监控日志**：
```bash
tail -100 /home/xiaobai/.hermes/logs/hermes_monitor.log
```

**手动启动**：
```bash
/home/xiaobai/hermes-agent/scripts/hermes_monitor.sh start
```

### 4. 微信通知未发送

**检查配置**：
```bash
grep "WX_PUSHER" /home/xiaobai/.hermes/.env
```

**检查脚本权限**：
```bash
ls -la /home/xiaobai/.hermes/scripts/wxpusher.py
```

**测试发送**：
```bash
python3 /home/xiaobai/.hermes/scripts/wxpusher.py test
```

### 5. Windows 任务计划未触发

**查看任务历史**：
1. 打开"任务计划程序"
2. 找到 "Hermes WSL Startup"
3. 点击"属性" > "历史记录"

**手动触发测试**：
1. 右键任务
2. 选择"运行"

**检查权限**：
- 确保任务配置为"使用最高权限运行"
- 确保用户有 WSL 访问权限

---

## 日志文件位置

| 日志文件 | 路径 |
|---------|------|
| WSL 自动启动日志 | `/home/xiaobai/.hermes/logs/wsl_auto_start.log` |
| Gateway 日志 | `/home/xiaobai/.hermes/logs/gateway.log` |
| Dashboard 日志 | `/home/xiaobai/.hermes/logs/dashboard.log` |
| WebUI 日志 | `/home/xiaobai/.hermes/logs/webui.log` |
| 监控服务日志 | `/home/xiaobai/.hermes/logs/hermes_monitor.log` |
| 管理器日志 | `/home/xiaobai/.hermes/logs/hermes_manager.log` |

---

## 高级配置

### 修改健康检查间隔

编辑 `hermes_monitor.sh`：
```bash
HEALTH_CHECK_INTERVAL=60  # 改为需要的秒数
```

### 修改重启次数限制

编辑 `hermes_monitor.sh`：
```bash
MAX_RESTART_ATTEMPTS=3  # 改为需要的次数
```

### 禁用自动启动

临时禁用 WSL 自动启动：
```bash
export HERMES_AUTO_START_DISABLE=1
```

### 自定义微信告警阈值

编辑 `hermes_monitor.sh` 中的 `check_resources()` 函数，修改磁盘和内存的阈值百分比。

---

## 最佳实践

1. **定期检查日志**：建议每天查看一次监控日志
2. **测试告警通道**：每周发送一次测试消息确保微信通知正常
3. **清理旧日志**：每月清理一次日志文件，避免占用过多磁盘空间
4. **监控资源使用**：关注磁盘和内存使用率，及时扩容

---

## 技术支持

如遇到问题，请提供以下信息：

1. WSL 自动启动日志
2. 相关服务日志
3. Windows 任务计划程序历史记录
4. 微信告警配置（隐藏敏感信息）

---

**最后更新**: 2026-04-22  
**版本**: v2.0
