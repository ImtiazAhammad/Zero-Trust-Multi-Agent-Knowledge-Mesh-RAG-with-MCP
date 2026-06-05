import os
from typing import List
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Setup client for intent classification (optional, fallback to rule-based routing)
client = None
if os.getenv("OPENAI_API_KEY"):
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY", "mock-key"),
        base_url=os.getenv("OPENAI_API_BASE", "http://localhost:8000/v1")
    )

def route_query_with_llm(query: str) -> List[str]:
    """
    Asks the LLM to classify which source data systems (confluence, jira, slack)
    should be queried for the given input.
    """
    model_name = os.getenv("MODEL_NAME", "qwen2.5-14b")
    prompt = (
        f"You are a router that routes queries to corporate databases.\n"
        f"Databases available:\n"
        f"1. 'confluence' (for documentation, policies, wiki pages, design specs)\n"
        f"2. 'jira' (for task tracking, bugs, user stories, sprints, tickets)\n"
        f"3. 'slack' (for chat logs, channels, team discussions, DMs)\n\n"
        f"Analyze the user query: '{query}'\n"
        f"Return a comma-separated list of databases needed to answer the query (e.g., 'confluence,jira'). "
        f"Only return the list of databases, nothing else."
    )
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a direct, concise routing system."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=20,
            temperature=0.0,
        )
        result = response.choices[0].message.content.strip().lower()
        servers = [s.strip() for s in result.split(",") if s.strip() in ["confluence", "jira", "slack"]]
        return servers if servers else ["confluence", "jira", "slack"]
    except Exception as e:
        print(f"LLM routing failed, falling back to rule-based: {e}")
        return route_query_rules(query)

def route_query_rules(query: str) -> List[str]:
    """
    Fallback keyword rules to route query to the respective systems.
    """
    query_lower = query.lower()
    servers = []
    
    # Jira keywords
    if any(k in query_lower for k in ["ticket", "issue", "bug", "sprint", "jira", "story", "epic"]):
        servers.append("jira")
        
    # Confluence keywords
    if any(k in query_lower for k in ["doc", "wiki", "page", "policy", "spec", "confluence", "manual", "guide"]):
        servers.append("confluence")
        
    # Slack keywords
    if any(k in query_lower for k in ["message", "slack", "chat", "dm", "channel", "teams", "conversation"]):
        servers.append("slack")
        
    # Default fallback: check everything
    if not servers:
        return ["confluence", "jira", "slack"]
        
    return servers

def route_query(query: str) -> List[str]:
    """
    Determines which database mocks / MCP servers should be queried.
    """
    if client:
        return route_query_with_llm(query)
    return route_query_rules(query)
