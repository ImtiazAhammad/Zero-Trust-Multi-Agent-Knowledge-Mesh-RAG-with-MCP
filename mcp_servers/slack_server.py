from fastmcp import FastMCP
from vector_db.hybrid_search import search_db

mcp = FastMCP("Slack Server")

@mcp.tool()
async def search_slack(query: str, department: str, clearance_level: int) -> str:
    """
    Searches mock Slack channel logs, team chat discussions, and messages.
    Enforces document-level RBAC by filtering results with department and clearance level.
    """
    try:
        # Query the hybrid search engine, explicitly restricting source to 'slack'
        # and passing security contexts.
        results = await search_db(
            query=query,
            source="slack",
            department=department,
            clearance_level=clearance_level,
            limit=5
        )
        
        if not results:
            return "No Slack logs found matching query or authorized for user."
            
        formatted_results = []
        for doc in results:
            formatted_results.append(
                f"Channel/DM: {doc.get('channel')}\n"
                f"Sender: {doc.get('sender')}\n"
                f"Security: [Dept: {doc.get('department')}, Clearance: {doc.get('clearance_level')}]\n"
                f"Message: {doc.get('content')}\n"
                f"{'-'*40}"
            )
        return "\n".join(formatted_results)
    except Exception as e:
        return f"Error executing Slack search: {str(e)}"
