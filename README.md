# 🤖 AI Agent Chatbot — Data Center Customer Portal

> A multi-intent conversational agent built on **FastAPI + Llama/Mistral 7B** that handles general queries, RAG-based knowledge retrieval, and live backend API actions — all from a single chat interface.

---

## 🧰 Tech Stack

| Component | Technology |
|---|---|
| **Backend Framework** | FastAPI |
| **LLM** | Llama / Mistral 7B |
| **Vector Database** | FAISS |
| **Embedding Model** | nomic-embed-text |
| **Knowledge Source** | Company PDFs |
| **API Layer** | Internal REST Backend APIs |

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────┐
│              Customer Portal UI             │
│         (User sends chat message)           │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│              FastAPI Gateway                │
│   POST /chat · Session Context · Routing    │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│          Intent Classifier (LLM)            │
│             Llama / Mistral 7B              │
│   Classifies query into one of three types  │
└──────┬──────────────┬────────────────┬──────┘
       │              │                │
       ▼              ▼                ▼
┌────────────┐ ┌────────────┐ ┌──────────────┐
│  GENERAL   │ │ KNOWLEDGE  │ │    ACTION    │
│    INFO    │ │   (RAG)    │ │  (API Call)  │
└────────────┘ └────────────┘ └──────────────┘
       │              │                │
       ▼              ▼                ▼
  Direct LLM    Embed Query      Extract Intent
  (no fetch)    via nomic    +   + Parameters
                    │                  │
                    ▼                  ▼
              FAISS Semantic     Call Backend
              Search on PDF      REST API
              Vector Index           │
                    │                │
                    ▼                ▼
               Top-K Chunks     API Response
               Injected into    as Structured
               LLM Context           Data
       │              │                │
       └──────────────┴────────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │    LLM Response Generation   │
        │       Llama / Mistral 7B     │
        │  Query + Context → Answer    │
        └──────────────┬───────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │    FastAPI Response Handler  │
        │  Format · Session · Stream   │
        └──────────────┬───────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │     Response → User (UI)     │
        │  Grounded · Context-aware    │
        └──────────────────────────────┘
```

---

## 🔀 Intent Types

### 🌐 General Info
Handles broad conversational queries that don't require any external data fetch. The query is sent directly to the LLM with a system context prompt.

**Examples:**
- *"What is a data center?"*
- *"How does colocation work?"*
- *"What is PUE?"*

**Flow:** `User → Classifier → LLM → Response`

---

### 📚 Knowledge (RAG)
Handles company-specific queries by retrieving relevant content from internal PDF documents using semantic search.

**Flow:**
1. Query is embedded using `nomic-embed-text`
2. FAISS performs a similarity search on the indexed PDF vectors
3. Top-K most relevant chunks are retrieved
4. Chunks are injected into the LLM prompt as context
5. LLM generates a grounded, accurate response

**Examples:**
- *"What is our SLA for Tier-3 rack space?"*
- *"What are the power redundancy options?"*
- *"Show me the pricing for cross-connects."*

**Flow:** `User → Classifier → Embed → FAISS → Top-K Chunks → LLM → Response`

---

### ⚙️ Action (API Call)
Handles operational requests that require triggering a real backend action or fetching live data via internal REST APIs.

**Flow:**
1. LLM extracts the intent and required parameters from the query
2. Maps to the appropriate backend API endpoint + builds the payload
3. API is called and the result is returned as structured data
4. LLM formats the result into a human-readable response

**Examples:**
- *"Show my current power usage for Cabinet A3."*
- *"Raise a support ticket for rack cooling issue."*
- *"What's the status of my last order?"*

**Flow:** `User → Classifier → LLM (extract params) → Backend API → LLM → Response`


---

## ⚙️ Setup

### 1. Install dependencies
```bash
pip install fastapi uvicorn faiss-cpu sentence-transformers ollama
```

### 2. Pull the model (Ollama)
```bash
ollama pull mistral
```

### 3. Build the FAISS index from PDFs
```bash
python pipeline/rag.py --build-index --source knowledge/pdfs/
```

### 4. Run the server
```bash
uvicorn main:app --reload --port 8000
```

---

## 🔌 API

### `POST /chat`

**Request:**
```json
{
  "session_id": "user-123",
  "message": "What is the SLA for Tier-3 colocation?"
}
```

**Response:**
```json
{
  "intent": "knowledge",
  "response": "Based on the service agreement, Tier-3 colocation carries a 99.982% uptime SLA...",
  "sources": ["yotta_sla_guide_2024.pdf — page 12"]
}
```

---

## ⚠️ Notes & Recommendations

- **Classifier prompt quality is critical** — be explicit in the system prompt about what each intent type covers. Edge cases like *"show my power usage"* can look like both Knowledge and Action.
- **RAG chunk size** — for data center PDFs (SLAs, pricing, specs), aim for ~400–500 token chunks with ~50 token overlap for best FAISS recall.
- **Action safety** — add a confirmation step in the UI before executing any write operations (ticket creation, config changes etc.).
- **Session context** — pass recent conversation history into the classifier prompt to handle follow-up queries correctly.

---

## 🗺️ Roadmap

- [ ] Streaming responses via FastAPI `StreamingResponse`
- [ ] Hybrid retrieval: FAISS + BM25 keyword fallback
- [ ] Action confirmation UI step for write operations
- [ ] Multi-turn conversation memory (Redis session store)
- [ ] Azure OpenAI swap-in for production scaling
