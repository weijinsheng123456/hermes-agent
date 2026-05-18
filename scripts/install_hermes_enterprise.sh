#!/bin/bash
# Hermes 企业级功能安装脚本
# 使用：./install_hermes_enterprise.sh

set -e

echo "=============================================="
echo "Hermes 企业级功能安装脚本"
echo "=============================================="

# 检查 Python 环境
echo ""
echo "[1/5] 检查 Python 环境..."
if ! command -v python3 &> /dev/null; then
    echo "错误：未找到 Python3"
    exit 1
fi
python3 --version

# 检查虚拟环境
echo ""
echo "[2/5] 检查虚拟环境..."
HERMES_DIR="$HOME/hermes-agent"
if [ ! -d "$HERMES_DIR/.venv" ]; then
    echo "错误：未找到 Hermes 虚拟环境"
    exit 1
fi

# 激活虚拟环境
source "$HERMES_DIR/.venv/bin/activate"

# 安装依赖
echo ""
echo "[3/5] 验证依赖..."
python -c "import pytest; import requests; print('依赖验证通过')"

# 运行测试
echo ""
echo "[4/5] 运行测试..."
cd "$HERMES_DIR"
python -m pytest tests/enterprise/ -v --tb=short -q

# 验证安装
echo ""
echo "[5/5] 验证安装..."
python -c "
from hermes_enterprise import get_tenant_system, get_security_system, get_ha_system
print('✅ 多租户系统：OK')
print('✅ 安全合规系统：OK')
print('✅ 高可用系统：OK')
"

echo ""
echo "=============================================="
echo "✅ 安装完成!"
echo "=============================================="
echo ""
echo "文档位置：$HERMES_DIR/docs/"
echo "  - ENTERPRISE_API.md    : API 文档"
echo "  - CRON_CONFIG.md       : 定时任务配置"
echo ""
echo "脚本位置：$HERMES_DIR/scripts/"
echo "  - monitor_hermes.py    : 监控脚本"
echo "  - benchmark_hermes.py  : 性能测试"
echo ""
echo "测试位置：$HERMES_DIR/tests/enterprise/"
echo ""
echo "下一步:"
echo "  1. 配置监控：crontab -e"
echo "  2. 运行监控：python scripts/monitor_hermes.py"
echo "  3. 查看文档：cat docs/ENTERPRISE_API.md"
echo ""
