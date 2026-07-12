import sys
from pathlib import Path

# Bootstrap project root to allow importing packages
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


from packages.knowledge.index import VectorIndex
from packages.providers.ollama import OllamaEmbeddingProvider

import asyncio

embedding = OllamaEmbeddingProvider()
index = VectorIndex()

query = "I missed my workout."


async def main():
    # Wait, embedding.embed(query) returns list[float].
    # VectorIndex.search expects list[list[float]] for query_embeddings.
    query_vector = await embedding.embed(query)
    results = index.search(
        query_embeddings=[query_vector],
        n_results=5,
    )

    for i, result in enumerate(results, start=1):
        print(f"\nResult {i}")
        print(result)


if __name__ == "__main__":
    asyncio.run(main())