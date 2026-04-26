import json
import os
from typing import List, Dict

import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer


STORE_PATH = "backend/app/db/vector_store.json"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

model = SentenceTransformer(MODEL_NAME)


def chunk_text(text: str, chunk_size: int = 180, overlap: int = 40) -> List[str]:
    words = text.split()
    chunks = []

    start = 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        start += chunk_size - overlap

    return chunks


def load_store() -> List[Dict]:
    if not os.path.exists(STORE_PATH):
        return []

    with open(STORE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_store(data: List[Dict]):
    os.makedirs(os.path.dirname(STORE_PATH), exist_ok=True)

    with open(STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def ingest_text(filename: str, text: str):
    store = load_store()
    chunks = chunk_text(text)

    embeddings = model.encode(
        chunks,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    start_id = len(store)

    for i, chunk in enumerate(chunks):
        store.append({
            "id": start_id + i,
            "source": filename,
            "text": chunk,
            "embedding": embeddings[i].tolist()
        })

    save_store(store)

    return {
        "filename": filename,
        "chunks_added": len(chunks),
        "total_chunks": len(store)
    }


def cosine_similarity(a, b):
    return float(np.dot(a, b))


def hybrid_search(query: str, top_k: int = 5):
    store = load_store()

    if not store:
        return []

    texts = [item["text"] for item in store]
    embeddings = np.array([item["embedding"] for item in store])

    # Semantic vector search
    query_embedding = model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True
    )[0]

    vector_scores = np.dot(embeddings, query_embedding)

    # BM25 keyword search
    tokenized_docs = [text.lower().split() for text in texts]
    bm25 = BM25Okapi(tokenized_docs)
    bm25_scores = bm25.get_scores(query.lower().split())

    # Normalize scores
    vector_scores = np.array(vector_scores)
    bm25_scores = np.array(bm25_scores)

    if bm25_scores.max() > 0:
        bm25_scores = bm25_scores / bm25_scores.max()

    combined_scores = (0.7 * vector_scores) + (0.3 * bm25_scores)

    top_indices = combined_scores.argsort()[::-1][:top_k]

    results = []

    for idx in top_indices:
        item = store[int(idx)]

        results.append({
            "source": item["source"],
            "text": item["text"],
            "score": float(combined_scores[idx])
        })

    return results