# Hermes Agent 性能优化指南

## 版本信息
- **版本**: 1.0
- **创建日期**: 2026-04-22

## 1. 缓存层使用

### 初始化缓存

```python
from hermes_cache import init_cache

# 初始化全局缓存（内存 + 磁盘）
cache = init_cache(
    memory_cache=True,
    disk_cache=True,
    cache_dir=Path.home() / '.hermes' / 'cache',
    default_ttl=3600  # 1 小时
)
```

### 基本使用

```python
# 设置缓存
cache.set('my_key', {'data': 'value'}, ttl=3600)

# 获取缓存
value = cache.get('my_key')

# 删除缓存
cache.delete('my_key')

# 清空缓存
cache.clear()
```

### 装饰器用法

```python
@cache.cached(prefix='api_response', ttl=3600)
def fetch_api_data(url: str):
    # 第一次调用会执行，后续调用直接从缓存返回
    return requests.get(url).json()
```

### 缓存统计

```python
stats = cache.stats()
print(stats)
# {'backends': [
#   {'backend': 'memory', 'size': 100, 'hits': 500, 'misses': 100, 'hit_rate': '83.3%'},
#   {'backend': 'disk', 'size': 1000, 'total_size_mb': '50.5'}
# ]}
```

## 2. 工具调用优化

### 初始化工具优化器

```python
from hermes_cache import init_optimizer

optimizer = init_optimizer(
    max_workers=4,        # 最大并行工作线程
    default_timeout=30,   # 默认超时时间（秒）
    enable_batching=True, # 启用批量合并
    enable_parallel=True  # 启用并行执行
)
```

### 注册工具处理器

```python
optimizer.register_handler('read_file', read_file_handler)
optimizer.register_handler('search_files', search_files_handler)
```

### 执行单个调用

```python
from hermes_cache import ToolCall

call = ToolCall(
    tool_name='read_file',
    args={'path': '/path/to/file.txt'},
    timeout=30,
    priority=0
)

result = optimizer.execute(call)
if result.success:
    print(result.result)
else:
    print(f"错误：{result.error}")
```

### 批量执行

```python
calls = [
    ToolCall(tool_name='read_file', args={'path': 'file1.txt'}),
    ToolCall(tool_name='read_file', args={'path': 'file2.txt'}),
    ToolCall(tool_name='search_files', args={'pattern': '*.py'}),
]

# 并行执行所有调用
results = optimizer.execute_batch(calls, parallel=True)

for result in results:
    print(f"{result.tool_name}: {'成功' if result.success else '失败'}")
```

### 优化器统计

```python
stats = optimizer.get_stats()
print(stats)
# {'total_calls': 100, 'successful_calls': 95, 'failed_calls': 5,
#   'success_rate': 95.0, 'avg_duration_ms': 150.5}
```

## 3. 性能最佳实践

### 3.1 缓存策略

| 场景 | 推荐 TTL | 缓存类型 |
|------|----------|----------|
| API 响应 | 5-60 分钟 | 内存 + 磁盘 |
| 文件内容 | 1-5 分钟 | 内存 |
| 搜索结果 | 10-30 分钟 | 内存 + 磁盘 |
| 配置数据 | 直到变更 | 内存 + 磁盘 |
| 临时数据 | 30 秒 -1 分钟 | 仅内存 |

### 3.2 并行执行

**适合并行的场景:**
- 多个独立的文件读取
- 多个 API 请求
- 网络爬虫多页面抓取

**不适合并行的场景:**
- 有依赖关系的操作
- 写操作（避免竞态条件）
- 资源受限的操作

### 3.3 超时设置

| 操作类型 | 推荐超时 |
|----------|----------|
| 文件读取 | 5-10 秒 |
| 网络请求 | 10-30 秒 |
| API 调用 | 30-60 秒 |
| 代码执行 | 60-300 秒 |

### 3.4 内存管理

```python
# 定期清理过期缓存
import schedule

def cleanup_job():
    cache.cleanup_expired()

schedule.every(1).hours.do(cleanup_job)
```

## 4. 性能监控

### 4.1 缓存命中率

```python
stats = cache.stats()
for backend in stats['backends']:
    if 'hit_rate' in backend:
        print(f"{backend['backend']} 缓存命中率：{backend['hit_rate']}")
```

**目标:**
- 内存缓存命中率 > 80%
- 磁盘缓存命中率 > 60%

### 4.2 工具调用性能

```python
stats = optimizer.get_stats()
print(f"成功率：{stats['success_rate']:.1f}%")
print(f"平均耗时：{stats['avg_duration_ms']:.1f}ms")
```

**目标:**
- 工具调用成功率 > 95%
- 平均耗时 < 500ms

### 4.3 性能仪表板

创建定时任务，每小时生成性能报告：

```bash
hermes cron create \
  --name "性能监控" \
  --schedule "0 * * * *" \
  --prompt "分析缓存命中率和工具调用性能，生成性能报告发送到微信"
```

## 5. 故障排查

### 5.1 缓存未命中

**可能原因:**
- TTL 设置过短
- 缓存键不一致
- 缓存被清理

**解决方案:**
- 增加 TTL
- 检查键生成逻辑
- 调整缓存大小限制

### 5.2 工具调用超时

**可能原因:**
- 网络延迟
- 资源不足
- 死锁

**解决方案:**
- 增加超时时间
- 检查工作线程数
- 添加重试逻辑

### 5.3 内存占用过高

**可能原因:**
- 缓存条目过多
- 大对象缓存

**解决方案:**
- 减小 max_size
- 使用磁盘缓存
- 定期清理

---

*文档自动生成，最后更新：2026-04-22 11:38:59*
