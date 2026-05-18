#!/bin/bash
# ============================================================================
# Hermes Agent 统一管理服务脚本
# 功能：一键启动/停止/重启/状态检查所有 Hermes 服务
# 版本：v2.0 - 集成监控和微信告警
# ============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 路径配置
HERMES_HOME="/home/xiaobai/hermes-agent"
VENV_PATH="$HERMES_HOME/.venv"
LOG_DIR="/home/xiaobai/.hermes/logs"
PID_DIR="/home/xiaobai/.hermes/pids"
SCRIPTS_DIR="$HERMES_HOME/scripts"

# 端口配置
GATEWAY_PORT="8000"
DASHBOARD_PORT="9119"
WEBUI_PORT="8080"

# 日志文件
LOG_FILE="$LOG_DIR/hermes_manager.log"
mkdir -p "$LOG_DIR" "$PID_DIR"

# ============================================================================
# 工具函数
# ============================================================================

log() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "[$timestamp] $1" | tee -a "$LOG_FILE"
}

check_port() {
    local port=$1
    ss -tlnp 2>/dev/null | grep -q ":$port "
    return $?
}

check_process() {
    local pattern=$1
    pgrep -f "$pattern" > /dev/null 2>&1
    return $?
}

get_pid() {
    local pattern=$1
    pgrep -f "$pattern" | head -1
}

# ============================================================================
# 服务控制函数
# ============================================================================

start_gateway() {
    log "${BLUE}🚀 启动 Hermes Gateway...${NC}"
    
    if check_process "gateway/run.py"; then
        log "${YELLOW}⚠️  Gateway 已在运行 (PID: $(get_pid 'gateway/run.py'))${NC}"
        return 0
    fi
    
    cd "$HERMES_HOME"
    source "$VENV_PATH/bin/activate"
    
    # 使用 tmux 启动 Gateway
    if tmux has-session -t hermes-gateway 2>/dev/null; then
        tmux kill-session -t hermes-gateway
    fi
    
    tmux new-session -d -s hermes-gateway \
        "cd $HERMES_HOME && source $VENV_PATH/bin/activate && python gateway/run.py 2>&1 | tee -a $LOG_DIR/gateway.log"
    
    sleep 3
    
    if check_process "gateway/run.py"; then
        local pid=$(get_pid "gateway/run.py")
        echo "$pid" > "$PID_DIR/gateway.pid"
        log "${GREEN}✅ Gateway 启动成功 (PID: $pid)${NC}"
        return 0
    else
        log "${RED}❌ Gateway 启动失败${NC}"
        return 1
    fi
}

start_dashboard() {
    log "${BLUE}🚀 启动官方 Dashboard (端口 $DASHBOARD_PORT)...${NC}"
    
    if check_port $DASHBOARD_PORT; then
        log "${YELLOW}⚠️  Dashboard 端口 $DASHBOARD_PORT 已被占用${NC}"
        return 0
    fi
    
    cd "$HERMES_HOME"
    source "$VENV_PATH/bin/activate"
    
    # 使用 tmux 启动 Dashboard
    if tmux has-session -t hermes-dashboard 2>/dev/null; then
        tmux kill-session -t hermes-dashboard
    fi
    
    export HERMES_WEB_DIST="/home/xiaobai/hermes-agent/hermes_cli/web_dist"
    
    tmux new-session -d -s hermes-dashboard \
        "cd $HERMES_HOME && source $VENV_PATH/bin/activate && HERMES_WEB_DIST=$HERMES_WEB_DIST uvicorn hermes_cli.web_server:app --host 127.0.0.1 --port $DASHBOARD_PORT --log-level warning 2>&1 | tee -a $LOG_DIR/dashboard.log"
    
    sleep 3
    
    if check_port $DASHBOARD_PORT; then
        local pid=$(get_pid "hermes_cli.web_server:app")
        echo "$pid" > "$PID_DIR/dashboard.pid"
        log "${GREEN}✅ Dashboard 启动成功 (PID: $pid)${NC}"
        return 0
    else
        log "${RED}❌ Dashboard 启动失败${NC}"
        return 1
    fi
}

start_webui() {
    log "${BLUE}🚀 启动 WebUI (端口 $WEBUI_PORT)...${NC}"
    
    if check_port $WEBUI_PORT; then
        log "${YELLOW}⚠️  WebUI 端口 $WEBUI_PORT 已被占用${NC}"
        return 0
    fi
    
    cd "$HERMES_HOME"
    source "$VENV_PATH/bin/activate"
    
    # 使用 tmux 启动 WebUI
    if tmux has-session -t hermes-webui 2>/dev/null; then
        tmux kill-session -t hermes-webui
    fi
    
    tmux new-session -d -s hermes-webui \
        "cd $HERMES_HOME && source $VENV_PATH/bin/activate && python -m uvicorn hermes_webui.server:app --host 0.0.0.0 --port $WEBUI_PORT --log-level warning 2>&1 | tee -a $LOG_DIR/webui.log"
    
    sleep 3
    
    if check_port $WEBUI_PORT; then
        local pid=$(get_pid "hermes_webui.server:app")
        echo "$pid" > "$PID_DIR/webui.pid"
        log "${GREEN}✅ WebUI 启动成功 (PID: $pid)${NC}"
        return 0
    else
        log "${RED}❌ WebUI 启动失败${NC}"
        return 1
    fi
}

start_monitor() {
    log "${BLUE}🚀 启动监控服务...${NC}"
    
    if pgrep -f "hermes_monitor.sh run" > /dev/null 2>&1; then
        log "${YELLOW}⚠️  监控服务已在运行${NC}"
        return 0
    fi
    
    if [ -x "$SCRIPTS_DIR/hermes_monitor.sh" ]; then
        "$SCRIPTS_DIR/hermes_monitor.sh" start
        sleep 3
        
        if pgrep -f "hermes_monitor.sh run" > /dev/null 2>&1; then
            log "${GREEN}✅ 监控服务启动成功${NC}"
            return 0
        else
            log "${RED}❌ 监控服务启动失败${NC}"
            return 1
        fi
    else
        log "${RED}❌ 监控脚本不存在或不可执行${NC}"
        return 1
    fi
}

stop_gateway() {
    log "${BLUE}🛑 停止 Gateway...${NC}"
    
    if tmux has-session -t hermes-gateway 2>/dev/null; then
        tmux kill-session -t hermes-gateway
        log "${GREEN}✅ Gateway 已停止${NC}"
    else
        log "${YELLOW}⚠️  Gateway 未运行${NC}"
    fi
}

stop_dashboard() {
    log "${BLUE}🛑 停止 Dashboard...${NC}"
    
    if tmux has-session -t hermes-dashboard 2>/dev/null; then
        tmux kill-session -t hermes-dashboard
        log "${GREEN}✅ Dashboard 已停止${NC}"
    else
        log "${YELLOW}⚠️  Dashboard 未运行${NC}"
    fi
}

stop_webui() {
    log "${BLUE}🛑 停止 WebUI...${NC}"
    
    if tmux has-session -t hermes-webui 2>/dev/null; then
        tmux kill-session -t hermes-webui
        log "${GREEN}✅ WebUI 已停止${NC}"
    else
        log "${YELLOW}⚠️  WebUI 未运行${NC}"
    fi
}

stop_monitor() {
    log "${BLUE}🛑 停止监控服务...${NC}"
    
    if [ -x "$SCRIPTS_DIR/hermes_monitor.sh" ]; then
        "$SCRIPTS_DIR/hermes_monitor.sh" stop 2>/dev/null || true
        log "${GREEN}✅ 监控服务已停止${NC}"
    else
        log "${YELLOW}⚠️  监控脚本不存在${NC}"
    fi
}

# ============================================================================
# 状态显示
# ============================================================================

show_status() {
    echo ""
    log "${CYAN}========================================${NC}"
    log "${CYAN}📊 Hermes 服务状态${NC}"
    log "${CYAN}========================================${NC}"
    echo ""
    
    # Gateway 状态
    if check_process "gateway/run.py"; then
        local pid=$(get_pid "gateway/run.py")
        echo -e "  ${GREEN}●${NC} Gateway:    ${GREEN}运行中${NC} (PID: $pid)"
    else
        echo -e "  ${RED}○${NC} Gateway:    ${RED}未运行${NC}"
    fi
    
    # Dashboard 状态
    if check_port $DASHBOARD_PORT; then
        local pid=$(get_pid "hermes_cli.web_server:app")
        echo -e "  ${GREEN}●${NC} Dashboard:  ${GREEN}运行中${NC} (端口 $DASHBOARD_PORT, PID: $pid)"
    else
        echo -e "  ${RED}○${NC} Dashboard:  ${RED}未运行${NC}"
    fi
    
    # WebUI 状态
    if check_port $WEBUI_PORT; then
        local pid=$(get_pid "hermes_webui.server:app")
        echo -e "  ${GREEN}●${NC} WebUI:      ${GREEN}运行中${NC} (端口 $WEBUI_PORT, PID: $pid)"
    else
        echo -e "  ${RED}○${NC} WebUI:      ${RED}未运行${NC}"
    fi
    
    # Monitor 状态
    if pgrep -f "hermes_monitor.sh run" > /dev/null 2>&1; then
        local pid=$(pgrep -f "hermes_monitor.sh run" | head -1)
        echo -e "  ${GREEN}●${NC} Monitor:    ${GREEN}运行中${NC} (PID: $pid)"
    else
        echo -e "  ${RED}○${NC} Monitor:    ${RED}未运行${NC}"
    fi
    
    echo ""
    log "${CYAN}========================================${NC}"
    echo ""
    
    # tmux 会话列表
    log "${BLUE}📦 tmux 会话:${NC}"
    tmux list-sessions 2>/dev/null | grep -E "hermes-" || echo "  无 Hermes 相关会话"
    echo ""
}

# ============================================================================
# 主程序
# ============================================================================

show_help() {
    cat << EOF
${CYAN}Hermes Agent 统一管理服务${NC}

用法：$0 [命令]

命令:
  start         启动所有服务 (Gateway + Dashboard + WebUI + Monitor)
  stop          停止所有服务
  restart       重启所有服务
  status        显示所有服务状态
  
  start-gw      只启动 Gateway
  start-dash    只启动 Dashboard
  start-webui   只启动 WebUI
  start-mon     只启动监控服务
  
  stop-gw       只停止 Gateway
  stop-dash     只停止 Dashboard
  stop-webui    只停止 WebUI
  stop-mon      只停止监控服务
  
  auto-start    测试 WSL 自动启动脚本
  help          显示此帮助信息

示例:
  $0 start      # 启动所有服务
  $0 status     # 查看服务状态
  $0 stop-gw    # 只停止 Gateway

EOF
}

# 主程序
case "${1:-status}" in
    start)
        log "${GREEN}========================================${NC}"
        log "${GREEN}🚀 启动所有 Hermes 服务${NC}"
        log "${GREEN}========================================${NC}"
        
        start_gateway
        sleep 2
        start_dashboard
        sleep 2
        start_webui
        sleep 2
        start_monitor
        
        echo ""
        show_status
        ;;
    
    stop)
        log "${GREEN}========================================${NC}"
        log "${GREEN}🛑 停止所有 Hermes 服务${NC}"
        log "${GREEN}========================================${NC}"
        
        stop_monitor
        stop_webui
        stop_dashboard
        stop_gateway
        
        echo ""
        show_status
        ;;
    
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    
    status)
        show_status
        ;;
    
    start-gw|start-gateway)
        start_gateway
        ;;
    
    start-dash|start-dashboard)
        start_dashboard
        ;;
    
    start-webui)
        start_webui
        ;;
    
    start-mon|start-monitor)
        start_monitor
        ;;
    
    stop-gw|stop-gateway)
        stop_gateway
        ;;
    
    stop-dash|stop-dashboard)
        stop_dashboard
        ;;
    
    stop-webui)
        stop_webui
        ;;
    
    stop-mon|stop-monitor)
        stop_monitor
        ;;
    
    auto-start)
        log "${BLUE}🧪 测试 WSL 自动启动脚本...${NC}"
        if [ -x "$SCRIPTS_DIR/wsl_auto_start.sh" ]; then
            "$SCRIPTS_DIR/wsl_auto_start.sh"
        else
            log "${RED}❌ 自动启动脚本不存在或不可执行${NC}"
            exit 1
        fi
        ;;
    
    help|--help|-h)
        show_help
        ;;
    
    *)
        show_help
        exit 1
        ;;
esac

exit 0
