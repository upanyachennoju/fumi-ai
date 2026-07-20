import sys
from pathlib import Path

# Bootstrap project root to allow importing packages
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.providers.ollama import OllamaEmbeddingProvider


from numpy import dot
from numpy.linalg import norm

import asyncio

provider = OllamaEmbeddingProvider()


def cosine(x, y):
    return dot(x, y) / (norm(x) * norm(y))


async def main():
    a = await provider.embed("I skipped gym today.")
    b = await provider.embed("I missed my workout.")
    c = await provider.embed("I adopted a cat.")

    print(cosine(a, b))
    print(cosine(a, c))


if __name__ == "__main__":
    asyncio.run(main())