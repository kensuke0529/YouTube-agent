from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from typing import List, Tuple

import faiss  # type: ignore
import numpy as np


@dataclass
class Document:
    id: str
    text: str
    metadata: dict


class FaissStore:
    def __init__(self, dim: int, index_path: str):
        self.dim = dim
        self.index_path = index_path
        self.index = faiss.IndexFlatIP(dim)
        self.ids: List[str] = []
        self.texts: List[str] = []
        self.metadatas: List[dict] = []

        if os.path.exists(index_path) and os.path.exists(index_path + ".ids"):
            self.index = faiss.read_index(index_path)
            with open(index_path + ".ids", "r", encoding="utf-8") as f:
                self.ids = [line.strip() for line in f]
            with open(index_path + ".txt", "r", encoding="utf-8") as f:
                self.texts = [line.rstrip("\n") for line in f]
            with open(index_path + ".meta", "r", encoding="utf-8") as f:
                import json

                self.metadatas = [json.loads(line) for line in f]

    def _persist(self):
        faiss.write_index(self.index, self.index_path)
        with open(self.index_path + ".ids", "w", encoding="utf-8") as f:
            f.write("\n".join(self.ids))
        with open(self.index_path + ".txt", "w", encoding="utf-8") as f:
            f.write("\n".join(self.texts))
        with open(self.index_path + ".meta", "w", encoding="utf-8") as f:
            import json

            for m in self.metadatas:
                f.write(json.dumps(m) + "\n")

    def add_texts(self, embeddings: List[List[float]], texts: List[str], metadatas: List[dict]):
        # Filter out duplicates based on text content
        new_embeddings = []
        new_texts = []
        new_metadatas = []
        
        for embedding, text, meta in zip(embeddings, texts, metadatas):
            if text not in self.texts:
                new_embeddings.append(embedding)
                new_texts.append(text)
                new_metadatas.append(meta)
        
        if not new_embeddings:
            return 0  # No new texts to add
        
        vecs = np.array(new_embeddings, dtype="float32")
        # Normalize for cosine similarity with inner product
        faiss.normalize_L2(vecs)
        self.index.add(vecs)
        for text, meta in zip(new_texts, new_metadatas):
            self.ids.append(str(uuid.uuid4()))
            self.texts.append(text)
            self.metadatas.append(meta)
        self._persist()
        return len(new_texts)

    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Tuple[str, float, dict]]:
        q = np.array([query_embedding], dtype="float32")
        faiss.normalize_L2(q)
        scores, idxs = self.index.search(q, top_k)
        results: List[Tuple[str, float, dict]] = []
        for score, idx in zip(scores[0], idxs[0]):
            if idx == -1:
                continue
            results.append((self.texts[idx], float(score), self.metadatas[idx]))
        return results


