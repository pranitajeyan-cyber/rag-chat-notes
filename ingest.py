"""
Document Ingestion Pipeline
============================
Loads documents (PDF, TXT), splits them into chunks,
creates embeddings, and stores in ChromaDB.
"""

import os
from pathlib import Path

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

import config


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
