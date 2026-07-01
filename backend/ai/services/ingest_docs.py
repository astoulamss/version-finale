import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from ai.services.knowledge_service import index_all_docs, collection_stats, needs_reindex


def main():
    stats = collection_stats()
    print(f"Current index: {stats['total_chunks']} chunks in '{stats['collection']}'")
    print(f"ChromaDB directory: {stats['chroma_dir']}")
    print()

    if not needs_reindex():
        print("All documents are already indexed. Nothing to do.")
        return

    print("Indexing documents from ai/docs/ ...")
    results = index_all_docs()
    total = sum(results.values())
    print(f"\nDone! Indexed {total} chunks across {len(results)} documents:")
    for name, count in results.items():
        print(f"  {name}: {count} chunks")
    if not results:
        print("No PDF files found in ai/docs/ directory.")

    stats = collection_stats()
    print(f"\nTotal chunks in collection: {stats['total_chunks']}")


if __name__ == "__main__":
    main()
