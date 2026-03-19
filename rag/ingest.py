import os

from rag.embeddings import get_embedding
from rag.vector_store import VectorStore
from pypdf import PdfReader
RAG_FOLDER = "rag"


store = VectorStore()

async def handle_file(file):

    contents = await file.read()

    os.makedirs(RAG_FOLDER, exist_ok=True)
    save_path = os.path.join(RAG_FOLDER, file.filename)
    with open(save_path, "wb") as f:
        f.write(contents)
    
    file_path = os.path.join(RAG_FOLDER, file.filename)
    pdf_text = extract_pdf_text(file_path)  
    chunks = chunk_text(pdf_text)

    add = 0
    for chunk in chunks:
        print(f"Processing chunk: {chunk[:50]}...")  # Print the first 50 characters of the chunk
        embedding = get_embedding(chunk)
        store.add(embedding, chunk)
        add = add+1

    store.save()

    return {"message": f"File '{file.filename}' processed and added to vector store with {add} chunks."}


def extract_pdf_text(file_path: str) -> str:
    reader = PdfReader(file_path)
    text = ""

    for page in reader.pages:
        text += page.extract_text() + "\n"

    return text

def chunk_text(text, chunk_size=500, overlap=100):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap

    return chunks

# pdf_text = extract_pdf_text("Concepts.pdf")
# chunks = chunk_text(pdf_text)

# for chunk in chunks:
#     embedding = get_embedding(chunk)
#     store.add(embedding, chunk)


# with open("sample.txt", "r", encoding="utf-8") as f:
#     text = f.read()

# documents = [chunk.strip() for chunk in text.split("\n\n") if chunk.strip()]

# for doc in documents:
#     embedding = get_embedding(doc)
#     store.add(embedding, doc)

