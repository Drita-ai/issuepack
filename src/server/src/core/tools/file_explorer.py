from directory_tree import DisplayTree


EXCLUDED = {'.env', 'node_modules', 'package-lock.json', '.git', '.dockerignore'}

def get_directory_tree(ROOT_DIR) -> str | None:
    """
    Returns tree representation of provided Directory
    """
    return DisplayTree(ROOT_DIR, ignoreList=EXCLUDED)
