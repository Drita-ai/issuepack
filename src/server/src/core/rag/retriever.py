from typing import List, Any, Dict, Optional

from vector_store import VectorStore
from embedding import EmbeddingManager

class RAGRetriever:
    """Handles query-based retrieval from the vector store"""
    def __init__(self, vector_store: VectorStore, embedding_manager: EmbeddingManager, rrf_constant = 60):
        self.vector_store = vector_store
        self.embedding_manager = embedding_manager
        self.rrf_constant = rrf_constant
        
    def retrieve(
        self, 
        query: str, 
        top_k: int = 100, 
        score_threshold: float = 0.0,
        filter_metadata: bool = False,
        metadata_query: Optional[Dict] = None
        ) -> List[Dict[str, Any]]:
        """Retrieve relevant documents for a query"""
        if metadata_query is None:
            metadata_query = {}
        
        print(f"Retrieving documents for query: '{query}'")
        print(f"Top K: {top_k}, Score threshold: {score_threshold}")
        
        where_clause = metadata_query if filter_metadata else None
        
        fetch_limit = max(30, top_k * 3) if not filter_metadata else 100
        
        # Generate query embeddings
        query_embedding = self.embedding_manager.generate_embeddings([query])[0]
        
        # Search in vector store
        try:
            dense_results = self.vector_store.dense_collection.query(
                query_embeddings=[query_embedding.tolist()],
                where=where_clause,
                n_results=fetch_limit
            )
            
            bm25_results = self.vector_store.bm25_collection.query(
                query_texts=[query],
                where=where_clause,
                n_results=fetch_limit
            )
            
            # Registries to aggregate positions across both streams
            doc_registry = {}  # { doc_id: { "content": ..., "metadata": ... } }
            rank_tracker = {}  # { doc_id: [dense_rank, bm25_rank] }
            
            # Parse Dense Stream Ranks
            if dense_results and dense_results.get('documents') and dense_results['documents'][0]:
                for rank_idx, (d_id, doc, meta) in enumerate(zip(dense_results['ids'][0], dense_results['documents'][0], dense_results['metadatas'][0])):
                    doc_registry[d_id] = {"content": doc, "metadata": meta}
                    rank_tracker[d_id] = [rank_idx + 1, None] 
            
            # Parse Native BM25 Stream Ranks
            if bm25_results and bm25_results.get('documents') and bm25_results['documents'][0]:
                for rank_idx, (b_id, doc, meta) in enumerate(zip(bm25_results['ids'][0], bm25_results['documents'][0], bm25_results['metadatas'][0])):
                    if b_id not in doc_registry:
                        doc_registry[b_id] = {"content": doc, "metadata": meta}
                    
                    if b_id not in rank_tracker:
                        rank_tracker[b_id] = [None, rank_idx + 1]
                    else:
                        rank_tracker[b_id][1] = rank_idx + 1  
                        
            retrieved_docs = []
            
            for doc_id, ranks in rank_tracker.items():
                dense_pos, bm25_pos = ranks
                
                dense_score = 1.0 / (self.rrf_constant + dense_pos) if dense_pos is not None else 0.0
                bm25_score = 1.0 / (self.rrf_constant + bm25_pos) if bm25_pos is not None else 0.0
                rrf_score = dense_score + bm25_score
                
                # FIXED: Keep if the calculated score satisfies or exceeds threshold metric
                if rrf_score >= score_threshold:
                    retrieved_docs.append({
                        'id': doc_id,
                        'content': doc_registry[doc_id]['content'],
                        'metadata': doc_registry[doc_id]['metadata'],
                        'similarity_score': round(rrf_score, 6),
                        'dense_rank': dense_pos,
                        'bm25_rank': bm25_pos
                    })
            
            # Sort final pool by highest combined RRF priority and truncate
            retrieved_docs = sorted(retrieved_docs, key=lambda x: x['similarity_score'], reverse=True)
            final_docs = retrieved_docs[:top_k]
            
            # Reassign clean sequential display ranks
            for idx, doc in enumerate(final_docs):
                doc['rank'] = idx + 1
                
            print(f"Retrieved {len(final_docs)} documents (after native hybrid RRF pipeline optimization)")
            return final_docs    
        except Exception as e:
            print(f"Error during retrieval: {e}")
            return []
        
# Lemme do it
rr = RAGRetriever(VectorStore(), EmbeddingManager())