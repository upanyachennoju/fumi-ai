import sys
from pathlib import Path
import asyncio

# Bootstrap project root to allow importing packages
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.knowledge.vault import Vault
from packages.knowledge.indexer import Indexer
from packages.knowledge.index import VectorIndex
from packages.providers.ollama import OllamaEmbeddingProvider


async def main():
    vault = Vault()
    embedding = OllamaEmbeddingProvider()
    index = VectorIndex()
    
    indexer = Indexer(
        vault=vault,
        embedding_provider=embedding,
        index=index,
    )

    vault_path = Path("vault")

    for file in vault_path.rglob("*.md"):
        print(f"Indexing {file.name}")
        # Wait, index_document expects a document object or vault model.
        # But we can also pass a frontmatter post or custom doc!
        # Let's load the file using frontmatter
        import frontmatter
        try:
            post = frontmatter.load(file)
            # Create a simple duck-typed document
            class Doc:
                def __init__(self, id_val, content_val, metadata_val):
                    self.id = id_val
                    self.content = content_val
                    self.metadata = metadata_val
            
            doc = Doc(
                id_val=post.metadata.get("id", file.stem),
                content_val=post.content,
                metadata_val=post.metadata
            )
            await indexer.index_document(doc)
        except Exception as e:
            print(f"Failed to index {file.name}: {e}")

    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())