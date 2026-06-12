import json
from typing import Optional

from .client import LMStudioClient
from .tools import ToolRegistry, Tool
from .prompts import SYSTEM_PROMPT, TOOL_SCHEMAS


MAX_ITERATIONS = 8

AUTO_RAG_PROMPT = """Use the following documents to answer the user's question. If the documents don't contain relevant information, rely on your general knowledge.

Relevant documents:
{context}

---"""


class AgentLoop:
    def __init__(self, llm_client: LMStudioClient, tool_registry: ToolRegistry,
                 model: str = "local", max_tokens: int = 4096,
                 auto_rag: bool = True, rag_k: int = 3):
        self.llm = llm_client
        self.tools = tool_registry
        self.model = model
        self.max_tokens = max_tokens
        self.auto_rag = auto_rag
        self.rag_k = rag_k
        self._rag = None
        self._register_builtin_handlers()

    def _register_builtin_handlers(self):
        from ..core.memory.hybrid import HybridMemory
        from ..rag.engine import RAGEngine

        self._mem = None
        self._rag = None
        self._skill_loader = None

        try:
            from ..core.config import load_config, resolve_path
            cfg = resolve_path(load_config())
            try:
                from ..core.memory.episodic import EpisodicMemory
                from ..core.memory.semantic import SemanticMemory
                epi = EpisodicMemory(cfg.memory.episodic.database_path, cfg.memory.episodic.faiss_index_path)
                sem = SemanticMemory(cfg.memory.semantic.graph_path, cfg.memory.semantic.schema_path)
                self._mem = HybridMemory(epi, sem)
            except Exception:
                pass
            try:
                self._rag = RAGEngine("rag_index.faiss", "rag_meta.jsonl")
            except Exception:
                pass
        except Exception:
            pass

        try:
            from ..skills.loader import SkillLoader
            self._skill_loader = SkillLoader()
        except Exception:
            pass

        def search_memory(query: str, limit: int = 5) -> str:
            if not self._mem:
                return "Memory not available"
            results = self._mem.search(query, top_k=limit)
            if not results:
                return "No results found in memory."
            return json.dumps(results[:limit], indent=2, default=str)

        def store_memory(text: str, category: str = "note") -> str:
            if not self._mem:
                return "Memory not available"
            try:
                from datetime import datetime
                self._mem.remember(text, user_id="default", metadata={"category": category, "timestamp": datetime.utcnow().isoformat()})
                return f"Stored in memory under category '{category}'."
            except Exception as e:
                return f"Failed to store: {e}"

        def search_documents(query: str, k: int = 3) -> str:
            if not self._rag:
                return "RAG not available (no documents ingested)"
            try:
                results, context = self._rag.build_context(query, k)
                return context or "No relevant documents found."
            except Exception as e:
                return f"RAG search failed: {e}"

        def list_skills(category: str = "") -> str:
            if not self._skill_loader:
                return "Skill system not available"
            skills = self._skill_loader.discover_skills()
            if category:
                skills = [s for s in skills if s.category.lower() == category.lower()]
            if not skills:
                return "No skills found."
            lines = [f"  - {s.name} ({s.category}): {s.description}" for s in skills]
            return "Available skills:\n" + "\n".join(lines)

        def execute_skill(skill_name: str, params: Optional[dict] = None) -> str:
            if not self._skill_loader:
                return "Skill system not available"
            params = params or {}
            for s in self._skill_loader.discover_skills():
                if s.name.lower() == skill_name.lower():
                    try:
                        result = s.execute(**params)
                        return json.dumps(result, indent=2, default=str)
                    except Exception as e:
                        return f"Skill execution error: {e}"
            return f"Skill '{skill_name}' not found."

        self.tools.register(Tool("search_memory", "Search past conversations and stored knowledge",
                                  TOOL_SCHEMAS["search_memory"]["function"]["parameters"],
                                  search_memory))
        self.tools.register(Tool("store_memory", "Store a fact or piece of information in long-term memory",
                                  TOOL_SCHEMAS["store_memory"]["function"]["parameters"],
                                  store_memory))
        self.tools.register(Tool("search_documents", "Search ingested documents for relevant information",
                                  TOOL_SCHEMAS["search_documents"]["function"]["parameters"],
                                  search_documents))
        self.tools.register(Tool("list_skills", "List all available skills and their capabilities",
                                  TOOL_SCHEMAS["list_skills"]["function"]["parameters"],
                                  list_skills))
        self.tools.register(Tool("execute_skill", "Execute a specific skill by name with parameters",
                                  TOOL_SCHEMAS["execute_skill"]["function"]["parameters"],
                                  execute_skill))

    def _build_rag_context(self, query: str) -> str:
        if not self._rag:
            try:
                from ..rag.engine import RAGEngine
                self._rag = RAGEngine("rag_index.faiss", "rag_meta.jsonl")
            except Exception:
                return ""
        if self._rag.store.count() == 0:
            return ""
        try:
            _, context = self._rag.build_context(query, self.rag_k)
            return context or ""
        except Exception:
            return ""

    def run(self, user_message: str, conversation_history: Optional[list[dict]] = None,
            system_prompt: Optional[str] = None) -> tuple[str, list[dict]]:
        history = list(conversation_history or [])
        base_system = system_prompt or SYSTEM_PROMPT
        effective_system = base_system

        if self.auto_rag:
            rag_context = self._build_rag_context(user_message)
            if rag_context:
                effective_system = base_system + "\n\n" + AUTO_RAG_PROMPT.format(context=rag_context)

        messages = [{"role": "system", "content": effective_system}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        turn_count = 0
        final_content = ""

        while turn_count < MAX_ITERATIONS:
            response = self.llm.chat(
                messages=messages,
                model=self.model,
                max_tokens=self.max_tokens,
                tools=self.tools.schemas(),
            )

            if response.finish_reason == "error":
                final_content = response.content or "[LLM error]"
                break

            if response.content:
                messages.append({"role": "assistant", "content": response.content})

            if not response.tool_calls:
                final_content = response.content or ""
                break

            for tc in response.tool_calls:
                fn = tc.get("function", {})
                name = fn.get("name", "")
                args = fn.get("arguments", {})

                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": tc.get("id", ""),
                        "type": "function",
                        "function": {"name": name, "arguments": json.dumps(args)},
                    }],
                })

                result = self.tools.execute(name, **args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.get("id", ""),
                    "content": result,
                })

            turn_count += 1

        if turn_count >= MAX_ITERATIONS and not final_content:
            final_content = "[Agent reached max reasoning depth]"

        new_history = messages[1:] if messages[0]["role"] == "system" else messages
        return final_content, new_history

    def check_available(self) -> bool:
        return self.llm.check_available()
