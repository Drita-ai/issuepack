from pathlib import Path

from langchain_community.document_loaders import TextLoader


EXCLUDED = {"venv", ".git", "__pycache__", "node_modules"}

def process_all_files(root_dir: str, file_ext: str):
    """"Process all files"""
    all_documents = []
    rd = Path(root_dir)
    
    files = list(file for file in rd.rglob(f"**/*.{file_ext}") if not any(part in EXCLUDED for part in file.parts))
    
    print(f"Found {len(files)} py files to process")
    
    for file in files:
        print(f"\nProcessing: {file.name}") 
        try:
            loader = TextLoader(str(file))
            documents = loader.load()

            # Add information to metadata
            # For files like py which is a single file, we can omit looping here but
            # for files like pdf, docx, this is a necessary step
            for doc in documents:
                doc.metadata['source_file'] = file.name
                doc.metadata['file_type'] = file_ext
            
            all_documents.extend(documents)
            print(f"Loaded {len(documents)} pages")
        except Exception as e:
            print(f"Error : {e}")
            
    print(f"\n Total documents loaded: {len(all_documents)}")
    
    return all_documents