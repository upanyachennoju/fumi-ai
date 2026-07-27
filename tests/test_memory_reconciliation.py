import sys
from pathlib import Path

# Bootstrap project root and virtualenv packages to allow importing packages in sandbox
venv_site = Path(__file__).resolve().parent.parent / f".venv/lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages"
if venv_site.exists():
    sys.path.insert(0, str(venv_site))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import shutil
import tempfile
import asyncio
import unittest
import frontmatter

from packages.knowledge.vault import Vault
from packages.knowledge.index import VectorIndex, SearchResult
from packages.knowledge.indexer import Indexer
from packages.knowledge.schemas import Message
from packages.memory.schemas import MemoryExtraction
from packages.memory.manager import MemoryManager, merge_memory
from packages.memory.resolver import MemoryResolver, MemoryOperation
from packages.memory.links import LinkBuilder, add_relationship_link


class MockEmbeddingProvider:
    """Predetermined vectors to control Chroma L2 distances and similarity scores."""
    def __init__(self):
        self.vectors = {
            # High similarity (> 0.90) to "fumi project"
            "update fumi project": [0.95, 0.312, 0.0], # L2 dist ~0.10, similarity ~0.95
            # Uncertain similarity (0.70 - 0.90) to "fumi project"
            "uncertain fumi project": [0.80, 0.60, 0.0], # L2 dist ~0.40, similarity ~0.80
            # Base entity for project
            "fumi project": [1.0, 0.0, 0.0],
            # Low similarity (< 0.70)
            "completely new project": [0.0, 1.0, 0.0], # L2 dist 2.0, similarity ~0.0
        }

    async def embed(self, text: str) -> list[float]:
        text_lower = text.lower()
        for k, v in self.vectors.items():
            if k in text_lower:
                return v
        return [0.0, 0.0, 1.0]


class MockLLMProvider:
    """Mock LLM to return configurable decisions."""
    def __init__(self):
        self.decision = "UPDATE"

    def generate(self, prompt: str) -> dict:
        return {
            "content": self.decision,
            "metrics": {}
        }


class TestMemoryReconciliation(unittest.TestCase):
    def setUp(self):
        # Create temp dirs for Vault and Chroma
        self.temp_vault_dir = Path(tempfile.mkdtemp())
        self.temp_chroma_dir = Path(tempfile.mkdtemp())

        self.vault = Vault(root=self.temp_vault_dir)
        self.embedder = MockEmbeddingProvider()
        self.index = VectorIndex(
            persist_directory=self.temp_chroma_dir,
            embedding_provider=self.embedder
        )
        self.llm = MockLLMProvider()
        
        self.resolver = MemoryResolver(self.index, self.llm, threshold=0.90)
        self.manager = MemoryManager(self.vault, self.resolver)
        self.link_builder = LinkBuilder(self.vault)
        self.indexer = Indexer(self.vault, self.index, self.embedder)

    def tearDown(self):
        # Clean up temp dirs
        shutil.rmtree(self.temp_vault_dir, ignore_errors=True)
        shutil.rmtree(self.temp_chroma_dir, ignore_errors=True)

    async def async_test_create(self):
        """Test CREATE action: New memory is created with sanitized filename and frontmatter id."""
        extraction = MemoryExtraction(
            preferences=[],
            goals=[],
            projects=["Fumi Project"],
            people=[],
            habits=[],
            memories=[]
        )

        ops = await self.resolver.resolve(extraction)
        self.assertEqual(len(ops), 1)
        self.assertEqual(ops[0].action, "create")
        self.assertEqual(ops[0].category, "project")
        self.assertEqual(ops[0].extracted_memory, "Fumi Project")

        paths = await self.manager.update_vault(ops)
        self.assertEqual(len(paths), 1)
        
        created_file = paths[0]
        self.assertEqual(created_file.name, "Fumi Project.md")
        self.assertTrue(created_file.exists())

        post = frontmatter.load(created_file)
        self.assertEqual(post.content, "Fumi Project")
        self.assertEqual(post.metadata["type"], "project")
        self.assertTrue("id" in post.metadata)

    async def async_test_update_high_similarity(self):
        """Test automatic UPDATE action on high similarity."""
        # 1. Create initial memory and index it
        proj_dir = self.temp_vault_dir / "projects"
        proj_dir.mkdir(parents=True, exist_ok=True)
        initial_file = proj_dir / "Fumi Project.md"
        post = frontmatter.Post(
            content="Fumi Project",
            id="fumi_proj_id",
            created="2026-07-24T12:00:00",
            updated="2026-07-24T12:00:00",
            type="project",
            progress=["initial setup"]
        )
        with open(initial_file, "w") as f:
            frontmatter.dump(post, f)

        # Index the document
        class Doc:
            id = "fumi_proj_id"
            content = "Fumi Project"
            metadata = post.metadata

        await self.indexer.index_document(Doc())

        # 2. Extract highly similar memory (updates automatically)
        extraction = MemoryExtraction(
            preferences=[],
            goals=[],
            projects=["update Fumi Project"], # contains "update fumi project" -> high similarity vector
            people=[],
            habits=[],
            memories=[]
        )

        ops = await self.resolver.resolve(extraction)
        self.assertEqual(len(ops), 1)
        self.assertEqual(ops[0].action, "update")
        self.assertEqual(ops[0].existing_memory.metadata.get("doc_id"), "fumi_proj_id")

        paths = await self.manager.update_vault(ops)
        self.assertEqual(len(paths), 1)
        self.assertEqual(paths[0], initial_file) # Filename preserved

        # Verify structured merge: since "progress" is a list key, it should append the new content
        updated_post = frontmatter.load(initial_file)
        self.assertEqual(updated_post.metadata["id"], "fumi_proj_id") # ID preserved
        self.assertIn("initial setup", updated_post.metadata["progress"])
        self.assertIn("update Fumi Project", updated_post.metadata["progress"])
        self.assertNotEqual(updated_post.metadata["updated"], "2026-07-24T12:00:00")

    async def async_test_uncertain_llm_update(self):
        """Test uncertain similarity (0.70 - 0.90) resolved to UPDATE by LLM."""
        # 1. Create initial memory and index it
        proj_dir = self.temp_vault_dir / "projects"
        proj_dir.mkdir(parents=True, exist_ok=True)
        initial_file = proj_dir / "Fumi Project.md"
        post = frontmatter.Post(
            content="Fumi Project",
            id="fumi_proj_id",
            created="2026-07-24T12:00:00",
            updated="2026-07-24T12:00:00",
            type="project",
            progress=["setup"]
        )
        with open(initial_file, "w") as f:
            frontmatter.dump(post, f)

        class Doc:
            id = "fumi_proj_id"
            content = "Fumi Project"
            metadata = post.metadata

        await self.indexer.index_document(Doc())

        # 2. Extract uncertain similarity and stub LLM to return UPDATE
        self.llm.decision = "UPDATE"
        extraction = MemoryExtraction(
            preferences=[],
            goals=[],
            projects=["uncertain Fumi Project"], # triggers 0.80 similarity
            people=[],
            habits=[],
            memories=[]
        )

        ops = await self.resolver.resolve(extraction)
        self.assertEqual(len(ops), 1)
        self.assertEqual(ops[0].action, "update")
        self.assertEqual(ops[0].existing_memory.metadata.get("doc_id"), "fumi_proj_id")

        paths = await self.manager.update_vault(ops)
        updated_post = frontmatter.load(initial_file)
        self.assertIn("uncertain Fumi Project", updated_post.metadata["progress"])

    async def async_test_uncertain_llm_create(self):
        """Test uncertain similarity resolved to CREATE by LLM."""
        proj_dir = self.temp_vault_dir / "projects"
        proj_dir.mkdir(parents=True, exist_ok=True)
        initial_file = proj_dir / "Fumi Project.md"
        post = frontmatter.Post(
            content="Fumi Project",
            id="fumi_proj_id",
            created="2026-07-24T12:00:00",
            updated="2026-07-24T12:00:00",
            type="project"
        )
        with open(initial_file, "w") as f:
            frontmatter.dump(post, f)

        class Doc:
            id = "fumi_proj_id"
            content = "Fumi Project"
            metadata = post.metadata
        await self.indexer.index_document(Doc())

        self.llm.decision = "CREATE"
        extraction = MemoryExtraction(
            preferences=[],
            goals=[],
            projects=["uncertain Fumi Project"],
            people=[],
            habits=[],
            memories=[]
        )

        ops = await self.resolver.resolve(extraction)
        self.assertEqual(len(ops), 1)
        self.assertEqual(ops[0].action, "create")

        paths = await self.manager.update_vault(ops)
        self.assertEqual(len(paths), 1)
        self.assertEqual(paths[0].name, "uncertain Fumi Project.md")

    async def async_test_uncertain_llm_ignore(self):
        """Test uncertain similarity resolved to IGNORE by LLM."""
        proj_dir = self.temp_vault_dir / "projects"
        proj_dir.mkdir(parents=True, exist_ok=True)
        initial_file = proj_dir / "Fumi Project.md"
        post = frontmatter.Post(
            content="Fumi Project",
            id="fumi_proj_id",
            created="2026-07-24T12:00:00",
            updated="2026-07-24T12:00:00",
            type="project"
        )
        with open(initial_file, "w") as f:
            frontmatter.dump(post, f)

        class Doc:
            id = "fumi_proj_id"
            content = "Fumi Project"
            metadata = post.metadata
        await self.indexer.index_document(Doc())

        self.llm.decision = "IGNORE"
        extraction = MemoryExtraction(
            preferences=[],
            goals=[],
            projects=["uncertain Fumi Project"],
            people=[],
            habits=[],
            memories=[]
        )

        ops = await self.resolver.resolve(extraction)
        self.assertEqual(len(ops), 1)
        self.assertEqual(ops[0].action, "ignore")

        paths = await self.manager.update_vault(ops)
        self.assertEqual(len(paths), 0)

    async def async_test_duplicate_prevention(self):
        """Test duplicate creation prevention in the same transaction."""
        extraction = MemoryExtraction(
            preferences=[],
            goals=[],
            projects=["Fumi Project", "Fumi Project", "fumi project  "],
            people=[],
            habits=[],
            memories=[]
        )

        ops = await self.resolver.resolve(extraction)
        paths = await self.manager.update_vault(ops)
        # Should only create one file
        self.assertEqual(len(paths), 1)

    async def async_test_wiki_linking(self):
        """Test LinkBuilder generates Obsidian wiki links between co-occurring entities using filename stems."""
        extraction = MemoryExtraction(
            preferences=[],
            goals=["Build Fumi"],
            projects=["Fumi"],
            people=[],
            habits=[],
            memories=[]
        )

        ops = await self.resolver.resolve(extraction)
        paths = await self.manager.update_vault(ops)
        self.assertEqual(len(paths), 2)

        # Cross link them
        await self.link_builder.build_links(paths)

        # Verify links
        fumi_file = self.temp_vault_dir / "projects" / "Fumi.md"
        build_file = self.temp_vault_dir / "goals" / "Build Fumi.md"

        fumi_post = frontmatter.load(fumi_file)
        build_post = frontmatter.load(build_file)

        self.assertIn("## related goals", fumi_post.content)
        self.assertIn("- [[Build Fumi]]", fumi_post.content)

        self.assertIn("## related projects", build_post.content)
        self.assertIn("- [[Fumi]]", build_post.content)

    # Runner adapters for unittest
    def test_create(self):
        asyncio.run(self.async_test_create())

    def test_update_high_similarity(self):
        asyncio.run(self.async_test_update_high_similarity())

    def test_uncertain_llm_update(self):
        asyncio.run(self.async_test_uncertain_llm_update())

    def test_uncertain_llm_create(self):
        asyncio.run(self.async_test_uncertain_llm_create())

    def test_uncertain_llm_ignore(self):
        asyncio.run(self.async_test_uncertain_llm_ignore())

    def test_duplicate_prevention(self):
        asyncio.run(self.async_test_duplicate_prevention())

    def test_wiki_linking(self):
        asyncio.run(self.async_test_wiki_linking())


if __name__ == "__main__":
    unittest.main()
