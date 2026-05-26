from typing import Annotated, List
from typing_extensions import Optional
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages


class State(MessagesState):
    messages: Annotated[list, add_messages]
    next_agent: Optional[str] = None
    org_name: str
    repo_name: str
    issue_number: int
    issue_title: Optional[str] = None
    issue_description: Optional[str] = None
    rag_query: Optional[str] = None
    relevant_code: Optional[str] = None
    selected_files: Optional[List[str]] = None
    missing_files_backlog: List[str] = None
    fetched_file_contents: Optional[dict] = None
    verification_status: Optional[str] = None
    verification_attempts: int
    code_skeleton: str