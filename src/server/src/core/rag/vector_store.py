import os

import chromadb
from typing import List, Any
import numpy as np
import uuid


class VectorStore:
    """Manages document embeddings in a ChromaDB vector store"""
    def __init__(self, collection_name: str = "js_documents", persist_directory: str = "vector_store"):
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.client = None
        self.collection = None
        self._initialize_store()
        
    def _initialize_store(self):
        """Initialize ChromaDB client and collection"""
        try:
            # Create persistent ChromaDB client:
            os.makedirs(self.persist_directory, exist_ok=True)
            self.client = chromadb.PersistentClient(path=self.persist_directory)
            
            # Get collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "py document embeddings for RAG"}
            )
            print(f"Vector store initialized. Collection: {self.collection_name}")
            print(f"Existing documents in collection: {self.collection.count()}")
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
        embeddings_list = []
        
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
            embeddings_list.append(embedding.tolist())
        
        # Add to collection    
        try:
            self.collection.add(
                ids=ids,
                embeddings=embeddings_list,
                metadatas=metadatas,
                documents=documents_text
            )
            
            print(f"Successfully added {len(documents)} documents to vector shape")
            print(f"Total documents in collection: {self.collection.count()}")
        except Exception as e:
            print(f"Error adding documents to vector store: {e}")
            raise