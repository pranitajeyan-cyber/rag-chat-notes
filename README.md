# 📚 RAG Chat with Your Notes

**Chat with your study documents using RAG (Retrieval-Augmented Generation).**  
Upload PDFs and text files, then ask questions — the AI answers using only your content.

Built as an M.Tech CSE project. Works with free APIs (Gemini, Groq) or fully local (Ollama).

---

## ✨ Features

- **Document Ingestion** — Upload PDF, TXT, or Markdown files
- **Smart Chunking** — Documents split into overlapping chunks for better retrieval
- **Vector Search** — Finds the most relevant chunks using sentence embeddings (runs locally, free)
- **LLM-Powered Answers** — Generates answers using Gemini, Groq, or local Ollama
- **Source Citations** — Every answer shows which documents were used
- **Beautiful UI** — Clean chat interface with dark sidebar, source badges, and document management
- **Document Management** — View, delete indexed documents from the sidebar

---

## 🧠 Architecture

```
User Question
     │
     ▼
┌─────────────────┐
│  Embed Question  │  ← sentence-transformers (local, free)
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────┐
│  Retrieve Top-k  │────▶│  ChromaDB    │
│  Similar Chunks  │◀────│  (Vector DB) │
└────────┬────────┘     └──────────────┘
         │
         ▼
┌─────────────────┐
│  Build Prompt   │  ← context + question
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Generate        │  ← Gemini / Groq / Ollama
│  Answer          │
└────────┬────────┘
         │
         ▼
   Final Answer + Sources
```

### Data Flow

1. **Upload** → Documents are loaded (PDF/TXT/MD)
2. **Chunk** → Split into overlapping pieces (configurable size)
3. **Embed** → Each chunk converted to a vector using `all-MiniLM-L6-v2`
4. **Store** → Vectors saved in ChromaDB (on disk)
5. **Query** → Your question is embedded with the same model
6. **Retrieve** → Top-k most similar chunks fetched from ChromaDB
7. **Generate** → LLM receives chunks as context + your question → answers

---

## 🚀 Quick Start — 3 Ways to Run

### 🐍 Option 1: Python (recommended for development)

**Prerequisites:** [Download Python 3.9+](https://www.python.org/downloads/)

```bash
# Download the project
git clone https://github.com/pranitajeyan-cyber/rag-chat-notes.git
cd rag-chat-notes

# Install dependencies (one-time)
pip install -r requirements.txt

# Set up free API key (pick one)
```

| Provider | Get API Key | Then in `.env` set |
|---|---|---|
| **Gemini** ✅ | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) | `GEMINI_API_KEY=your-key` |
| **Groq** 🚀 | [console.groq.com/keys](https://console.groq.com/keys) | `LLM_PROVIDER=groq` and `GROQ_API_KEY=your-key` |
| **Ollama** 💻 | [ollama.com](https://ollama.com) + `ollama pull llama3.2` | `LLM_PROVIDER=ollama` |

```bash
# Create .env file (edit with your key)
copy .env.example .env

# Run the app
streamlit run app.py
```

Browser opens at [http://localhost:8501](http://localhost:8501) 🎉

---

### 🐳 Option 2: Docker (works on Windows/Mac/Linux — no Python needed)

**Prerequisites:** [Download Docker Desktop](https://www.docker.com/products/docker-desktop/)

```bash
# Download the project
git clone https://github.com/pranitajeyan-cyber/rag-chat-notes.git
cd rag-chat-notes

# Create .env with your API key
copy .env.example .env
# Edit .env and add your GEMINI_API_KEY

# One command to build & run
docker compose up -d
```

Open [http://localhost:8501](http://localhost:8501) 🎉

To stop: `docker compose down`

---

### 🪟 Option 3: Windows .exe (double-click to run — no install needed)

**Prerequisites:** [Download Python 3.9+](https://www.python.org/downloads/)

```bash
# Build the .exe (one-time, takes 2-5 min)
python scripts/build_exe.py
```

The `.exe` will be at `dist/rag-chat-notes/rag-chat-notes.exe`

- **Size:** ~300-400 MB (bundles Python + all libraries)
- **To run:** Double-click the .exe, your browser opens automatically
- **Windows only** (Mac/Linux users use Docker instead)

---

## 🎮 How to Use

---

## 🎮 How to Use (Step by Step)

### Step 1: Upload Documents
Look at the **sidebar (left panel)** → click **"Browse files"** → select your PDF, TXT, or Markdown files. You can upload multiple at once.

### Step 2: Wait for Indexing
You'll see a spinner "Indexing documents..." followed by a green success message like:
> ✅ Indexed 15 chunks from 2 file(s)

Your files are now stored in the vector database.

### Step 3: Verify Your Documents
The sidebar shows all indexed documents under **"Indexed Documents"**. You can delete any document by clicking **✕** next to it.

### Step 4: Ask a Question
Type your question in the **chat input box** at the bottom of the page and press Enter. For example:

> What is transfer learning in machine learning?

### Step 5: Read the Answer
The AI responds using **only your uploaded documents**. Every answer shows **source badges** — small green labels indicating which document(s) provided the information.

### Step 6: Tweak Settings (Optional)
In the sidebar, adjust **"Chunks to retrieve"** — higher values (6-10) give more context but may include irrelevant info. Lower values (1-3) are stricter.

### Quick Test
The repo includes `docs/sample.txt` with ML fundamentals. Upload it and ask:
- "What are the types of machine learning?"
- "What is overfitting?"
- "Explain the bias-variance tradeoff"

---

## 📁 Project Structure

```
rag-chat-notes/
├── app.py              # Streamlit UI (main entry point)
├── config.py           # Configuration (reads .env)
├── ingest.py           # Document loading, chunking, embedding, storage
├── rag_engine.py       # Retrieval + generation pipeline
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
├── .gitignore
├── docs/               # Sample documents to try
│   └── sample.txt
└── README.md
```

---

## 🛠️ Configuration

All settings via `.env` file:

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `gemini` | `gemini`, `groq`, or `ollama` |
| `GEMINI_API_KEY` | — | Google Gemini API key |
| `GROQ_API_KEY` | — | Groq API key |
| `OLLAMA_MODEL` | `llama3.2` | Local model name |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence transformer model |
| `CHUNK_SIZE` | `512` | Characters per chunk |
| `CHUNK_OVERLAP` | `64` | Overlap between chunks |
| `TOP_K` | `4` | Number of chunks to retrieve |

---

## 🎯 Use Cases

- **Study Notes Q&A** — Upload your lecture notes, ask questions during revision
- **Research Paper Analysis** — Upload PDFs of papers, ask about methodology/results
- **Project Documentation** — Upload project specs, get quick answers
- **Exam Preparation** — Upload textbooks chapters, practice with questions

---

## 📈 Future Enhancements

- [ ] Web scraping support (URL ingestion)
- [ ] Multi-modal RAG (images in documents)
- [ ] Chat history persistence
- [ ] Document summarization
- [ ] Citation highlighting (exact spans in source)
- [ ] Docker deployment

---

## 🤝 License

MIT

---

*Built as part of M.Tech CSE — Pranita Jeyan*
