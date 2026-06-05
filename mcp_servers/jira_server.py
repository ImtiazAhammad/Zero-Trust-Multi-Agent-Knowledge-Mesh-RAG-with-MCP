from fastmcp import FastMCP
from vector_db.hybrid_search import search_db

mcp = FastMCP("Jira Server")

@mcp.tool()
async def search_jira(query: str, department: str, clearance_level: int) -> str:
    """
    Searches mock Jira tickets, task descriptions, and bugs.
    Enforces document-level RBAC by filtering results with department and clearance level.
    """
    try:
        # Query the hybrid search engine, explicitly restricting source to 'jira'
        # and passing security contexts.
        results = await search_db(
            query=query,
            source="jira",
            department=department,
            clearance_level=clearance_level,
            limit=5
        )
        
        if not results:
            return "No Jira tickets found matching query or authorized for user."
            
        formatted_results = []
        for doc in results:
            formatted_results.append(
                f"Ticket ID: {doc.get('ticket_id')}\n"
                f"Status: {doc.get('status')}\n"
                f"Summary: {doc.get('title')}\n"
                f"Security: [Dept: {doc.get('department')}, Clearance: {doc.get('clearance_level')}]\n"
                f"Description: {doc.get('content')}\n"
                f"{'-'*40}"
            )
        return "\n".join(formatted_results)
    except Exception as e:
        return f"Error executing Jira search: {str(e)}"
