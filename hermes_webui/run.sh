#!/bin/bash
# Hermes Web UI 启动脚本
# 使用方法：bash ~/hermes-agent/hermes_webui/run.sh

set -e

cd ~/hermes-agent
source .venv/bin/activate

echo ""
echo "╔═══════════════════════════════════════════════╗"
echo "║                                               ║"
echo "║   🚀 Hermes Web Console                       ║"
echo "║                                               ║"
echo "╚═══════════════════════════════════════════════╝"
echo ""
echo "访问地址：http://localhost:8080"
echo "按 Ctrl+C 停止服务器"
echo ""

# 使用 Python 内置 HTTP 服务器
python hermes_webui/simple_server.py
