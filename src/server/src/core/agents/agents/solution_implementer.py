import os

from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import ToolNode
from langchain_core.messages import ToolMessage
from langgraph.graph import END

from .llm import llm
from .tools import write_file
from .prompts import SOLUTION_IMPLEMENTER_PROMPT


SOLUTION_IMPLEMENTER_PROMPT_TEMPLATE = ChatPromptTemplate.from_messages([
   ("system", SOLUTION_IMPLEMENTER_PROMPT),
   ("user", "path: {path} \ncontent: {content}")
])

def solution_implementer_agent(state):
    """Agent responsible to implement the solution"""
    messages = state["messages"]

    if messages and isinstance(messages[-1], ToolMessage):
        try:
            print("successfully implemented")
            return {
                "next_agent": END 
            }
        except Exception as e:
            print(e)
            # return {"next_agent": END}
    relevant_code = state.get("relevant_code")
    
    fetcher_llm = llm.bind_tools([write_file])
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "APIFeatures.js")
    
    formatted_prompt = SOLUTION_IMPLEMENTER_PROMPT_TEMPLATE.format_messages(
        content=relevant_code,
        path=path
    )
    
    response = fetcher_llm.invoke(formatted_prompt)
    
    return {
        "messages": [response],
    }
