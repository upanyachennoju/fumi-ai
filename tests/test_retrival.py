import sys
from pathlib import Path

# Bootstrap project root and virtualenv packages to allow importing packages in sandbox
venv_site = Path(__file__).resolve().parent.parent / f".venv/lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages"
if venv_site.exists():
    sys.path.insert(0, str(venv_site))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


from packages.knowledge.index import VectorIndex
from packages.providers.ollama import OllamaEmbeddingProvider

import asyncio

embedding = OllamaEmbeddingProvider()
index = VectorIndex(embedding_provider=embedding)

query = "I missed my workout."


async def main():
    # Wait, embedding.embed(query) returns list[float].
    # VectorIndex.search expects list[list[float]] for query_embeddings.
    query_vector = await embedding.embed(query)
    results = await index.search(
        query_embeddings=[query_vector],
        n_results=5,
    )

    for i, result in enumerate(results, start=1):
        print(f"\nResult {i}")
        print(result)


if __name__ == "__main__":
    asyncio.run(main())