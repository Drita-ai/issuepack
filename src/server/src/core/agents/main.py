from langchain_core.tracers.langchain import LangChainTracer
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from agents.state import State
from agents.github_issue_fetcher import github_issue_fetcher_agent
from agents.rag_query_generator import rag_query_generator_agent
from agents.issue_solver import issue_solver_agent
from agents.solution_implementer import solution_implementer_agent
from agents.tools import fetch_github_issues, fetch_relevant_files, write_file

    

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
    workflow.add_node("rag_query_generator", rag_query_generator_agent)
    workflow.add_node("issue_solver", issue_solver_agent)
    workflow.add_node("solution_implementer", solution_implementer_agent)
    workflow.add_node("github_tools", ToolNode([fetch_github_issues]))
    workflow.add_node("implementation_tools", ToolNode([fetch_relevant_files, write_file]))

    # flow
    workflow.set_entry_point("github_issue_fetcher")
    workflow.add_conditional_edges("github_issue_fetcher", router, {
        "tools": "github_tools",
        "rag_query_generator": "rag_query_generator",
        "__end__": END
    })
    workflow.add_edge("github_tools", "github_issue_fetcher")
    workflow.add_edge("rag_query_generator", "issue_solver")
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
    
    final_workflow.invoke(
        {
        "messages": [HumanMessage(content="Solve issue #422")],
    },  
        # config={"callbacks": [tracer]} # uncomment for tracing
    )