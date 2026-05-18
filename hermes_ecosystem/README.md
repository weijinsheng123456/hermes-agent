# Hermes 生态系统

**版本**: 1.0
**创建日期**: 2026-04-22

## 模块组成

### 1. 开发者 SDK (`sdk/`)

功能:
- API 客户端
- 测试沙箱
- 示例代码库

使用示例:
```python
from hermes_ecosystem import HermesSDK

sdk = HermesSDK()

# API 调用
response = sdk.client.chat("你好")

# 沙箱测试
result = sdk.sandbox.run_code("print('Hello')")

# 查看示例
examples = sdk.examples.list_examples()
```

### 2. 插件市场 (`plugins/`)

功能:
- 插件加载和管理
- 垂直行业插件
- 工具集成插件
- AI 模型插件

使用示例:
```python
from hermes_ecosystem import get_plugin_manager, get_plugin_marketplace

# 浏览市场
marketplace = get_plugin_marketplace()
plugins = marketplace.browse(category='industry')

# 管理插件
manager = get_plugin_manager()
installed = manager.list_plugins()
```

### 3. 用户社区 (`community/`)

功能:
- 技术论坛
- 最佳实践分享
- 收益分成管理

使用示例:
```python
from hermes_ecosystem import get_community_system

community = get_community_system()

# 论坛
post_id = community.forum.create_post("标题", "内容", "作者")
posts = community.forum.list_posts()

# 最佳实践
practices = community.practices.list_practices()

# 收益分成
earnings = community.revenue.get_author_earnings("作者")
```

---

*Hermes 生态系统*
