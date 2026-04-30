from pathlib import Path

from directory_tree import DisplayTree


EXCLUDED = {'.env', 'node_modules', 'package-lock.json', '.git', '.dockerignore'}

def get_directory_tree(ROOT_DIR) -> str | None:
    """
    Returns tree representation of provided Directory
    """
    return DisplayTree(ROOT_DIR, ignoreList=EXCLUDED)

def _get_all_files(ROOT_DIR):
    """
    Returns  all files of from the provided directory
    """
    _root_dir = Path(ROOT_DIR)
    
    _excluded_suffixes = tuple(EXCLUDED)
    
    for item in _root_dir.iterdir():
        if item.name in EXCLUDED or item.name.startswith('.'):
            continue
        
        if item.name.endswith(_excluded_suffixes):
            continue
        
        if item.is_file():
            yield item
            
        if item.is_dir():
            yield from _get_all_files(item)