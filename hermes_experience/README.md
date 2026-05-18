# Hermes 用户体验优化模块

**版本**: 1.0
**创建日期**: 2026-04-22

## 模块组成

### 1. 智能上下文感知 (`context_aware.py`)

功能:
- Windows/Linux 桌面环境检测
- WSL 环境识别
- 文件类型智能路由
- 用户习惯学习

使用示例:
```python
from hermes_experience import get_context_system

ctx = get_context_system()

# 获取上下文
context = ctx.get_context()
print(context.os_type)  # wsl, linux, windows

# 获取桌面文件
files = ctx.get_desktop_files('windows')

# 文件路由
routing = ctx.route_file('document.pdf')
# {'category': 'document', 'preferred_app': 'pdf_reader', ...}
```

### 2. ROI 仪表盘 (`roi_dashboard.py`)

功能:
- 时间节省量化
- 成本降低计算
- 商业价值报告
- 微信自动发送

使用示例:
```python
from hermes_experience import get_roi_dashboard

dashboard = get_roi_dashboard()

# 记录任务
dashboard.record_task('email_summary', automated=True)

# 获取时间节省
time_savings = dashboard.get_time_savings(days=7)
# {'total_hours': 5.5, 'by_task': {...}}

# 获取成本节省
cost_savings = dashboard.get_cost_savings(days=30)
# {'total_amount': 550.0, ...}

# 生成报告
report = dashboard.generate_report()
```

### 3. 竞品分析自动化 (`competitor_analysis.py`)

功能:
- GitHub 趋势监控
- 竞品分析
- 市场洞察
- 应对策略建议

使用示例:
```python
from hermes_experience import get_competitor_analyzer

analyzer = get_competitor_analyzer()

# 获取 GitHub 趋势
trends = analyzer.fetch_github_trends()

# 分析竞品
competitor = analyzer.analyze_competitor('AutoGPT', 'ai-agent')

# 生成报告
report = analyzer.generate_report()

# 获取市场洞察
insights = analyzer.get_market_insights()
```

## 集成使用

```python
from hermes_experience import (
    get_context_system,
    get_roi_dashboard,
    get_competitor_analyzer
)

# 完整工作流
ctx = get_context_system()
dashboard = get_roi_dashboard()
analyzer = get_competitor_analyzer()

# 1. 检测环境
context = ctx.get_context()

# 2. 记录自动化任务
dashboard.record_task('file_organization', automated=True)

# 3. 获取竞品趋势
trends = analyzer.fetch_github_trends()

# 4. 生成 ROI 报告
report = dashboard.generate_report()
```

---

*Hermes Agent 用户体验优化模块*
