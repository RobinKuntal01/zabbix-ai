import os
import uuid
import re
from pinecone import Pinecone, ServerlessSpec
from pypdf import PdfReader

from rag.embeddings import get_embedding

RAG_FOLDER = "rag"
INDEX_NAME = "company-documents"

async def handle_file(file):
    contents = await file.read()

    os.makedirs(RAG_FOLDER, exist_ok=True)

    file_path = os.path.join(RAG_FOLDER, file.filename)

    with open(file_path, "wb") as f:
        f.write(contents)
    if file.filename.endswith(".pdf"):
        extracted_text = extract_pdf_text(file_path)
    elif file.filename.endswith(".txt"):
        extracted_text = process_text_file(file_path)
    
    extracted_text = clean_text(extracted_text)
    chunks = chunk_text(extracted_text)

    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

    # Create index if it doesn't exist
    existing_indexes = pc.list_indexes().names()

    if INDEX_NAME not in existing_indexes:
        pc.create_index(
            name=INDEX_NAME,
            dimension=768,  # Change if your embedding model uses a different dimension
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )

    index = pc.Index(INDEX_NAME)

    vectors = []

    for chunk_no, chunk in enumerate(chunks):
        print(f"Processing chunk {chunk_no}")

        embedding = get_embedding(chunk)
        print(len(embedding))
        vectors.append({
            "id": str(uuid.uuid4()),
            "values": embedding,
            "metadata": {
                "text": chunk,
                "filename": file.filename,
                "chunk_number": chunk_no
            }
        })

    # Batch upsert
    batch_size = 100

    for i in range(0, len(vectors), batch_size):
        index.upsert(
            vectors=vectors[i:i + batch_size]
        )

    return {
        "message": f"Successfully processed {file.filename}",
        "chunks_added": len(vectors)
    }


def extract_pdf_text(file_path: str) -> str:
    reader = PdfReader(file_path)

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text

def process_text_file(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    return text

def chunk_text(text, chunk_size=500, overlap=100):
    chunks = []

    start = 0

    while start < len(text):
        end = start + chunk_size

        chunks.append(text[start:end])

        start = end - overlap

    return chunks


def clean_text(text):
    # Replace multiple whitespace/newlines with a single space
    text = re.sub(r'\s+', ' ', text)

    # Remove leading/trailing spaces
    return text.strip()