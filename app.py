"""
RAG Chat with Your Notes
========================
A beautiful Streamlit app for chatting with your documents.
Upload PDFs/TXT files, then ask questions about them.
"""

import os
import tempfile
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="RAG Chat - Study Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS for a polished look ──
st.markdown(
    """
<style>
    /* Main chat area */
    .stApp { background-color: #f8f9fa; }
    .main > div { padding: 1rem 2rem; }

    /* Chat message styling */
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

    /* Sidebar styling */
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

    /* Upload area */
    [data-testid="stFileUploader"] { border: 2px dashed #5c6bc0; border-radius: 12px; padding: 1rem; }

    /* Buttons */
    .stButton button {
        border-radius: 20px;
        font-weight: 500;
        transition: all 0.2s;
    }
    .stButton button:hover { transform: translateY(-1px); box-shadow: 0 4px 8px rgba(0,0,0,0.1); }

    /* Input */
    div[data-testid="stChatInput"] { border-radius: 24px !important; border: 1px solid #ddd !important; }
</style>
""",
    unsafe_allow_html=True,
)

# ── Import our modules ──
from ingest import index_documents, list_indexed_sources, delete_source
from rag_engine import answer


# ── Initialize session state ──
if "messages" not in st.session_state:
    st.session_state.messages = []
if "sources" not in st.session_state:
    st.session_state.sources = list_indexed_sources()
if "processing" not in st.session_state:
    st.session_state.processing = False


# ── Helper Functions ──

def refresh_sources():
    st.session_state.sources = list_indexed_sources()


def process_uploaded_files(uploaded_files):
    """Save uploaded files temporarily, index them, then clean up."""
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

    # Upload section
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown("#### 📤 Upload Documents")
    uploaded_files = st.file_uploader(
        "Drop PDF or TXT files here",
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

    # Document list
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown("#### 📄 Indexed Documents")
    if st.session_state.sources:
        for src in st.session_state.sources:
            col1, col2 = st.columns([4, 1])
            col1.markdown(f"📄 {src}")
            if col2.button("✕", key=f"del_{src}"):
                deleted = delete_source(src)
                refresh_sources()
                st.rerun()
    else:
        st.markdown("*No documents indexed yet*")
    st.markdown("</div>", unsafe_allow_html=True)

    # Settings
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown("#### ⚙️ Settings")
    k = st.slider("Chunks to retrieve", min_value=1, max_value=10, value=4)
    st.markdown("</div>", unsafe_allow_html=True)

    # Footer
    st.markdown("---")
    st.markdown(
        "<small style='opacity:0.6'>Built with Streamlit + LangChain + ChromaDB</small>",
        unsafe_allow_html=True,
    )


# ── Main Chat Area ──

# Header
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("# 💬 Chat with Your Notes")
    st.markdown("Ask questions about your uploaded documents — get answers with sources.")
with col2:
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

st.markdown("---")

# Display chat history
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
    with st.spinner("Searching documents and generating answer..."):
        response, sources = answer(prompt, k=k)
    st.session_state.messages.append(
        {"role": "assistant", "content": response, "sources": list(sources)}
    )
    st.rerun()

# Empty state
if not st.session_state.messages:
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            """
            <div style="text-align:center; padding:3rem 1rem; color:#666;">
                <h2 style="color:#1a237e;">📖 Ready to learn</h2>
                <p>Upload documents in the sidebar,<br>then ask questions here.</p>
                <p style="font-size:0.9rem; color:#999;">
                    Supports PDF, TXT, and Markdown files
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
