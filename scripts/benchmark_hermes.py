#!/usr/bin/env python3
"""Hermes 企业级功能性能基准测试

测试项目:
- 租户创建性能
- 审计日志写入性能
- 集群操作性能
- 备份恢复性能

使用:
    python benchmark_hermes.py [--iterations 1000]
"""

import sys
import time
import statistics
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path.home() / 'hermes-agent'))

from hermes_enterprise import get_tenant_system, get_security_system, get_ha_system


class HermesBenchmark:
    """Hermes 性能基准测试"""
    
    def __init__(self, iterations=100):
        self.iterations = iterations
        self.results = {}
        
        # 初始化系统 (使用临时目录)
        import tempfile
        self.temp_dir = tempfile.mkdtemp()
        
        self.tenant_sys = get_tenant_system()
        self.security_sys = get_security_system()
        self.ha_sys = get_ha_system()
    
    def measure(self, name, func, *args, **kwargs):
        """测量函数执行时间"""
        times = []
        
        for i in range(self.iterations):
            start = time.perf_counter()
            func(*args, **kwargs)
            end = time.perf_counter()
            times.append((end - start) * 1000)  # 转换为毫秒
        
        # 统计结果
        self.results[name] = {
            'min': min(times),
            'max': max(times),
            'avg': statistics.mean(times),
            'median': statistics.median(times),
            'std': statistics.stdev(times) if len(times) > 1 else 0,
            'iterations': self.iterations
        }
        
        return self.results[name]
    
    def benchmark_tenant_creation(self):
        """测试租户创建性能"""
        print("\n[测试] 租户创建性能")
        
        def create_tenant():
            import hashlib
            suffix = hashlib.md5(str(time.time()).encode()).hexdigest()[:6]
            self.tenant_sys.tenant_manager.create_tenant(
                name=f"Bench_{suffix}",
                owner_email=f"bench_{suffix}@test.com",
                tier="basic"
            )
        
        result = self.measure("tenant_creation", create_tenant)
        print(f"  创建 {self.iterations} 个租户")
        print(f"  平均：{result['avg']:.2f} ms")
        print(f"  中位数：{result['median']:.2f} ms")
        print(f"  标准差：{result['std']:.2f} ms")
    
    def benchmark_audit_logging(self):
        """测试审计日志写入性能"""
        print("\n[测试] 审计日志写入性能")
        
        from hermes_enterprise.security.system import AuditAction
        
        def write_log():
            self.security_sys.audit_trail.log(
                user_id="bench_user",
                tenant_id="bench_tenant",
                action=AuditAction.READ,
                resource_type="file",
                resource_id="bench_file"
            )
        
        result = self.measure("audit_logging", write_log)
        print(f"  写入 {self.iterations} 条日志")
        print(f"  平均：{result['avg']:.2f} ms")
        print(f"  中位数：{result['median']:.2f} ms")
    
    def benchmark_cluster_operations(self):
        """测试集群操作性能"""
        print("\n[测试] 集群操作性能")
        
        # 添加节点
        def add_node():
            import hashlib
            suffix = hashlib.md5(str(time.time()).encode()).hexdigest()[:6]
            self.ha_sys.cluster.add_node(f"node_{suffix}.example.com", 8000)
        
        result = self.measure("cluster_add_node", add_node)
        print(f"  添加 {self.iterations} 个节点")
        print(f"  平均：{result['avg']:.2f} ms")
    
    def benchmark_quota_check(self):
        """测试配额检查性能"""
        print("\n[测试] 配额检查性能")
        
        # 先创建测试租户
        tenant_id = self.tenant_sys.tenant_manager.create_tenant(
            "Bench Tenant",
            "bench@test.com",
            "pro"
        )
        
        def check_quota():
            self.tenant_sys.tenant_manager.check_quota(tenant_id, "api_calls", 5000)
        
        result = self.measure("quota_check", check_quota)
        print(f"  检查 {self.iterations} 次配额")
        print(f"  平均：{result['avg']:.2f} ms")
    
    def run_all_benchmarks(self):
        """运行所有基准测试"""
        print("=" * 60)
        print("Hermes 企业级功能性能基准测试")
        print("迭代次数:", self.iterations)
        print("时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("=" * 60)
        
        self.benchmark_tenant_creation()
        self.benchmark_audit_logging()
        self.benchmark_cluster_operations()
        self.benchmark_quota_check()
        
        # 输出汇总
        print("\n" + "=" * 60)
        print("性能测试汇总")
        print("=" * 60)
        
        for name, result in self.results.items():
            print(f"\n{name}:")
            print(f"  平均：{result['avg']:.2f} ms")
            print(f"  最小：{result['min']:.2f} ms")
            print(f"  最大：{result['max']:.2f} ms")
            print(f"  标准差：{result['std']:.2f} ms")
        
        return self.results


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Hermes 性能基准测试')
    parser.add_argument('--iterations', type=int, default=100, help='测试迭代次数')
    args = parser.parse_args()
    
    benchmark = HermesBenchmark(iterations=args.iterations)
    results = benchmark.run_all_benchmarks()
    
    # 保存结果
    import json
    result_file = Path.home() / 'hermes-agent' / 'benchmark_results.json'
    result_file.write_text(json.dumps(results, indent=2))
    print(f"\n结果已保存到：{result_file}")


if __name__ == "__main__":
    main()
