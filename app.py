"""
RAG Chat with Your Notes
========================
Chat with documents, webpages, and YouTube videos.
Upload files or paste links — then ask questions.
"""

import os
import json
import glob
import tempfile
from pathlib import Path
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="RAG Chat - Study Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ──
st.markdown(
    """
<style>
    .stApp { background-color: #f8f9fa; }
    .main > div { padding: 1rem 2rem; }
    .user-message {
        background: #e3f2fd;
        padding: 1rem 1.2rem;
        border-radius: 18px 18px 4px 18px;
        margin: 0.5rem 0;
        max-width: 80%;
        margin-left: auto;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    .assistant-message {
        background: white;
        padding: 1rem 1.2rem;
        border-radius: 18px 18px 18px 4px;
        margin: 0.5rem 0;
        max-width: 80%;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        border: 1px solid #e9ecef;
    }
    .source-badge {
        display: inline-block;
        background: #e8f5e9;
        color: #2e7d32;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        margin: 2px 4px 2px 0;
    }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a237e 0%, #283593 100%);
        color: white;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p { color: white; }
    .sidebar-section {
        background: rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
    }
    [data-testid="stFileUploader"] { border: 2px dashed #5c6bc0; border-radius: 12px; padding: 1rem; }
    .stButton button {
        border-radius: 20px;
        font-weight: 500;
        transition: all 0.2s;
    }
    .stButton button:hover { transform: translateY(-1px); box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    div[data-testid="stChatInput"] { border-radius: 24px !important; border: 1px solid #ddd !important; }
    .chat-item {
        cursor: pointer;
        padding: 6px 10px;
        border-radius: 8px;
        margin: 2px 0;
        background: rgba(255,255,255,0.05);
        font-size: 0.85rem;
    }
    .chat-item:hover { background: rgba(255,255,255,0.15); }
</style>
""",
    unsafe_allow_html=True,
)

# ── Imports ──
from ingest import index_documents, list_indexed_sources, delete_source, ingest_from_url
from rag_engine import answer

# ── Constants ──
CHAT_HISTORY_DIR = "history"

# ── Chat History Functions ──

def ensure_history_dir():
    os.makedirs(CHAT_HISTORY_DIR, exist_ok=True)

def save_chat(name, messages):
    ensure_history_dir()
    path = os.path.join(CHAT_HISTORY_DIR, f"{name}.json")
    data = {
        "name": name,
        "messages": messages,
        "timestamp": datetime.now().isoformat(),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_chat(name):
    path = os.path.join(CHAT_HISTORY_DIR, f"{name}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def list_chats():
    ensure_history_dir()
    chats = []
    for f in sorted(glob.glob(os.path.join(CHAT_HISTORY_DIR, "*.json")), key=os.path.getmtime, reverse=True):
        try:
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
                chats.append(data)
        except Exception:
            pass
    return chats

def delete_chat(name):
    path = os.path.join(CHAT_HISTORY_DIR, f"{name}.json")
    if os.path.exists(path):
        os.remove(path)

def generate_chat_name(messages):
    """Auto-name chat from first user message or timestamp."""
    if messages:
        for m in messages:
            if m["role"] == "user":
                name = m["content"][:50].strip()
                return name
    return f"Chat {datetime.now().strftime('%d %b %H:%M')}"

# ── Session State ──
if "chat_name" not in st.session_state:
    st.session_state.chat_name = generate_chat_name([])
if "messages" not in st.session_state:
    st.session_state.messages = []
if "sources" not in st.session_state:
    st.session_state.sources = list_indexed_sources()
if "processing" not in st.session_state:
    st.session_state.processing = False

# ── Helpers ──

def refresh_sources():
    st.session_state.sources = list_indexed_sources()

def new_chat():
    save_chat(st.session_state.chat_name, st.session_state.messages)
    st.session_state.messages = []
    st.session_state.chat_name = generate_chat_name([])

def process_uploaded_files(uploaded_files):
    st.session_state.processing = True
    file_paths = []
    for uploaded_file in uploaded_files:
        suffix = Path(uploaded_file.name).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.getvalue())
            file_paths.append(tmp.name)
    try:
        count = index_documents(file_paths)
        refresh_sources()
        return count
    finally:
        for path in file_paths:
            try:
                os.unlink(path)
            except Exception:
                pass
        st.session_state.processing = False

# ── Sidebar ──

with st.sidebar:
    st.markdown("# 📚 RAG Chat")
    st.markdown("### Study Assistant")
    st.markdown("---")

    # Upload files
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown("#### 📤 Upload Files")
    uploaded_files = st.file_uploader(
        "Drop PDF, TXT, or MD files here",
        type=["pdf", "txt", "md"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )
    if uploaded_files:
        with st.spinner("Indexing documents..."):
            count = process_uploaded_files(uploaded_files)
        if count:
            st.success(f"✅ Indexed {count} chunks from {len(uploaded_files)} file(s)")
        else:
            st.warning("No content could be extracted.")
    st.markdown("</div>", unsafe_allow_html=True)

    # URL / YouTube input
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown("#### 🌐 Add from Link")
    url = st.text_input(
        "Paste a webpage or YouTube link",
        placeholder="https://...",
        label_visibility="collapsed",
    )
    if url:
        icon = "🎬" if "youtube" in url.lower() or "youtu.be" in url.lower() else "🌐"
        label = "Fetch YouTube Transcript" if "youtube" in url.lower() or "youtu.be" in url.lower() else "Fetch Webpage"
        if st.button(f"{icon} {label}", use_container_width=True):
            with st.spinner("Fetching and indexing..."):
                count, source = ingest_from_url(url)
            if count > 0:
                st.success(f"✅ Indexed {count} chunks from {source}")
                refresh_sources()
            else:
                st.error(source)
    st.markdown("</div>", unsafe_allow_html=True)

    # Indexed documents
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown("#### 📄 Indexed Sources")
    if st.session_state.sources:
        for src in st.session_state.sources:
            col1, col2 = st.columns([4, 1])
            col1.markdown(f"📄 {src[:35]}{'...' if len(src) > 35 else ''}")
            if col2.button("✕", key=f"del_{src}"):
                delete_source(src)
                refresh_sources()
                st.rerun()
    else:
        st.markdown("*No sources indexed yet*")
    st.markdown("</div>", unsafe_allow_html=True)

    # Chat history
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown("#### 💬 Chat History")
    if st.button("➕ New Chat", use_container_width=True):
        new_chat()
        st.rerun()
    chats = list_chats()
    if chats:
        for chat in chats[:10]:
            name = chat.get("name", "Unknown")[:30]
            if st.button(f"💬 {name}", key=f"chat_{chat['name']}", use_container_width=True):
                st.session_state.messages = chat["messages"]
                st.session_state.chat_name = chat["name"]
                st.rerun()
    else:
        st.markdown("*No saved chats*")
    st.markdown("</div>", unsafe_allow_html=True)

    # Settings
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown("#### ⚙️ Settings")
    k = st.slider("Chunks to retrieve", min_value=1, max_value=10, value=4)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(
        "<small style='opacity:0.6'>Built with Streamlit + LangChain + ChromaDB</small>",
        unsafe_allow_html=True,
    )

# ── Main Chat Area ──

col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("# 💬 Chat with Your Notes")
    st.markdown("Ask questions about your documents, webpages, and YouTube videos.")
with col2:
    if st.button("🗑️ Clear Chat"):
        save_chat(st.session_state.chat_name, st.session_state.messages)
        st.session_state.messages = []
        st.rerun()

st.markdown("---")

# Display messages
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(
            f'<div class="user-message"><strong>You</strong><br>{msg["content"]}</div>',
            unsafe_allow_html=True,
        )
    else:
        sources_html = ""
        if msg.get("sources"):
            src_list = "".join(
                f'<span class="source-badge">📄 {s}</span>' for s in msg["sources"]
            )
            sources_html = f'<br><div style="margin-top:8px">{src_list}</div>'
        st.markdown(
            f'<div class="assistant-message">'
            f'<strong>Assistant</strong><br>{msg["content"]}{sources_html}</div>',
            unsafe_allow_html=True,
        )

# Chat input
if prompt := st.chat_input("Ask a question about your documents..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.spinner("Searching and generating answer..."):
        response, sources = answer(prompt, k=k)
    st.session_state.messages.append(
        {"role": "assistant", "content": response, "sources": list(sources)}
    )
    st.session_state.chat_name = generate_chat_name(st.session_state.messages)
    save_chat(st.session_state.chat_name, st.session_state.messages)
    st.rerun()

# Empty state
if not st.session_state.messages:
    st.markdown("---")
    c1, c2, c3 = st.columns([1, 3, 1])
    with c2:
        st.markdown(
            """
            <div style="text-align:center; padding:2rem 1rem; color:#666;">
                <h2 style="color:#1a237e;">📖 How to Use</h2>
                <div style="text-align:left; max-width:500px; margin:0 auto;">
                <p><strong>Step 1:</strong> Add content — upload files, paste a webpage URL, or a YouTube link (sidebar → left)</p>
                <p><strong>Step 2:</strong> Wait for indexing — you'll see a success message</p>
                <p><strong>Step 3:</strong> Type a question in the chat box below and press Enter</p>
                <p><strong>Step 4:</strong> Read the answer — generated from your content only, with source badges</p>
                </div>
                <hr style="margin:2rem auto; width:50%;">
                <p style="font-size:0.9rem; color:#999;">
                Supports PDF, TXT, MD, webpages, and YouTube videos
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
