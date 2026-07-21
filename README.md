# Fumi

> A local-first AI companion that remembers what matters.

Fumi is an offline-first AI companion that helps users stay accountable to their goals while keeping complete ownership of their personal data. Instead of storing conversations in the cloud, Fumi runs entirely on your machine, stores its knowledge as human-readable Markdown files, and uses Retrieval-Augmented Generation (RAG) to remember relevant context across conversations.

Unlike traditional AI chatbots that forget previous interactions, Fumi builds a persistent understanding of the user through structured long-term memory, allowing conversations to become more personalized over time while remaining completely private.

---

## ✨ Features

* **Local-first** — Runs entirely on your machine using Ollama.
* **Privacy-focused** — No cloud storage or external APIs required.
* **Persistent Memory** — Stores knowledge in a Markdown vault compatible with Obsidian.
* **Semantic Search (RAG)** — Retrieves relevant memories using ChromaDB and vector embeddings.
* **Natural Conversations** — Maintains short-term conversation history alongside long-term memory.
* **Goal Management** — Uses tool calling to create, update, and track goals.
* **Proactive Check-ins** — Background scheduler generates accountability check-ins.
* **Desktop Application** — Built with Tauri, React, and Python.

---

# Architecture

Fumi is composed of several independent components that work together.

```text
React (Tauri Desktop App)
            │
            ▼
      FastAPI Backend
            │
            ▼
     Prompt Builder
            │
 ┌──────────┼──────────┐
 │          │          │
 ▼          ▼          ▼
System    RAG      Conversation
Prompt   Context     History
            │
            ▼
      Local LLM (Ollama)
            │
            ▼
     Assistant Response
            │
            ▼
 Conversation Persistence
            │
            ▼
      Memory Pipeline
            │
 ┌──────────┼──────────┐
 ▼          ▼          ▼
Summary  Extraction  Updates
            │
            ▼
 Markdown Vault
            │
            ▼
 ChromaDB Index
```

---

# How It Works

When a user sends a message:

1. The desktop application sends the request to the FastAPI backend.
2. Recent conversation history is loaded.
3. The user's message is embedded using `nomic-embed-text`.
4. ChromaDB retrieves the most relevant memories from the Markdown vault.
5. The Prompt Builder combines:

   * Fumi's system prompt
   * Retrieved memories
   * Recent conversation history
   * The user's latest message
6. The assembled prompt is sent to the local LLM through Ollama.
7. The assistant's response is streamed back to the desktop application.
8. The conversation is saved to the Markdown vault.
9. The memory pipeline summarizes the conversation, extracts durable information, updates the vault, and re-indexes any modified files.

---

# Memory System

Fumi separates short-term conversation from long-term memory.

### Short-Term Memory

* Recent conversation history
* Included directly in the prompt
* Used to maintain conversational continuity

### Long-Term Memory

* Goals
* Preferences
* Projects
* Habits
* People
* Important memories

Long-term memories are stored as Markdown files with YAML frontmatter and indexed into ChromaDB for semantic retrieval.

---

# Retrieval-Augmented Generation (RAG)

Fumi uses RAG to provide context-aware responses.

```text
Markdown Vault
      │
      ▼
 Chunk Documents
      │
      ▼
Generate Embeddings
      │
      ▼
 Store in ChromaDB

User Question
      │
      ▼
Generate Query Embedding
      │
      ▼
Semantic Search
      │
      ▼
Relevant Memories
      │
      ▼
Prompt Builder
      │
      ▼
Local LLM
```

The Markdown vault remains the source of truth, while ChromaDB acts as a searchable semantic index that can be rebuilt at any time.

---

# Tool Calling

Fumi uses structured Python tools instead of allowing the language model to modify files directly.

Examples include:

* Create Goal
* Update Goal
* Complete Goal
* Create Journal Entry
* Create Notes
* Search Memory

This keeps updates deterministic, auditable, and easy to extend.

---

# Scheduler

A lightweight background scheduler periodically performs proactive tasks such as:

* Daily accountability check-ins
* Goal progress monitoring
* Reminder execution

The scheduler reuses the same tool system as the chat interface instead of interacting with the vault directly.

---

# Tech Stack

## Frontend

* React
* TypeScript
* Tauri

## Backend

* Python
* FastAPI

## AI

* Ollama
* Local Language Models
* `nomic-embed-text`

## Memory

* Markdown Vault
* ChromaDB

## Scheduling

* APScheduler

---

# Design Principles

* Local-first by default
* User owns all data
* Markdown is the source of truth
* ChromaDB is a disposable search index
* Python orchestrates the application
* The LLM reasons; it does not directly modify files
* Components have a single responsibility
* Modular and provider-agnostic architecture

---

# Project Structure

```text
apps/
├── desktop/
└── backend/

packages/
├── core/
├── knowledge/
├── memory/
├── prompts/
├── providers/
├── rag/
├── schedulers/
├── shared/
└── tools/

vault/
chroma/
tests/
config/
```
---

# License

This project is licensed under the MIT License.
