# Hermes 企业级功能快速使用指南

## 新增模块概览

本次三阶段优化新增了 9 个企业级模块，覆盖预测执行、多模态处理、工作流引擎、上下文感知、ROI 分析和竞品监控。

---

## 1. 预测性执行框架

**位置**: `hermes_enterprise/predictive/executor.py`

### 基本使用

```python
from hermes_enterprise.predictive.executor import get_predictive_executor

executor = get_predictive_executor()

# 记录用户行为（自动学习）
executor.execute_with_learning(
    action='code_review',
    context={'file': 'main.py', 'type': 'python'},
    func=your_function,
    *args, **kwargs
)

# 获取预测
prediction = executor.get_prediction(context={'time': 'morning'})
print(f"预测操作：{prediction.predicted_action}")
print(f"置信度：{prediction.confidence}")
print(f"推荐任务链：{prediction.suggested_chain}")

# 获取工作流推荐
workflow = executor.suggest_workflow()
```

### 使用场景
- 自动推荐下一步操作
- 智能任务链生成
- 用户行为模式分析

---

## 2. 多模态能力扩展

**位置**: `hermes_enterprise/multimodal/processor.py`

### 图像处理

```python
from hermes_enterprise.multimodal.processor import analyze_image

# 生成图像描述
result = analyze_image('/path/to/image.png', task='caption')
print(result.description)

# 对象检测
result = analyze_image('/path/to/image.png', task='detect')
print(result.bounding_boxes)

# 图像分割
result = analyze_image('/path/to/image.png', task='segment')
print(result.segmentation_mask)
```

### 音频处理

```python
from hermes_enterprise.multimodal.processor import transcribe_audio, generate_audio

# 音频转录
result = transcribe_audio('/path/to/audio.mp3', language='zh')
print(result.transcript)

# 语音生成
audio_path = generate_audio('你好，这是语音合成测试', voice='default')
```

### 文档解析

```python
from hermes_enterprise.multimodal.processor import parse_document

# 解析 PDF
doc = parse_document('/path/to/document.pdf')
print(doc.text)
print(doc.metadata)

# 解析 Word
doc = parse_document('/path/to/document.docx')

# 解析 Excel
doc = parse_document('/path/to/spreadsheet.xlsx')
print(doc.tables)
```

---

## 3. 自然语言工作流引擎

**位置**: `hermes_enterprise/workflow/engine.py`

### 创建工作流

```python
from hermes_enterprise.workflow.engine import create_workflow_from_text, execute_workflow

# 用自然语言定义工作流
workflow_text = """
工作流：每日竞品分析
第 1 步：搜索 GitHub  trending AI 项目
第 2 步：分析前 10 个项目的 star 增长
第 3 步：生成竞品分析报告
第 4 步：发送到微信
"""

workflow = create_workflow_from_text(workflow_text)
print(f"工作流 ID: {workflow.id}")
print(f"步骤数：{len(workflow.steps)}")
```

### 执行工作流

```python
# 注册动作处理器
from hermes_enterprise.workflow.engine import get_workflow_engine

engine = get_workflow_engine()

engine.register_handler('search', lambda params, ctx: {...})
engine.register_handler('analyze', lambda params, ctx: {...})
engine.register_handler('report', lambda params, ctx: {...})

# 执行工作流
result = execute_workflow(workflow.id)
print(result)
```

### 可视化工作流

```python
visualization = engine.visualize_workflow(workflow.id)
print(visualization)
```

---

## 4. 智能上下文感知

**位置**: `hermes_enterprise/context/detector.py`

### 桌面上下文检测

```python
from hermes_enterprise.context.detector import get_context_detector

detector = get_context_detector()

# 获取桌面路径（自动判断 Windows/WSL）
desktop_path = detector.get_desktop_path()

# 明确指定桌面类型
win_desktop = detector.get_desktop_path('windows')
linux_desktop = detector.get_desktop_path('linux')

# 检测用户意图
intent = detector.detect_intent('打开桌面上的 Python 文件')
print(f"意图类型：{intent['type']}")
print(f"建议操作：{intent['suggested_action']}")
```

### 文件路由

```python
from hermes_enterprise.context.detector import get_file_router

router = get_file_router()

# 单个文件路由
route = router.route_file('/path/to/file.py')
print(f"建议操作：{route.suggested_action}")
print(f"处理器：{route.handler}")

# 批量路由
routes = router.batch_route(['/file1.py', '/file2.pdf', '/file3.xlsx'])
```

### 用户习惯学习

```python
from hermes_enterprise.context.detector import get_habit_learner

learner = get_habit_learner()

# 记录操作
learner.record_action('.py', 'edit_in_vscode')
learner.record_action('.pdf', 'read_only')

# 获取首选操作
preferred = learner.get_preferred_action('.py')
print(f"首选操作：{preferred}")
```

---

## 5. ROI 仪表盘

**位置**: `hermes_enterprise/analytics/roi.py`

### 跟踪时间节省

```python
from hermes_enterprise.analytics.roi import track_time_saving, generate_roi_report

# 跟踪代码审查时间节省
track_time_saving(
    task_type='代码审查',
    manual=30,  # 手动 30 分钟
    automated=5,  # 自动 5 分钟
    freq=3  # 每天 3 次
)

# 跟踪其他任务
track_time_saving('文档生成', 60, 10, 2)
track_time_saving('测试执行', 45, 5, 5)
```

### 跟踪成本降低

```python
from hermes_enterprise.analytics.roi import get_roi_tracker

tracker = get_roi_tracker()

tracker.track_cost_reduction(
    category='API 调用成本',
    original=1000,
    current=300
)

tracker.track_cost_reduction(
    category='人力成本',
    original=5000,
    current=2000
)
```

### 生成报告

```python
# 文本格式报告
report = generate_roi_report(format='text')
print(report)

# Markdown 格式
report_md = generate_roi_report(format='markdown')

# JSON 格式
report_json = generate_roi_report(format='json')
```

---

## 6. 竞品分析自动化

**位置**: `hermes_enterprise/competitive/analyzer.py`

### 监控 GitHub 趋势

```python
from hermes_enterprise.competitive.analyzer import get_competitive_analyzer

analyzer = get_competitive_analyzer()

# 获取 trending 仓库
repos = analyzer.github_monitor.get_trending_repos(
    language='Python',
    since='daily'
)

# 分析特定项目
project = analyzer.github_monitor.analyze_project('langchain-ai', 'langchain')
print(f"Stars: {project['stars']}")
print(f"语言：{project['language']}")
```

### 检测 AI 技术趋势

```python
trends = analyzer.github_monitor.detect_ai_trends()
for trend in trends:
    print(f"技术：{trend.technology}")
    print(f"趋势：{trend.trend_direction}")
    print(f"机会：{trend.market_opportunity}")
```

### 生成竞品分析报告

```python
# 生成完整报告
report = analyzer.generate_report(focus_areas=['AI Agent', 'Automation', 'LLM Tools'])

print(f"报告 ID: {report.report_id}")
print(f"生成时间：{report.generated_at}")
print(f"市场概览：{report.market_overview}")
print(f"建议：{report.recommendations}")
print(f"行动项：{report.action_items}")

# 查看所有报告
reports = analyzer.list_reports()
```

---

## 集成使用示例

### 完整的自动化工作流

```python
from hermes_enterprise.predictive.executor import get_predictive_executor
from hermes_enterprise.workflow.engine import create_workflow_from_text
from hermes_enterprise.analytics.roi import track_time_saving
from hermes_enterprise.competitive.analyzer import generate_competitive_report

# 1. 创建竞品分析工作流
workflow = create_workflow_from_text("""
工作流：每周竞品分析
第 1 步：监控 GitHub AI 趋势
第 2 步：生成竞品分析报告
第 3 步：计算 ROI 指标
第 4 步：发送微信报告
""")

# 2. 执行工作流并学习
executor = get_predictive_executor()
executor.execute_with_learning(
    action='competitive_analysis',
    context={'focus': 'AI tools'},
    func=generate_competitive_report
)

# 3. 跟踪时间节省
track_time_saving(
    task_type='竞品分析',
    manual=120,  # 手动 2 小时
    automated=10,  # 自动 10 分钟
    freq=1  # 每周 1 次
)

# 4. 生成 ROI 报告
roi_report = generate_roi_report(format='markdown')
```

---

## 配置说明

### 环境变量

```bash
# GitHub API（可选，提高限额）
export GITHUB_TOKEN=your_token

# 微信推送
export WX_PUSHER_APP_TOKEN=your_app_token
export WX_PUSHER_UID=your_uid
```

### 配置文件

用户偏好：`~/.hermes/user_preferences.json`
行为数据：`~/.hermes/behavior_data/`
工作流：`~/.hermes/workflows/`
ROI 数据：`~/.hermes/roi_data/`
竞品报告：`~/.hermes/competitive_reports/`

---

## 最佳实践

1. **预测性执行**: 至少记录 10 次用户行为后，预测准确度会显著提升
2. **多模态处理**: 大文件建议先缓存，避免重复处理
3. **工作流引擎**: 复杂工作流建议先测试单个步骤
4. **上下文感知**: 首次使用需明确指定桌面类型以建立偏好
5. **ROI 跟踪**: 建议每日记录，月度生成报告
6. **竞品分析**: 每周执行一次，跟踪长期趋势

---

## 故障排查

### 预测不准确
- 检查行为历史数据量（至少 10 条）
- 确认上下文信息完整

### 文件路由错误
- 检查文件扩展名是否支持
- 确认文件路径存在

### ROI 数据为空
- 确认已调用 track_* 函数记录数据
- 检查数据目录权限

### GitHub API 限流
- 配置 GITHUB_TOKEN
- 使用缓存数据降级

---

## 技术支持

- 文档位置：`~/hermes-agent/docs/`
- 示例代码：`~/hermes-agent/examples/`
- 问题反馈：GitHub Issues
