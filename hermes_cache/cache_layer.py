"""Hermes Agent 请求缓存层

功能:
- LLM API 响应缓存
- 工具调用结果缓存
- 自动过期和清理
- 支持内存和磁盘缓存

版本：1.0
创建日期：2026-04-22
"""

import hashlib
import json
import time
import threading
from pathlib import Path
from typing import Any, Dict, Optional, Callable
from dataclasses import dataclass, field
from functools import wraps
import logging

logger = logging.getLogger('hermes.cache')


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: float
    expires_at: float
    hit_count: int = 0
    metadata: Dict = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        return time.time() > self.expires_at
    
    def ttl(self) -> float:
        return max(0, self.expires_at - time.time())


class CacheBackend:
    """缓存后端基类"""
    
    def get(self, key: str) -> Optional[CacheEntry]:
        raise NotImplementedError
    
    def set(self, key: str, entry: CacheEntry) -> None:
        raise NotImplementedError
    
    def delete(self, key: str) -> bool:
        raise NotImplementedError
    
    def clear(self) -> None:
        raise NotImplementedError
    
    def stats(self) -> Dict:
        raise NotImplementedError


class MemoryCacheBackend(CacheBackend):
    """内存缓存后端"""
    
    def __init__(self, max_size: int = 1000):
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._max_size = max_size
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[CacheEntry]:
        with self._lock:
            entry = self._cache.get(key)
            if entry:
                if entry.is_expired():
                    del self._cache[key]
                    self._misses += 1
                    return None
                entry.hit_count += 1
                self._hits += 1
                return entry
            self._misses += 1
            return None
    
    def set(self, key: str, entry: CacheEntry) -> None:
        with self._lock:
            # LRU 淘汰
            if len(self._cache) >= self._max_size:
                oldest_key = min(
                    self._cache.keys(),
                    key=lambda k: self._cache[k].created_at
                )
                del self._cache[oldest_key]
            
            self._cache[key] = entry
    
    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
    
    def stats(self) -> Dict:
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0
            return {
                'backend': 'memory',
                'size': len(self._cache),
                'max_size': self._max_size,
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': f"{hit_rate:.1f}%"
            }


class DiskCacheBackend(CacheBackend):
    """磁盘缓存后端"""
    
    def __init__(self, cache_dir: Path, max_size_mb: float = 100.0):
        self._cache_dir = Path(cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._max_size_bytes = int(max_size_mb * 1024 * 1024)
        self._index_file = self._cache_dir / 'index.json'
        self._index: Dict[str, Dict] = self._load_index()
    
    def _load_index(self) -> Dict:
        if self._index_file.exists():
            try:
                return json.loads(self._index_file.read_text())
            except Exception:
                return {}
        return {}
    
    def _save_index(self):
        try:
            self._index_file.write_text(json.dumps(self._index, indent=2))
        except Exception as e:
            logger.error(f"保存索引失败：{e}")
    
    def _key_to_filename(self, key: str) -> str:
        return hashlib.sha256(key.encode()).hexdigest()[:16] + '.json'
    
    def get(self, key: str) -> Optional[CacheEntry]:
        with self._lock:
            if key not in self._index:
                return None
            
            meta = self._index[key]
            if time.time() > meta['expires_at']:
                self.delete(key)
                return None
            
            file_path = self._cache_dir / self._key_to_filename(key)
            if not file_path.exists():
                del self._index[key]
                self._save_index()
                return None
            
            try:
                data = json.loads(file_path.read_text())
                entry = CacheEntry(**data)
                entry.hit_count += 1
                # 更新命中计数
                meta['hit_count'] = entry.hit_count
                self._save_index()
                return entry
            except Exception as e:
                logger.error(f"读取缓存失败：{e}")
                return None
    
    def set(self, key: str, entry: CacheEntry) -> None:
        with self._lock:
            # 检查磁盘空间
            current_size = sum(
                f.stat().st_size for f in self._cache_dir.glob('*.json')
                if f.is_file()
            )
            
            # 如果超过限制，清理最旧的条目
            while current_size > self._max_size_bytes and self._index:
                oldest_key = min(
                    self._index.keys(),
                    key=lambda k: self._index[k]['created_at']
                )
                self.delete(oldest_key)
                current_size = sum(
                    f.stat().st_size for f in self._cache_dir.glob('*.json')
                    if f.is_file()
                )
            
            # 保存条目
            file_path = self._cache_dir / self._key_to_filename(key)
            data = {
                'key': entry.key,
                'value': entry.value,
                'created_at': entry.created_at,
                'expires_at': entry.expires_at,
                'hit_count': entry.hit_count,
                'metadata': entry.metadata
            }
            file_path.write_text(json.dumps(data, indent=2))
            
            self._index[key] = {
                'created_at': entry.created_at,
                'expires_at': entry.expires_at,
                'hit_count': entry.hit_count,
                'file': file_path.name
            }
            self._save_index()
    
    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._index:
                file_name = self._index[key].get('file')
                if file_name:
                    file_path = self._cache_dir / file_name
                    if file_path.exists():
                        file_path.unlink()
                del self._index[key]
                self._save_index()
                return True
            return False
    
    def clear(self) -> None:
        with self._lock:
            for f in self._cache_dir.glob('*.json'):
                if f.is_file():
                    f.unlink()
            self._index = {}
            self._save_index()
    
    def stats(self) -> Dict:
        with self._lock:
            total_size = sum(
                f.stat().st_size for f in self._cache_dir.glob('*.json')
                if f.is_file()
            )
            return {
                'backend': 'disk',
                'size': len(self._index),
                'total_size_mb': f"{total_size / 1024 / 1024:.2f}",
                'max_size_mb': f"{self._max_size_bytes / 1024 / 1024:.2f}"
            }


class HermesCache:
    """Hermes 统一缓存系统"""
    
    def __init__(
        self,
        memory_cache: bool = True,
        disk_cache: bool = True,
        cache_dir: Optional[Path] = None,
        default_ttl: int = 3600,  # 1 小时
        memory_max_size: int = 1000,
        disk_max_size_mb: float = 100.0
    ):
        self._memory_backend = MemoryCacheBackend(memory_max_size) if memory_cache else None
        self._disk_backend = DiskCacheBackend(
            cache_dir or Path.home() / '.hermes' / 'cache',
            disk_max_size_mb
        ) if disk_cache else None
        self._default_ttl = default_ttl
        self._lock = threading.RLock()
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """生成缓存键"""
        key_data = json.dumps({'args': args, 'kwargs': kwargs}, sort_keys=True)
        hash_value = hashlib.sha256(key_data.encode()).hexdigest()[:16]
        return f"{prefix}:{hash_value}"
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        # 先查内存
        if self._memory_backend:
            entry = self._memory_backend.get(key)
            if entry:
                return entry.value
        
        # 再查磁盘
        if self._disk_backend:
            entry = self._disk_backend.get(key)
            if entry:
                # 回填到内存
                if self._memory_backend:
                    self._memory_backend.set(key, entry)
                return entry.value
        
        return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        metadata: Optional[Dict] = None
    ) -> None:
        """设置缓存值"""
        ttl = ttl or self._default_ttl
        now = time.time()
        
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=now,
            expires_at=now + ttl,
            metadata=metadata or {}
        )
        
        # 同时写入内存和磁盘
        if self._memory_backend:
            self._memory_backend.set(key, entry)
        if self._disk_backend:
            self._disk_backend.set(key, entry)
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        deleted = False
        if self._memory_backend:
            deleted = self._memory_backend.delete(key) or deleted
        if self._disk_backend:
            deleted = self._disk_backend.delete(key) or deleted
        return deleted
    
    def clear(self) -> None:
        """清空缓存"""
        if self._memory_backend:
            self._memory_backend.clear()
        if self._disk_backend:
            self._disk_backend.clear()
    
    def cached(
        self,
        prefix: str = 'default',
        ttl: Optional[int] = None,
        key_fn: Optional[Callable] = None
    ):
        """缓存装饰器
        
        Usage:
            @cache.cached(prefix='api_response', ttl=3600)
            def fetch_data(url):
                ...
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # 生成缓存键
                if key_fn:
                    cache_key = key_fn(*args, **kwargs)
                else:
                    cache_key = self._generate_key(prefix, *args, **kwargs)
                
                # 尝试从缓存获取
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    logger.debug(f"缓存命中：{cache_key}")
                    return cached_value
                
                # 执行函数
                result = func(*args, **kwargs)
                
                # 存入缓存
                self.set(cache_key, result, ttl=ttl)
                logger.debug(f"缓存已设置：{cache_key}")
                
                return result
            return wrapper
        return decorator
    
    def stats(self) -> Dict:
        """获取缓存统计"""
        stats = {'backends': []}
        
        if self._memory_backend:
            stats['backends'].append(self._memory_backend.stats())
        if self._disk_backend:
            stats['backends'].append(self._disk_backend.stats())
        
        return stats
    
    def cleanup_expired(self) -> int:
        """清理过期条目"""
        count = 0
        
        # 内存缓存会自动清理
        # 磁盘缓存需要手动清理
        if self._disk_backend:
            with self._disk_backend._lock:
                expired_keys = [
                    key for key, meta in self._disk_backend._index.items()
                    if time.time() > meta['expires_at']
                ]
                for key in expired_keys:
                    self._disk_backend.delete(key)
                    count += 1
        
        logger.info(f"清理了 {count} 个过期缓存条目")
        return count


# 全局缓存实例
_global_cache: Optional[HermesCache] = None


def get_cache() -> HermesCache:
    """获取全局缓存实例"""
    global _global_cache
    if _global_cache is None:
        _global_cache = HermesCache()
    return _global_cache


def init_cache(
    memory_cache: bool = True,
    disk_cache: bool = True,
    cache_dir: Optional[Path] = None,
    default_ttl: int = 3600
) -> HermesCache:
    """初始化全局缓存"""
    global _global_cache
    _global_cache = HermesCache(
        memory_cache=memory_cache,
        disk_cache=disk_cache,
        cache_dir=cache_dir,
        default_ttl=default_ttl
    )
    return _global_cache


__all__ = [
    'CacheEntry',
    'CacheBackend',
    'MemoryCacheBackend',
    'DiskCacheBackend',
    'HermesCache',
    'get_cache',
    'init_cache'
]
