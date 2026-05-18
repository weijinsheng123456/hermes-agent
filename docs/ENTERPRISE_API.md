# Hermes 企业级功能 API 文档

**版本**: 1.0.0
**更新日期**: 2026-04-22

---

## 目录

1. 多租户系统
2. 安全合规系统
3. 高可用部署系统
4. 故障排查

---

## 多租户系统

### 导入模块

```python
from hermes_enterprise import get_tenant_system
system = get_tenant_system()
```

### 租户管理

#### 创建租户

```python
tenant_id = system.tenant_manager.create_tenant(
    name="公司名称",
    owner_email="admin@company.com",
    tier="pro"  # free, basic, pro, enterprise
)
```

#### 获取租户信息

```python
tenant = system.tenant_manager.get_tenant(tenant_id)
```

#### 列出租户

```python
tenants = system.tenant_manager.list_tenants()
active_tenants = system.tenant_manager.list_tenants(status="active")
```

#### 暂停/删除租户

```python
system.tenant_manager.suspend_tenant(tenant_id)
system.tenant_manager.delete_tenant(tenant_id)
```

### 用户管理

#### 添加用户

```python
user_id = system.tenant_manager.add_user(
    tenant_id=tenant_id,
    email="user@company.com",
    name="张三",
    role="member"  # owner, admin, member
)
```

#### 检查权限

```python
from hermes_enterprise.tenant.system import Permission
has_read = system.tenant_manager.check_permission(user_id, Permission.READ)
```

### 资源配额

#### 获取配额

```python
quota = system.tenant_manager.get_quota(tenant_id)
```

#### 记录使用量

```python
system.tenant_manager.record_usage(
    tenant_id=tenant_id,
    api_calls=100,
    storage_mb=50.0,
    tasks=10
)
```

### 计费系统

#### 生成账单

```python
invoice = system.billing_manager.generate_invoice(
    tenant_id=tenant_id,
    period_start="2026-04-01",
    period_end="2026-04-30"
)
```

#### 列出账单

```python
invoices = system.billing_manager.list_invoices()
```

#### 标记为已支付

```python
system.billing_manager.mark_paid(invoice.record_id)
```

### 租户等级

| 等级 | 用户数 | API 调用/天 | 价格 |
|------|--------|-------------|------|
| FREE | 1 | 100 | 0 元/月 |
| BASIC | 5 | 1,000 | 99 元/月 |
| PRO | 20 | 10,000 | 499 元/月 |
| ENTERPRISE | 无限 | 无限 | 2999 元/月 |

---

## 安全合规系统

### 导入模块

```python
from hermes_enterprise import get_security_system
from hermes_enterprise.security.system import AuditAction
system = get_security_system()
```

### 审计追踪

#### 记录操作日志

```python
log_id = system.audit_trail.log(
    user_id="user123",
    tenant_id="tenant456",
    action=AuditAction.READ,
    resource_type="file",
    resource_id="file789"
)
```

#### 查询日志

```python
logs = system.audit_trail.query_logs(tenant_id="tenant456")
logs = system.audit_trail.query_logs(user_id="user123")
logs = system.audit_trail.query_logs(action=AuditAction.DELETE)
```

#### 导出日志

```python
export_path = system.audit_trail.export_logs(
    tenant_id="tenant456",
    start_time="2026-04-01",
    end_time="2026-04-30"
)
```

### GDPR 合规

#### 注册个人数据

```python
data_id = system.gdpr.register_personal_data(
    user_id="user123",
    tenant_id="tenant456",
    data_type="email",
    data_value="user@example.com"
)
```

#### 给予/撤回同意

```python
system.gdpr.give_consent(data_id, user_id="user123")
system.gdpr.withdraw_consent(data_id, user_id="user123")
```

#### 导出/删除用户数据

```python
export = system.gdpr.export_user_data(user_id="user123")
deleted_count = system.gdpr.delete_user_data(user_id="user123")
```

### 漏洞扫描

```python
reports = system.scanner.scan("api_server")
reports = system.scanner.get_all_reports()
system.scanner.resolve_vulnerability(report_id)
```

---

## 高可用部署系统

### 导入模块

```python
from hermes_enterprise import get_ha_system
from hermes_enterprise.high_availability.system import ClusterRole
system = get_ha_system()
```

### 集群管理

#### 添加节点

```python
primary_id = system.cluster.add_node("primary.example.com", 8000, role="PRIMARY")
replica_id = system.cluster.add_node("replica.example.com", 8001, role="REPLICA")
```

#### 更新心跳

```python
system.cluster.update_heartbeat(node_id, {'cpu': 50, 'memory': 60})
```

#### 获取集群状态

```python
status = system.cluster.get_cluster_status()
```

#### 提升副本为主节点

```python
system.cluster.promote_replica(replica_id)
```

### 故障转移

```python
system.failover.enable_auto_failover(True)
event = system.failover.check_and_failover()
events = system.failover.get_events(limit=50)
```

### 备份恢复

#### 创建备份

```python
backup = system.backup.create_backup("/path/to/data", backup_type="full")
```

#### 恢复备份

```python
system.backup.restore_backup(backup_id, "/path/to/restore")
```

#### 列出备份

```python
backups = system.backup.list_backups()
```

---

## 故障排查

### 常见问题

**问题 1**: 租户创建失败
- 检查租户名称是否重复

**问题 2**: 权限检查失败
- 确认用户状态为 active
- 检查用户角色权限

**问题 3**: 集群节点离线
- 检查心跳是否正常
- 执行故障转移

### 日志位置

- 租户数据：`~/.hermes/enterprise/tenants/`
- 审计日志：`~/.hermes/enterprise/audit/`
- 备份文件：`~/.hermes/enterprise/backups/`
- 集群配置：`~/.hermes/enterprise/cluster/`

---

*Hermes 企业级功能 API 文档 v1.0.0*
