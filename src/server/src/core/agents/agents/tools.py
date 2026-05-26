from pathlib import Path
import json

from langchain_core.tools import tool
from langchain_core.messages import AIMessage

from rag.retriever import rr


APIFeaturesCode = """
        class APIFeatures {
  constructor(query, queryString) {
    this.query = query;
    this.queryString = queryString;
  }

  filter() {
    // Filtering
    const queryObj = { ...this.queryString };
    const excludedFields = ["page", "sort", "limit", "fields"];

    excludedFields.forEach((el) => delete queryObj[el]);

    // Advanced Filtering
    let queryStr = JSON.stringify(queryObj);
    queryStr = queryStr.replace(/\b(gte|gt|lte|lt)\b/g, (match) => `$${match}`);

    this.query = this.query.find(JSON.parse(queryStr));

    return this;
  }

  sort() {
    // Sorting
    if (this.queryString.sort) {
      // sort('price ratingsAverage') ~ /tours?sort=price,ratingsAverage
      const sortBy = this.queryString.sort.split(",").join(" ");
      this.query = this.query.sort(sortBy);
    } else {
      // If user doesn't specify any sorting criteria, then default will be this
      this.query = this.query.sort("-createdAt");
    }

    return this;
  }

  limitFields() {
    // Field Limiting
    if (this.queryString.fields) {
      const fields = this.queryString.fields.split(",").join(" ");
      this.query = this.query.select(fields);
    } else {
      this.query = this.query.select("-__v");
    }

    return this;
  }

  paginate() {
    // Pagination
    const page = this.queryString.page * 1 || 1;
    const limit = this.queryString.limit * 1 || 10;
    const skip = (page - 1) * limit;

    this.query = this.query.skip(skip).limit(limit);

    return this;
  }
}

module.exports = APIFeatures;
"""

@tool
def fetch_github_issues():
    """
    Fetches github issues 
    
    Returns:
        A dictionary containing 'issue_title' and 'issue_description' keys.
    """
    
    return {
      "issue_title": "Revamp APIFeatures",
      "issue_description": "Improve the structure and add caching and several different advance functionalities inside APIFeatures"
      }
        
def fetch_relevant_files(state):
    """
    Fetches relevant files necessary to solve the issue
    
    Args: 
      query: Query to retrieve files from the vector database
    
    Returns:
        List of the relevant files.
    """
    selected_files = state.get("selected_files", [])
    relevant_contents = []
    
    print(f"Active file-fetching queue: {selected_files}")
    
    for file in selected_files:
        res = rr.retrieve(
            query=str(file), 
            filter_metadata=True, 
            metadata_query={"source_file": file}
            )
        
        res = _order_code_chunks(res)
        res = _reconstruct_chunks(res)
        
        relevant_contents.append(f"--- FILE: {file} ---\n{res}")
    
    combined_contents = "\n\n".join(relevant_contents)
    return {
        "messages": [AIMessage(content=combined_contents)],
        "next_agent": "relevant_files_verifier"
    }

@tool
def write_file(path: str, content: str) -> str:
    """
    Writes or overwrites a file at the specified path with the provided content.
    If the parent directories do not exist, they will be created automatically.
    
    Args:
        path: The relative or absolute path to the file (e.g., 'src/utils/example.js').
        content: The full string content to be written into the file.
    
    Returns:
        A success message or an error message if the write fails.
    """
    try:
        file_path = Path(path)
        
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        return f"Successfully wrote to {path}"
        
    except Exception as e:
        return f"Error writing to {path}: {str(e)}"
      

# Util functions for fetch_relevant_files 
def _order_code_chunks(results):
    processed = []

    for x in results:
        try:
            data = json.loads(x['content'])
        except:
            data = {}

        type_ = data.get("type")
        start = data.get("byte_range", {}).get("start")

        processed.append((type_, start, x))

    processed.sort(
        key=lambda item: (
            item[0] != "import",                 
            item[1] is None and item[0] != "import",
            item[1] if item[1] is not None else float("inf")
        )
    )

    return [item[2] for item in processed]

def _reconstruct_class_chunks(filtered_results):
    reconstructed = []

    class_code = None
    methods = []

    for chunk in filtered_results:
        data = json.loads(chunk['content'])
        code = data.get("code", "").strip()

        if code.startswith("class"):
            if code.endswith("}"):
                code = code[:-1].rstrip()
            class_code = code
        else:
            methods.append(code)

    if class_code:
        reconstructed.append(class_code)

    reconstructed.extend(methods)

    reconstructed.append("}")

    final_code = "\n".join(reconstructed)
    return final_code

def _reconstruct_chunks(filtered_results):
    reconstructed = []
    
    for chunk in filtered_results:
        data = json.loads(chunk['content'])
        code = data.get("code", "").strip()
        reconstructed.append(code)
    
    return "\n".join(reconstructed)