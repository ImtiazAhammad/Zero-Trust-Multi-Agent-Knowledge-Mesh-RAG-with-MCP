import sys
import os
# Add root path to PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vector_db.hybrid_search import init_db, insert_document

MOCK_SLACK_MESSAGES = [
    {
        "source": "slack",
        "title": "Slack Chat in #general-discussion",
        "content": "Alice: Has anyone noticed the server latency? Bob: Yes, the staging environment is responding slowly, checking database connection pools. Charlie: Looks like pool overflow, restarting postgres resolved it.",
        "channel": "#general-discussion",
        "sender": "Alice, Bob, Charlie",
        "department": "Shared",
        "clearance_level": 1
    },
    {
        "source": "slack",
        "title": "Slack DM: Database leak alert",
        "content": "Security-Officer: Hey Lead-Dev, we noticed an external IP trying to brute force postgres port 5432. We must block it immediately on the security group settings. Lead-Dev: On it, applying firewall block now.",
        "channel": "Direct Message (Security <-> Lead-Dev)",
        "sender": "Security-Officer",
        "department": "Engineering",
        "clearance_level": 2
    },
    {
        "source": "slack",
        "title": "Slack Chat in #executive-lounge",
        "content": "CEO: We are finalizing the negotiations for the TakteekIAI acquisition. The final valuation is settled at $14M. CFO: Perfect. The transaction contract is prepared and ready for signatures on Monday.",
        "channel": "#executive-lounge",
        "sender": "CEO, CFO",
        "department": "Executive",
        "clearance_level": 3
    }
]

def seed():
    print("Initializing database...")
    init_db()
    
    print("Seeding mock Slack messages...")
    for doc in MOCK_SLACK_MESSAGES:
        try:
            insert_document(doc)
            print(f"Successfully indexed Slack msg: '{doc['title']}' (Clearance: {doc['clearance_level']})")
        except Exception as e:
            print(f"Error seeding slack msg '{doc['title']}': {e}")

if __name__ == "__main__":
    seed()
