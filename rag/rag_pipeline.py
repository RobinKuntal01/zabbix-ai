from rag.embeddings import get_embedding
from pinecone import Pinecone
import os
from dotenv import load_dotenv

load_dotenv()

LLM_MODEL = "mistral"

def answer_with_rag(query):
    """Answer a query using Retrieval-Augmented Generation (RAG) approach."""
    query_embedding = get_embedding(query)
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY", ""))
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

   