import faiss
import numpy as np
import pickle

DIMENSION = 768

class VectorStore:
    def __init__(self):
        self.index = faiss.IndexFlatL2(DIMENSION)
        self.text_chunks = []

    def add(self, embedding, text):
        vector = np.array([embedding]).astype("float32")
        self.index.add(vector)
        self.text_chunks.append(text)

    def search(self, embedding, top_k=5):
        vector = np.array([embedding]).astype("float32")
        distances, indices = self.index.search(vector, top_k)

        results = []
        for idx in indices[0]:
            if idx < len(self.text_chunks):
                results.append(self.text_chunks[idx])

        return results

    def save(self, path="vector_store.pkl"):
        with open(path, "wb") as f:
            pickle.dump((self.index, self.text_chunks), f)

    def load(self, path="rag/vector_store.pkl"):
        with open(path, "rb") as f:
            self.index, self.text_chunks = pickle.load(f)