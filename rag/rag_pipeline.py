from rag.embeddings import get_embedding
from rag.vector_store import VectorStore
from pinecone import Pinecone
from config import PINECONE_API_KEY
LLM_MODEL = "mistral"


def answer_with_rag(query):
    """Answer a query using Retrieval-Augmented Generation (RAG) approach."""
    query_embedding = get_embedding(query)
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index("company-documents")

    results = index.query(
        vector=query_embedding,
        top_k=5,
        include_metadata=True
    )

    context = "\n\n".join(
        match["metadata"]["text"]
        for match in results["matches"]
    )

    print(context)

     # You can further process the context and query to generate a final answer using an LLM
    return context

   