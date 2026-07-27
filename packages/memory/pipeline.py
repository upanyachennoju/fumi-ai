import inspect
from pathlib import Path
from datetime import datetime
import frontmatter

from packages.knowledge.vault import Vault
from packages.knowledge.indexer import Indexer
from .summarizer import ConversationSummarizer
from .extractor import MemoryExtractor
from .manager import MemoryManager
from .resolver import MemoryResolver
from .links import LinkBuilder


class MemoryPipeline:
    """
    Orchestrates the entire memory lifecycle after a conversation session completes:
    Conversation -> Summarizer -> Extractor -> MemoryResolver -> MemoryManager -> LinkBuilder -> Vault Update -> Re-index.
    """

    def __init__(
        self,
        vault: Vault,
        indexer: Indexer,
        summarizer: ConversationSummarizer,
        extractor: MemoryExtractor,
        manager: MemoryManager,
        resolver: MemoryResolver | None = None,
        link_builder: LinkBuilder | None = None,
    ):
        self.vault = vault
        self.indexer = indexer
        self.summarizer = summarizer
        self.extractor = extractor
        self.manager = manager
        
        # Get resolver from the manager or fallback to getattr
        if resolver is not None:
            self.resolver = resolver
        else:
            self.resolver = getattr(manager, "resolver", None)
            
        # Get link_builder or construct a default
        if link_builder is not None:
            self.link_builder = link_builder
        else:
            self.link_builder = LinkBuilder(vault)

    async def run(self, session_id: str):
        """
        Processes a completed conversation session to summarize it, extract key
        long-term memory points, write/update those memory points in the Vault
        using memory reconciliation and Obsidian cross-linking, mark the session
        as processed, and index the updated memory records.
        """
        # 1. Load the conversation messages from the Vault
        session, messages = self.vault.load_session(session_id)
        if not messages:
            return

        # 2. Generate a concise conversation summary
        summary = await self.summarizer.summarize(messages)

        # 3. Mark the conversation file as processed and attach the summary
        self._mark_as_processed(session_id, summary)

        # 4. Extract structured memories using the LLM Extractor
        extraction = await self.extractor.extract(messages)

        # 5. Resolve memory operations (CREATE, UPDATE, IGNORE)
        operations = await self.resolver.resolve(extraction)

        # 6. Apply operations to create/update vault markdown files
        updated_paths = await self.manager.update_vault(operations)

        # 7. Generate Obsidian wiki links for co-occurring/related entities
        await self.link_builder.build_links(updated_paths)

        # 8. Index the newly created/updated memory Markdown files into the Vector Index
        for path in updated_paths:
            try:
                post = frontmatter.load(path)

                # Construct a duck-typed document object for the chunker/indexer
                class MemoryDoc:
                    def __init__(self, id_val, content_val, metadata_val):
                        self.id = id_val
                        self.content = content_val
                        self.metadata = metadata_val

                doc = MemoryDoc(
                    id_val=post.metadata.get("id", path.stem),
                    content_val=post.content,
                    metadata_val=post.metadata,
                )
                await self.indexer.index_document(doc)
            except Exception:
                continue

    def _mark_as_processed(self, session_id: str, summary: str):
        """
        Update the conversation Markdown file's frontmatter to record its summary
        and set processed status to True.
        """
        path = self.vault.get_session_path(session_id)
        if not path or not path.exists():
            return

        post = frontmatter.load(path)
        post.metadata["processed"] = True
        post.metadata["summary"] = summary
        post.metadata["updated"] = datetime.now().isoformat()

        with open(path, "w", encoding="utf-8") as f:
            frontmatter.dump(post, f)
