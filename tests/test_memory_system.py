import sys
from pathlib import Path
import asyncio

# Bootstrap project root to allow importing packages
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.knowledge.vault import Vault
from packages.knowledge.index import VectorIndex
from packages.knowledge.indexer import Indexer
from packages.providers.ollama import OllamaProvider, OllamaEmbeddingProvider
from packages.memory.summarizer import ConversationSummarizer
from packages.memory.extractor import MemoryExtractor
from packages.memory.manager import MemoryManager
from packages.memory.pipeline import MemoryPipeline
from packages.knowledge.schemas import Message


async def main():
    print("Initializing Fumi Memory System...")
    vault = Vault()
    index = VectorIndex(persist_directory="./chroma")
    llm = OllamaProvider()
    embedder = OllamaEmbeddingProvider()

    # Create instances of core modules
    indexer = Indexer(vault, index, embedder)
    summarizer = ConversationSummarizer(llm)
    extractor = MemoryExtractor(llm)
    manager = MemoryManager(vault)

    # Initialize the memory pipeline
    pipeline = MemoryPipeline(
        vault=vault,
        indexer=indexer,
        summarizer=summarizer,
        extractor=extractor,
        manager=manager,
    )

    # 1. Create a dummy active conversation session
    print("\nCreating a test conversation session...")
    session = vault.create_session(model="gemma3:4b")
    vault.append_message(
        session.id,
        Message(
            role="user",
            content="Hey! I love writing code in VS Code, and John is my mentor. I want to wake up at 6 AM every morning to workout. I also prefer espresso over latte.",
        ),
    )
    vault.append_message(
        session.id,
        Message(
            role="fumi",
            content="That's awesome! Congratualtions on having John as your mentor. Waking up at 6 AM sounds like a great routine. I'll remember that you like espresso!",
        ),
    )

    # 2. Run the memory pipeline
    print(f"Running memory pipeline for session {session.id}...")
    await pipeline.run(session.id)

    # 3. Verify that the session is marked as processed
    sess_path = vault.get_session_path(session.id)
    import frontmatter
    post = frontmatter.load(sess_path)
    print("\n--- Processed Session File ---")
    print(f"Processed: {post.metadata.get('processed')}")
    print(f"Summary: '{post.metadata.get('summary')}'")

    # 4. Search the vector index to verify indexing
    print("\nSearching index for 'espresso'...")
    query_vector = await embedder.embed("espresso")
    results = index.search(query_embeddings=[query_vector], n_results=3)
    for i, res in enumerate(results, start=1):
        print(f"Result {i}: {res['text']} (Type: {res['metadata'].get('type')})")

    print("\nSearching index for 'VS Code'...")
    query_vector_vscode = await embedder.embed("VS Code")
    results_vscode = index.search(query_embeddings=[query_vector_vscode], n_results=3)
    for i, res in enumerate(results_vscode, start=1):
        print(f"Result {i}: {res['text']} (Type: {res['metadata'].get('type')})")


if __name__ == "__main__":
    asyncio.run(main())
