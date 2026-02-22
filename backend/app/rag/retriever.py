"""RAG retriever for semantic product search."""

from typing import List, Dict, Any
from app.rag.embeddings import EmbeddingGenerator
from app.rag.vector_store import create_vector_store, VectorStore
from app import fake_store


class RAGRetriever:
    """RAG-based product retriever."""
    
    def __init__(self):
        """Initialize RAG retriever."""
        self.embedding_generator = EmbeddingGenerator()
        self.vector_store = create_vector_store()
        self._initialized = False
    
    async def initialize(self):
        """Initialize vector store with products from FakeStoreAPI."""
        if self._initialized:
            return
        
        # Fetch all products
        products = await fake_store.get_all_products()
        
        if not products:
            return
        
        # Generate embeddings
        texts = [
            f"{p.get('title', '')} {p.get('description', '')} {p.get('category', '')}"
            for p in products
        ]
        embeddings = self.embedding_generator.encode(texts)
        
        # Add to vector store
        await self.vector_store.add_products(products, embeddings.tolist())
        self._initialized = True
    
    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for products using semantic similarity."""
        # Ensure initialized
        await self.initialize()
        
        # Generate query embedding
        query_embedding = self.embedding_generator.encode_single(query)
        
        # Search vector store
        results = await self.vector_store.search(query_embedding, top_k=top_k)
        
        # Fetch full product details
        enriched_results = []
        for result in results:
            try:
                product = await fake_store.get_product(result["id"])
                product["similarity_score"] = result.get("score", 0)
                enriched_results.append(product)
            except Exception:
                continue
        
        return enriched_results
    
    async def refresh(self):
        """Refresh the vector store with latest products."""
        await self.vector_store.delete_all()
        self._initialized = False
        await self.initialize()
