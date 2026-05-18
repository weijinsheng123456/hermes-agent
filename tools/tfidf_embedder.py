#!/usr/bin/env python3
"""
Lightweight TF-IDF Embedding Provider

当 sentence-transformers 不可用时（huggingface 不可达），
提供纯 Python TF-IDF 方案作为 embedding fallback。

优点：
- 零依赖下载
- scikit-learn 已安装
- 支持中文（基于字符级n-gram）
- 与 sentence-transformers API 兼容
"""

import logging
import os
import pickle
from pathlib import Path
from typing import List, Optional

import numpy as np

logger = logging.getLogger(__name__)

# 默认输出维度（与常见embedding模型兼容）
DEFAULT_EMBEDDING_DIM = 384

# 模型缓存路径
def _get_cache_dir() -> Path:
    hermes_home = os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes"))
    cache = Path(hermes_home) / "tfidf_cache"
    cache.mkdir(parents=True, exist_ok=True)
    return cache


class TfidfEmbedder:
    """
    TF-IDF based text embedder.
    
    API compatible with sentence_transformers.SentenceTransformer.encode()
    """
    
    def __init__(self, dim: int = DEFAULT_EMBEDDING_DIM):
        self.dim = dim
        self._vectorizer = None
        self._fitted = False
    
    def fit(self, texts: List[str]):
        """在语料上拟合TF-IDF"""
        from sklearn.feature_extraction.text import TfidfVectorizer
        
        self._vectorizer = TfidfVectorizer(
            max_features=self.dim,
            analyzer='char_wb',  # 字符级word-boundary，支持中文
            ngram_range=(2, 4),  # 2-4 gram
            sublinear_tf=True,
        )
        self._vectorizer.fit(texts)
        self._fitted = True
        logger.info(f"TF-IDF fitted on {len(texts)} texts, vocab={len(self._vectorizer.vocabulary_)}")
    
    def encode(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress_bar: bool = False,
        **kwargs,
    ) -> np.ndarray:
        """编码文本为embedding向量"""
        if not self._fitted:
            # 未拟合时使用零向量（引导阶段）
            return np.zeros((len(texts), self.dim), dtype=np.float32)
        
        if isinstance(texts, str):
            texts = [texts]
        
        # 转换
        sparse = self._vectorizer.transform(texts)
        
        # 补零到目标维度
        n_features = sparse.shape[1]
        if n_features < self.dim:
            dense = sparse.toarray().astype(np.float32)
            padded = np.zeros((len(texts), self.dim), dtype=np.float32)
            padded[:, :n_features] = dense
        else:
            padded = sparse[:, :self.dim].toarray().astype(np.float32)
        
        # L2归一化
        norms = np.linalg.norm(padded, axis=1, keepdims=True)
        norms[norms == 0] = 1
        return padded / norms
    
    def save(self, path: Optional[Path] = None):
        """保存TF-IDF模型"""
        if path is None:
            path = _get_cache_dir() / "tfidf_model.pkl"
        with open(path, 'wb') as f:
            pickle.dump({
                'vectorizer': self._vectorizer,
                'dim': self.dim,
                'fitted': self._fitted,
            }, f)
        logger.info(f"TF-IDF model saved to {path}")
    
    @classmethod
    def load(cls, path: Optional[Path] = None) -> 'TfidfEmbedder':
        """加载TF-IDF模型"""
        if path is None:
            path = _get_cache_dir() / "tfidf_model.pkl"
        
        embedder = cls()
        if path.exists():
            with open(path, 'rb') as f:
                data = pickle.load(f)
            embedder._vectorizer = data['vectorizer']
            embedder.dim = data.get('dim', DEFAULT_EMBEDDING_DIM)
            embedder._fitted = data.get('fitted', True)
            logger.info(f"TF-IDF model loaded from {path}")
        else:
            logger.warning(f"No cached TF-IDF model at {path}")
        
        return embedder


# ============================================================
# 全局单例
# ============================================================

_tfidf_embedder: Optional[TfidfEmbedder] = None


def get_tfidf_embedder(auto_load: bool = True) -> Optional[TfidfEmbedder]:
    """获取全局TF-IDF embedder实例"""
    global _tfidf_embedder
    
    if _tfidf_embedder is not None:
        return _tfidf_embedder
    
    if auto_load:
        _tfidf_embedder = TfidfEmbedder.load()
    
    return _tfidf_embedder


def fit_on_corpus(texts: List[str], save: bool = True):
    """在语料上训练TF-IDF"""
    global _tfidf_embedder
    
    _tfidf_embedder = TfidfEmbedder()
    _tfidf_embedder.fit(texts)
    if save:
        _tfidf_embedder.save()
    
    return _tfidf_embedder


# ============================================================
# SentenceTransformer 兼容接口
# ============================================================

class TfidfSentenceTransformer:
    """
    模拟 sentence_transformers.SentenceTransformer 的接口
    
    用于替代 _get_embedding_model() 中的 SentenceTransformer
    """
    
    def __init__(self, model_name: str = "tfidf-local"):
        self.model_name = model_name
        self._embedder = get_tfidf_embedder()
        
        if self._embedder is None or not self._embedder._fitted:
            # 自动用引导语料拟合
            logger.info("TF-IDF not fitted, using bootstrap corpus")
            bootstrap_texts = [
                "系统配置 环境变量 API密钥 DeepSeek",
                "微信 iLink Gateway 消息发送",
                "Cron 定时任务 调度",
                "技能 工具 Python 脚本",
                "记忆 存储 向量 数据库 ChromaDB",
                "代码质量 ruff lint 检查",
                "内容创作 公众号 小红书",
                "Niche站 SEO affiliate Amazon",
                "错误 重试 自愈 降级",
                "追踪 监控 日志 成本",
            ]
            self._embedder = fit_on_corpus(bootstrap_texts + [
                # 从技能描述中提取的高频词
                "hermes agent gateway cron weixin feishu",
                "token memory skill tool session",
                "config yaml json sqlite database",
                "wsl windows linux bash terminal",
                "deepseek openai api provider model",
            ])
    
    def encode(self, texts, **kwargs):
        if isinstance(texts, str):
            texts = [texts]
        return self._embedder.encode(texts, **kwargs)


# ============================================================
# 导出
# ============================================================

__all__ = [
    "TfidfEmbedder",
    "TfidfSentenceTransformer",
    "get_tfidf_embedder",
    "fit_on_corpus",
    "DEFAULT_EMBEDDING_DIM",
]
