#!/bin/bash
# ============================================================================
# Hermes Agent 进程监控与自动重启脚本
# 功能：监控所有 Hermes 服务，异常时自动重启 + 微信告警
# 版本：v2.0 - 集成微信通知
# ============================================================================

# 配置
LOG_FILE="/home/xiaobai/.hermes/logs/hermes_monitor.log"
PID_DIR="/home/xiaobai/.hermes/pids"
HEALTH_CHECK_INTERVAL=60  # 健康检查间隔（秒）
MAX_RESTART_ATTEMPTS=3    # 最大重启尝试次数
RESTART_COOLDOWN=30       # 重启冷却时间（秒）

# 重启计数文件
RESTART_COUNT_FILE="/tmp/hermes_restart_count"

# 微信通知配置
WECHAT_NOTIFY_SCRIPT="/home/xiaobai/.hermes/scripts/wxpusher.py"
WECHAT_ENABLED=false

# 检查微信配置
if [ -f "/home/xiaobai/.hermes/.env" ]; then
    if grep -q "^WX_PUSHER_APP_TOKEN=" /home/xiaobai/.hermes/.env && \
       grep -q "^WX_PUSHER_UID=" /home/xiaobai/.hermes/.env; then
        WECHAT_ENABLED=true
    fi
fi

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 初始化
mkdir -p "$PID_DIR"

log() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "[$timestamp] $1" | tee -a "$LOG_FILE"
}

# 发送微信通知
send_wechat_alert() {
    local title="$1"
    local content="$2"
    local level="${3:-WARNING}"  # INFO, SUCCESS, WARNING, ERROR
    
    if [ "$WECHAT_ENABLED" = false ]; then
        return 0
    fi
    
    log "${BLUE}📱 发送微信告警：$title${NC}"
    
    # 使用 WxPusher 脚本发送
    if [ -x "$WECHAT_NOTIFY_SCRIPT" ]; then
        python3 "$WECHAT_NOTIFY_SCRIPT" send "$title" "$content" --level "$level" 2>/dev/null
    else
        # 备用方案：直接使用 curl
        local app_token=$(grep "^WX_PUSHER_APP_TOKEN=" /home/xiaobai/.hermes/.env 2>/dev/null | cut -d'=' -f2)
        local uid=$(grep "^WX_PUSHER_UID=" /home/xiaobai/.hermes/.env 2>/dev/null | cut -d'=' -f2)
        
        if [ -n "$app_token" ] && [ -n "$uid" ]; then
            local message="[$level] $title\n$content"
            curl -s -X POST "https://wxpusher.zjiecode.com/api/send/message" \
                -H "Content-Type: application/json" \
                -d "{
                    \"appToken\": \"$app_token\",
                    \"content\": \"$message\",
                    \"summary\": \"$title\",
                    \"contentType\": 1,
                    \"uids\": [\"$uid\"]
                }" > /dev/null
        fi
    fi
}

# 获取重启计数
get_restart_count() {
    local service=$1
    if [ -f "$RESTART_COUNT_FILE" ]; then
        grep "^$service:" "$RESTART_COUNT_FILE" 2>/dev/null | cut -d: -f2 || echo "0"
    else
        echo "0"
    fi
}

# 设置重启计数
set_restart_count() {
    local service=$1
    local count=$2
    
    if [ -f "$RESTART_COUNT_FILE" ]; then
        if grep -q "^$service:" "$RESTART_COUNT_FILE" 2>/dev/null; then
            sed -i "s/^$service:.*/$service:$count/" "$RESTART_COUNT_FILE"
        else
            echo "$service:$count" >> "$RESTART_COUNT_FILE"
        fi
    else
        echo "$service:$count" > "$RESTART_COUNT_FILE"
    fi
}

# 重置重启计数
reset_restart_count() {
    local service=$1
    if [ -f "$RESTART_COUNT_FILE" ]; then
        sed -i "/^$service:/d" "$RESTART_COUNT_FILE"
    fi
}

# 检查进程是否运行
check_process() {
    local pattern=$1
    pgrep -f "$pattern" > /dev/null 2>&1
    return $?
}

# 检查端口是否监听
check_port() {
    local port=$1
    ss -tlnp 2>/dev/null | grep -q ":$port "
    return $?
}

# 重启服务
restart_service() {
    local service=$1
    local start_cmd=$2
    local check_pattern=$3
    
    local count=$(get_restart_count "$service")
    
    if [ "$count" -ge "$MAX_RESTART_ATTEMPTS" ]; then
        log "${RED}❌ $service 已达到最大重启次数 ($MAX_RESTART_ATTEMPTS)，停止自动重启${NC}"
        send_wechat_alert "服务重启失败" "$service 已达到最大重启次数 ($MAX_RESTART_ATTEMPTS)，需要人工干预\n\n请检查日志：$LOG_FILE" "ERROR"
        return 1
    fi
    
    count=$((count + 1))
    set_restart_count "$service" "$count"
    
    log "${YELLOW}⚠️  $service 异常，尝试重启 (第 $count/$MAX_RESTART_ATTEMPTS 次)...${NC}"
    send_wechat_alert "服务异常告警" "$service 检测到异常，正在尝试重启 (第 $count/$MAX_RESTART_ATTEMPTS 次)" "WARNING"
    
    # 执行重启命令
    eval "$start_cmd" &
    
    # 等待启动
    sleep 10
    
    # 检查是否启动成功
    if eval "check_process '$check_pattern'"; then
        log "${GREEN}✅ $service 重启成功${NC}"
        reset_restart_count "$service"
        send_wechat_alert "服务重启成功" "$service 已成功重启并恢复运行" "SUCCESS"
        return 0
    else
        log "${RED}❌ $service 重启失败${NC}"
        send_wechat_alert "服务重启失败" "$service 重启失败，需要人工干预\n\n请检查日志：$LOG_FILE" "ERROR"
        return 1
    fi
}

# Gateway 健康检查
check_gateway() {
    log "${BLUE}🔍 检查 Gateway...${NC}"
    
    if ! check_process "gateway/run.py"; then
        log "${RED}❌ Gateway 进程未运行${NC}"
        restart_service "gateway" \
            "cd /home/xiaobai/hermes-agent && source .venv/bin/activate && python gateway/run.py >> /home/xiaobai/.hermes/logs/gateway.log 2>&1" \
            "gateway/run.py"
        return $?
    fi
    
    # 检查 Gateway 是否响应（可以添加 HTTP 检查）
    log "${GREEN}✅ Gateway 正常${NC}"
    return 0
}

# Dashboard 健康检查
check_dashboard() {
    log "${BLUE}🔍 检查 Dashboard...${NC}"
    
    if ! check_port 9119; then
        log "${RED}❌ Dashboard 端口 9119 未监听${NC}"
        restart_service "dashboard" \
            "cd /home/xiaobai/hermes-agent && source .venv/bin/activate && export HERMES_WEB_DIST=/home/xiaobai/hermes-agent/hermes_cli/web_dist && uvicorn hermes_cli.web_server:app --host 127.0.0.1 --port 9119 >> /home/xiaobai/.hermes/logs/dashboard.log 2>&1" \
            "hermes_cli.web_server:app"
        return $?
    fi
    
    log "${GREEN}✅ Dashboard 正常${NC}"
    return 0
}

# WebUI 健康检查
check_webui() {
    log "${BLUE}🔍 检查 WebUI...${NC}"
    
    if ! check_port 8080; then
        log "${RED}❌ WebUI 端口 8080 未监听${NC}"
        restart_service "webui" \
            "cd /home/xiaobai/hermes-agent && source .venv/bin/activate && python -m uvicorn hermes_webui.server:app --host 0.0.0.0 --port 8080 >> /home/xiaobai/.hermes/logs/webui.log 2>&1" \
            "hermes_webui.server:app"
        return $?
    fi
    
    log "${GREEN}✅ WebUI 正常${NC}"
    return 0
}

# 系统资源检查
check_resources() {
    log "${BLUE}🔍 检查系统资源...${NC}"
    
    # 磁盘检查
    local disk_usage=$(df /home | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$disk_usage" -ge 95 ]; then
        log "${RED}❌ 磁盘空间严重不足 (${disk_usage}%)${NC}"
        send_wechat_alert "磁盘空间严重不足" "系统磁盘使用率已达 ${disk_usage}%，可能导致服务异常\n\n建议立即清理日志文件或扩容" "ERROR"
        return 1
    elif [ "$disk_usage" -ge 90 ]; then
        log "${YELLOW}⚠️  磁盘空间不足 (${disk_usage}%)${NC}"
        send_wechat_alert "磁盘空间不足" "系统磁盘使用率已达 ${disk_usage}%，建议清理日志文件" "WARNING"
    fi
    
    # 内存检查
    local mem_usage=$(free | awk '/Mem:/ {printf "%.0f", $3/$2 * 100}')
    if [ "$mem_usage" -ge 95 ]; then
        log "${RED}❌ 内存严重不足 (${mem_usage}%)${NC}"
        send_wechat_alert "内存严重不足" "系统内存使用率已达 ${mem_usage}%，可能导致服务异常\n\n建议检查进程或增加内存" "ERROR"
        return 1
    elif [ "$mem_usage" -ge 90 ]; then
        log "${YELLOW}⚠️  内存不足 (${mem_usage}%)${NC}"
        send_wechat_alert "内存不足" "系统内存使用率已达 ${mem_usage}%" "WARNING"
    fi
    
    log "${GREEN}✅ 系统资源正常${NC}"
    return 0
}

# 清理过期重启计数
cleanup_restart_counts() {
    # 每小时重置一次计数（防止临时问题导致永久禁用）
    local hour=$(date +%H)
    if [ "$hour" = "00" ]; then
        rm -f "$RESTART_COUNT_FILE"
        log "${BLUE}🔄 已重置所有重启计数${NC}"
    fi
}

# 主监控循环
main_loop() {
    log "${GREEN}========================================${NC}"
    log "${GREEN}🚀 Hermes 监控服务启动${NC}"
    log "${GREEN}========================================${NC}"
    
    local check_count=0
    
    while true; do
        check_count=$((check_count + 1))
        log "${BLUE}----------------------------------------${NC}"
        log "${BLUE}📊 第 $check_count 次健康检查${NC}"
        
        # 执行检查
        check_gateway
        check_dashboard
        check_webui
        check_resources
        cleanup_restart_counts
        
        # 等待下次检查
        log "${BLUE}⏳ 下次检查将在 ${HEALTH_CHECK_INTERVAL} 秒后${NC}"
        sleep $HEALTH_CHECK_INTERVAL
    done
}

# 单次检查模式
single_check() {
    log "${BLUE}🔍 执行单次健康检查...${NC}"
    
    local errors=0
    
    check_gateway || ((errors++))
    check_dashboard || ((errors++))
    check_webui || ((errors++))
    check_resources || ((errors++))
    
    if [ $errors -eq 0 ]; then
        log "${GREEN}✅ 所有检查通过${NC}"
        return 0
    else
        log "${RED}❌ 发现 $errors 个问题${NC}"
        return 1
    fi
}

# 显示帮助
show_help() {
    cat << EOF
Hermes 进程监控器

用法：$0 [命令]

命令:
  start       启动监控服务（后台运行）
  check       执行单次健康检查
  status      显示监控状态
  help        显示帮助信息

示例:
  $0 start    # 启动后台监控
  $0 check    # 单次检查

EOF
}

# 主程序
case "${1:-start}" in
    start)
        # 检查是否已在运行（检查 run 模式，而不是 start 命令）
        if pgrep -f "hermes_monitor.sh run" > /dev/null 2>&1; then
            echo "监控服务已在运行"
            exit 0
        fi
        
        # 后台启动
        nohup "$0" run > /dev/null 2>&1 &
        sleep 2
        
        # 验证是否启动成功
        if pgrep -f "hermes_monitor.sh run" > /dev/null 2>&1; then
            echo "监控服务已启动 (PID: $(pgrep -f 'hermes_monitor.sh run' | head -1))"
        else
            echo "监控服务启动失败，请查看日志：$LOG_FILE"
            exit 1
        fi
        ;;
    run)
        main_loop
        ;;
    check)
        single_check
        ;;
    status)
        echo "监控状态:"
        if pgrep -f "hermes_monitor.sh run" > /dev/null 2>&1; then
            echo "  监控服务：运行中"
        else
            echo "  监控服务：未运行"
        fi
        
        if [ -f "$RESTART_COUNT_FILE" ]; then
            echo "  重启计数:"
            cat "$RESTART_COUNT_FILE" | while read line; do
                echo "    $line"
            done
        fi
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        show_help
        ;;
esac
