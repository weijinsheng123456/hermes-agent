# Hermes 系统监控定时任务

## 每小时健康检查

```bash
# 编辑 crontab
crontab -e

# 添加以下行 (每小时执行一次)
0 * * * * cd ~/hermes-agent && source .venv/bin/activate && python scripts/monitor_hermes.py >> ~/hermes-agent/logs/monitor.log 2>&1
```

## 每日报告

```bash
# 每天早上 8 点生成报告
0 8 * * * cd ~/hermes-agent && source .venv/bin/activate && python scripts/generate_daily_report.py >> ~/hermes-agent/logs/daily.log 2>&1
```

## 每周备份检查

```bash
# 每周一检查备份完整性
0 9 * * 1 cd ~/hermes-agent && source .venv/bin/activate && python scripts/verify_backups.py >> ~/hermes-agent/logs/backup.log 2>&1
```
