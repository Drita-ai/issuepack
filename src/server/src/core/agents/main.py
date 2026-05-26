import sys 

from langchain_core.tracers.langchain import LangChainTracer
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from agents.state import State
from agents.github_issue_fetcher import github_issue_fetcher_agent
from agents.rag_query_generator import rag_query_generator_agent
from agents.issue_solver import issue_solver_agent
from agents.solution_implementer import solution_implementer_agent
from agents.relevant_files_selector import relevant_files_selector_agent
from agents.relevant_files_verifier import relevant_files_verifier_agent
from agents.tools import fetch_github_issues, fetch_relevant_files, write_file, append_missing_files_node

    

def router(state: State):
    last_message = state["messages"][-1]

    # If the LLM wants to use a tool, go to tools node
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    
    # If the agent set a next_agent in the state, go there
    if state.get("next_agent"):
        return state["next_agent"]

    return END

if __name__ == "__main__":
    # build graph
    workflow = StateGraph(State)

    # nodes
    workflow.add_node("github_issue_fetcher", github_issue_fetcher_agent)
    # workflow.add_node("rag_query_generator", rag_query_generator_agent)
    workflow.add_node("relevant_files_selector", relevant_files_selector_agent)
    workflow.add_node("relevant_files_verifier", relevant_files_verifier_agent)
    workflow.add_node("issue_solver", issue_solver_agent)
    workflow.add_node("solution_implementer", solution_implementer_agent)
    workflow.add_node("fetch_missing_files", append_missing_files_node)
    workflow.add_node("file_fetcher", fetch_relevant_files)
    workflow.add_node("github_tools", ToolNode([fetch_github_issues]))
    workflow.add_node("implementation_tools", ToolNode([fetch_relevant_files, write_file]))

    # flow
    workflow.set_entry_point("github_issue_fetcher")
    workflow.add_conditional_edges("github_issue_fetcher", router, {
        "tools": "github_tools",
        "relevant_files_selector": "relevant_files_selector",
    })
    workflow.add_edge("github_tools", "github_issue_fetcher")
    workflow.add_edge("relevant_files_selector", "file_fetcher")
    workflow.add_edge("file_fetcher", "relevant_files_verifier")
    workflow.add_conditional_edges(
    "relevant_files_verifier",
    router,
    {
        "fetch_missing_files": "fetch_missing_files",
        "issue_solver": "issue_solver",
    })
    workflow.add_edge("fetch_missing_files", "file_fetcher")
    workflow.add_edge("issue_solver", "solution_implementer")
    workflow.add_conditional_edges("solution_implementer", router, {
        "tools": "implementation_tools",
        "solution_implementer": "solution_implementer",
        "__end__": END
    })
    workflow.add_edge("implementation_tools", "solution_implementer")
    workflow.add_edge("solution_implementer", END)

    final_workflow = workflow.compile()
    
    # Create an explicit tracer pointing to your project
    tracer = LangChainTracer(project_name="issuepack")
    
    # Get skeletonized contents
    skeletonized_content = ''
    with open("skeleton.txt", "r", encoding="utf-8") as f:
        for line in f:
            skeletonized_content = skeletonized_content + line
    
    final_workflow.invoke(
        {
        "messages": [HumanMessage(content="Solve issue #422")],
        # To be accepted through CLI for now
        "org_name": sys.argv[1],
        "repo_name": sys.argv[2],
        "issue_number": sys.argv[3],
        "code_skeleton": skeletonized_content
    },  
        # config={"callbacks": [tracer]} # uncomment for tracing
    )