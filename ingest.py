"""
Document Ingestion Pipeline
============================
Loads documents (PDF, TXT, MD), URLs, and YouTube transcripts,
splits them into chunks, creates embeddings, and stores in ChromaDB.
"""

import os
import re
from pathlib import Path

import trafilatura
from youtube_transcript_api import YouTubeTranscriptApi
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_chroma import Chroma

import config


def extract_youtube_id(url):
    """Extract video ID from various YouTube URL formats."""
    patterns = [
        r"(?:youtube\.com/watch\?v=)([\w-]+)",
        r"(?:youtu\.be/)([\w-]+)",
        r"(?:youtube\.com/embed/)([\w-]+)",
        r"(?:youtube\.com/shorts/)([\w-]+)",
    ]
    for p in patterns:
        match = re.search(p, url)
        if match:
            return match.group(1)
    return None


def is_youtube_url(url):
    """Check if URL is a YouTube link."""
    return extract_youtube_id(url) is not None


def fetch_youtube_transcript(url):
    """Fetch transcript from a YouTube video. Returns (text, title)."""
    video_id = extract_youtube_id(url)
    transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
    text = " ".join(item["text"] for item in transcript_list)
    # Try to get video title from the URL (or use a placeholder)
    title = f"YouTube Video ({video_id})"
    return text, title


def fetch_webpage_text(url):
    """Fetch and extract clean text from a webpage. Returns text or None."""
    downloaded = trafilatura.fetch_url(url)
    if downloaded:
        text = trafilatura.extract(downloaded)
        if text:
            return text
    return None


def load_documents(file_paths):
    """Load documents from PDF and TXT files."""
    docs = []
    for path in file_paths:
        ext = Path(path).suffix.lower()
        try:
            if ext == ".pdf":
                loader = PyPDFLoader(path)
                docs.extend(loader.load())
            elif ext == ".txt":
                loader = TextLoader(path, encoding="utf-8")
                docs.extend(loader.load())
            elif ext == ".md":
                loader = TextLoader(path, encoding="utf-8")
                docs.extend(loader.load())
        except Exception as e:
            print(f"Error loading {path}: {e}")
    return docs


def chunk_documents(documents):
    """Split documents into overlapping chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    return splitter.split_documents(documents)


def get_embedding_model():
    """Get the embedding model (runs locally, free)."""
    return HuggingFaceEmbeddings(
        model_name=f"sentence-transformers/{config.EMBEDDING_MODEL}",
        model_kwargs={"device": "cpu"},
    )


def get_vector_store():
    """Load or create the ChromaDB vector store."""
    embeddings = get_embedding_model()
    return Chroma(
        persist_directory=config.DB_DIR,
        embedding_function=embeddings,
    )


def index_documents(file_paths):
    """
    Full pipeline: load -> chunk -> embed -> store.
    Returns the number of chunks indexed.
    """
    docs = load_documents(file_paths)
    if not docs:
        return 0

    chunks = chunk_documents(docs)

    for chunk in chunks:
        chunk.metadata["source"] = Path(chunk.metadata.get("source", "unknown")).name

    vector_store = get_vector_store()
    vector_store.add_documents(chunks)

    return len(chunks)


def index_text(text, source_name):
    """Index raw text directly (for URLs, YouTube, etc.)."""
    if not text or not text.strip():
        return 0
    doc = Document(page_content=text, metadata={"source": source_name})
    chunks = chunk_documents([doc])
    for chunk in chunks:
        chunk.metadata["source"] = source_name
    vector_store = get_vector_store()
    vector_store.add_documents(chunks)
    return len(chunks)


def ingest_from_url(url):
    """
    Detect URL type (YouTube or webpage) and index content.
    Returns (chunks_count, source_name) or (0, error_message).
    """
    if is_youtube_url(url):
        try:
            text, title = fetch_youtube_transcript(url)
            source = f"YouTube: {title[:40]}"
            count = index_text(text, source)
            return count, source
        except Exception as e:
            return 0, f"YouTube error: {str(e)}"

    try:
        text = fetch_webpage_text(url)
        if text:
            source = url.split("//")[1].split("/")[0][:40]
            count = index_text(text, source)
            return count, source
        return 0, "Could not extract text from this URL"
    except Exception as e:
        return 0, f"URL error: {str(e)}"


def list_indexed_sources():
    """List all unique sources in the vector store."""
    vector_store = get_vector_store()
    try:
        data = vector_store.get()
        sources = set()
        for meta in data.get("metadatas", []):
            if meta and "source" in meta:
                sources.add(meta["source"])
        return sorted(sources)
    except Exception:
        return []


def delete_source(source_name):
    """Delete all chunks from a specific source."""
    vector_store = get_vector_store()
    data = vector_store.get()
    ids_to_delete = []
    for i, meta in enumerate(data.get("metadatas", [])):
        if meta and meta.get("source") == source_name:
            ids_to_delete.append(data["ids"][i])
    if ids_to_delete:
        vector_store.delete(ids_to_delete)
    return len(ids_to_delete)
