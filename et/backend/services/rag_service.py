from __future__ import annotations

from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer


class SimpleRAGService:
    def __init__(self, storage_dir: str) -> None:
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.documents: list[str] = []
        self.metadata: list[str] = []
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.matrix = None

    def add_documents(self, docs: list[str], metadata: list[str]) -> None:
        self.documents.extend(docs)
        self.metadata.extend(metadata)
        if self.documents:
            self.matrix = self.vectorizer.fit_transform(self.documents)

    def retrieve(self, query: str, top_k: int = 3) -> list[str]:
        if not self.documents:
            return []
        if self.matrix is None:
            self.matrix = self.vectorizer.fit_transform(self.documents)
        query_vector = self.vectorizer.transform([query])
        scores = (self.matrix @ query_vector.T).toarray().ravel()
        ranked_indices = np.argsort(scores)[::-1][:top_k]
        results: list[str] = []
        for index in ranked_indices:
            if scores[index] <= 0:
                continue
            results.append(f"{self.metadata[index]}: {self.documents[index]}")
        return results
