#!/bin/bash
# ============================================================================
# Hermes Agent 自动启动系统验证脚本
# 功能：快速验证所有组件是否正常工作
# 用法：./verify_autostart.sh
# ============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 统计
TOTAL=0
PASSED=0
FAILED=0

# 测试函数
test_result() {
    local name="$1"
    local result="$2"
    TOTAL=$((TOTAL + 1))
    
    if [ "$result" -eq 0 ]; then
        echo -e "  ${GREEN}✓${NC} $name"
        PASSED=$((PASSED + 1))
    else
        echo -e "  ${RED}✗${NC} $name"
        FAILED=$((FAILED + 1))
    fi
}

echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}Hermes 自动启动系统验证${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# 1. 检查脚本文件是否存在
echo -e "${BLUE}[1/8] 检查脚本文件...${NC}"
[ -x "/home/xiaobai/hermes-agent/scripts/wsl_auto_start.sh" ]
test_result "wsl_auto_start.sh 存在且可执行" $?

[ -x "/home/xiaobai/hermes-agent/scripts/hermes_monitor.sh" ]
test_result "hermes_monitor.sh 存在且可执行" $?

[ -x "/home/xiaobai/hermes-agent/scripts/hermes_manager.sh" ]
test_result "hermes_manager.sh 存在且可执行" $?

[ -f "/home/xiaobai/hermes-agent/scripts/hermes_wsl_startup.xml" ]
test_result "hermes_wsl_startup.xml 存在" $?

[ -f "/home/xiaobai/hermes-agent/scripts/README_AUTOSTART.md" ]
test_result "README_AUTOSTART.md 存在" $?
echo ""

# 2. 检查 Windows 文件
echo -e "${BLUE}[2/8] 检查 Windows 文件...${NC}"
[ -f "/mnt/c/Users/31308/Desktop/启动 Hermes.bat" ]
test_result "启动 Hermes.bat 存在" $?

[ -f "/mnt/c/Users/31308/Desktop/配置 Hermes 开机启动.bat" ]
test_result "配置 Hermes 开机启动.bat 存在" $?
echo ""

# 3. 检查 .bashrc 配置
echo -e "${BLUE}[3/8] 检查 .bashrc 配置...${NC}"
grep -q "wsl_auto_start.sh" /home/xiaobai/.bashrc
test_result ".bashrc 包含自动启动调用" $?
echo ""

# 4. 检查服务状态
echo -e "${BLUE}[4/8] 检查当前服务状态...${NC}"
pgrep -f "gateway/run.py" > /dev/null 2>&1
test_result "Gateway 进程运行中" $?

ss -tlnp 2>/dev/null | grep -q ":9119 "
test_result "Dashboard 端口 9119 监听中" $?

ss -tlnp 2>/dev/null | grep -q ":8080 "
test_result "WebUI 端口 8080 监听中" $?

pgrep -f "hermes_monitor.sh run" > /dev/null 2>&1
test_result "监控服务运行中" $?
echo ""

# 5. 检查 tmux 会话
echo -e "${BLUE}[5/8] 检查 tmux 会话...${NC}"
tmux has-session -t hermes-gateway 2>/dev/null
test_result "hermes-gateway 会话存在" $?

# Dashboard 和 WebUI 可能不是用 tmux 启动的，只检查进程
pgrep -f "hermes_cli.web_server:app" > /dev/null 2>&1
test_result "Dashboard 进程运行中" $?

pgrep -f "hermes_webui.server:app" > /dev/null 2>&1
test_result "WebUI 进程运行中" $?
echo ""

# 6. 检查日志文件
echo -e "${BLUE}[6/8] 检查日志系统...${NC}"
[ -d "/home/xiaobai/.hermes/logs" ]
test_result "日志目录存在" $?

[ -f "/home/xiaobai/.hermes/logs/wsl_auto_start.log" ]
test_result "自动启动日志存在" $?

[ -f "/home/xiaobai/.hermes/logs/hermes_monitor.log" ]
test_result "监控日志存在" $?

[ -f "/home/xiaobai/.hermes/logs/gateway.log" ]
test_result "Gateway 日志存在" $?
echo ""

# 7. 检查微信配置（可选）
echo -e "${BLUE}[7/8] 检查微信告警配置（可选）...${NC}"
if [ -f "/home/xiaobai/.hermes/.env" ]; then
    if grep -q "WX_PUSHER_APP_TOKEN" /home/xiaobai/.hermes/.env && \
       grep -q "WX_PUSHER_UID" /home/xiaobai/.hermes/.env; then
        test_result "WxPusher 已配置" 0
    else
        test_result "WxPusher 未配置（可选）" 1
    fi
else
    test_result ".env 文件不存在（可选）" 1
fi
echo ""

# 8. 检查锁文件机制
echo -e "${BLUE}[8/8] 检查锁文件机制...${NC}"
[ ! -f "/tmp/hermes_auto_start.lock" ]
test_result "无 stale 锁文件" $?
echo ""

# 总结
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}验证结果${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""
echo -e "  总计：${TOTAL} 项"
echo -e "  ${GREEN}通过：${PASSED} 项${NC}"
echo -e "  ${RED}失败：${FAILED} 项${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ 所有检查通过！系统配置完整${NC}"
    echo ""
    echo -e "${YELLOW}📝 下一步操作:${NC}"
    echo "  1. 配置微信告警（可选）："
    echo "     编辑 /home/xiaobai/.hermes/.env"
    echo "     添加 WX_PUSHER_APP_TOKEN 和 WX_PUSHER_UID"
    echo ""
    echo "  2. 安装 Windows 任务计划（推荐）："
    echo "     以管理员身份运行："
    echo "     C:\\Users\\31308\\Desktop\\配置 Hermes 开机启动.bat"
    echo ""
    echo "  3. 测试 WSL 自动启动："
    echo "     powershell.exe: wsl --shutdown"
    echo "     重新打开 WSL 终端"
    echo ""
    exit 0
else
    echo -e "${RED}❌ 发现 $FAILED 个问题，请检查上述失败项${NC}"
    echo ""
    echo -e "${YELLOW}💡 建议:${NC}"
    echo "  - 确保所有脚本都有执行权限 (chmod +x)"
    echo "  - 确保在正确的路径下执行"
    echo "  - 查看相关日志获取更多信息"
    echo ""
    exit 1
fi
