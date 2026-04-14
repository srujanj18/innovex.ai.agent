import chromadb
from app.memory.embedder import get_embedding

# 🔥 Initialize ChromaDB
client = chromadb.Client()

collection = client.get_or_create_collection(name="agent_memory")


class VectorStore:

    def add(self, doc_id: str, content: str):
        try:
            embedding = get_embedding(content)

            collection.add(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[content]
            )

        except Exception as e:
            print("❌ Memory add failed:", e)

    def search(self, query: str, k=3):
        try:
            embedding = get_embedding(query)

            results = collection.query(
                query_embeddings=[embedding],
                n_results=k
            )

            return results.get("documents", [[]])[0]

        except Exception as e:
            print("❌ Memory search failed:", e)
            return []