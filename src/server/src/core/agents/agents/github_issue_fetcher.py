import json

from langchain_core.messages import ToolMessage, SystemMessage

from .state import State
from .llm import llm
from .tools import fetch_github_issues
from .prompts import FETCH_GITHUB_ISSUE_PROMPT

def github_issue_fetcher_agent(state: State):
    """Agent responsible to fetch github issues"""
    messages = state["messages"]

    if messages and isinstance(messages[-1], ToolMessage):
        try:
            data = json.loads(messages[-1].content)
            return {
                "issue_title": data.get("issue_title", ""),
                "issue_description": data.get("issue_description", ""),
                "next_agent": "relevant_files_selector" 
            }
        except Exception as e:
            print(e)
            # return {"next_agent": "rag_query_generator"}

    system_msg = SystemMessage(content=FETCH_GITHUB_ISSUE_PROMPT)
    fetcher_llm = llm.bind_tools([fetch_github_issues])
    response = fetcher_llm.invoke([system_msg] + messages)
    
    return {"messages": [response]}