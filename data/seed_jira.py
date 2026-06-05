import sys
import os
# Add root path to PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vector_db.hybrid_search import init_db, insert_document

MOCK_JIRA_TICKETS = [
    {
        "source": "jira",
        "title": "JIRA-4021: Fix styling anomalies on Login page",
        "content": "Users report that button alignments are offset on Safari. Align items to center in login-button container. Expected fix in next sprint.",
        "ticket_id": "JIRA-4021",
        "status": "In Progress",
        "department": "Engineering",
        "clearance_level": 1
    },
    {
        "source": "jira",
        "title": "JIRA-9102: Address zero-day vulnerability in Authentication Middleware",
        "content": "CRITICAL SECURITY BUG: The JWT signature validation can be bypassed under specific timing conditions due to non-constant-time comparisons. Replace simple equality check with hmac.compare_digest in authentication routes.",
        "ticket_id": "JIRA-9102",
        "status": "Open",
        "department": "Engineering",
        "clearance_level": 3
    },
    {
        "source": "jira",
        "title": "JIRA-1122: Design assets upload for Marketing Campaign",
        "content": "Upload high-res vector graphics and SVG logos to the Shared S3 Bucket. Target folder is /assets/marketing/q3-campaign-v2. Please ping product lead when complete.",
        "ticket_id": "JIRA-1122",
        "status": "Done",
        "department": "Marketing",
        "clearance_level": 1
    }
]

def seed():
    print("Initializing database...")
    init_db()
    
    print("Seeding mock Jira tickets...")
    for doc in MOCK_JIRA_TICKETS:
        try:
            insert_document(doc)
            print(f"Successfully indexed Jira ticket: '{doc['title']}' (Clearance: {doc['clearance_level']})")
        except Exception as e:
            print(f"Error seeding ticket '{doc['title']}': {e}")

if __name__ == "__main__":
    seed()
