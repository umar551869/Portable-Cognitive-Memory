# ⚙️ PCG Backend: Technical Reference

This directory contains the core logic for the **Portable Cognitive Graph** system. It handles ingestion, graph-building, semantic retrieval, and the REST API.

---

## 🏗️ Core Architecture

The backend is built as a modular pipeline:

1.  **`pcg.api`**: FastAPI endpoints for memory interaction.
2.  **`pcg.processing`**: The ingestion pipeline (Chunking -> Extraction -> Resolution).
3.  **`pcg.providers`**: Abstraction layer for Gemini, OpenAI, and Ollama.
4.  **`pcg.storage`**: Async repositories for Nodes, Edges, Chunks, and Embeddings.

---

## ⚡ Hybrid Ingestion (v2)

We now utilize a **Multi-Provider Fallback** strategy to maximize ingestion throughput while respecting API rate limits:

*   **Gemini (Primary)**: High-speed extraction for bulk files.
*   **OpenAI (Secondary)**: Reliable fallback when Gemini quotas are hit.
*   **Local Ollama (Tertiary)**: 100% uptime fallback for sensitive or disconnected work.

To trigger the master ingestion:
```bash
python ingest_hybrid.py
```

---

## 🛠️ CLI Operations

The `pcg` module provides a comprehensive CLI:

| Command | Description |
| :--- | :--- |
| `python -m pcg serve` | Launch the FastAPI server |
| `python -m pcg initdb` | Initialize/Migrate the SQLite schema |
| `python -m pcg rebuild` | Purge and rebuild the graph from raw logs |
| `python -m pcg reindex` | Update all embeddings for a new model/version |

---

## 📄 Source of Truth
The system follows a **Log-Based Architecture**. The `raw_logs` table is the immutable source of truth. The Knowledge Graph (Nodes/Edges) is a derived projection that can be destroyed and rebuilt at any time without data loss.

---
👉 *For project-wide setup and vision, see the [Root README](../README.md).*
