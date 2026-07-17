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


class ConversationService:
    def __init__(self):
        self.provider = get_llm_provider()
        self.vault = Vault()
        self.index = VectorIndex()
        self.embedding_provider = OllamaEmbeddingProvider()
        self.retriever = Retriever(self.index, self.embedding_provider)
        self.prompt_builder = PromptBuilder()

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

    async def chat(self, message: str) -> str:
        # 1. Retrieve the active conversation session, or create one if none exists
        sessions = self.vault.list_sessions()
        if sessions:
            session_id = sessions[0].id
        else:
            model_name = getattr(self.provider, "model", "gemma3:4b")
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

        # 5. Call LLM provider with messages
        res = self.provider.generate(messages)
        if inspect.iscoroutine(res):
            reply = await res
        else:
            reply = res

        # 6. Save the new conversation turn (user message & Fumi reply) to the Vault
        self.vault.append_message(session_id, Message(role="user", content=message))
        self.vault.append_message(session_id, Message(role="fumi", content=reply))

        # 7. Asynchronously trigger the MemoryPipeline in the background to summarize,
        # extract new memories, update the Vault, and re-index them.
        asyncio.create_task(self.pipeline.run(session_id))

        return reply