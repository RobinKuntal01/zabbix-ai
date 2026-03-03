from rag.embeddings import get_embedding
from rag.vector_store import VectorStore

LLM_MODEL = "mistral"

store = VectorStore()
store.load()

def answer_with_rag(query):
    """Answer a query using Retrieval-Augmented Generation (RAG) approach."""
    query_embedding = get_embedding(query)
    docs = store.search(query_embedding, top_k=3)

    context = "\n\n".join(docs)
    print(f"RAG context retrieved: {context}")

     # You can further process the context and query to generate a final answer using an LLM
    return context

   