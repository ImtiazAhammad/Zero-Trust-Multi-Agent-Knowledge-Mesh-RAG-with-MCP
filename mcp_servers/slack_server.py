import datetime
import random
import sys
from typing import List, Dict
from fastmcp import FastMCP

# Initialize FastMCP Server
mcp = FastMCP("slack-mcp")

# Generate 200 mock Slack messages
def generate_mock_slack_messages() -> List[Dict]:
    random.seed(1337)
    
    channels = {
        "#general-discussion": ("Shared", 1),
        "#hr-portal": ("HR", 1),
        "#engineering-sprint": ("Engineering", 2),
        "#finance-auditing": ("Finance", 2),
        "#marketing-brainstorm": ("Marketing", 1),
        "#security-ops": ("Engineering", 3),
        "#executive-lounge": ("Executive", 3)
    }
    
    users = {
        "alice": "Shared", "bob": "Shared", "charlie": "Shared",
        "hr-manager": "HR", "recruiter": "HR",
        "lead-dev": "Engineering", "qa-engineer": "Engineering", "devops-engineer": "Engineering",
        "marketing-lead": "Marketing", "designer": "Marketing",
        "cfo": "Finance", "accountant": "Finance",
        "ceo": "Executive", "security-officer": "Engineering"
    }
    
    content_templates = {
        "Shared": [
            "Has anyone seen the server status today?",
            "The staging environment seems to be responding normally now.",
            "Reminder to submit your timesheets by Friday afternoon.",
            "Happy birthday to Alice! Cake in the cafeteria at 3 PM.",
            "Can someone point me to the handbook page on remote work?",
            "Lunch delivery is arriving in the lobby, check your orders.",
            "Is anyone else experiencing VPN connection drops?",
            "The cafeteria is serving taco bowls today, highly recommended."
        ],
        "HR": [
            "We have updated the onboarding checklist for new remote hires.",
            "The training budget request portal is open for Q3 certification.",
            "Please ensure you complete the annual security awareness training.",
            "We are offering a wellness stipend of $50/month starting next week.",
            "Biological and adoptive parents are eligible for 12 weeks paid leave.",
            "Misconduct reports should be routed confidentially to the HR manager.",
            "Our employee referral bonus is $2,500 for mid-level engineering positions.",
            "New hires must submit tax forms within their first week of work."
        ],
        "Engineering": [
            "CI/CD pipeline failed due to a missing environment variable in staging.",
            "I checked the database connection pool; it looks like we had a socket leak.",
            "Please run the test suite locally using pytest before pushing changes.",
            "The Next.js frontend is throwing hydration errors in Safari.",
            "We need to configure Prometheus alertmanager to notify on-call.",
            "Argon2id hashing is working on the new authentication module.",
            "We should write Alembic migration scripts for the user profile table.",
            "FastMCP tool registry works asynchronously with the agent mesh."
        ],
        "Finance": [
            "Expense reports must be submitted within 30 days of the purchase date.",
            "Travel reimbursement requires receipt uploads for all transactions.",
            "Q3 revenue forecast predicts a 12% quarter-over-quarter growth.",
            "Please compile the assets register before the external audit.",
            "Wire transfers exceeding $10,000 require dual authorization.",
            "The weekly vendor payment processing is scheduled for Thursday.",
            "Cloud resource savings from shutting down staging saved us 15%.",
            "Invoices must reference a valid Purchase Order number."
        ],
        "Executive": [
            "Negotiations for the TakteekIAI acquisition are closing in Q4.",
            "The board memo recommends a $14 million cash transaction.",
            "CFO is preparing the final signature documents for the board review.",
            "We are targeting the announcement release for next Monday.",
            "Keep all acquisition details strictly private to executive members.",
            "We need to review the Q3 margin forecasts before the board call.",
            "The board approved the strategic pivot to decentralized RAG.",
            "C-suite alignment is complete on the new KMS migration path."
        ]
    }
    
    messages = []
    # Distribute 200 messages over the last 72 hours ending now
    now = datetime.datetime.now(datetime.timezone.utc)
    base_time = now - datetime.timedelta(hours=72)
    
    for i in range(200):
        # Pick channel
        channel_name, (chan_dept, chan_clearance) = random.choice(list(channels.items()))
        
        # Pick user matching department or shared
        eligible_users = [u for u, d in users.items() if d == chan_dept or d == "Shared"]
        user = random.choice(eligible_users)
        
        # Pick text template matching channel department
        dept_key = chan_dept if chan_dept in content_templates else "Shared"
        text_template = random.choice(content_templates[dept_key])
        text = f"[{user}] {text_template} (Msg ID: #{i+1000})"
        
        # Distribute timestamp sequentially
        timestamp = base_time + datetime.timedelta(minutes=i * 21.6)
        
        messages.append({
            "channel": channel_name,
            "user": user,
            "timestamp": timestamp.isoformat(),
            "text": text,
            "department": chan_dept,
            "clearance_level": chan_clearance
        })
        
    return messages

MOCK_SLACK_MESSAGES = generate_mock_slack_messages()

@mcp.tool()
async def search_slack(query: str, time_window_hours: int, department: str) -> List[Dict]:
    """
    Searches mock Slack messages by keyword.
    Enforces RBAC department filters and filters messages to within the last time_window_hours.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    cutoff_time = now - datetime.timedelta(hours=time_window_hours)
    
    query_lower = query.lower()
    
    # Extract keywords (filtering out common short words and punctuation)
    stop_words = {"how", "do", "i", "fix", "the", "in", "what", "are", "we", "have", "for", "new", "hires", "about", "recent", "is", "there", "any"}
    keywords = [w.strip("?,.!") for w in query_lower.split()]
    keywords = [w for w in keywords if w not in stop_words and len(w) > 2]
    if not keywords:
        keywords = [query_lower]

    results = []
    for msg in MOCK_SLACK_MESSAGES:
        # Enforce RBAC department bounds:
        # Message department must match user department OR be part of 'Shared'
        if msg["department"] != "Shared" and msg["department"].lower() != department.lower():
            continue
            
        # Enforce time window
        msg_time = datetime.datetime.fromisoformat(msg["timestamp"])
        if msg_time < cutoff_time:
            continue
            
        # Match if query is direct substring or if any keyword matches
        text_lower = msg["text"].lower()
        chan_lower = msg["channel"].lower()
        
        matches = (
            query_lower in text_lower or 
            query_lower in chan_lower or
            any(kw in text_lower or kw in chan_lower for kw in keywords)
        )
        if matches:
            results.append(msg)
            
    return results[:20]

@mcp.tool()
async def get_channel_history(channel: str, limit: int = 50) -> List[Dict]:
    """
    Returns the message history of a specific Slack channel, sorted by timestamp descending.
    """
    results = []
    # Normalize channel name (e.g. general -> #general-discussion, hr -> #hr-portal)
    target_channel = channel.lower()
    if not target_channel.startswith("#"):
        target_channel = f"#{target_channel}"
        
    for msg in MOCK_SLACK_MESSAGES:
        if msg["channel"].lower() == target_channel or msg["channel"].lower().startswith(target_channel):
            results.append(msg)
            
    # Sort descending by timestamp
    results.sort(key=lambda x: x["timestamp"], reverse=True)
    return results[:limit]

if __name__ == "__main__":
    print("Starting Slack MCP server on port 9003 using SSE transport...")
    mcp.run(transport="sse", host="0.0.0.0", port=9003)
