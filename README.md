# 🤖 AI Agent Chatbot — Data Center Customer Portal

> A multi-intent conversational agent built on **FastAPI + Mistral 7B (Ollama)** that handles general queries, RAG-based knowledge retrieval, live Zabbix API actions, and a full **ReAct agent loop** — all from a single chat interface with persistent session history.

---

## 🧰 Tech Stack

| Component | Technology |
|---|---|
| **Backend Framework** | FastAPI |
| **LLM** | Mistral 7B (via Ollama) |
| **Vector Database** | FAISS |
| **Embedding Model** | nomic-embed-text |
| **Knowledge Source** | Company PDFs |
| **API Layer** | Zabbix Client (CPU & Power stubs) |
| **Session Store** | Redis (async via `redis.asyncio`) |
| **Agent Pattern** | Custom ReAct loop (plain Python, no framework) |

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────┐
│              Customer Portal UI             │
│   chat_v2.html (sidebar + dark mode)        │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│              FastAPI Gateway                │
│  POST /chat   · POST /agent                 │
│  GET  /sidebar· GET /chat-history/{id}      │
│  POST /upload-dox                           │
└──────┬──────────────────────────┬───────────┘
       │                          │
       ▼                          ▼
┌─────────────┐         ┌─────────────────────┐
│   Classic   │         │    ReAct Agent Loop  │
│  Pipeline   │         │  react_agent.py      │
│  /chat      │         │  /agent              │
└──────┬──────┘         └──────────┬──────────┘
       │                           │
       ▼                           ▼
┌─────────────────┐    ┌──────────────────────┐
│ Intent Classify │    │ Thought → Action      │
│ (LLM, Mistral)  │    │ → Observation loop   │
└──┬──────┬───┬───┘    │ MAX_STEPS = 6        │
   │      │   │        │ Loop detection       │
   ▼      ▼   ▼        └──────────┬───────────┘
 Info   RAG  Action               │
  │      │     │                  ▼
  │      │     │       ┌──────────────────────┐
  │      │     │       │   Tool Registry      │
  │      │  Zabbix     │ get_server_cpu        │
  │   FAISS   Client   │ get_rack_power        │
  │   + LLM            │ list_servers_in_rack  │
  │                    │ list_available_racks  │
  │                    │ get_cooling_status    │
  └────────────────────┴──────────────────────┘
                  │
                  ▼
     ┌────────────────────────────┐
     │   FastAPI Response Handler │
     │  /chat  → {reply}          │
     │  /agent → {steps[], …}     │
     └────────────┬───────────────┘
                  │
                  ▼
     ┌────────────────────────────┐
     │  Redis Session Store       │
     │  chat:{user}:{session_id}  │
     │  chats:{user} (sidebar)    │
     └────────────────────────────┘
```

---

## 🔀 Intent Types (Classic Pipeline — POST /chat)

### 🌐 General Info
Handles broad conversational queries that don't require any external data fetch. The query is sent directly to the LLM with a system context prompt.

**Examples:** `"What is a data center?"` · `"How does PUE work?"`

**Flow:** `User → Classifier → LLM → Response`

---

### 📚 Knowledge (RAG)
Handles company-specific queries by retrieving relevant content from internal PDF documents using semantic search.

**Flow:**
1. Query embedded using `nomic-embed-text`
2. FAISS similarity search on indexed PDF vectors
3. Top-K most relevant chunks retrieved
4. Chunks injected into LLM prompt as context
5. LLM generates a grounded response

**Examples:** `"What's our SLA for Tier-3 rack space?"` · `"AstraVault cooling thresholds?"`

**Flow:** `User → Classifier → Embed → FAISS → Top-K Chunks → LLM → Response`

---

### ⚙️ Action (Zabbix API)
Handles operational requests that require fetching live data via the Zabbix client.

**Flow:**
1. LLM classifies tool (`get_cpu_usage` or `get_power_usage`) and extracts parameters
2. Tool is dispatched via an allowlist check
3. Raw metric result passed back to LLM for natural language explanation

**Examples:** `"Show NM1 CPU usage"` · `"What's the power draw on RACK-A1?"`

**Flow:** `User → Classifier → LLM (extract params) → Zabbix Client → LLM explain → Response`

---

## 🤖 ReAct Agent Loop (POST /agent)

A custom Reason + Act agent implemented from scratch in plain Python — no LangChain or framework required. The core loop is **prompt formatting + regex/JSON parsing**.

### How it works

```
messages = [system_prompt, user_query]

loop (up to MAX_STEPS = 6):
    raw = LLM(messages)           # FORMAT A or FORMAT B
    parsed = json.loads(raw)

    if "final_answer" in parsed:  # FORMAT B → done
        return answer

    action = parsed["action"]     # FORMAT A → dispatch tool
    observation = dispatch(action, parsed["action_input"])

    messages += [assistant: raw, user: f"Observation: {observation}"]
    # Scratchpad IS the message history (Mistral workaround — no tool role)
```

### Key implementation details

- **Low temperature** is used for deterministic tool-call JSON output
- **Loop detection** tracks `(action, json_input)` pairs — duplicate calls abort
- **MAX_STEPS = 6** is the safety ceiling against runaway loops
- **Tool dispatch** is a plain `dict` registry decorated with `@add_tool`
- **Scratchpad-as-messages** is the Mistral/Ollama workaround (no native `tool` role)

### Registered tools

| Tool | Description |
|---|---|
| `get_server_cpu` | CPU % for a named server |
| `get_rack_power` | Power draw (W) for a rack |
| `list_servers_in_rack` | Servers physically in a given rack |
| `list_available_racks` | All known rack IDs |
| `get_cooling_status` | Inlet temp (°C) and cooling mode |

> All tools are currently stubs with predefined data — swap the function bodies for real Zabbix API calls to go live.

### Response shape

```json
{
  "final_answer": "RACK-C2 is at 99% power and 27.8°C inlet — critical.",
  "total_steps": 3,
  "steps": [
    {
      "step": 1,
      "type": "tool_call",
      "thought": "...",
      "action": "get_rack_power",
      "action_input": {"rack_id": "RACK-C2"},
      "observation": "{\"watts\": 4950, ...}"
    },
    { "step": 2, "type": "final_answer", "thought": "...", "content": "..." }
  ]
}
```

The `/agent` trace viewer (`agent.html`) renders each step as a Thought → Action → Observation timeline.

---

## 🗃️ Session Storage (Redis)

Every conversation is persisted in Redis under two key patterns:

| Key | Type | Contents |
|---|---|---|
| `chat:{user_id}:{session_id}` | List | Ordered `MessageStore` objects (role, text, timestamp) |
| `chats:{user_id}` | Hash | `ChatMetadata` per session (session_id, title, updated_at) |

The sidebar (`GET /sidebar`) reads the hash, sorts by `updated_at` descending, and returns the list. The v2 chat UI (`chat_v2.html`) loads history via `GET /chat-history/{session_id}` when switching sessions.

---

## 🖥️ UI Pages

| Route | Template | Description |
|---|---|---|
| `GET /` | `chat_v2.html` | Main chat UI — sidebar, dark mode, session switching |
| `GET /agent` | `agent.html` | ReAct trace viewer — step-by-step Thought/Action/Observation |
| `GET /add-dox` | `add_dox.html` | PDF upload → FAISS ingestion |

---

## ⚙️ Setup

### 1. Install dependencies
```bash
pip install fastapi uvicorn faiss-cpu ollama redis pypdf
```

### 2. Pull the model (Ollama)
```bash
ollama pull mistral
ollama pull nomic-embed-text
```

### 3. Start Redis
```bash
# macOS/Linux
redis-server

# Windows
redis-server.exe
```

### 4. Ingest documents into FAISS (optional)
Upload PDFs via the UI at `/add-dox`, or ingest manually:
```python
# In rag/ingest.py — call handle_file() or adapt the commented-out snippet at the bottom
```

### 5. Run the server
```bash
uvicorn main:app --reload --port 8000
```

---

## 🔌 API Reference

### `POST /chat`
```json
// Request
{ "message": "Is RACK-C2 at risk?", "session_id": "uuid-here" }

// Response
{ "reply": "Yes — RACK-C2 is running critically..." }
```

### `POST /agent`
```json
// Request
{ "message": "Which servers in RACK-C2 are overloaded?", "session_id": "uuid-here" }

// Response
{ "final_answer": "...", "total_steps": 3, "steps": [...] }
```

### `GET /sidebar`
Returns sorted list of `ChatMetadata` objects for the current user's session history.

### `GET /chat-history/{session_id}`
Returns the full ordered message list (`role`, `text`, `timestamp`) for a session.

### `POST /upload-dox`
Accepts a PDF file upload, chunks and embeds it, and adds it to the FAISS vector store.

---

## ⚠️ Known Issues & Notes

- **Intent classifier JSON parsing**: The classifier sometimes returns the full JSON object as a string inside the `category` field (see `app.log`). The double-parse in `process_llm_call` handles this — keep the `category['category']` access pattern.
- **Mistral tool role workaround**: Ollama's Mistral doesn't support a native `tool` role in the chat API. Tool observations are injected as `user` turn messages — this is intentional.
- **Redis required**: The `/chat` endpoint, sidebar, and history all depend on Redis. Run `redis-server` before starting FastAPI.
- **RAG chunk size**: Aim for ~400–500 char chunks with ~100 char overlap for data center PDFs (SLAs, specs). Adjust in `rag/ingest.py`.
- **Action safety**: Add a confirmation step in the UI before executing any write operations (ticket creation, config changes).

---

## 🗺️ Roadmap

- [ ] Streaming responses via FastAPI `StreamingResponse`
- [ ] Hybrid retrieval: FAISS + BM25 keyword fallback
- [ ] Wire ReAct tools to real Zabbix API calls
- [ ] Action confirmation UI step for write operations
- [ ] Multi-turn context passed into classifier prompt (follow-up query handling)
- [ ] Azure OpenAI swap-in for production scaling
