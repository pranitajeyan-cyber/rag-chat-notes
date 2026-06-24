"""
RAG Engine
===========
Retrieves relevant document chunks and generates answers
using the configured LLM (Gemini, Groq, or local Ollama).
"""

import config
from ingest import get_vector_store


def retrieve_context(query, k=None):
    """Retrieve top-k relevant chunks for a query."""
    k = k or config.TOP_K
    vector_store = get_vector_store()
    results = vector_store.similarity_search_with_score(query, k=k)
    return results


def format_context(results):
    """Format retrieved chunks into a context string with sources."""
    context_parts = []
    sources = set()
    for doc, score in results:
        source = doc.metadata.get("source", "unknown")
        sources.add(source)
        context_parts.append(f"[Source: {source}]\n{doc.page_content}")
    return "\n\n".join(context_parts), sources


def build_prompt(query, context):
    """Build a prompt that includes context and the user's question."""
    return f"""You are a helpful study assistant. Answer the question based ONLY on the provided context.
If the context doesn't contain enough information, say "I couldn't find enough information in your documents to answer that."

Context:
---
{context}
---

Question: {query}

Answer:"""


def query_gemini(prompt):
    """Generate answer using Google Gemini (free tier available)."""
    import google.generativeai as genai

    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    return response.text


def query_groq(prompt):
    """Generate answer using Groq (free tier, very fast)."""
    import requests

    headers = {
        "Authorization": f"Bearer {config.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "mixtral-8x7b-32768",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
    }
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=data,
    )
    return resp.json()["choices"][0]["message"]["content"]


def query_ollama(prompt):
    """Generate answer using local Ollama model."""
    import requests

    data = {
        "model": config.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }
    resp = requests.post(f"{config.OLLAMA_BASE_URL}/api/generate", json=data)
    return resp.json()["response"]


def answer(query, k=None):
    """
    Full RAG pipeline: retrieve -> format -> generate.
    Returns (answer_text, sources_set).
    """
    results = retrieve_context(query, k)

    if not results:
        return ("No documents found. Please upload some documents first.", set())

    context, sources = format_context(results)
    prompt = build_prompt(query, context)

    provider = config.LLM_PROVIDER.lower()
    if provider == "gemini":
        response = query_gemini(prompt)
    elif provider == "groq":
        response = query_groq(prompt)
    elif provider == "ollama":
        response = query_ollama(prompt)
    else:
        response = f"Unknown LLM provider: {provider}"

    return response, sources
