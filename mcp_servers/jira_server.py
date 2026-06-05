import random
import sys
from typing import List, Dict
from fastmcp import FastMCP

# Initialize FastMCP Server
mcp = FastMCP("jira-mcp")

# Generate 100 mock Jira tickets
def generate_mock_jira_tickets() -> List[Dict]:
    random.seed(99)
    departments = ["Engineering", "HR", "Marketing", "Finance"]
    statuses = ["Open", "In Progress", "Code Review", "Testing", "Done"]
    
    assignees = {
        "Engineering": ["lead-dev", "qa-engineer", "devops-engineer", "junior-dev"],
        "HR": ["hr-manager", "recruiter", "benefits-coordinator"],
        "Marketing": ["marketing-lead", "designer", "copywriter"],
        "Finance": ["cfo", "accountant", "billing-specialist"]
    }
    
    templates = {
        "Engineering": {
            "titles": [
                "Fix socket leak in connection pool", "Migrate authentication db schema", 
                "Optimize token refresh performance", "Resolve Safari button alignment bug",
                "Integrate FlashRank cross-encoder", "Set up Prometheus metrics routing",
                "Deploy local vLLM cluster", "Resolve memory leak in semantic caching",
                "Configure HTTPS for internal registry", "Implement JWT validation middleware",
                "Refactor Alembic migration files", "Review security patch for SQL injection",
                "Update standard pytest config", "Optimize Dockerfile Layer caching",
                "Setup health/readiness endpoints", "Implement rate limiter on API gateway",
                "Document gRPC communication protocols", "Implement BM25 text tokenizer",
                "Debug PyTorch float8 tensor issues", "Upgrade sentence-transformers BGE engine",
                "Fix CORS settings on staging server", "Improve error handling in db client",
                "Reduce container startup latency", "Verify backup restoration procedures",
                "Audit KMS secret rotation configurations"
            ],
            "descriptions": [
                "Connection pool exhausts resources under load. Verify socket closing logic in db module.",
                "Create Alembic script to add title column to documents and index it.",
                "Ensure token generation avoids round-trips to datastore on every endpoint check.",
                "Center login-button container styles inside CSS definitions.",
                "Update reranker script to support single-batch prediction via SentenceTransformers.",
                "Expose metrics on /metrics route and verify Prometheus scrape configurations.",
                "Passthrough host GPU capabilities using NVIDIA toolkit settings.",
                "Cache entries leak in memory because TTL is not correctly applied in Redis client.",
                "SSL certificate renewal is required for registry subdomains.",
                "Configure middleware to check authorization bearer header with secret keys.",
                "Migrations are currently out of order. Merge head branches to repair.",
                "Analyze query inputs to ensure parameter binding is utilized everywhere.",
                "Add pytest-asyncio to test environment and mark async tests.",
                "Leverage multi-stage builds to lower image size to under 200MB.",
                "Kubernetes probes need correct status codes returned from microservices.",
                "Reject clients exceeding maximum allowable requests per minute.",
                "Standardize protobuf definitions and compile using latest grpcio compiler.",
                "Ensure English analyzer is used during tsvector document conversions.",
                "Torch model loading throws AttributeError for float8 floating point formats.",
                "Ensure embeddings service uses CPU-only builds to preserve GPU VRAM.",
                "Allow specific trusted subdomains to access staging resources.",
                "Catch database driver exceptions and return proper JSON error structures.",
                "Use alpine-based base images and pre-compiled wheels for faster deployments.",
                "Run test recovery on backup volumes and check integrity of rows.",
                "Validate KMS decryption keys can resolve credentials in all target environments."
            ]
        },
        "HR": {
            "titles": [
                "Onboard new senior engineer", "Audit annual security training", 
                "Update remote work handbook section", "Review wellness benefits providers",
                "Publish job description for QA role", "Coordinate career development budgets",
                "Plan company annual team building", "Review performance bonus eligibility",
                "Manage background check vendor setup", "Refactor diversity hiring initiatives",
                "Process maternity leave request", "Coordinate security compliance exam",
                "Review remote setup stipends", "Draft workplace harassment policies",
                "Update retirement contribution forms", "Plan onboarding program orientation",
                "Audit health insurance claims", "Review relocation budget requests",
                "Initiate quarterly performance cycles", "Review exit interview feedback",
                "Configure employee referral tracking", "Update payroll enrollment checklist",
                "Coordinate remote ergonomics assessments", "Verify background screen for lead dev",
                "Manage retirement planning seminar bookings"
            ],
            "descriptions": [
                "Collect signed contracts, arrange workstation delivery, and set up slack account.",
                "Generate list of employees who have not completed the annual compliance coursework.",
                "Rewrite remote agreement to specify company VPN access rules.",
                "Assess if current providers meet dental and vision requirements.",
                "Verify skills criteria are correct for QA engineer positions.",
                "Review applications for Q3 professional development training grants.",
                "Evaluate venues for team conference event scheduled in November.",
                "Managers need templates to report quarterly bonus candidate justifications.",
                "Validate vendor meets our privacy policies and background checks standards.",
                "Audit sourcing pipelines to ensure diverse candidate pools are utilized.",
                "Coordinate transition of project tasks before parental leave begins.",
                "All staff must complete compliance test within 30 days.",
                "Assess expense receipts for remote hardware reimbursements.",
                "Conduct review of internal reporting flow and verify confidentiality.",
                "Validate 401k match rates are correctly set in the payroll system.",
                "Coordinate schedules for upcoming group orientation sessions.",
                "Review claim reports from insurance provider and reconcile totals.",
                "Process relocations for engineers shifting to central headquarters.",
                "Send notifications for self-evaluations and peer reviews.",
                "Analyze feedback reports to identify key retention opportunities.",
                "Enable automated tracking of referred candidates in internal portal.",
                "Standardize direct deposit forms and payroll enrollment documents.",
                "Ensure remote workstations meet occupational safety guidelines.",
                "Run background verification checks prior to contract finalization.",
                "Schedule retirement sessions with certified financial advisors."
            ]
        },
        "Marketing": {
            "titles": [
                "Design Q3 campaign social graphics", "Conduct SEO keyword target research", 
                "Draft press release for RAG system", "Update brand identity SVG logos",
                "Analyze conversion funnel dropoffs", "Create LinkedIn content calendar",
                "Design layout for email newsletters", "Draft competitor product analysis",
                "Coordinate booth setup for conference", "Audit paid search ad conversions",
                "Set up partner affiliate portal", "Publish blog post on FastMCP",
                "Review creative asset guidelines", "Optimize homepage landing layout",
                "Test conversion rates on call-to-actions", "Draft press package for release",
                "Analyze buyer persona data", "Design banners for Twitter profile",
                "Manage marketing list segmentations", "Verify branding colors on web portal",
                "Analyze organic search rankings", "Draft product showcase video script",
                "Review partner sponsorship package", "Optimize mobile landing page speed",
                "Coordinate webinar invitation campaigns"
            ],
            "descriptions": [
                "Create vector banners and custom illustrations for social network ads.",
                "Locate high-volume, low-competition terms for secure RAG keywords.",
                "Draft release highlighting our zero-trust architecture and pgvector scaling.",
                "Deliver logo versions optimized for light and dark backgrounds.",
                "Locate phase where users leave checkout funnel and run tests.",
                "Draft posts on corporate handbook design and RAG security updates.",
                "Standardize newsletter templates with clean, responsive HTML tables.",
                "Compare row-level DB security against cloud-only vector databases.",
                "Ensure tables, monitors, and brochures are shipped to conference hall.",
                "Verify return on ad spend and adjust search budgets accordingly.",
                "Configure registration flows for affiliate referral partners.",
                "Write technical guide demonstrating local server integration methods.",
                "Document typography, brand red Hex #E30613, and charcoal Hex #1A1A1A.",
                "Simplify registration form fields to boost sign-ups.",
                "A/B test different colors and sizes for critical demo call-to-actions.",
                "Gather product screenshots, logo files, and team boilerplates.",
                "Review user research logs to refine 'Dave' and 'Dan' buyer profiles.",
                "Deliver updated header graphics matching Q3 marketing themes.",
                "Segment list into separate folders for developers and enterprise leads.",
                "Confirm Hex colors align with primary brand style guide values.",
                "Track search position movements for core industry keyword lists.",
                "Write introductory voiceover script highlighting multi-agent features.",
                "Assess if sponsorship benefits justify event package pricing.",
                "Compress homepage images to improve load times under 3 seconds.",
                "Manage invitation emails and track registrants for upcoming event."
            ]
        },
        "Finance": {
            "titles": [
                "Process monthly expense audits", "Draft Q3 travel budget allowances", 
                "Reconcile bank accounts for audits", "Update payroll processing schedules",
                "Review vendor procurement requests", "Prepare corporate tax provisions",
                "Process equity options board grants", "Model cloud resource cost savings",
                "Manage weekly vendor payments", "Audit flight upgrade justifications",
                "Verify bank details for wire transfers", "Process billing portal integrations",
                "Update travel reimbursement templates", "Review annual budget submissions",
                "Manage tax filing deadlines", "Assess capital investment models",
                "Verify invoice reference POs", "Optimize cloud licensing expenditures",
                "Reconcile merchant portal accounts", "Generate financial health reports",
                "Verify payroll direct deposits", "Draft travel safety guidelines",
                "Process software license renewals", "Audit phone stipend allowances",
                "Draft procurement compliance reports"
            ],
            "descriptions": [
                "Inspect expense submissions and verify receipts for compliance.",
                "Establish daily accommodation and travel spending caps by city tier.",
                "Perform bank reconciliation checks ahead of external audit.",
                "Verify processing calendar dates with payroll provider.",
                "Review purchase orders exceeding $5,000 for competitive bids.",
                "Calculate tax deductions and compile reporting schedules.",
                "Prepare stock option grant folders for executive sign-off.",
                "Reconcile monthly cloud statements against resource optimization targets.",
                "Initiate weekly payments and check wire transfers for accuracy.",
                "Validate class upgrades are supported by business justifications.",
                "Confirm banking information matches direct vendor contact data.",
                "Integrate stripe events with internal bookkeeping systems.",
                "Release simplified spreadsheet templates for travel receipts.",
                "Consolidate department proposals for executive consolidation.",
                "Ensure electronic tax filing confirmations are stored in secure folder.",
                "Compare infrastructure migration models for bare-metal host setups.",
                "Check that vendor invoices reference a valid pre-approved PO number.",
                "Evaluate subscription counts and eliminate inactive seat licenses.",
                "Reconcile processing fees against monthly volume registers.",
                "Compile balance sheet and income statement metrics for reviews.",
                "Initiate direct deposits and verify total payroll sum transfers.",
                "Document insurance rules and travel security expectations.",
                "Verify budget approval is active for upcoming software licenses.",
                "Confirm phone stipend allocations align with job criteria rules.",
                "Document procurement compliance metrics for annual internal audit."
            ]
        }
    }
    
    tickets = []
    ticket_counter = 1001
    
    for dept in departments:
        dept_titles = templates[dept]["titles"]
        dept_descs = templates[dept]["descriptions"]
        
        # Generate 25 tickets for each department
        for i in range(25):
            ticket_id = f"JIRA-{ticket_counter}"
            # clearance levels: 10 public, 10 internal, 5 confidential
            if i < 10:
                clearance = 1
            elif i < 20:
                clearance = 2
            else:
                clearance = 3
                
            status = statuses[i % len(statuses)]
            assignee = assignees[dept][i % len(assignees[dept])]
            
            tickets.append({
                "ticket_id": ticket_id,
                "title": dept_titles[i],
                "description": dept_descs[i],
                "status": status,
                "assignee": assignee,
                "department": dept,
                "clearance_level": clearance
            })
            ticket_counter += 1
            
    return tickets

MOCK_JIRA_TICKETS = generate_mock_jira_tickets()

@mcp.tool()
async def search_jira(query: str, department: str) -> List[Dict]:
    """
    Searches mock Jira tickets by keyword in the title or description.
    Enforces RBAC department filters (user can only query tickets in their own department).
    """
    results = []
    query_lower = query.lower()
    
    # Extract keywords (filtering out common short words and punctuation)
    stop_words = {"how", "do", "i", "fix", "the", "in", "what", "are", "we", "have", "for", "new", "hires", "about", "recent", "is", "there", "any"}
    keywords = [w.strip("?,.!") for w in query_lower.split()]
    keywords = [w for w in keywords if w not in stop_words and len(w) > 2]
    if not keywords:
        keywords = [query_lower]

    for ticket in MOCK_JIRA_TICKETS:
        # Enforce RBAC department boundary
        if ticket["department"].lower() != department.lower():
            continue
            
        # Match if query is direct substring or if any keyword matches
        title_lower = ticket["title"].lower()
        desc_lower = ticket["description"].lower()
        id_lower = ticket["ticket_id"].lower()
        
        matches = (
            query_lower in title_lower or 
            query_lower in desc_lower or 
            query_lower in id_lower or
            any(kw in title_lower or kw in desc_lower or kw in id_lower for kw in keywords)
        )
        if matches:
            results.append(ticket)
            
    return results[:20]

@mcp.tool()
async def get_ticket(ticket_id: str) -> Dict:
    """
    Fetches details of a specific Jira ticket by its ticket ID (e.g., JIRA-1001).
    """
    target_id = ticket_id.upper().strip()
    for ticket in MOCK_JIRA_TICKETS:
        if ticket["ticket_id"] == target_id:
            return ticket
            
    return {"error": f"Jira ticket not found: {ticket_id}"}

if __name__ == "__main__":
    print("Starting Jira MCP server on port 9002 using SSE transport...")
    mcp.run(transport="sse", host="0.0.0.0", port=9002)
