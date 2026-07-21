import asyncio
import inspect
from packages.providers.factory import get_llm_provider
from packages.providers.ollama import OllamaEmbeddingProvider
from packages.knowledge.vault import Vault
from packages.knowledge.index import VectorIndex
from packages.knowledge.retriever import Retriever
from packages.knowledge.prompt_builder import PromptBuilder
from packages.knowledge.indexer import Indexer
from packages.knowledge.schemas import Message
from packages.memory.summarizer import ConversationSummarizer
from packages.memory.extractor import MemoryExtractor
from packages.memory.manager import MemoryManager
from packages.memory.pipeline import MemoryPipeline
from packages.prompts.system_prompt import SYSTEM_PROMPT

from packages.tools.registry import ToolRegistry
from packages.tools.goals import ListGoalsTool, CreateGoalTool, CompleteGoalTool, DeleteGoalTool
from packages.tools.memories import SearchMemoryTool
from packages.tools.checkins import CreateCheckinTool, ListPendingCheckinsTool, MarkCheckinReadTool
from packages.tools.reminders import CreateReminderTool, ListRemindersTool, UpdateReminderTool, DeleteReminderTool

class ConversationService:
    """
    A service class for managing conversation flows, memory, and tool usage.
    """
    def __init__(self, registry: ToolRegistry | None = None):
        self.provider = get_llm_provider()
        self.vault = Vault()
        self.index = VectorIndex()
        self.embedding_provider = OllamaEmbeddingProvider()
        self.retriever = Retriever(self.index, self.embedding_provider)
        self.prompt_builder = PromptBuilder()

        # Initialize or assign ToolRegistry
        if registry is not None:
            self.registry = registry
        else:
            self.registry = ToolRegistry()
            self.registry.register(ListGoalsTool(self.vault))
            self.registry.register(CreateGoalTool(self.vault))
            self.registry.register(CompleteGoalTool(self.vault))
            self.registry.register(DeleteGoalTool(self.vault))
            self.registry.register(SearchMemoryTool(self.retriever))
            self.registry.register(CreateCheckinTool(self.vault))
            self.registry.register(ListPendingCheckinsTool(self.vault))
            self.registry.register(MarkCheckinReadTool(self.vault))
            self.registry.register(CreateReminderTool(self.vault))
            self.registry.register(ListRemindersTool(self.vault))
            self.registry.register(UpdateReminderTool(self.vault))
            self.registry.register(DeleteReminderTool(self.vault))

        # Initialize Memory Pipeline components for background processing
        self.indexer = Indexer(self.vault, self.index, self.embedding_provider)
        self.summarizer = ConversationSummarizer(self.provider)
        self.extractor = MemoryExtractor(self.provider)
        self.manager = MemoryManager(self.vault)
        self.pipeline = MemoryPipeline(
            vault=self.vault,
            indexer=self.indexer,
            summarizer=self.summarizer,
            extractor=self.extractor,
            manager=self.manager,
        )

    async def chat(self, message: str) -> dict:
        # 1. Retrieve the active conversation session, or create one if none exists
        sessions = self.vault.list_sessions()
        if sessions:
            session_id = sessions[0].id
        else:
            model_name = getattr(self.provider, "model", "qwen2.5:7b-instruct")
            session = self.vault.create_session(model=model_name)
            session_id = session.id

        # 2. Retrieve conversation history before appending the current message
        _, history = self.vault.load_session(session_id)

        # 3. Retrieve memories (semantic context chunks from vector index)
        retrieved_chunks = []
        try:
            retrieved_chunks = await self.retriever.retrieve(message, n_results=3)
        except Exception as e:
            # Gracefully log retrieval/embedding issues to prevent breaking conversation
            print(f"Memory retrieval failed: {e}")

        # 4. Build prompt messages using system prompt, chunks, history, and current message
        messages = self.prompt_builder.build(
            system_prompt=SYSTEM_PROMPT,
            retrieved_chunks=retrieved_chunks,
            current_conversation=history,
            current_user_message=message,
        )

        # Get schemas for registered tools
        schemas = self.registry.get_schemas() if self.registry else []

        # 5. Call LLM provider with messages and tools
        res = self.provider.generate(messages, tools=schemas)
        if inspect.iscoroutine(res):
            result = await res
        else:
            result = res

        # Unpack result dict
        if isinstance(result, dict):
            reply = result.get("content", "")
            tool_calls = result.get("tool_calls", [])
            metrics = result.get("metrics", {})
        else:
            reply = str(result)
            tool_calls = []
            metrics = {}

        # 6. Execute Tool Calls if requested by LLM
        if tool_calls and self.registry:
            tool_summaries = []
            for tc in tool_calls:
                tool_name = tc.get("name")
                tool_args = tc.get("args", {})
                print(f"Executing tool call: {tool_name}({tool_args})")

                exec_res = await self.registry.execute_tool(tool_name, tool_args)
                if exec_res.get("success"):
                    tool_summaries.append(f"Tool '{tool_name}' output: {exec_res.get('result')}")
                else:
                    tool_summaries.append(f"Tool '{tool_name}' failed: {exec_res.get('error')}")

            # Send tool output back to the LLM for a natural response
            tool_output_msg = "\n".join(tool_summaries)
            messages.append(Message(role="fumi", content=reply if reply else "Executing action..."))
            messages.append(Message(role="system", content=f"Tool Execution Results:\n{tool_output_msg}\nConfirm the action briefly to the user in your lower-case tone."))

            followup_res = self.provider.generate(messages)
            if inspect.iscoroutine(followup_res):
                followup_result = await followup_res
            else:
                followup_result = followup_res

            if isinstance(followup_result, dict):
                reply = followup_result.get("content") or reply
                f_metrics = followup_result.get("metrics", {})
                metrics["tokens_generated"] = metrics.get("tokens_generated", 0) + f_metrics.get("tokens_generated", 0)
                metrics["response_time_sec"] = round(metrics.get("response_time_sec", 0.0) + f_metrics.get("response_time_sec", 0.0), 2)
            elif isinstance(followup_result, str):
                reply = followup_result

        if not reply:
            reply = "done."

        # 7. Save the new conversation turn (user message & Fumi reply) to the Vault
        self.vault.append_message(session_id, Message(role="user", content=message))
        self.vault.append_message(session_id, Message(role="fumi", content=reply))

        # 8. Asynchronously trigger the MemoryPipeline in the background to summarize,
        # extract new memories, update the Vault, and re-index them.
        asyncio.create_task(self.pipeline.run(session_id)) 

        return {"reply": reply, "metrics": metrics}