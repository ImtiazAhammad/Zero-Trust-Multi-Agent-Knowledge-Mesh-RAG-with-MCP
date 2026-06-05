from fastmcp import FastMCP
from vector_db.hybrid_search import search_db

mcp = FastMCP("Confluence Server")

@mcp.tool()
def search_confluence(query: str, department: str, clearance_level: int) -> str:
    """
    Searches mock Confluence wiki pages and documentation.
    Enforces document-level RBAC by filtering results with department and clearance level.
    """
    try:
        # Query the hybrid search engine, explicitly restricting source to 'confluence'
        # and passing security contexts.
        results = search_db(
            query=query,
            source="confluence",
            department=department,
            clearance_level=clearance_level,
            limit=5
        )
        
        if not results:
            return "No Confluence documents found matching query or authorized for user."
            
        formatted_results = []
        for doc in results:
            formatted_results.append(
                f"Title: {doc.get('title')}\n"
                f"URL: {doc.get('url')}\n"
                f"Security: [Dept: {doc.get('department')}, Clearance: {doc.get('clearance_level')}]\n"
                f"Content: {doc.get('content')}\n"
                f"{'-'*40}"
            )
        return "\n".join(formatted_results)
    except Exception as e:
        return f"Error executing Confluence search: {str(e)}"
