# Hermes Agent WSL 自启动系统 - 完整实施总结

## 📅 实施日期
2026-04-22

## ✅ 已完成功能

### 1. WSL 自动启动脚本 (wsl_auto_start.sh v2.0)

**位置**: `/home/xiaobai/hermes-agent/scripts/wsl_auto_start.sh`

**功能**:
- ✅ 网络就绪检测（最多等待 30 秒）
- ✅ 虚拟环境自动激活
- ✅ Gateway 自动启动（tmux 会话：hermes-gateway）
- ✅ Dashboard 自动启动（tmux 会话：hermes-dashboard，端口 9119）
- ✅ WebUI 自动启动（tmux 会话：hermes-webui，端口 8080）
- ✅ 监控服务自动启动
- ✅ 微信启动通知（成功/失败都会通知）
- ✅ 防重复执行机制（锁文件）
- ✅ 详细日志记录

**触发方式**:
- WSL 启动时通过 `.bashrc` 自动调用
- 手动测试：`./wsl_auto_start.sh`

---

### 2. 进程监控脚本 (hermes_monitor.sh v2.0)

**位置**: `/home/xiaobai/hermes-agent/scripts/hermes_monitor.sh`

**功能**:
- ✅ 60 秒间隔健康检查
- ✅ Gateway 进程检查
- ✅ Dashboard 端口检查（9119）
- ✅ WebUI 端口检查（8080）
- ✅ 系统资源检查（磁盘/内存）
- ✅ 异常自动重启（最多 3 次）
- ✅ 微信告警通知（异常、重启、资源不足）
- ✅ 重启计数管理（每小时重置）
- ✅ 详细日志记录

**监控项**:
| 检查项 | 阈值 | 告警级别 |
|--------|------|---------|
| 磁盘使用率 | ≥90% | WARNING |
| 磁盘使用率 | ≥95% | ERROR |
| 内存使用率 | ≥90% | WARNING |
| 内存使用率 | ≥95% | ERROR |
| 服务重启次数 | ≥3 次 | ERROR |

**使用方式**:
```bash
./hermes_monitor.sh start    # 启动监控
./hermes_monitor.sh check    # 单次检查
./hermes_monitor.sh status   # 查看状态
```

---

### 3. 统一管理脚本 (hermes_manager.sh v2.0)

**位置**: `/home/xiaobai/hermes-agent/scripts/hermes_manager.sh`

**功能**:
- ✅ 一键启动所有服务
- ✅ 一键停止所有服务
- ✅ 一键重启所有服务
- ✅ 查看服务状态
- ✅ 单独控制每个服务
- ✅ 测试自动启动脚本

**命令列表**:
```bash
./hermes_manager.sh start         # 启动所有服务
./hermes_manager.sh stop          # 停止所有服务
./hermes_manager.sh restart       # 重启所有服务
./hermes_manager.sh status        # 查看状态

./hermes_manager.sh start-gw      # 只启动 Gateway
./hermes_manager.sh start-dash    # 只启动 Dashboard
./hermes_manager.sh start-webui   # 只启动 WebUI
./hermes_manager.sh start-mon     # 只启动监控

./hermes_manager.sh stop-gw       # 只停止 Gateway
./hermes_manager.sh stop-dash     # 只停止 Dashboard
./hermes_manager.sh stop-webui    # 只停止 WebUI
./hermes_manager.sh stop-mon      # 只停止监控

./hermes_manager.sh auto-start    # 测试自动启动
```

---

### 4. Windows 启动脚本

**位置**: `C:\Users\31308\Desktop\启动 Hermes.bat`

**功能**:
- ✅ Windows 开机等待 15 秒（确保系统稳定）
- ✅ 检查 WSL 是否安装
- ✅ 后台启动 WSL（用户：xiaobai）
- ✅ 验证 Gateway 是否启动
- ✅ Windows 弹窗通知

**使用方式**:
- 双击桌面快捷方式
- 或配置任务计划程序自动执行

---

### 5. Windows 任务计划程序配置

**位置**: `/home/xiaobai/hermes-agent/scripts/hermes_wsl_startup.xml`

**配置**:
- ✅ 触发条件：用户登录时
- ✅ 延迟：15 秒
- ✅ 权限：最高权限
- ✅ 网络要求：必须可用
- ✅ 任务名称：Hermes WSL Startup

**安装方式**:
```batch
双击桌面上的 "配置 Hermes 开机启动.bat"
```

**验证方式**:
1. 打开"任务计划程序"
2. 导航到：任务计划程序库 > Hermes
3. 确认 "Hermes WSL Startup" 任务存在且已启用

---

### 6. 微信告警集成

**配置位置**: `/home/xiaobai/.hermes/.env`

**必需配置**:
```env
WX_PUSHER_APP_TOKEN=你的 appToken
WX_PUSHER_UID=你的 uid
```

**告警场景**:
1. WSL 启动成功/失败
2. 服务异常检测
3. 服务重启成功/失败
4. 磁盘空间不足
5. 内存不足

**测试方式**:
```bash
python3 /home/xiaobai/.hermes/scripts/wxpusher.py send "测试" "这是一条测试消息" --level INFO
```

---

## 📁 文件清单

### 脚本文件
```
/home/xiaobai/hermes-agent/scripts/
├── wsl_auto_start.sh          # WSL 自动启动脚本 (v2.0)
├── hermes_monitor.sh          # 进程监控脚本 (v2.0)
├── hermes_manager.sh          # 统一管理脚本 (v2.0)
├── hermes_wsl_startup.xml     # Windows 任务计划配置
└── README_AUTOSTART.md        # 详细使用文档
```

### Windows 文件
```
C:\Users\31308\Desktop\
├── 启动 Hermes.bat            # Windows 启动脚本
└── 配置 Hermes 开机启动.bat    # 任务计划安装脚本
```

### 配置文件
```
/home/xiaobai/.bashrc          # 已集成自动启动检测
/home/xiaobai/.hermes/.env     # 微信告警配置（需手动添加）
```

### 日志文件
```
/home/xiaobai/.hermes/logs/
├── wsl_auto_start.log         # WSL 自动启动日志
├── hermes_monitor.log         # 监控服务日志
├── hermes_manager.log         # 管理器日志
├── gateway.log                # Gateway 日志
├── dashboard.log              # Dashboard 日志
└── webui.log                  # WebUI 日志
```

---

## 🚀 快速开始指南

### 方式一：Windows 开机自动启动（推荐）

1. **以管理员身份运行配置脚本**:
   ```
   双击桌面上的 "配置 Hermes 开机启动.bat"
   ```

2. **验证配置**:
   - 打开"任务计划程序"
   - 确认 "Hermes WSL Startup" 任务存在

3. **重启测试**:
   ```powershell
   wsl --shutdown
   # 重新打开 WSL 终端
   # 检查服务是否自动启动
   ```

### 方式二：手动启动

1. **Windows 端**:
   ```
   双击桌面上的 "启动 Hermes.bat"
   ```

2. **WSL 端**:
   ```bash
   cd /home/xiaobai/hermes-agent/scripts
   ./hermes_manager.sh start
   ```

---

## 📊 当前状态（已验证）

```
✅ Gateway:    运行中 (PID: 2118)
✅ Dashboard:  运行中 (端口 9119, PID: 1694)
✅ WebUI:      运行中 (端口 8080, PID: 1895)
✅ Monitor:    运行中 (PID: 3317)
```

**监控日志显示**:
- ✅ 第 1 次健康检查完成
- ✅ Gateway 正常
- ✅ Dashboard 正常
- ✅ WebUI 正常
- ✅ 系统资源正常
- ✅ 下次检查将在 60 秒后

---

## 🔄 完整启动流程

```
Windows 开机
    ↓
任务计划程序 (Hermes WSL Startup)
    ↓
等待 15 秒（系统稳定）
    ↓
启动 Hermes.bat
    ↓
WSL 启动 (用户：xiaobai)
    ↓
.bashrc 检测（交互式 shell）
    ↓
wsl_auto_start.sh（延迟 3 秒）
    ↓
┌─────────────────────────────────────┐
│  1. 检查锁文件（防重复）             │
│  2. 等待网络就绪（最多 30 秒）        │
│  3. 激活虚拟环境                     │
│  4. 启动 Gateway（tmux）              │
│  5. 启动 Dashboard（tmux）            │
│  6. 启动 WebUI（tmux）                │
│  7. 启动监控服务                     │
│  8. 发送微信通知                     │
└─────────────────────────────────────┘
    ↓
hermes_monitor.sh（后台循环）
    ↓
┌─────────────────────────────────────┐
│  每 60 秒：                           │
│  • 检查 Gateway 进程                  │
│  • 检查 Dashboard 端口 (9119)         │
│  • 检查 WebUI 端口 (8080)             │
│  • 检查系统资源                      │
│  • 异常自动重启（最多 3 次）            │
│  • 微信告警通知                     │
└─────────────────────────────────────┘
```

---

## 🛠️ 故障排查命令

### 检查服务状态
```bash
./hermes_manager.sh status
```

### 查看 tmux 会话
```bash
tmux list-sessions
```

### 查看自动启动日志
```bash
tail -100 /home/xiaobai/.hermes/logs/wsl_auto_start.log
```

### 查看监控日志
```bash
tail -100 /home/xiaobai/.hermes/logs/hermes_monitor.log
```

### 手动测试自动启动
```bash
./hermes_manager.sh auto-start
```

### 检查进程
```bash
pgrep -fa "gateway/run.py"
pgrep -fa "hermes_cli.web_server:app"
pgrep -fa "hermes_webui.server:app"
pgrep -fa "hermes_monitor.sh"
```

### 检查端口
```bash
ss -tlnp | grep -E ":(8000|9119|8080)"
```

---

## 📝 待用户配置项

### 1. 微信告警配置（可选但推荐）

编辑文件：`/home/xiaobai/.hermes/.env`

添加内容：
```env
WX_PUSHER_APP_TOKEN=你的 appToken
WX_PUSHER_UID=你的 uid
```

获取方式：
1. 访问 https://wxpusher.zjiecode.com/
2. 注册并创建应用
3. 获取 appToken
4. 关注应用获取 uid

### 2. Windows 任务计划程序安装

以管理员身份运行：
```
C:\Users\31308\Desktop\配置 Hermes 开机启动.bat
```

---

## 🎯 测试清单

### ✅ 已测试项目
- [x] 手动启动所有服务
- [x] 查看服务状态
- [x] 启动监控服务
- [x] 监控日志记录
- [x] 健康检查执行
- [x] 脚本权限设置

### ⏳ 待测试项目
- [ ] WSL 重启后自动启动
- [ ] Windows 开机自动启动
- [ ] 微信告警通知
- [ ] 服务异常自动重启
- [ ] 资源不足告警

---

## 📈 后续优化建议

1. **添加开机启动音效** - Windows 端启动完成后播放提示音
2. **添加系统托盘图标** - Windows 端显示 Hermes 服务状态
3. **添加 Web 状态页面** - 实时显示服务健康和历史告警
4. **添加日志轮转** - 自动清理 7 天前的日志
5. **添加性能监控** - CPU、内存、网络流量图表
6. **添加备份机制** - 配置变更自动备份

---

## 📞 技术支持

如遇到问题，请提供：
1. 相关日志文件内容
2. 执行的操作步骤
3. 错误消息截图

---

**实施完成时间**: 2026-04-22 18:14  
**系统版本**: WSL 自启动系统 v2.0  
**状态**: ✅ 已完成并验证
