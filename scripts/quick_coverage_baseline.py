#!/usr/bin/env python3
"""
快速覆盖率基线测试

只测试核心工具模块，快速建立覆盖率基线。

Usage:
    python scripts/quick_coverage_baseline.py
"""

import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent

print("=" * 60)
print("📊 快速覆盖率基线测试")
print("=" * 60)

# 只测试核心工具模块
core_modules = [
    "tools.registry",
    "tools.hub",
    "tools.json_output",
    "tools.file_tools",
    "tools.terminal_tool",
]

print(f"\n测试模块：{len(core_modules)} 个核心模块")
for mod in core_modules:
    print(f"  • {mod}")

# 运行简化版覆盖率测试
cmd = [
    sys.executable, "-m", "pytest",
    "tests/tools/",  # 只测试工具相关测试
    "-q",
    "--cov=tools",
    "--cov-report=term-missing",
    "--no-cov-on-fail",
    "-x",  # 第一个失败就停止
    "--tb=short",
]

print(f"\n运行命令：{' '.join(cmd)}")
print("-" * 60)

try:
    result = subprocess.run(
        cmd,
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=120,  # 2 分钟超时
    )
    
    # 解析输出
    output = result.stdout + result.stderr
    
    # 提取覆盖率行
    coverage_line = None
    for line in output.split("\n"):
        if "TOTAL" in line and "%" in line:
            coverage_line = line
    
    print(output[-2000:])  # 显示最后 2000 字符
    
    if coverage_line:
        print("\n" + "=" * 60)
        print(f"覆盖率：{coverage_line.strip()}")
        print("=" * 60)
        
        # 保存结果
        baseline_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "coverage_line": coverage_line.strip(),
            "test_scope": "tools only",
            "duration_seconds": result.elapsed.total_seconds() if hasattr(result, 'elapsed') else None,
        }
        
        output_file = project_root / "coverage" / "baseline_quick.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w") as f:
            json.dump(baseline_data, f, indent=2)
        
        print(f"\n基线数据已保存：{output_file}")
        
    else:
        print("\n⚠️  无法解析覆盖率数据")
        
except subprocess.TimeoutExpired:
    print("\n⏱️  测试超时 (2 分钟)")
    print("建议使用完整测试：python scripts/enhance_coverage.py run")
except Exception as e:
    print(f"\n❌ 测试失败：{e}")

print("\n" + "=" * 60)
