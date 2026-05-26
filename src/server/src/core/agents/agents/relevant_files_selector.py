from typing import Literal, List
from pydantic import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage

from prompts import RELEVANT_FILES_SELECTOR_PROMPT 
from llm import llm


class FileSelectionTarget(BaseModel):
    analysis: str = Field(description="Technical justification explaining the path to selected files.")
    target_files: List[str] = Field(description="List of relative files from the skeleton map.")

class VerificationResult(BaseModel):
    status: Literal["APPROVED", "REJECTED"] = Field(description="APPROVED if files are sufficient, REJECTED if missing files.")
    missing_files: List[str] = Field(default=[], description="List of missing files if REJECTED.")

RELEVANT_FILES_SELECTOR_PROMPT_TEMPLATE = ChatPromptTemplate.from_messages([
   ("system", RELEVANT_FILES_SELECTOR_PROMPT),
   ("user", "codebase_skeleton: {codebase_skeleton} \ntitle: {issue_title} \ndescription: {issue_description}")
])

def relevant_files_selector_agent(state):
    """Agent responsible to select relevant files from skeleton to solve issue"""
    title = state.get("issue_title", "Unknown Title")
    description = state.get("issue_description", "No description provided")
    codebase_skeleton = state.get("code_skeleton", "No skeleton provided")
    
    parser = JsonOutputParser(pydantic_object=FileSelectionTarget)
    
    chain = RELEVANT_FILES_SELECTOR_PROMPT_TEMPLATE | llm | parser
    
    response = chain.invoke({
        "issue_title": title, 
        "issue_description": description,
        "codebase_skeleton": codebase_skeleton
    })
    
    target_files = response.get("target_files", [])

    return {
        "messages": [AIMessage(content=f"Selected files: {target_files}")],
        "selected_files": target_files,
        "next_agent": "file_fetcher"
    }