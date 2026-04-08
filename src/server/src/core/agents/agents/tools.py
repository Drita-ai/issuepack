from pathlib import Path

from langchain_core.tools import tool


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
        
def fetch_relevant_files():
    """
    Fetches relevant files necessary to solve the issue
    
    Returns:
        List of the relevant files.
    """

    return [APIFeaturesCode]

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