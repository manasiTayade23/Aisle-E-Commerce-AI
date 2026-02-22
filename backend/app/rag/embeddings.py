"""Embedding generation for product RAG."""

from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer
from app.config import EMBEDDING_MODEL


class EmbeddingGenerator:
    """Generate embeddings for products."""
    
    def __init__(self, model_name: str = None):
        """Initialize embedding model."""
        self.model_name = model_name or EMBEDDING_MODEL
        self.model = SentenceTransformer(self.model_name)
    
    def encode(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of texts."""
        return self.model.encode(texts, convert_to_numpy=True)
    
    def encode_single(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def get_dimension(self) -> int:
        """Get embedding dimension."""
        # Test with a dummy text
        test_embedding = self.encode_single("test")
        return len(test_embedding)
