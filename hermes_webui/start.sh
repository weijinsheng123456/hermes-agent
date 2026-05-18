#!/bin/bash
# Hermes Web UI 启动脚本
cd ~/hermes-agent
source .venv/bin/activate

echo "正在启动 Hermes Web UI..."
echo "访问地址：http://localhost:8080"
echo ""

# 启动服务器
exec python -m uvicorn hermes_webui.server:app --host 0.0.0.0 --port 8080 --log-level info
