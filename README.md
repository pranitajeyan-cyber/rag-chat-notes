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

## 🚀 Quick Start

### 1. Clone & Setup

```bash
git clone https://github.com/pranitajeyan-cyber/rag-chat-notes.git
cd rag-chat-notes
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up LLM (pick one)

#### Option A: Google Gemini (recommended — free tier)
1. Get a free API key from [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Copy `.env.example` to `.env` and add your key:
```bash
cp .env.example .env
# Edit .env: GEMINI_API_KEY=your-key-here
```

#### Option B: Groq (free, very fast)
1. Get a free API key from [console.groq.com](https://console.groq.com/keys)
2. Set in `.env`: `LLM_PROVIDER=groq` and `GROQ_API_KEY=your-key`

#### Option C: Ollama (fully local, requires install)
1. Install [Ollama](https://ollama.com)
2. Pull a model: `ollama pull llama3.2`
3. Set in `.env`: `LLM_PROVIDER=ollama`

### 4. Run the App

```bash
streamlit run app.py
```

Open the URL shown in terminal (usually `http://localhost:8501`).

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
