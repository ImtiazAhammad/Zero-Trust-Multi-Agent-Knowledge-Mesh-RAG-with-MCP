import os
import sys
import json
import asyncio
from typing import List, Dict
from openai import AsyncOpenAI
from mcp import ClientSession
from mcp.client.sse import sse_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "http://localhost:8001/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "mock-key")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-7B-Instruct-AWQ")

# Port mappings for MCP servers
TOOL_SERVERS = {
    "search_confluence": "http://localhost:9001/sse",
    "search_jira": "http://localhost:9002/sse",
    "search_slack": "http://localhost:9003/sse"
}

# Initialize Async OpenAI Client for vLLM
openai_client = AsyncOpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_API_BASE
)

async def call_mcp_tool(tool_name: str, query: str, rbac_context: dict) -> str:
    """
    Connects to the appropriate MCP server via SSE and executes the tool call.
    """
    if tool_name not in TOOL_SERVERS:
        return f"Error: Tool '{tool_name}' has no registered SSE endpoint."
        
    url = TOOL_SERVERS[tool_name]
    
    # Construct arguments from query and rbac_context
    arguments = {"query": query}
    if "department" in rbac_context:
        arguments["department"] = rbac_context["department"]
        
    if tool_name == "search_confluence":
        if "clearance_level" in rbac_context:
            arguments["clearance_level"] = int(rbac_context["clearance_level"])
    elif tool_name == "search_slack":
        arguments["time_window_hours"] = int(rbac_context.get("time_window_hours", 72))
        
    try:
        # Establish SSE connection and invoke the tool
        async with sse_client(url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                print(f"[Orchestrator] Calling {tool_name} with arguments: {arguments}")
                result = await session.call_tool(tool_name, arguments=arguments)
                
                # Merge content blocks text
                text_content = ""
                for block in result.content:
                    if hasattr(block, "text"):
                        text_content += block.text + "\n"
                        
                return f"=== Source: {tool_name} ===\n{text_content}"
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[Orchestrator] Error calling {tool_name}: {e}")
        return f"=== Source: {tool_name} (Error) ===\nFailed to fetch results: {str(e)}"

async def route_query(query: str, rbac_context: dict) -> str:
    """
    Orchestrates a query:
    1. Asks vLLM to select tools based on user query.
    2. Runs selected tool calls in parallel over SSE.
    3. Combines contexts and prompts vLLM to formulate a secure RAG answer.
    """
    # 1. Ask vLLM to select tools using a JSON formatting constraint
    tool_select_prompt = (
        f"Given this query: '{query}', which tools should be called? "
        f"Available tools: {', '.join(TOOL_SERVERS.keys())}. "
        f"Respond with JSON: {{'tools': ['tool_name'], 'reasoning': '...'}}"
    )
    try:
        completion = await openai_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "You are an AI router that selects tools to answer a user's question. "
                        "Here are the descriptions of the available tools:\n"
                        "- search_confluence: Searches wiki pages, policies, guidelines, technical documents, and checklists.\n"
                        "- search_jira: Searches software tickets, bug reports, tasks, and issue descriptions.\n"
                        "- search_slack: Searches chat logs, informal messages, and conversations in team channels.\n"
                        "Respond ONLY with a JSON object containing the 'tools' and 'reasoning' fields."
                    )
                },
                {"role": "user", "content": tool_select_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        
        raw_response = completion.choices[0].message.content
        print(f"[Orchestrator] Tool selection response: {raw_response}")
        selection = json.loads(raw_response)
        selected_tools = selection.get("tools", [])
    except Exception as e:
        print(f"[Orchestrator] Failed to parse tool selection: {e}")
        selected_tools = []
        
    # Filter selected tools to only valid ones
    selected_tools = [t for t in selected_tools if t in TOOL_SERVERS]
    
    if not selected_tools:
        print("[Orchestrator] No tools selected. Proceeding directly to LLM.")
        context_str = "No search context retrieved."
    else:
        print(f"[Orchestrator] Selected tools: {selected_tools}")
        
        # 2. Invoke tools concurrently
        tasks = [call_mcp_tool(t, query, rbac_context) for t in selected_tools]
        results = await asyncio.gather(*tasks)
        
        # 3. Merge all returned chunks
        context_str = "\n\n".join(results)
        
    # 4. Call vLLM again with the RAG prompt
    rag_prompt = f"Context:\n{context_str}\n\nAnswer this question using ONLY the context above: {query}"
    
    try:
        rag_completion = await openai_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a secure corporate assistant. Answer the user's question using ONLY the provided context. If the answer cannot be found in the context, state that you do not have sufficient information. Do not invent any facts."},
                {"role": "user", "content": rag_prompt}
            ],
            temperature=0.0
        )
        return rag_completion.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating answer: {str(e)}"
