"""Vector database abstraction for product embeddings."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from app.config import VECTOR_DB_TYPE, CHROMA_PERSIST_DIR, QDRANT_URL


class VectorStore(ABC):
    """Base class for vector stores."""
    
    @abstractmethod
    async def add_products(self, products: List[Dict[str, Any]], embeddings: List[List[float]]):
        """Add products with embeddings to the store."""
        pass
    
    @abstractmethod
    async def search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar products."""
        pass
    
    @abstractmethod
    async def delete_all(self):
        """Delete all products from the store."""
        pass


class ChromaVectorStore(VectorStore):
    """ChromaDB implementation."""
    
    def __init__(self, collection_name: str = "products", persist_directory: str = None):
        """Initialize ChromaDB."""
        self.persist_directory = persist_directory or CHROMA_PERSIST_DIR
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    
    async def add_products(self, products: List[Dict[str, Any]], embeddings: List[List[float]]):
        """Add products to ChromaDB."""
        ids = [str(p["id"]) for p in products]
        documents = [
            f"{p.get('title', '')} {p.get('description', '')} {p.get('category', '')}"
            for p in products
        ]
        metadatas = [
            {
                "title": p.get("title", ""),
                "price": p.get("price", 0),
                "category": p.get("category", ""),
                "rating": p.get("rating", {}).get("rate", 0) if isinstance(p.get("rating"), dict) else 0,
            }
            for p in products
        ]
        
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
    
    async def search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Search ChromaDB for similar products."""
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["metadatas", "documents", "distances"]
        )
        
        products = []
        if results["ids"] and len(results["ids"][0]) > 0:
            for i, product_id in enumerate(results["ids"][0]):
                products.append({
                    "id": int(product_id),
                    "title": results["metadatas"][0][i].get("title", ""),
                    "price": results["metadatas"][0][i].get("price", 0),
                    "category": results["metadatas"][0][i].get("category", ""),
                    "rating": {"rate": results["metadatas"][0][i].get("rating", 0)},
                    "score": 1 - results["distances"][0][i],  # Convert distance to similarity
                })
        
        return products
    
    async def delete_all(self):
        """Delete all products from ChromaDB."""
        # Get all IDs and delete
        all_results = self.collection.get()
        if all_results["ids"]:
            self.collection.delete(ids=all_results["ids"])


def create_vector_store(store_type: str = None) -> VectorStore:
    """Create vector store instance."""
    store_type = store_type or VECTOR_DB_TYPE
    
    if store_type == "chroma":
        return ChromaVectorStore()
    elif store_type == "qdrant":
        # TODO: Implement Qdrant support
        raise NotImplementedError("Qdrant support coming soon")
    else:
        raise ValueError(f"Unsupported vector store type: {store_type}")
