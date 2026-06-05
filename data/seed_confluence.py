import sys
import os
# Add root path to PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vector_db.hybrid_search import init_db, insert_document

MOCK_CONFLUENCE_PAGES = [
    {
        "source": "confluence",
        "title": "Corporate Employee Handbook & Leave Policies",
        "content": "Welcome to the corporate handbook. Standard annual leave is 20 days. Maternity leave is 12 weeks. All employees are required to submit timesheets by Friday 5 PM.",
        "url": "https://wiki.corp.internal/hr/handbook",
        "department": "Shared",
        "clearance_level": 1
    },
    {
        "source": "confluence",
        "title": "Marketing Campaign Roadmap - Q3",
        "content": "The Q3 marketing campaign focuses on social media expansions. The budget is $150,000. Target demographics include tech professionals aged 25-45. Creative assets are due in August.",
        "url": "https://wiki.corp.internal/marketing/q3-roadmap",
        "department": "Marketing",
        "clearance_level": 1
    },
    {
        "source": "confluence",
        "title": "Project Spanish-Stitch Frontend System Design",
        "content": "Architecture doc for Spanish-Stitch. Built on Next.js 14 App Router, using Tailwind CSS and TypeScript. Integrates with Python CMS backend API for content synchronization. Stores secure upload hashes in SQLite.",
        "url": "https://wiki.corp.internal/engineering/spanish-stitch-design",
        "department": "Engineering",
        "clearance_level": 2
    },
    {
        "source": "confluence",
        "title": "Project Alpha Secret Acquisition Board Memorandum",
        "content": "Highly Confidential: This memo discusses the board decision to acquire startup TakteekIAI for $14 million. The acquisition will close in Q4 2026. Keep all details strictly private to executive members.",
        "url": "https://wiki.corp.internal/executive/project-alpha-acquisition",
        "department": "Executive",
        "clearance_level": 3
    }
]

def seed():
    print("Initializing database...")
    init_db()
    
    print("Seeding mock Confluence documents...")
    for doc in MOCK_CONFLUENCE_PAGES:
        try:
            insert_document(doc)
            print(f"Successfully indexed Confluence doc: '{doc['title']}' (Clearance: {doc['clearance_level']})")
        except Exception as e:
            print(f"Error seeding doc '{doc['title']}': {e}")

if __name__ == "__main__":
    seed()
