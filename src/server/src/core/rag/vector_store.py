import os

import chromadb
from chromadb.utils.embedding_functions import ChromaBm25EmbeddingFunction
from typing import List, Any
import numpy as np
import uuid


class VectorStore:
    """Manages document embeddings in a ChromaDB vector store"""
    def __init__(self, collection_name: str = "js_documents", persist_directory: str = "vector_store"):
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.client = None
        self.dense_collection = None
        self.bm25_collection = None
        self._initialize_store()
        
    def _initialize_store(self):
        """Initialize ChromaDB client and collection"""
        try:
            # Create persistent ChromaDB client:
            os.makedirs(self.persist_directory, exist_ok=True)
            self.client = chromadb.PersistentClient(path=self.persist_directory)
            
            # Get collection
            self.dense_collection = self.client.get_or_create_collection(
                name=f"{self.collection_name}_dense",
                metadata={"description": "Dense text embedding for code snippets"}
            )
            
            self.bm25_collection = self.client.get_or_create_collection(
                name=f"{self.collection_name}_bm25",
                metadata={"description": "Chroma BM25 embedding for code snippets"}
            )
            
            print(f"Dense Docs Count: {self.dense_collection.count()}")
            print(f"BM25 Docs Count: {self.bm25_collection.count()}")
        except Exception as e:
            print(f"Error initializing vector store: {e}")
            raise
    
    def add_documents(self, documents: List[Any], embeddings: np.ndarray):
        """Add documents and their embeddings to the vector store"""
        if len(documents) != len(embeddings):
            raise ValueError("Number of documents must match number of embeddings")
        
        print(f"Adding {len(documents)} documents to vector store...")
        
        # Prepare data for ChromaDB
        ids = []
        metadatas = []
        documents_text = []
        dense_embeddings_list = []
        
        for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
            # Generate unique id for specific record
            doc_id = f"doc_{uuid.uuid4().hex[:8]}_{i}"
            ids.append(doc_id)
            
            # Prepare metadata
            metadata = dict(doc.metadata)
            metadata['doc_index'] = i
            metadata['content_length'] = len(doc.page_content)
            metadatas.append(metadata)
            
            # Get document content
            documents_text.append(doc.page_content)
            
            # Get document embedding
            dense_embeddings_list.append([float(x) for x in embedding])
        
        # Add to collection    
        try:
            self.dense_collection.add(
                ids=ids,
                embeddings=dense_embeddings_list,
                metadatas=metadatas,
                documents=documents_text
            )
                        
            self.bm25_collection.add(
                ids=ids,
                metadatas=metadatas,
                documents=documents_text
            )
            
            print(f"Successfully added {len(documents)} documents to vector shape")
            print(f"Dense Collection Count: {self.dense_collection.count()}")
            print(f"BM25 Collection Count: {self.bm25_collection.count()}")
        except Exception as e:
            print(f"Error adding documents to vector store: {e}")
            raise