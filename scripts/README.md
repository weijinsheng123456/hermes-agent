# 🚀 Hermes Agent 统一启动与自动管理指南

## 📋 目录

1. [快速开始](#快速开始)
2. [系统架构](#系统架构)
3. [脚本说明](#脚本说明)
4. [使用指南](#使用指南)
5. [自动启动配置](#自动启动配置)
6. [故障排查](#故障排查)

---

## 🎯 快速开始

### 一键启动所有服务
```bash
/home/xiaobai/hermes-agent/scripts/hermes_manager.sh start
```

### 查看状态
```bash
/home/xiaobai/hermes-agent/scripts/hermes_manager.sh status
```

### 健康检查
```bash
/home/xiaobai/hermes-agent/scripts/hermes_manager.sh health
```

---

## 🏗️ 系统架构

### 服务组成

| 服务 | 端口 | 进程 | 说明 |
|------|------|------|------|
| **Gateway** | - | `gateway/run.py` | 消息网关（微信/飞书等） |
| **Dashboard** | 9119 | `hermes_cli.web_server:app` | 官方 Web 管理界面 |
| **WebUI** | 8080 | `hermes_webui.server:app` | 社区版 Web 界面 |

### 进程管理架构

```
WSL 启动
    │
    └─→ wsl_auto_start.sh (自动启动脚本)
            │
            ├─→ tmux: hermes-gateway
            ├─→ tmux: hermes-dashboard
            └─→ tmux: hermes-webui
                    │
                    └─→ hermes_monitor.sh (监控脚本)
                            │
                            └─→ 自动重启异常服务
```

---

## 📜 脚本说明

### 1. `hermes_manager.sh` - 统一管理器

**功能**: 启动、停止、重启、状态查看、健康检查

**命令**:
```bash
# 启动所有服务
./hermes_manager.sh start

# 停止所有服务
./hermes_manager.sh stop

# 重启所有服务
./hermes_manager.sh restart

# 查看状态
./hermes_manager.sh status

# 健康检查
./hermes_manager.sh health

# 单独控制
./hermes_manager.sh start-gateway    # 只启动 Gateway
./hermes_manager.sh stop-dashboard   # 只停止 Dashboard
```

### 2. `wsl_auto_start.sh` - WSL 自动启动

**功能**: WSL 启动时自动启动所有 Hermes 服务

**特性**:
- ✅ 网络就绪检测
- ✅ 防止重复启动
- ✅ 启动状态日志
- ✅ 可通过环境变量禁用

**禁用自动启动**:
```bash
export HERMES_AUTO_START_DISABLE=1
```

### 3. `hermes_monitor.sh` - 进程监控器

**功能**: 监控服务状态，异常时自动重启

**命令**:
```bash
# 启动监控服务（后台）
./hermes_monitor.sh start

# 单次健康检查
./hermes_monitor.sh check

# 查看监控状态
./hermes_monitor.sh status
```

**配置** (在脚本顶部):
```bash
HEALTH_CHECK_INTERVAL=60   # 检查间隔（秒）
MAX_RESTART_ATTEMPTS=3     # 最大重启次数
RESTART_COOLDOWN=30        # 重启冷却时间（秒）
```

---

## 📖 使用指南

### 手动启动流程

```bash
# 1. 激活虚拟环境
cd /home/xiaobai/hermes-agent
source .venv/bin/activate

# 2. 启动所有服务
./scripts/hermes_manager.sh start

# 3. 验证启动
./scripts/hermes_manager.sh status

# 4. 访问 Web 界面
# Dashboard: http://127.0.0.1:9119
# WebUI:     http://127.0.0.1:8080
```

### 查看日志

```bash
# 启动日志
tail -f /home/xiaobai/.hermes/logs/wsl_auto_start.log

# Gateway 日志
tail -f /home/xiaobai/.hermes/logs/gateway.log

# Dashboard 日志
tail -f /home/xiaobai/.hermes/logs/dashboard.log

# WebUI 日志
tail -f /home/xiaobai/.hermes/logs/webui.log

# 监控日志
tail -f /home/xiaobai/.hermes/logs/hermes_monitor.log
```

### tmux 会话管理

```bash
# 列出所有 tmux 会话
tmux list-sessions

# 连接到 Gateway 会话
tmux attach -t hermes-gateway

# 连接到 Dashboard 会话
tmux attach -t hermes-dashboard

# 连接到 WebUI 会话
tmux attach -t hermes-webui

# 断开会话 (不终止)
# 按 Ctrl+B, 然后按 D
```

---

## ⚙️ 自动启动配置

### 已配置项

✅ **`.bashrc` 集成**
- 在交互式 shell 启动时自动检测
- 延迟 3 秒启动，确保系统稳定
- 检查是否已有 tmux 会话，避免重复

### WSL 启动流程

```
WSL 启动
    │
    └─→ 加载 /home/xiaobai/.bashrc
            │
            └─→ 检测交互式 shell
                    │
                    └─→ 检测 tmux 会话
                            │
                            └─→ 无会话 → 启动 wsl_auto_start.sh
                                    │
                                    ├─→ 等待网络就绪
                                    ├─→ 启动 Gateway
                                    ├─→ 启动 Dashboard
                                    └─→ 启动 WebUI
```

### 验证自动启动

1. **重启 WSL**:
```powershell
# Windows PowerShell
wsl --shutdown
```

2. **重新打开 WSL 终端**

3. **检查服务状态**:
```bash
/home/xiaobai/hermes-agent/scripts/hermes_manager.sh status
```

4. **查看启动日志**:
```bash
tail -20 /home/xiaobai/.hermes/logs/wsl_auto_start.log
```

---

## 🔧 故障排查

### 问题 1: 服务启动失败

**症状**: 执行 `start` 命令后服务未运行

**排查步骤**:
```bash
# 1. 查看详细日志
tail -50 /home/xiaobai/.hermes/logs/wsl_auto_start.log

# 2. 检查端口占用
ss -tlnp | grep -E '9119|8080'

# 3. 检查虚拟环境
cd /home/xiaobai/hermes-agent
source .venv/bin/activate
python -c "import fastapi; print('OK')"

# 4. 手动启动测试
python gateway/run.py
```

### 问题 2: 自动启动不生效

**症状**: WSL 重启后服务未自动启动

**排查步骤**:
```bash
# 1. 检查 .bashrc 配置
grep -A 10 "Hermes Agent 自动启动" ~/.bashrc

# 2. 检查脚本权限
ls -la /home/xiaobai/hermes-agent/scripts/wsl_auto_start.sh

# 3. 手动执行自动启动脚本
/home/xiaobai/hermes-agent/scripts/wsl_auto_start.sh

# 4. 查看自动启动日志
tail -50 /home/xiaobai/.hermes/logs/wsl_auto_start.log
```

### 问题 3: 服务频繁重启

**症状**: 监控脚本反复重启某个服务

**解决方案**:
```bash
# 1. 查看重启计数
cat /tmp/hermes_restart_count

# 2. 重置重启计数
rm /tmp/hermes_restart_count

# 3. 检查服务日志
tail -100 /home/xiaobai/.hermes/logs/gateway.log

# 4. 临时禁用监控
pkill -f hermes_monitor.sh
```

### 问题 4: 端口冲突

**症状**: 启动时报端口已被占用

**解决方案**:
```bash
# 1. 查找占用端口的进程
ss -tlnp | grep 9119

# 2. 终止占用进程
kill <PID>

# 3. 或者修改配置端口
# 编辑 hermes_manager.sh，修改端口配置
```

### 问题 5: tmux 会话残留

**症状**: 无法创建新的 tmux 会话

**解决方案**:
```bash
# 1. 列出所有会话
tmux list-sessions

# 2. 清理残留会话
tmux kill-session -t hermes-gateway
tmux kill-session -t hermes-dashboard
tmux kill-session -t hermes-webui

# 3. 或者清理所有 hermes 会话
tmux list-sessions | grep hermes | cut -d: -f1 | xargs -I {} tmux kill-session -t {}
```

---

## 📊 监控与告警

### 实时监控

```bash
# 使用 htop 监控进程
htop -p $(pgrep -d, -f "gateway|dashboard|webui")

# 监控端口
watch -n 1 'ss -tlnp | grep -E "9119|8080"'

# 监控日志
tail -f /home/xiaobai/.hermes/logs/*.log
```

### 健康检查脚本

创建定时任务（可选）:
```bash
# 编辑 crontab
crontab -e

# 添加每小时健康检查
0 * * * * /home/xiaobai/hermes-agent/scripts/hermes_monitor.sh check >> /home/xiaobai/.hermes/logs/health_cron.log 2>&1
```

---

## 🎓 最佳实践

### 1. 启动顺序
```
1. Gateway (消息网关)
2. Dashboard (管理界面)
3. WebUI (用户界面)
```

### 2. 停止顺序
```
1. 停止接收新请求 (Gateway)
2. 停止 Web 界面 (WebUI, Dashboard)
3. 清理进程和锁文件
```

### 3. 更新流程
```bash
# 1. 停止所有服务
./hermes_manager.sh stop

# 2. 更新代码
cd /home/xiaobai/hermes-agent
git pull

# 3. 更新依赖
source .venv/bin/activate
pip install -r requirements.txt

# 4. 重新启动服务
./hermes_manager.sh start

# 5. 验证
./hermes_manager.sh health
```

### 4. 备份配置
```bash
# 备份重要配置
cp ~/.hermes/config.yaml ~/.hermes/config.yaml.backup
cp ~/.hermes/.env ~/.hermes/.env.backup

# 备份脚本
cp -r /home/xiaobai/hermes-agent/scripts/ ~/backup/hermes_scripts/
```

---

## 📞 支持与反馈

### 日志位置
- 启动日志：`/home/xiaobai/.hermes/logs/wsl_auto_start.log`
- Gateway 日志：`/home/xiaobai/.hermes/logs/gateway.log`
- Dashboard 日志：`/home/xiaobai/.hermes/logs/dashboard.log`
- WebUI 日志：`/home/xiaobai/.hermes/logs/webui.log`
- 监控日志：`/home/xiaobai/.hermes/logs/hermes_monitor.log`

### 配置文件
- 主配置：`~/.hermes/config.yaml`
- 环境变量：`~/.hermes/.env`
- 脚本配置：`/home/xiaobai/hermes-agent/scripts/*.sh`

---

## 📝 更新日志

### v1.0.0 (2026-04-22)
- ✅ 创建统一启动脚本 `hermes_manager.sh`
- ✅ 创建 WSL 自动启动脚本 `wsl_auto_start.sh`
- ✅ 创建进程监控脚本 `hermes_monitor.sh`
- ✅ 集成到 `.bashrc` 实现自动启动
- ✅ 完整的使用文档和故障排查指南

---

**最后更新**: 2026-04-22  
**维护者**: Hermes Team
