"""MemPalace Memory Provider — ChromaDB backend integration.

Simple integration using MemPalace's ChromaDB backend directly.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent.memory_provider import MemoryProvider

logger = logging.getLogger(__name__)

try:
    from mempalace.backends.chroma import ChromaBackend
    MEMPALACE_AVAILABLE = True
except ImportError:
    MEMPALACE_AVAILABLE = False
    ChromaBackend = None


class MempalaceMemoryProvider(MemoryProvider):
    """MemPalace integration for Hermes Agent."""
    
    def __init__(self, palace_path: Optional[str] = None):
        self._palace_path = palace_path
        self._collection = None
        self._backend: Optional[ChromaBackend] = None
        self._session_id = ""
        self._initialized = False
    
    @property
    def name(self) -> str:
        return "mempalace"
    
    def is_available(self) -> bool:
        if not MEMPALACE_AVAILABLE:
            return False
        return True
    
    def initialize(self, session_id: str, **kwargs) -> None:
        self._session_id = session_id
        hermes_home = kwargs.get("hermes_home", str(Path.home() / ".hermes"))
        
        if self._palace_path:
            palace_path = Path(self._palace_path)
        else:
            palace_path = Path(hermes_home) / "mempalace"
        
        try:
            palace_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Initializing MemPalace at {palace_path}")
            
            self._backend = ChromaBackend()
            self._collection = self._backend.get_collection(
                str(palace_path),
                collection_name="hermes_memory",
                create=True
            )
            self._initialized = True
            logger.info("MemPalace initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize MemPalace: {e}")
            self._initialized = False
    
    def system_prompt_block(self) -> str:
        if not self._initialized:
            return ""
        return """
## MemPalace Memory

Local AI memory with semantic search. Use mempalace_search/mempalace_store tools.
"""
    
    def prefetch(self, query: str, *, session_id: str = "") -> str:
        if not self._initialized or not self._collection:
            return ""
        try:
            results = self._collection.query(query_texts=[query], n_results=3)
            if not results or not results.get('documents'):
                return ""
            docs = results['documents'][0] if results['documents'] else []
            return "## MemPalace\n\n" + "\n".join(f"- {d}" for d in docs[:3])
        except Exception as e:
            logger.debug(f"MemPalace prefetch error: {e}")
            return ""
    
    def sync_turn(self, user_content: str, assistant_content: str, 
                  *, session_id: str = "") -> None:
        if not self._initialized or not self._collection:
            return
        try:
            conversation = f"User: {user_content}\n\nAssistant: {assistant_content}"
            doc_id = f"turn_{session_id}_{len(self._collection.get()['ids'])}"
            self._collection.add(
                documents=[conversation],
                ids=[doc_id],
                metadatas=[{"session": session_id}]
            )
        except Exception as e:
            logger.debug(f"MemPalace sync_turn error: {e}")
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        if not MEMPALACE_AVAILABLE:
            return []
        return [
            {
                "name": "mempalace_search",
                "description": "Search MemPalace memory",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "limit": {"type": "integer", "default": 5}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "mempalace_store",
                "description": "Store content in MemPalace",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["content"]
                }
            }
        ]
    
    def handle_tool_call(self, tool_name: str, args: Dict[str, Any], **kwargs) -> str:
        if not self._initialized or not self._collection:
            return json.dumps({"error": "MemPalace not initialized"})
        try:
            if tool_name == "mempalace_search":
                query = args.get("query", "")
                limit = args.get("limit", 5)
                results = self._collection.query(query_texts=[query], n_results=limit)
                docs = results['documents'][0] if results['documents'] else []
                return json.dumps({"success": True, "results": docs, "count": len(docs)})
            elif tool_name == "mempalace_store":
                content = args.get("content", "")
                doc_id = f"doc_{len(self._collection.get()['ids'])}"
                self._collection.add(documents=[content], ids=[doc_id])
                return json.dumps({"success": True, "id": doc_id})
            else:
                return json.dumps({"error": f"Unknown tool: {tool_name}"})
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    def shutdown(self) -> None:
        self._collection = None
        self._backend = None
        self._initialized = False
