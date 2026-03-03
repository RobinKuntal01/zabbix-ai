from embeddings import get_embedding
from vector_store import VectorStore
from pypdf import PdfReader

store = VectorStore()



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

pdf_text = extract_pdf_text("Concepts.pdf")
chunks = chunk_text(pdf_text)

for chunk in chunks:
    embedding = get_embedding(chunk)
    store.add(embedding, chunk)


# with open("sample.txt", "r", encoding="utf-8") as f:
#     text = f.read()

# documents = [chunk.strip() for chunk in text.split("\n\n") if chunk.strip()]

# for doc in documents:
#     embedding = get_embedding(doc)
#     store.add(embedding, doc)

store.save()