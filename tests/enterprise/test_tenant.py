"""多租户系统单元测试

覆盖范围:
- 租户创建和管理
- 用户权限管理
- 资源配额控制
- 计费系统

目标覆盖率：80%+
"""

import pytest
import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path.home() / 'hermes-agent'))

from hermes_enterprise.tenant.system import (
    TenantManager, BillingManager, TenantTier, Permission,
    TIER_QUOTAS, EnterpriseTenantSystem
)


class TestTenantTier:
    """测试租户等级枚举"""
    
    def test_tier_values(self):
        """测试等级值"""
        assert TenantTier.FREE.value == "free"
        assert TenantTier.BASIC.value == "basic"
        assert TenantTier.PRO.value == "pro"
        assert TenantTier.ENTERPRISE.value == "enterprise"
    
    def test_tier_from_string(self):
        """测试从字符串创建"""
        assert TenantTier("free") == TenantTier.FREE
        assert TenantTier("basic") == TenantTier.BASIC
        assert TenantTier("pro") == TenantTier.PRO
        assert TenantTier("enterprise") == TenantTier.ENTERPRISE


class TestTierQuotas:
    """测试等级配额"""
    
    def test_free_tier_quota(self):
        """测试免费层配额"""
        quota = TIER_QUOTAS[TenantTier.FREE]
        assert quota['max_users'] == 1
        assert quota['max_api_calls_per_day'] == 100
        assert quota['max_storage_mb'] == 100
        assert quota['support_level'] == 'community'
    
    def test_basic_tier_quota(self):
        """测试基础层配额"""
        quota = TIER_QUOTAS[TenantTier.BASIC]
        assert quota['max_users'] == 5
        assert quota['max_api_calls_per_day'] == 1000
        assert quota['max_storage_mb'] == 1000
        assert quota['support_level'] == 'email'
    
    def test_pro_tier_quota(self):
        """测试专业层配额"""
        quota = TIER_QUOTAS[TenantTier.PRO]
        assert quota['max_users'] == 20
        assert quota['max_api_calls_per_day'] == 10000
        assert quota['max_storage_mb'] == 10000
        assert quota['support_level'] == 'priority'
    
    def test_enterprise_tier_quota(self):
        """测试企业层配额 (无限制)"""
        quota = TIER_QUOTAS[TenantTier.ENTERPRISE]
        assert quota['max_users'] == -1  # -1 表示无限制
        assert quota['max_api_calls_per_day'] == -1
        assert quota['support_level'] == 'dedicated'


class TestTenantManager:
    """测试租户管理器"""
    
    @pytest.fixture
    def manager(self, tmp_path):
        """创建测试用管理器"""
        return TenantManager(data_dir=tmp_path)
    
    def test_create_tenant(self, manager):
        """测试创建租户"""
        tenant_id = manager.create_tenant(
            name="测试公司",
            owner_email="test@example.com",
            tier="pro"
        )
        
        assert tenant_id is not None
        assert len(tenant_id) == 12
        
        tenant = manager.get_tenant(tenant_id)
        assert tenant is not None
        assert tenant.name == "测试公司"
        assert tenant.owner_email == "test@example.com"
        assert tenant.tier == TenantTier.PRO
    
    def test_create_tenant_with_enum(self, manager):
        """测试使用枚举创建租户"""
        tenant_id = manager.create_tenant(
            name="测试公司 2",
            owner_email="test2@example.com",
            tier=TenantTier.BASIC
        )
        
        tenant = manager.get_tenant(tenant_id)
        assert tenant.tier == TenantTier.BASIC
    
    def test_list_tenants(self, manager):
        """测试列出租户"""
        manager.create_tenant("公司 A", "a@example.com", "free")
        manager.create_tenant("公司 B", "b@example.com", "basic")
        
        tenants = manager.list_tenants()
        assert len(tenants) == 2
        
        # 测试按状态过滤
        active = manager.list_tenants(status="active")
        assert len(active) == 2
    
    def test_suspend_tenant(self, manager):
        """测试暂停租户"""
        tenant_id = manager.create_tenant("测试", "test@example.com")
        
        result = manager.suspend_tenant(tenant_id)
        assert result is True
        
        tenant = manager.get_tenant(tenant_id)
        assert tenant.status == "suspended"
    
    def test_suspend_nonexistent_tenant(self, manager):
        """测试暂停不存在的租户"""
        result = manager.suspend_tenant("nonexistent")
        assert result is False
    
    def test_delete_tenant(self, manager):
        """测试删除租户"""
        tenant_id = manager.create_tenant("测试", "test@example.com")
        
        result = manager.delete_tenant(tenant_id)
        assert result is True
        
        tenant = manager.get_tenant(tenant_id)
        assert tenant.status == "deleted"
    
    def test_add_user(self, manager):
        """测试添加用户"""
        tenant_id = manager.create_tenant("测试", "owner@example.com")
        
        user_id = manager.add_user(
            tenant_id=tenant_id,
            email="user@example.com",
            name="测试用户",
            role="member"
        )
        
        assert user_id is not None
        user = manager.get_user(user_id)
        assert user.email == "user@example.com"
        assert user.role == "member"
    
    def test_add_user_with_different_roles(self, manager):
        """测试添加不同角色的用户"""
        tenant_id = manager.create_tenant("测试", "owner@example.com")
        
        # 添加管理员
        admin_id = manager.add_user(tenant_id, "admin@example.com", "Admin", "admin")
        admin = manager.get_user(admin_id)
        assert admin.role == "admin"
        assert Permission.READ in admin.permissions
        assert Permission.WRITE in admin.permissions
        assert Permission.DELETE in admin.permissions
        
        # 添加普通成员
        member_id = manager.add_user(tenant_id, "member@example.com", "Member", "member")
        member = manager.get_user(member_id)
        assert member.role == "member"
        assert Permission.READ in member.permissions
        assert Permission.WRITE in member.permissions
    
    def test_check_permission(self, manager):
        """测试权限检查"""
        tenant_id = manager.create_tenant("测试", "owner@example.com")
        user_id = manager.add_user(tenant_id, "user@example.com", "User", "member")
        
        # 成员应该有 READ 权限
        assert manager.check_permission(user_id, Permission.READ) is True
        assert manager.check_permission(user_id, Permission.WRITE) is True
        
        # 成员不应该有 ADMIN 权限
        assert manager.check_permission(user_id, Permission.ADMIN) is False
        
        # 不存在的用户
        assert manager.check_permission("nonexistent", Permission.READ) is False
    
    def test_get_quota(self, manager):
        """测试获取配额"""
        tenant_id = manager.create_tenant("测试", "test@example.com", "pro")
        
        quota = manager.get_quota(tenant_id)
        assert quota == TIER_QUOTAS[TenantTier.PRO]
    
    def test_get_quota_nonexistent_tenant(self, manager):
        """测试获取不存在租户的配额"""
        with pytest.raises(Exception):
            manager.get_quota("nonexistent")
    
    def test_check_quota(self, manager):
        """测试检查配额"""
        tenant_id = manager.create_tenant("测试", "test@example.com", "basic")
        
        # 未超限
        assert manager.check_quota(tenant_id, "users", 3) is True
        
        # 超限
        assert manager.check_quota(tenant_id, "users", 10) is False
        
        # 企业层无限制
        enterprise_id = manager.create_tenant("企业", "ent@example.com", "enterprise")
        assert manager.check_quota(enterprise_id, "users", 1000) is True
    
    def test_record_and_get_usage(self, manager):
        """测试记录和使用量查询"""
        tenant_id = manager.create_tenant("测试", "test@example.com")
        
        # 记录使用量
        manager.record_usage(tenant_id, api_calls=100, storage_mb=50.0, tasks=10)
        
        # 查询使用量
        usage = manager.get_usage(tenant_id)
        assert usage['api_calls'] == 100
        assert usage['storage_mb'] == 50.0
        assert usage['tasks_executed'] == 10
    
    def test_get_stats(self, manager):
        """测试获取统计信息"""
        manager.create_tenant("公司 A", "a@example.com", "free")
        manager.create_tenant("公司 B", "b@example.com", "pro")
        
        stats = manager.get_stats()
        assert stats['total_tenants'] == 2
        assert stats['active_tenants'] == 2
        assert stats['by_tier']['free'] == 1
        assert stats['by_tier']['pro'] == 1


class TestBillingManager:
    """测试计费管理器"""
    
    @pytest.fixture
    def billing_setup(self, tmp_path):
        """创建测试环境"""
        # 使用独立的临时目录避免数据污染
        tenant_dir = tmp_path / 'tenants' / str(os.getpid())
        billing_dir = tmp_path / 'billing' / str(os.getpid())
        tenant_mgr = TenantManager(data_dir=tenant_dir)
        billing_mgr = BillingManager.__new__(BillingManager)
        billing_mgr._tenant_manager = tenant_mgr
        billing_mgr._data_dir = billing_dir
        billing_mgr._data_dir.mkdir(parents=True, exist_ok=True)
        billing_mgr._records = {}
        
        # 创建测试租户
        tenant_id = tenant_mgr.create_tenant("测试", "test@example.com", "pro")
        
        return {
            'tenant_mgr': tenant_mgr,
            'billing_mgr': billing_mgr,
            'tenant_id': tenant_id
        }
    
    def test_generate_invoice(self, billing_setup):
        """测试生成账单"""
        billing_mgr = billing_setup['billing_mgr']
        tenant_id = billing_setup['tenant_id']
        
        invoice = billing_mgr.generate_invoice(
            tenant_id=tenant_id,
            period_start="2026-04-01",
            period_end="2026-04-30"
        )
        
        assert invoice.record_id is not None
        assert invoice.tenant_id == tenant_id
        assert invoice.amount == 499.0  # PRO 套餐价格
        assert invoice.status == "pending"
    
    def test_generate_invoice_with_overage(self, billing_setup):
        """测试生成含超额使用的账单"""
        billing_mgr = billing_setup['billing_mgr']
        tenant_mgr = billing_setup['tenant_mgr']
        tenant_id = billing_setup['tenant_id']
        
        # 记录超额使用
        tenant_mgr.record_usage(tenant_id, api_calls=15000)  # PRO 层限额 10000
        
        invoice = billing_mgr.generate_invoice(
            tenant_id=tenant_id,
            period_start="2026-04-01",
            period_end="2026-04-30"
        )
        
        # 基础费用 + 超额费用
        assert invoice.amount >= 499.0
        assert len(invoice.items) >= 1
    
    def test_list_invoices(self, billing_setup):
        """测试列出账单"""
        billing_mgr = billing_setup['billing_mgr']
        tenant_id = billing_setup['tenant_id']
        
        # 清除之前测试的残留数据
        billing_mgr._records = {}
        
        billing_mgr.generate_invoice(tenant_id, "2026-03-01", "2026-03-31")
        billing_mgr.generate_invoice(tenant_id, "2026-04-01", "2026-04-30")
        
        invoices = billing_mgr.list_invoices()
        assert len(invoices) == 2
        
        # 按租户过滤
        tenant_invoices = billing_mgr.list_invoices(tenant_id=tenant_id)
        assert len(tenant_invoices) == 2
    
    def test_mark_paid(self, billing_setup):
        """测试标记为已支付"""
        billing_mgr = billing_setup['billing_mgr']
        tenant_id = billing_setup['tenant_id']
        
        invoice = billing_mgr.generate_invoice(tenant_id, "2026-04-01", "2026-04-30")
        
        result = billing_mgr.mark_paid(invoice.record_id)
        assert result is True
        
        updated = billing_mgr.get_invoice(invoice.record_id)
        assert updated.status == "paid"
    
    def test_get_revenue(self, billing_setup):
        """测试获取收入统计"""
        billing_mgr = billing_setup['billing_mgr']
        tenant_id = billing_setup['tenant_id']
        
        # 清除之前测试的残留数据
        billing_mgr._records = {}
        
        invoice = billing_mgr.generate_invoice(tenant_id, "2026-04-01", "2026-04-30")
        billing_mgr.mark_paid(invoice.record_id)
        
        revenue = billing_mgr.get_revenue("2026-04-01", "2026-04-30")
        assert revenue['total_revenue'] == 499.0
        assert revenue['invoice_count'] == 1
    
    def test_get_stats(self, billing_setup):
        """测试获取统计信息"""
        billing_mgr = billing_setup['billing_mgr']
        tenant_id = billing_setup['tenant_id']
        
        invoice = billing_mgr.generate_invoice(tenant_id, "2026-04-01", "2026-04-30")
        billing_mgr.mark_paid(invoice.record_id)
        
        stats = billing_mgr.get_stats()
        assert stats['total_invoices'] == 1
        assert stats['total_revenue'] == 499.0


class TestEnterpriseTenantSystem:
    """测试企业级租户系统"""
    
    @pytest.fixture
    def system(self, tmp_path):
        """创建测试系统"""
        # 需要 mock 全局变量，这里简化测试
        return EnterpriseTenantSystem()
    
    def test_get_overall_stats(self, system):
        """测试获取整体统计"""
        stats = system.get_overall_stats()
        
        assert 'tenants' in stats
        assert 'billing' in stats
        assert 'total_tenants' in stats['tenants']
        assert 'total_invoices' in stats['billing']


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
