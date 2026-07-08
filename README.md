# Fumi

Fumi is a modular personal AI assistant designed with a Tauri + React desktop frontend, a FastAPI backend, and local Python packages.

## Directory Structure

```
fumi/
│
├── apps/
│   ├── desktop/              # Tauri + React frontend
│   └── backend/              # FastAPI backend
│
├── packages/
│   ├── core/                 # Business logic
│   ├── providers/            # LLM & embedding providers
│   ├── memory/               # Memory Manager
│   ├── rag/                  # Retrieval pipeline
│   ├── tools/                # Tool implementations
│   ├── scheduler/            # Background jobs
│   ├── prompts/              # Prompt templates
│   └── shared/               # Shared types & utilities
│
├── vault/                    # User's markdown knowledge
│
├── chroma/                   # ChromaDB storage
│
├── config/                   # App configurations
│
├── scripts/                  # Utility scripts
│
├── tests/                    # Unit/integration tests
│
├── pyproject.toml            # Python project workspace config
├── README.md                 # Project documentation
└── .env                      # Local environment configuration
```

## Getting Started

### Backend Setup
1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -e .
   ```
3. Run the backend:
   ```bash
   uvicorn apps.backend.main:app --reload
   ```

### Desktop Setup
1. Navigate to desktop directory:
   ```bash
   cd apps/desktop
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run in development mode:
   ```bash
   npm run tauri dev
   ```
