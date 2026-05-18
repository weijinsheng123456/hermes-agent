# Hermes Agent 错误监控系统

## 功能

- ✅ 自动监控日志文件中的错误模式
- ✅ 统计错误频率和类型分布
- ✅ 超过阈值时发送微信告警
- ✅ 生成错误分析报告
- ✅ 支持持续监控和单次运行

## 安装

```bash
cd ~/hermes-agent/scripts/monitoring
./install.sh
```

## 使用

### 单次运行

```bash
python error_monitor.py --once
```

### 持续监控

```bash
python error_monitor.py --interval 300  # 每 5 分钟检查一次
```

### 定时任务

系统会自动创建每小时运行一次的定时任务

## 告警阈值

| 指标 | 阈值 | 说明 |
|------|------|------|
| error_count_1h | 10 | 1 小时内错误数 |
| error_count_24h | 50 | 24 小时内错误数 |
| same_error_count | 5 | 同一错误重复次数 |
| critical_error_count | 1 | 严重错误次数 |

## 错误分类

- `api_connection` - API 连接失败
- `api_auth` - API 认证失败
- `api_rate_limit` - API 频率限制
- `tool_error` - 工具执行错误
- `system_error` - 系统级错误
- `permission` - 权限相关错误

## 文件结构

```
monitoring/
├── error_monitor.py    # 主监控脚本
├── install.sh          # 安装脚本
├── cron_config.yaml    # 定时任务配置
└── README.md           # 本文档
```

## 输出

- 日志文件：`~/.hermes/logs/hermes.log`
- 错误报告：`~/.hermes/logs/error_report.json`
- 状态文件：`~/.hermes/logs/monitor_state.json`

---

*版本：1.0 | 创建日期：2026-04-22*
