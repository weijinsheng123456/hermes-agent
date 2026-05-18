#!/bin/bash
# ============================================================================
# Hermes Agent WSL 启动时自动启动脚本 (增强版)
# 功能：WSL 启动时自动启动所有 Hermes 服务 + 监控服务
# 版本：v2.0 - 集成监控告警闭环
# ============================================================================

# 配置
LOG_FILE="/home/xiaobai/.hermes/logs/wsl_auto_start.log"
LOCK_FILE="/tmp/hermes_auto_start.lock"
RESTART_COUNT_FILE="/tmp/hermes_restart_count"
WECHAT_NOTIFY_SCRIPT="/home/xiaobai/.hermes/scripts/wxpusher.py"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 初始化
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "[$timestamp] $1" | tee -a "$LOG_FILE"
}

# 发送微信通知
send_wechat_notification() {
    local title="$1"
    local content="$2"
    local level="${3:-INFO}"  # INFO, SUCCESS, WARNING, ERROR
    
    # 检查是否配置了 WxPusher
    if [ ! -f "/home/xiaobai/.hermes/.env" ]; then
        log "${YELLOW}⚠️  .env 文件不存在，跳过微信通知${NC}"
        return 1
    fi
    
    local app_token=$(grep "^WX_PUSHER_APP_TOKEN=" /home/xiaobai/.hermes/.env 2>/dev/null | cut -d'=' -f2)
    local uid=$(grep "^WX_PUSHER_UID=" /home/xiaobai/.hermes/.env 2>/dev/null | cut -d'=' -f2)
    
    if [ -z "$app_token" ] || [ -z "$uid" ]; then
        log "${YELLOW}⚠️  WxPusher 未配置，跳过微信通知${NC}"
        return 1
    fi
    
    log "${BLUE}📱 发送微信通知：$title${NC}"
    
    # 使用 WxPusher 脚本发送
    if [ -x "$WECHAT_NOTIFY_SCRIPT" ]; then
        python3 "$WECHAT_NOTIFY_SCRIPT" send "$title" "$content" --level "$level" 2>/dev/null
        return $?
    else
        # 备用方案：直接使用 curl
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
        return $?
    fi
}

# 防止重复执行
if [ -f "$LOCK_FILE" ]; then
    if [ $(find "$LOCK_FILE" -mmin +5 2>/dev/null) ]; then
        log "${YELLOW}⚠️  检测到 stale lock file，清理中...${NC}"
        rm -f "$LOCK_FILE"
    else
        log "${BLUE}ℹ️  自动启动流程已在运行，跳过${NC}"
        exit 0
    fi
fi

# 创建锁文件
touch "$LOCK_FILE"

# 记录启动时间
START_TIME=$(date '+%Y-%m-%d %H:%M:%S')
log "${GREEN}========================================${NC}"
log "${GREEN}🚀 WSL 启动，开始 Hermes 自动启动流程...${NC}"
log "${GREEN}========================================${NC}"

# 等待网络就绪（最多等待 30 秒）
log "${BLUE}🌐 等待网络就绪...${NC}"
network_ready=false
for i in {1..30}; do
    if ping -c 1 -W 1 8.8.8.8 > /dev/null 2>&1; then
        log "${GREEN}✅ 网络已就绪${NC}"
        network_ready=true
        break
    fi
    if [ $i -eq 30 ]; then
        log "${YELLOW}⚠️  网络等待超时，继续启动...${NC}"
    fi
    sleep 1
done

# 等待 5 秒确保系统稳定
sleep 5

# 切换到 Hermes 目录
cd /home/xiaobai/hermes-agent || {
    log "${RED}❌ 无法切换到 Hermes 目录${NC}"
    send_wechat_notification "WSL 启动失败" "无法切换到 Hermes 目录" "ERROR"
    rm -f "$LOCK_FILE"
    exit 1
}

# 激活虚拟环境
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate || {
        log "${RED}❌ 虚拟环境激活失败${NC}"
        send_wechat_notification "WSL 启动失败" "虚拟环境激活失败" "ERROR"
        rm -f "$LOCK_FILE"
        exit 1
    }
else
    log "${RED}❌ 虚拟环境不存在${NC}"
    send_wechat_notification "WSL 启动失败" "虚拟环境不存在 (.venv)" "ERROR"
    rm -f "$LOCK_FILE"
    exit 1
fi

# 检查进程是否运行
check_running() {
    local pattern=$1
    local name=$2
    
    if pgrep -f "$pattern" > /dev/null 2>&1; then
        local pid=$(pgrep -f "$pattern" | head -1)
        log "${GREEN}✅ $name 已在运行 (PID: $pid)，跳过启动${NC}"
        return 0
    fi
    return 1
}

# 检查端口是否被占用
check_port_occupied() {
    local port=$1
    local name=$2
    
    if ss -tlnp 2>/dev/null | grep -q ":$port "; then
        log "${GREEN}✅ $name 端口 $port 已被占用，跳过启动${NC}"
        return 0
    fi
    return 1
}

# 启动 Gateway
start_gateway() {
    log "${BLUE}🚀 启动 Gateway...${NC}"
    
    if check_running "gateway/run.py" "Gateway"; then
        return 0
    fi
    
    # 清理旧 tmux 会话
    if tmux has-session -t hermes-gateway 2>/dev/null; then
        tmux kill-session -t hermes-gateway
    fi
    
    # 启动 Gateway
    tmux new-session -d -s hermes-gateway \
        "cd /home/xiaobai/hermes-agent && source .venv/bin/activate && python gateway/run.py >> /home/xiaobai/.hermes/logs/gateway.log 2>&1"
    
    sleep 5
    
    if check_running "gateway/run.py" "Gateway"; then
        return 0
    else
        log "${RED}❌ Gateway 启动失败${NC}"
        send_wechat_notification "Gateway 启动失败" "WSL 启动时 Gateway 未能成功启动，请检查日志" "ERROR"
        return 1
    fi
}

# 启动 Dashboard
start_dashboard() {
    log "${BLUE}🚀 启动 Dashboard...${NC}"
    
    if check_port_occupied 9119 "Dashboard"; then
        return 0
    fi
    
    # 清理旧 tmux 会话
    if tmux has-session -t hermes-dashboard 2>/dev/null; then
        tmux kill-session -t hermes-dashboard
    fi
    
    # 设置环境变量
    export HERMES_WEB_DIST="/home/xiaobai/hermes-agent/hermes_cli/web_dist"
    
    # 启动 Dashboard
    tmux new-session -d -s hermes-dashboard \
        "cd /home/xiaobai/hermes-agent && source .venv/bin/activate && HERMES_WEB_DIST=$HERMES_WEB_DIST uvicorn hermes_cli.web_server:app --host 127.0.0.1 --port 9119 --log-level warning >> /home/xiaobai/.hermes/logs/dashboard.log 2>&1"
    
    sleep 5
    
    if check_port_occupied 9119 "Dashboard"; then
        return 0
    else
        log "${RED}❌ Dashboard 启动失败${NC}"
        send_wechat_notification "Dashboard 启动失败" "WSL 启动时 Dashboard 未能成功启动 (端口 9119)" "ERROR"
        return 1
    fi
}

# 启动 WebUI
start_webui() {
    log "${BLUE}🚀 启动 WebUI...${NC}"
    
    if check_port_occupied 8080 "WebUI"; then
        return 0
    fi
    
    # 清理旧 tmux 会话
    if tmux has-session -t hermes-webui 2>/dev/null; then
        tmux kill-session -t hermes-webui
    fi
    
    # 启动 WebUI
    tmux new-session -d -s hermes-webui \
        "cd /home/xiaobai/hermes-agent && source .venv/bin/activate && python -m uvicorn hermes_webui.server:app --host 0.0.0.0 --port 8080 --log-level warning >> /home/xiaobai/.hermes/logs/webui.log 2>&1"
    
    sleep 5
    
    if check_port_occupied 8080 "WebUI"; then
        return 0
    else
        log "${RED}❌ WebUI 启动失败${NC}"
        send_wechat_notification "WebUI 启动失败" "WSL 启动时 WebUI 未能成功启动 (端口 8080)" "ERROR"
        return 1
    fi
}

# 启动监控服务
start_monitor() {
    log "${BLUE}🚀 启动监控服务...${NC}"
    
    if pgrep -f "hermes_monitor.sh run" > /dev/null 2>&1; then
        log "${GREEN}✅ 监控服务已在运行，跳过启动${NC}"
        return 0
    fi
    
    # 启动监控脚本
    if [ -x "/home/xiaobai/hermes-agent/scripts/hermes_monitor.sh" ]; then
        /home/xiaobai/hermes-agent/scripts/hermes_monitor.sh start
        sleep 3
        
        if pgrep -f "hermes_monitor.sh run" > /dev/null 2>&1; then
            log "${GREEN}✅ 监控服务启动成功${NC}"
            return 0
        else
            log "${RED}❌ 监控服务启动失败${NC}"
            send_wechat_notification "监控服务启动失败" "WSL 启动时监控服务未能成功启动" "ERROR"
            return 1
        fi
    else
        log "${YELLOW}⚠️  监控脚本不存在或不可执行${NC}"
        return 1
    fi
}

# 执行启动
log "${BLUE}----------------------------------------${NC}"

# 检查是否需要启动（可以通过环境变量控制）
if [ "${HERMES_AUTO_START_DISABLE}" = "1" ]; then
    log "${YELLOW}ℹ️  自动启动已禁用 (HERMES_AUTO_START_DISABLE=1)${NC}"
    rm -f "$LOCK_FILE"
    exit 0
fi

# 只在新启动的 WSL 会话中启动（通过检查 tmux 是否已有会话）
if tmux has-session -t hermes-gateway 2>/dev/null; then
    log "${YELLOW}ℹ️  检测到已有 tmux 会话，可能是 WSL 重启而非新启动${NC}"
    log "${YELLOW}ℹ️  跳过自动启动，避免重复${NC}"
    rm -f "$LOCK_FILE"
    exit 0
fi

# 执行各服务启动
errors=0

start_gateway || ((errors++))
sleep 2
start_dashboard || ((errors++))
sleep 2
start_webui || ((errors++))
sleep 2
start_monitor || ((errors++))

# 最终状态检查
log "${BLUE}----------------------------------------${NC}"
log "${BLUE}📊 启动完成状态:${NC}"

gateway_status="❌ 未运行"
dashboard_status="❌ 未运行"
webui_status="❌ 未运行"
monitor_status="❌ 未运行"

if pgrep -f "gateway/run.py" > /dev/null 2>&1; then
    gateway_status="✅ 运行中"
fi

if ss -tlnp 2>/dev/null | grep -q ":9119 "; then
    dashboard_status="✅ 运行中"
fi

if ss -tlnp 2>/dev/null | grep -q ":8080 "; then
    webui_status="✅ 运行中"
fi

if pgrep -f "hermes_monitor.sh run" > /dev/null 2>&1; then
    monitor_status="✅ 运行中"
fi

log "  Gateway:  $gateway_status"
log "  Dashboard: $dashboard_status"
log "  WebUI:    $webui_status"
log "  Monitor:  $monitor_status"

END_TIME=$(date '+%Y-%m-%d %H:%M:%S')
log "${GREEN}========================================${NC}"
log "${GREEN}✅ WSL 自动启动完成${NC}"
log "${GREEN}========================================${NC}"
log ""

# 清理锁文件
rm -f "$LOCK_FILE"

# 发送启动通知
if [ $errors -eq 0 ]; then
    # 全部成功
    message="所有服务启动成功：\n"
    message+="• Gateway: 运行中\n"
    message+="• Dashboard: 运行中 (端口 9119)\n"
    message+="• WebUI: 运行中 (端口 8080)\n"
    message+="• Monitor: 运行中"
    
    send_wechat_notification "WSL 启动成功" "$message" "SUCCESS"
else
    # 部分失败
    message="启动完成，但发现 $errors 个问题：\n"
    message+="• Gateway: $gateway_status\n"
    message+="• Dashboard: $dashboard_status\n"
    message+="• WebUI: $webui_status\n"
    message+="• Monitor: $monitor_status\n\n"
    message+="请检查日志：$LOG_FILE"
    
    send_wechat_notification "WSL 启动完成（部分失败）" "$message" "WARNING"
fi

exit 0
