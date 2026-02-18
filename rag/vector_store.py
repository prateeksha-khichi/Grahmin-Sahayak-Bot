"""
Vector Store - FAISS-based vector database
Handles indexing and persistence (memory-safe & incremental)
"""

import os
import pickle
import numpy as np
import faiss
from typing import List, Dict, Tuple
from loguru import logger


class VectorStore:
    def __init__(self, index_path: str = "data/processed/faiss_index"):
        self.index_path = index_path
        self.index = None
        self.chunks: List[Dict] = []
        self.dimension = None

        os.makedirs(index_path, exist_ok=True)

    # ------------------------------------------------------------------
    # 🔹 CREATE INDEX (ONE-SHOT)
    # ------------------------------------------------------------------
    def create_index(self, embeddings: np.ndarray, chunks: List[Dict]):
        """
        Create FAISS index from embeddings (one-shot)
        """
        self.dimension = embeddings.shape[1]
        n_embeddings = embeddings.shape[0]

        logger.info(f"🔄 Creating FAISS index - {n_embeddings} vectors, dim={self.dimension}")

        self.index = faiss.IndexFlatL2(self.dimension)
        self.index.add(embeddings.astype("float32"))
        self.chunks = chunks

        logger.info(f"✅ Index created with {self.index.ntotal} vectors")

    # ------------------------------------------------------------------
    # 🔹 ADD VECTORS (INCREMENTAL / STREAMING)
    # ------------------------------------------------------------------
    def add(self, embeddings: np.ndarray, chunks: List[Dict]):
        """
        Incrementally add vectors + metadata (SAFE FOR LARGE DATA)
        """
        embeddings = embeddings.astype("float32")

        if self.index is None:
            # First batch → create index
            self.dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatL2(self.dimension)
            logger.info(f"🆕 Created FAISS index (dim={self.dimension})")

        self.index.add(embeddings)
        self.chunks.extend(chunks)

        logger.info(f"➕ Added {len(chunks)} vectors | Total = {self.index.ntotal}")

    # ------------------------------------------------------------------
    # 🔹 SEARCH
    # ------------------------------------------------------------------
    def search(self, query_embedding: np.ndarray, k: int = 3) -> List[Tuple[Dict, float]]:
        if self.index is None:
            logger.error("❌ Index not loaded!")
            return []

        query_vector = query_embedding.reshape(1, -1).astype("float32")
        distances, indices = self.index.search(query_vector, k)

        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.chunks):
                similarity = 1 / (1 + distance)
                results.append((self.chunks[idx], float(similarity)))

        logger.info(f"🔍 Retrieved {len(results)} chunks")
        return results

    # ------------------------------------------------------------------
    # 🔹 SAVE
    # ------------------------------------------------------------------
    def save(self):
        index_file = os.path.join(self.index_path, "faiss.index")
        chunks_file = os.path.join(self.index_path, "chunks.pkl")

        faiss.write_index(self.index, index_file)

        with open(chunks_file, "wb") as f:
            pickle.dump(self.chunks, f)

        logger.info(f"💾 Index saved to {self.index_path}")

    # ------------------------------------------------------------------
    # 🔹 LOAD
    # ------------------------------------------------------------------
    def load(self) -> bool:
        index_file = os.path.join(self.index_path, "faiss.index")
        chunks_file = os.path.join(self.index_path, "chunks.pkl")

        if not os.path.exists(index_file) or not os.path.exists(chunks_file):
            logger.warning("⚠️ Index files not found")
            return False

        try:
            self.index = faiss.read_index(index_file)

            with open(chunks_file, "rb") as f:
                self.chunks = pickle.load(f)

            self.dimension = self.index.d
            logger.info(f"✅ Loaded index with {self.index.ntotal} vectors")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to load index: {e}")
            return False
