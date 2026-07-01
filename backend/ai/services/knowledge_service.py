import os
import hashlib
from pathlib import Path
from typing import Optional
import chromadb
from chromadb.config import Settings
from pypdf import PdfReader


CHROMA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")
DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs")
COLLECTION_NAME = "hr_policies"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150

_collection = None


def _get_collection():
    global _collection
    if _collection is not None:
        return _collection
    os.makedirs(CHROMA_DIR, exist_ok=True)
    client = chromadb.PersistentClient(path=CHROMA_DIR, settings=Settings(anonymized_telemetry=False))
    _collection = client.get_or_create_collection(name=COLLECTION_NAME)
    return _collection


def _chunk_text(text: str, file_name: str, page_num: int) -> list[dict]:
    chunks = []
    words = text.split()
    start = 0
    chunk_idx = 0
    while start < len(words):
        end = start + CHUNK_SIZE
        chunk_words = words[start:end]
        chunk_text = " ".join(chunk_words)
        if not chunk_text.strip():
            break
        chunk_id = hashlib.md5(f"{file_name}_p{page_num}_c{chunk_idx}".encode()).hexdigest()
        chunks.append({
            "id": chunk_id,
            "text": chunk_text,
            "metadata": {
                "source": file_name,
                "page": page_num,
                "chunk": chunk_idx,
            },
        })
        chunk_idx += 1
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def index_pdf(file_path: str) -> int:
    collection = _get_collection()
    file_name = os.path.basename(file_path)
    reader = PdfReader(file_path)
    all_chunks = []
    for page_num, page in enumerate(reader.pages, 1):
        text = page.extract_text()
        if not text.strip():
            continue
        all_chunks.extend(_chunk_text(text, file_name, page_num))
    if not all_chunks:
        return 0
    collection.add(
        ids=[c["id"] for c in all_chunks],
        documents=[c["text"] for c in all_chunks],
        metadatas=[c["metadata"] for c in all_chunks],
    )
    return len(all_chunks)


def index_all_docs() -> dict[str, int]:
    results = {}
    docs_path = Path(DOCS_DIR)
    if not docs_path.exists():
        return results
    for pdf_file in sorted(docs_path.glob("*.pdf")):
        count = index_pdf(str(pdf_file))
        results[pdf_file.name] = count
    return results


def search_documents(query: str, n_results: int = 5) -> list[dict]:
    collection = _get_collection()
    count = collection.count()
    if count == 0:
        return []
    results = collection.query(query_texts=[query], n_results=min(n_results, count))
    documents = []
    if not results["documents"]:
        return documents
    for i, doc in enumerate(results["documents"][0]):
        metadata = results["metadatas"][0][i] if results["metadatas"] else {}
        documents.append({
            "text": doc,
            "source": metadata.get("source", "unknown"),
            "page": metadata.get("page", 0),
            "relevance": results.get("distances", [[0]])[0][i] if results.get("distances") else 0,
        })
    return documents


def format_context(documents: list[dict]) -> str:
    if not documents:
        return ""
    lines = []
    for i, doc in enumerate(documents, 1):
        source = doc["source"].replace(".pdf", "").replace("_", " ").title()
        lines.append(f"[Document {i}] Source: {source} (page {doc['page']})")
        lines.append(doc["text"])
        lines.append("")
    return "\n".join(lines)


def collection_stats() -> dict:
    collection = _get_collection()
    count = collection.count()
    return {
        "total_chunks": count,
        "collection": COLLECTION_NAME,
        "chroma_dir": CHROMA_DIR,
    }


_last_reindex_check = 0.0

def needs_reindex() -> bool:
    global _last_reindex_check
    import time
    now = time.time()
    if now - _last_reindex_check < 10:
        return False
    _last_reindex_check = now
    collection = _get_collection()
    if collection.count() == 0:
        return True
    docs_path = Path(DOCS_DIR)
    if not docs_path.exists():
        return False
    pdf_files = list(docs_path.glob("*.pdf"))
    if not pdf_files:
        return True
    existing_sources = set()
    if collection.count() > 0:
        metadatas = collection.get(limit=collection.count())["metadatas"]
        if metadatas:
            existing_sources = {m["source"] for m in metadatas if m.get("source")}
    current_files = {f.name for f in pdf_files}
    if current_files != existing_sources:
        return True
    return False
