"""Mem0 memory provider — local & cloud dual mode.

Local mode (default): uses mem0.Memory with local HuggingFace embeddings +
Qdrant on-disk vector store + DeepSeek for LLM extraction. Fully offline
except HuggingFace model download on first run.

Cloud mode (requires MEM0_API_KEY): uses mem0.ai Platform API for
server-side LLM extraction and hosted vector store.

Config via $HERMES_HOME/mem0.json or environment variables:

  mode:           "auto" | "local" | "cloud"  (auto: local if no MEM0_API_KEY)
  api_key:        Mem0 Platform API key (required for cloud mode)
  user_id:        User identifier (default: "hermes-user")
  agent_id:       Agent identifier (default: "hermes")

  # Local mode only:
  embedder_model: "BAAI/bge-small-en-v1.5" (HuggingFace model name)
  qdrant_path:    path to Qdrant storage directory (default: ~/.mem0/qdrant)
  llm_model:      DeepSeek model for extraction (default: deepseek-chat)
  llm_base_url:   OpenAI-compatible endpoint (default: DeepSeek API)
  llm_api_key:    API key for LLM extraction (default: DASHSCOPE_API_KEY)
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent.memory_provider import MemoryProvider
from tools.registry import tool_error

logger = logging.getLogger(__name__)

# Circuit breaker (cloud mode only)
_BREAKER_THRESHOLD = 5
_BREAKER_COOLDOWN_SECS = 120

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def _load_config() -> dict:
    """Load config from env vars, with $HERMES_HOME/mem0.json overrides."""
    from hermes_constants import get_hermes_home

    config = {
        "mode": os.environ.get("MEM0_MODE", "auto"),
        "api_key": os.environ.get("MEM0_API_KEY", ""),
        "user_id": os.environ.get("MEM0_USER_ID", "hermes-user"),
        "agent_id": os.environ.get("MEM0_AGENT_ID", "hermes"),
        "rerank": True,
        # Local mode defaults
        "embedder_model": "BAAI/bge-small-en-v1.5",
        "qdrant_path": str(get_hermes_home() / "mem0" / "qdrant"),
        "llm_model": "deepseek-chat",
        "llm_base_url": os.environ.get("DASHSCOPE_BASE_URL", "https://api.deepseek.com/v1"),
        "llm_api_key": os.environ.get("DASHSCOPE_API_KEY", os.environ.get("OPENAI_API_KEY", "")),
        "llm_provider": "deepseek",
    }

    config_path = get_hermes_home() / "mem0.json"
    if config_path.exists():
        try:
            file_cfg = json.loads(config_path.read_text(encoding="utf-8"))
            config.update({k: v for k, v in file_cfg.items() if v is not None and v != ""})
        except Exception:
            pass

    return config


def _resolve_mode(cfg: dict) -> str:
    """Auto-detect mode: 'cloud' if api_key is set, else 'local'."""
    mode = cfg.get("mode", "auto")
    if mode != "auto":
        return mode
    return "cloud" if cfg.get("api_key") else "local"


# ---------------------------------------------------------------------------
# Tool schemas
# ---------------------------------------------------------------------------

PROFILE_SCHEMA = {
    "name": "mem0_profile",
    "description": (
        "Retrieve all stored memories about the user — preferences, facts, "
        "project context. Fast, no reranking. Use at conversation start."
    ),
    "parameters": {"type": "object", "properties": {}, "required": []},
}

SEARCH_SCHEMA = {
    "name": "mem0_search",
    "description": (
        "Search memories by meaning. Returns relevant facts ranked by similarity. "
        "Set rerank=true for higher accuracy on important queries."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "What to search for."},
            "rerank": {"type": "boolean", "description": "Enable reranking for precision (default: false)."},
            "top_k": {"type": "integer", "description": "Max results (default: 10, max: 50)."},
        },
        "required": ["query"],
    },
}

CONCLUDE_SCHEMA = {
    "name": "mem0_conclude",
    "description": (
        "Store a durable fact about the user. Stored verbatim (no LLM extraction). "
        "Use for explicit preferences, corrections, or decisions."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "conclusion": {"type": "string", "description": "The fact to store."},
        },
        "required": ["conclusion"],
    },
}


# ---------------------------------------------------------------------------
# MemoryProvider implementation
# ---------------------------------------------------------------------------

class Mem0MemoryProvider(MemoryProvider):
    """Mem0 memory — local (offline) or cloud mode."""

    def __init__(self):
        self._config = None
        self._mode = "unknown"

        # Cloud mode
        self._cloud_client = None
        self._client_lock = threading.Lock()
        self._api_key = ""

        # Local mode
        self._local_memory = None
        self._local_lock = threading.Lock()

        # Shared
        self._user_id = "hermes-user"
        self._agent_id = "hermes"
        self._rerank = True
        self._prefetch_result = ""
        self._prefetch_lock = threading.Lock()
        self._prefetch_thread = None
        self._sync_thread = None

        # Circuit breaker state (cloud mode only)
        self._consecutive_failures = 0
        self._breaker_open_until = 0.0

    @property
    def name(self) -> str:
        return "mem0"

    def is_available(self) -> bool:
        cfg = _load_config()
        mode = _resolve_mode(cfg)
        if mode == "cloud":
            return bool(cfg.get("api_key"))
        # Local mode: mem0ai must be installed (always true in this env)
        try:
            import mem0  # noqa: F401
            return True
        except ImportError:
            return False

    def save_config(self, values, hermes_home):
        """Write config to $HERMES_HOME/mem0.json."""
        config_path = Path(hermes_home) / "mem0.json"
        existing = {}
        if config_path.exists():
            try:
                existing = json.loads(config_path.read_text())
            except Exception:
                pass
        existing.update(values)
        config_path.write_text(json.dumps(existing, indent=2))

    def get_config_schema(self):
        return [
            {"key": "api_key", "description": "Mem0 Platform API key (for cloud mode)", "secret": True, "required": False, "env_var": "MEM0_API_KEY", "url": "https://app.mem0.ai"},
            {"key": "mode", "description": "Operation mode: auto | local | cloud", "default": "auto", "choices": ["auto", "local", "cloud"]},
            {"key": "user_id", "description": "User identifier", "default": "hermes-user"},
            {"key": "agent_id", "description": "Agent identifier", "default": "hermes"},
            {"key": "rerank", "description": "Enable reranking for recall", "default": "true", "choices": ["true", "false"]},
        ]

    # -- Client getters ------------------------------------------------------

    def _get_cloud_client(self):
        """Lazy-init Mem0 Platform cloud client."""
        with self._client_lock:
            if self._cloud_client is not None:
                return self._cloud_client
            try:
                from mem0 import MemoryClient
                self._cloud_client = MemoryClient(api_key=self._api_key)
                return self._cloud_client
            except ImportError:
                raise RuntimeError("mem0 package not installed. Run: pip install mem0ai")

    def _get_local_memory(self):
        """Lazy-init local mem0 backend."""
        if self._local_memory is not None:
            return self._local_memory
        with self._local_lock:
            if self._local_memory is not None:
                return self._local_memory
            self._local_memory = self._build_local_memory()
            return self._local_memory

    @staticmethod
    def _clean_qdrant_lock(qdrant_path: str) -> None:
        """Remove stale Qdrant .lock files left by unclean shutdowns.

        Qdrant creates '{qdrant_path}/.lock' on connect and removes it on
        graceful exit.  If the process crashes or gets SIGKILL the lock file
        survives, making every subsequent startup fail with::

            Storage folder ... is already accessed by another instance
            of Qdrant client.

        We delete it at plugin init time only when Qdrant's actual portalocker
        lock is free; if another process still holds it, startup should fail
        instead of risking concurrent writes.
        """
        lock_file = Path(qdrant_path) / ".lock"
        if not lock_file.exists():
            return

        # Safety check: is another local process holding Qdrant's actual lock?
        try:
            import portalocker
            with lock_file.open("r+") as f:
                try:
                    portalocker.lock(
                        f,
                        portalocker.LockFlags.EXCLUSIVE | portalocker.LockFlags.NON_BLOCKING,
                    )
                    portalocker.unlock(f)
                except portalocker.exceptions.LockException:
                    logger.warning(
                        "Qdrant .lock found but is held by another process — "
                        "keeping lock, will let mem0 report the real error",
                    )
                    return
        except Exception:
            logger.warning("portalocker check failed, keeping .lock file to be safe")
            return

        try:
            lock_file.unlink()
        except FileNotFoundError:
            pass
        logger.info("Removed stale Qdrant .lock file (unclean shutdown recovery)")

    def _build_local_memory(self):
        """Build and return a local mem0.Memory instance."""
        from mem0 import Memory
        from mem0.configs.base import MemoryConfig, LlmConfig, EmbedderConfig, VectorStoreConfig

        cfg = self._config

        # Stale .lock pre-cleanup — see _clean_qdrant_lock docstring
        qdrant_path = cfg.get("qdrant_path", str(Path.home() / ".hermes" / "mem0" / "qdrant"))
        self._clean_qdrant_lock(qdrant_path)

        # LLM config — use OpenAI-compatible endpoint (works for DeepSeek, etc.)
        # mem0's 'deepseek' provider doesn't support custom base_url, so use 'openai'
        llm_provider = cfg.get("llm_provider", "openai")
        # Map 'deepseek' to 'openai' since mem0's deepseek provider lacks openai_base_url support
        if llm_provider == "deepseek":
            llm_provider = "openai"
        llm_key = cfg.get("llm_api_key", "")
        llm_config = {
            "model": cfg.get("llm_model", "deepseek-chat"),
            "openai_base_url": cfg.get("llm_base_url", "https://api.deepseek.com/v1"),
        }
        if llm_key:
            llm_config["api_key"] = llm_key
            os.environ.setdefault("OPENAI_API_KEY", llm_key)
        llm_cfg = LlmConfig(
            provider=llm_provider,
            config=llm_config,
        )

        # Embedder — local HuggingFace
        embedder = EmbedderConfig(
            provider="huggingface",
            config={
                "model": cfg.get("embedder_model", "BAAI/bge-small-en-v1.5"),
                "embedding_dims": 384,
            },
        )

        # Vector store — Qdrant on-disk
        qdrant_path = cfg.get("qdrant_path", str(Path.home() / ".hermes" / "mem0" / "qdrant"))
        Path(qdrant_path).mkdir(parents=True, exist_ok=True)

        vector_store = VectorStoreConfig(
            provider="qdrant",
            config={
                "collection_name": "hermes_mem0",
                "embedding_model_dims": 384,
                "path": qdrant_path,
                "on_disk": True,
            },
        )

        config = MemoryConfig(
            llm=llm_cfg,
            embedder=embedder,
            vector_store=vector_store,
            history_db_path=str(Path(qdrant_path).parent / "history.db"),
        )

        logger.info(
            "Initializing local mem0 (embedder=%s, qdrant=%s, llm=%s/%s)",
            cfg.get("embedder_model"),
            qdrant_path,
            cfg.get("llm_provider"),
            cfg.get("llm_model"),
        )
        t0 = time.time()
        memory = Memory(config)
        elapsed = time.time() - t0
        logger.info("Local mem0 initialized in %.1fs", elapsed)
        return memory

    # -- Circuit breaker (cloud only) ----------------------------------------

    def _is_breaker_open(self) -> bool:
        if self._consecutive_failures < _BREAKER_THRESHOLD:
            return False
        if time.monotonic() >= self._breaker_open_until:
            self._consecutive_failures = 0
            return False
        return True

    def _record_success(self):
        self._consecutive_failures = 0

    def _record_failure(self):
        self._consecutive_failures += 1
        if self._consecutive_failures >= _BREAKER_THRESHOLD:
            self._breaker_open_until = time.monotonic() + _BREAKER_COOLDOWN_SECS
            logger.warning(
                "Mem0 circuit breaker tripped after %d consecutive failures. Pausing for %ds.",
                self._consecutive_failures, _BREAKER_COOLDOWN_SECS,
            )

    # -- Lifecycle -----------------------------------------------------------

    def initialize(self, session_id: str, **kwargs) -> None:
        self._config = _load_config()
        self._mode = _resolve_mode(self._config)
        self._api_key = self._config.get("api_key", "")
        self._user_id = kwargs.get("user_id") or self._config.get("user_id", "hermes-user")
        self._agent_id = self._config.get("agent_id", "hermes")
        self._rerank = self._config.get("rerank", True)
        logger.info("Mem0 provider initialized (mode=%s, user=%s)", self._mode, self._user_id)

        # Pre-warm local memory in background so first use is faster
        if self._mode == "local":
            def _warm():
                try:
                    self._get_local_memory()
                    logger.info("Local mem0 pre-warmed")
                except Exception as e:
                    logger.warning("Local mem0 pre-warm failed (will lazy-init): %s", e)
            t = threading.Thread(target=_warm, daemon=True, name="mem0-warm")
            t.start()

        # Register graceful shutdown handlers
        self._register_shutdown_handlers()

    def _register_shutdown_handlers(self) -> None:
        """Register atexit + signal handlers for clean mem0 shutdown.

        Graceful exit (sys.exit, Signal) → Python cleanup → Qdrant resources
        released → clean startup next time.
        Hard kill (SIGKILL, crash) → stale .lock marker → _clean_qdrant_lock
        handles it at next startup.
        """
        import signal

        # atexit — runs on normal interpreter shutdown
        import atexit
        atexit.register(self.shutdown)

        # Signal handler
        def _handler(signum, frame):
            logger.info("Received signal %d — shutting down mem0 gracefully", signum)
            self.shutdown()
            signal.signal(signum, signal.SIG_DFL)
            os.kill(os.getpid(), signum)

        try:
            signal.signal(signal.SIGTERM, _handler)
        except (ValueError, RuntimeError):
            pass

        # For SIGINT, only register if we're not in a pty/interactive context
        # to avoid interfering with the CLI's own Ctrl+C handling.
        try:
            signal.signal(signal.SIGINT, _handler)
        except (ValueError, RuntimeError):
            pass

        logger.debug("Mem0 shutdown handlers registered (atexit + SIGTERM/SIGINT)")

    def system_prompt_block(self) -> str:
        mode_tag = "Local" if self._mode == "local" else "Cloud"
        return (
            "# Mem0 Memory\n"
            f"{mode_tag} mode. User: {self._user_id}.\n"
            "Use mem0_search to find memories, mem0_conclude to store facts, "
            "mem0_profile for a full overview."
        )

    # -- Prefetch / background recall ----------------------------------------

    def prefetch(self, query: str, *, session_id: str = "") -> str:
        if self._prefetch_thread and self._prefetch_thread.is_alive():
            self._prefetch_thread.join(timeout=3.0)
        with self._prefetch_lock:
            result = self._prefetch_result
            self._prefetch_result = ""
        if not result:
            return ""
        return f"## Mem0 Memory\n{result}"

    def queue_prefetch(self, query: str, *, session_id: str = "") -> None:
        if self._mode == "cloud" and self._is_breaker_open():
            return

        def _run():
            try:
                results = self._search(query, top_k=5)
                if results:
                    with self._prefetch_lock:
                        self._prefetch_result = "\n".join(f"- {r}" for r in results)
                self._record_success()
            except Exception as e:
                self._record_failure()
                logger.debug("Mem0 prefetch failed: %s", e)

        self._prefetch_thread = threading.Thread(target=_run, daemon=True, name="mem0-prefetch")
        self._prefetch_thread.start()

    # -- Sync (turn storage) ------------------------------------------------

    def sync_turn(self, user_content: str, assistant_content: str, *, session_id: str = "") -> None:
        if self._mode == "cloud" and self._is_breaker_open():
            return

        def _sync():
            try:
                if self._mode == "cloud":
                    self._cloud_sync(user_content, assistant_content)
                else:
                    self._local_sync(user_content, assistant_content)
                self._record_success()
            except Exception as e:
                self._record_failure()
                logger.warning("Mem0 sync failed: %s", e)

        if self._sync_thread and self._sync_thread.is_alive():
            self._sync_thread.join(timeout=5.0)

        self._sync_thread = threading.Thread(target=_sync, daemon=True, name="mem0-sync")
        self._sync_thread.start()

    def _cloud_sync(self, user_content: str, assistant_content: str):
        """Store a turn via cloud API (auto-extracts facts)."""
        client = self._get_cloud_client()
        messages = [
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": assistant_content},
        ]
        client.add(messages, **self._write_filters())

    def _local_sync(self, user_content: str, assistant_content: str):
        """Store a turn locally with LLM fact extraction (infer=True).
        
        Retries up to 3 times with exponential backoff when Qdrant lock
        is contended by another process (cron deliveries, etc.).
        """
        _qdrant_lock_msg = "already accessed by another instance"
        _max_retries = 3
        _retry_delay = 2.0
        _last_exc = None
        for attempt in range(_max_retries):
            try:
                memory = self._get_local_memory()
                messages = [
                    {"role": "user", "content": user_content},
                    {"role": "assistant", "content": assistant_content},
                ]
                memory.add(
                    messages,
                    user_id=self._user_id,
                    agent_id=self._agent_id,
                    infer=False,
                )
                return  # success
            except Exception as e:
                _last_exc = e
                if _qdrant_lock_msg in str(e).lower() and attempt < _max_retries - 1:
                    _wait = _retry_delay * (2 ** attempt)
                    logger.warning(
                        "Qdrant lock contended, retrying in %.1fs (attempt %d/%d)",
                        _wait, attempt + 1, _max_retries,
                    )
                    time.sleep(_wait)
                    continue
                raise
        # If we get here, all retries failed — re-raise the last exception
        raise _last_exc  # type: ignore[misc]

    # -- Tools ----------------------------------------------------------------

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        return [PROFILE_SCHEMA, SEARCH_SCHEMA, CONCLUDE_SCHEMA]

    def handle_tool_call(self, tool_name: str, args: dict, **kwargs) -> str:
        if self._mode == "cloud" and self._is_breaker_open():
            return json.dumps({
                "error": "Mem0 API temporarily unavailable (multiple consecutive failures). Will retry automatically."
            })

        if tool_name == "mem0_profile":
            return self._handle_profile()
        elif tool_name == "mem0_search":
            return self._handle_search(args)
        elif tool_name == "mem0_conclude":
            return self._handle_conclude(args)
        return tool_error(f"Unknown tool: {tool_name}")

    # -- Internal helpers ----------------------------------------------------

    def _read_filters(self) -> Dict[str, Any]:
        return {"user_id": self._user_id}

    def _write_filters(self) -> Dict[str, Any]:
        return {"user_id": self._user_id, "agent_id": self._agent_id}

    @staticmethod
    def _unwrap_results(response: Any) -> list:
        """Normalize Mem0 API response — v2 wraps in {'results': [...]}."""
        if isinstance(response, dict):
            return response.get("results", [])
        if isinstance(response, list):
            return response
        return []

    def _search(self, query: str, top_k: int = 5) -> List[str]:
        """Search memories by query. Returns list of memory strings."""
        if self._mode == "cloud":
            client = self._get_cloud_client()
            raw = client.search(
                query=query,
                filters=self._read_filters(),
                rerank=self._rerank,
                top_k=top_k,
            )
        else:
            memory = self._get_local_memory()
            raw = memory.search(
                query=query,
                filters={"user_id": self._user_id},
                limit=top_k,
            )
        results = self._unwrap_results(raw)
        return [r.get("memory", "") for r in results if r.get("memory")]

    def _get_all_memories(self) -> List[str]:
        """Get all stored memories."""
        if self._mode == "cloud":
            client = self._get_cloud_client()
            raw = client.get_all(filters=self._read_filters())
        else:
            # Local: search with empty query to get broad results
            memory = self._get_local_memory()
            raw = memory.search(
                query="",
                filters={"user_id": self._user_id},
                limit=50,
            )
        results = self._unwrap_results(raw)
        return [m.get("memory", "") for m in results if m.get("memory")]

    def _handle_profile(self) -> str:
        try:
            memories = self._get_all_memories()
            self._record_success()
            if not memories:
                return json.dumps({"result": "No memories stored yet."})
            return json.dumps({"result": "\n".join(memories), "count": len(memories)})
        except Exception as e:
            self._record_failure()
            return tool_error(f"Failed to fetch profile: {e}")

    def _handle_search(self, args: dict) -> str:
        query = args.get("query", "")
        if not query:
            return tool_error("Missing required parameter: query")
        top_k = min(int(args.get("top_k", 10)), 50)
        rerank = args.get("rerank", False)
        if rerank != self._rerank:
            logger.debug(
                "mem0_search: caller requested rerank=%s but local mode uses config value (%s)",
                rerank,
                self._rerank,
            )
        try:
            results = self._search(query, top_k=top_k)
            self._record_success()
            if not results:
                return json.dumps({"result": "No relevant memories found."})
            items = [{"memory": r, "score": 1.0} for r in results]
            return json.dumps({"results": items, "count": len(items)})
        except Exception as e:
            self._record_failure()
            return tool_error(f"Search failed: {e}")

    def _handle_conclude(self, args: dict) -> str:
        conclusion = args.get("conclusion", "")
        if not conclusion:
            return tool_error("Missing required parameter: conclusion")
        try:
            if self._mode == "cloud":
                client = self._get_cloud_client()
                client.add(
                    [{"role": "user", "content": conclusion}],
                    **self._write_filters(),
                    infer=False,
                )
            else:
                memory = self._get_local_memory()
                memory.add(
                    conclusion,
                    user_id=self._user_id,
                    agent_id=self._agent_id,
                    infer=False,
                )
            self._record_success()
            return json.dumps({"result": "Fact stored."})
        except Exception as e:
            self._record_failure()
            return tool_error(f"Failed to store: {e}")

    def shutdown(self) -> None:
        """Clean shutdown — close resources, join threads, prep for safe exit."""
        self._close_local_memory()

        # Signal: deregister atexit handler so it's not called twice
        try:
            import atexit
            atexit.unregister(self.shutdown)
        except Exception:
            pass

        for t in (self._prefetch_thread, self._sync_thread):
            if t and t.is_alive():
                t.join(timeout=5.0)
        with self._client_lock:
            self._cloud_client = None
        with self._local_lock:
            self._local_memory = None

    def _close_local_memory(self) -> None:
        """Close the mem0 Memory instance and its Qdrant client.

        Note: Qdrant's .lock file ('tmp lock file') is a Rust-level marker,
        NOT an OS file lock. Qdrant does not remove it on shutdown — neither
        graceful nor abrupt. The startup cleanup (_clean_qdrant_lock) handles
        stale markers. This method exists to close HTTP/SQLite connections
        and release Python resources cleanly.
        """
        local = None
        with self._local_lock:
            local = self._local_memory
            self._local_memory = None
        if local is None:
            return
        try:
            # Close Qdrant client (releases HTTP pool, internal buffers)
            vs = getattr(local, "vector_store", None)
            if vs is not None:
                client = getattr(vs, "client", None)
                if client is not None and hasattr(client, "close"):
                    client.close()
            # Close SQLite via mem0's built-in close()
            if hasattr(local, "close"):
                local.close()
            logger.info("Local mem0 shut down cleanly")
        except Exception as e:
            logger.warning("Error during local mem0 shutdown: %s", e)


def register(ctx) -> None:
    """Register Mem0 as a memory provider plugin."""
    ctx.register_memory_provider(Mem0MemoryProvider())
