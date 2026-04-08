from langchain_core.prompts import ChatPromptTemplate

from .llm import llm
from .prompts import RAG_QUERY_GENERATOR_PROMPT

RAG_QUERY_GENERATOR_PROMPT_TEMPLATE = ChatPromptTemplate.from_messages([
   ("system", RAG_QUERY_GENERATOR_PROMPT),
   ("user", "title: {issue_title} \ndescription: {issue_description}")
])

def rag_query_generator_agent(state):
    """Agent responsible to generate query to fetch relevant files using RAG"""
    title = state.get("issue_title", "Unknown Title")
    description = state.get("issue_description", "No description provided")

    formatted_prompt = RAG_QUERY_GENERATOR_PROMPT_TEMPLATE.format_messages(
        issue_title=title, 
        issue_description=description
    )
    
    response = llm.invoke(formatted_prompt)   

    return {
        "messages": [response], 
        "rag_query": response.content,
        "next_agent": "issue_solver"
    }