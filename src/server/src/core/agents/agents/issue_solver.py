from langchain_core.prompts import ChatPromptTemplate

from .llm import llm
from .tools import APIFeaturesCode
from .prompts import ISSUE_SOLVER_PROMPT

ISSUE_SOLVER_PROMPT_TEMPLATE = ChatPromptTemplate.from_messages([
   ("system", ISSUE_SOLVER_PROMPT),
   ("user", "title: {issue_title} \ndescription: {issue_description} \nrelevant_code: {relevant_code}")
])

def issue_solver_agent(state):
    """Agent responsible to solve the issue"""
    title = state.get("issue_title", "Unknown Title")
    description = state.get("issue_description", "No description provided")
    
    formatted_prompt = ISSUE_SOLVER_PROMPT_TEMPLATE.format_messages(
        issue_title=title, 
        issue_description=description,
        relevant_code=APIFeaturesCode
    )
    
    response = llm.invoke(formatted_prompt)
    
    return {
        "messages": [response],
        "relevant_code": response.content,
        "next_agent": "solution_implementer"
    }
    