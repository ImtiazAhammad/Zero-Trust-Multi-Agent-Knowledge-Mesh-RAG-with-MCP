import os
import sys
import asyncpg
import uuid
from typing import List, Dict
from fastmcp import FastMCP
from dotenv import load_dotenv

# Add project root to path
sys.path.append("/home/imtiaz/Projects/zero-trust-rag")

from vector_db.hybrid_search import search_db
from vector_db.reranker import rerank

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5433/rag_db")

# Initialize FastMCP Server
mcp = FastMCP("confluence-mcp")

@mcp.tool()
async def search_confluence(query: str, department: str, clearance_level: int) -> List[Dict]:
    """
    Searches mock Confluence wiki pages and documentation.
    Applies RBAC filters (department, clearance_level), runs parallel hybrid search, 
    reranks via ms-marco-MiniLM cross-encoder, and returns the top-5 documents.
    """
    try:
        # 1. Fetch top-20 from parallel hybrid search
        hybrid_results = await search_db(
            query=query,
            department=department,
            clearance_level=clearance_level,
            source="confluence",
            limit=20
        )
        # 2. Rerank using the cross-encoder and return top-5
        top_five = rerank(query, hybrid_results)
        return top_five
    except Exception as e:
        print(f"Error in search_confluence: {e}")
        return [{"error": f"Search failed: {str(e)}"}]

@mcp.tool()
async def get_page(page_id: str) -> Dict:
    """
    Fetches a specific Confluence document from PostgreSQL by its UUID.
    """
    try:
        # Validate UUID
        try:
            page_uuid = uuid.UUID(page_id)
        except ValueError:
            return {"error": f"Invalid UUID format: {page_id}"}

        conn = await asyncpg.connect(DATABASE_URL)
        try:
            row = await conn.fetchrow(
                "SELECT id, title, content, source, department, clearance_level FROM documents WHERE id = $1 AND source = 'confluence'",
                page_uuid
            )
            if not row:
                return {"error": f"Confluence page not found: {page_id}"}
            
            return {
                "id": str(row["id"]),
                "title": row["title"] or "",
                "content": row["content"],
                "source": row["source"],
                "department": row["department"],
                "clearance_level": row["clearance_level"]
            }
        finally:
            await conn.close()
    except Exception as e:
        return {"error": f"Failed to fetch page: {str(e)}"}

@mcp.resource("confluence://pages/{department}")
async def get_pages(department: str) -> str:
    """
    Returns a text list of all document titles and IDs for the given department in Confluence.
    """
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        try:
            rows = await conn.fetch(
                "SELECT id, title FROM documents WHERE department = $1 AND source = 'confluence' ORDER BY title ASC",
                department
            )
            if not rows:
                return f"No Confluence pages found for department: {department}"
            
            lines = [f"- {row['title']} (ID: {row['id']})" for row in rows]
            return "\n".join(lines)
        finally:
            await conn.close()
    except Exception as e:
        return f"Error retrieving resource confluence://pages/{department}: {str(e)}"

if __name__ == "__main__":
    # Run the server on localhost:9001 using SSE transport
    print("Starting Confluence MCP server on port 9001 using SSE transport...")
    mcp.run(transport="sse", host="0.0.0.0", port=9001)
