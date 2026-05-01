import os
from dotenv import load_dotenv

from data_loader import process_all_files
from chunking import split_and_chunk_entities
from embedding import EmbeddingManager
from vector_store import VectorStore
from tools.skeletonizer import skeletonize

# Loading ENVs
load_dotenv()


if __name__ == "__main__":
    # Fetching the path of file to pass into the TextLoader
    root_dir = os.environ['ROOT_DIR']
    
    # Skeletonize
    skeletonize(root_dir)
    
    # Fetching all files from the target directory
    all_files = process_all_files(root_dir, "js")
    
    # Splitting and Chunking
    chunks = split_and_chunk_entities(all_files)
    
    # Initializing EmbeddingManager and VectorStore
    # TODO: Remove vector store if already exists ( for pre-existing files )
    embedding_manager = EmbeddingManager()
    vector_store = VectorStore()
    
    # Extracting all the page contents for embedding
    doc_contents = [doc.page_content for doc_chunk_list in chunks for doc in doc_chunk_list ]

    # Generate & Store the embedding
    embeddings = embedding_manager.generate_embeddings(doc_contents)
    vector_store.add_documents([doc for doc_chunk_list in chunks for doc in doc_chunk_list], embeddings)

    
    