from typing import Annotated
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
    code_skeleton: str