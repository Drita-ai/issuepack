import os

from typing import Literal, List
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.messages import AIMessage

from prompts import RELEVANT_FILES_VERIFIER_PROMPT
from llm import llm

class VerificationResult(BaseModel):
    status: Literal["APPROVED", "REJECTED"] = Field(description="APPROVED if files are sufficient, REJECTED if missing files.")
    missing_files: List[str] = Field(default=[], description="List of missing files if REJECTED.")
    

RELEVANT_FILES_VERIFIER_PROMPT_TEMPLATE = ChatPromptTemplate.from_messages([
   ("system", RELEVANT_FILES_VERIFIER_PROMPT),
   ("user", "codebase_skeleton: {codebase_skeleton} \ndescription: {issue_description} \nfetched_files_contents: {fetched_contents}")
])

def relevant_files_verifier_agent(state):
    """
    Agent responsible to verify selected files from skeleton to solve issue
    """
    description = state.get("issue_description", "No description provided")
    codebase_skeleton = state.get("code_skeleton", "No skeleton provided")
    current_attempts = state.get("verification_attempts", 0) + 1    
    
    fetched_contents = state.get("messages")[-1].content if state.get("messages") else ""
    
    parser = JsonOutputParser(pydantic_object=VerificationResult)
    
    chain = RELEVANT_FILES_VERIFIER_PROMPT_TEMPLATE | llm | parser
        
    response = chain.invoke({
        "codebase_skeleton": codebase_skeleton,
        "issue_description": description,
        "fetched_contents": fetched_contents
    })
    
    status = response.get("status", "REJECTED")
    
    missing_files = response.get("missing_files", [])
    
    existing_bases = [os.path.basename(f) for f in state.get("selected_files", [])]
    valid_missing_files = []
    for file_path in missing_files:
        base_name = os.path.basename(file_path)
        
        # Check if the file exists in the skeleton and hasn't been fetched yet
        if base_name in codebase_skeleton and base_name not in existing_bases:
            # Save the clean base_name for stable retrieval
            valid_missing_files.append(base_name)
            
    if status == "REJECTED" and not valid_missing_files:
        status = "APPROVED"

    next_step = "issue_solver" if status == "APPROVED" else "fetch_missing_files"
    
    print(response)
    return {
        "messages": [AIMessage(content=f"Verification Status: {status}. Missing files found: {missing_files}")], 
        "verification_status": status,
        "missing_files_backlog": valid_missing_files,
        "verification_attempts": current_attempts,
        "next_agent": next_step
    }