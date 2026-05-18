#!/bin/bash
# Hermes 健康监控脚本 - 带微信告警推送
LOG_FILE=~/hermes-agent/watchdog.log
ALERT_SENT_FILE=~/.hermes/.last_api_alert
HERMES_HOME=~/.hermes
SCRIPT_DIR=~/hermes-agent

echo "$(date '+%Y-%m-%d %H:%M:%S'): Running health check..." >> $LOG_FILE

# 发送微信告警的函数
send_wechat_alert() {
    local message="$1"
    cd $SCRIPT_DIR && source .venv/bin/activate && python3 send_wechat_alert.py "$message" >> $LOG_FILE 2>&1
}

# 检查 Gateway 进程
if ! pgrep -f "hermes gateway" > /dev/null; then
    echo "$(date '+%Y-%m-%d %H:%M:%S'): Gateway is down! Attempting restart..." >> $LOG_FILE
    cd ~/hermes-agent && source .venv/bin/activate && nohup hermes gateway run >> $LOG_FILE 2>&1 &
    
    # 发送微信告警
    ALERT_MSG="【Hermes 告警】Gateway 进程异常，已自动重启。时间：$(date '+%Y-%m-%d %H:%M:%S')"
    send_wechat_alert "$ALERT_MSG"
fi

# 检查 API 连通性（200 或 401 均视为可达）
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 https://dashscope.aliyuncs.com/)
if ! echo "$HTTP_CODE" | grep -qE "200|401"; then
    echo "$(date '+%Y-%m-%d %H:%M:%S'): API connection issue! (HTTP $HTTP_CODE)" >> $LOG_FILE
    
    # 检查是否在收敛期内（10 分钟=600 秒）
    SHOULD_ALERT=true
    if [ -f "$ALERT_SENT_FILE" ]; then
        LAST_ALERT=$(cat "$ALERT_SENT_FILE")
        NOW=$(date +%s)
        DIFF=$((NOW - LAST_ALERT))
        if [ $DIFF -lt 600 ]; then
            SHOULD_ALERT=false
            echo "$(date '+%Y-%m-%d %H:%M:%S'): API 告警在收敛期内，跳过推送（距上次告警 ${DIFF}秒）" >> $LOG_FILE
        fi
    fi
    
    if [ "$SHOULD_ALERT" = true ]; then
        ALERT_MSG="【Hermes 告警】API 连接异常（HTTP $HTTP_CODE），请检查网络。时间：$(date '+%Y-%m-%d %H:%M:%S')"
        send_wechat_alert "$ALERT_MSG"
        date +%s > "$ALERT_SENT_FILE"
        echo "$(date '+%Y-%m-%d %H:%M:%S'): API 告警已推送，标记文件已更新" >> $LOG_FILE
    fi
else
    echo "$(date '+%Y-%m-%d %H:%M:%S'): API 连接正常 (HTTP $HTTP_CODE)" >> $LOG_FILE
fi

# 检查磁盘使用率
DISK_USAGE=$(df -h ~ | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 80 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S'): Disk usage warning! (${DISK_USAGE}%)" >> $LOG_FILE
    ALERT_MSG="【Hermes 告警】磁盘使用率过高（${DISK_USAGE}%），请清理空间。时间：$(date '+%Y-%m-%d %H:%M:%S')"
    send_wechat_alert "$ALERT_MSG"
fi

echo "$(date '+%Y-%m-%d %H:%M:%S'): Health check completed." >> $LOG_FILE
