import sys
import os
import random
# Add root path to PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vector_db.hybrid_search import init_db, insert_document

# 50 high-quality realistic corporate documents mapped by title
MOCK_CONFLUENCE_DATA = {
    # --- ENGINEERING (13 documents) ---
    "CI/CD Pipeline Setup and Automation Guidelines": (
        "Engineering", 1, [
            "This document outlines the standard configuration for our continuous integration and continuous deployment (CI/CD) pipelines. We utilize GitHub Actions for version control events, which trigger build verification tests and code quality checks automatically. All pull requests must pass these checks prior to merge approval.",
            "The build process packages applications into Docker containers and uploads them to our secure container registry. Developers are encouraged to optimize their Dockerfiles to keep image sizes small and reduce build durations. Clean caching strategies should be implemented for npm, pip, and other dependency managers.",
            "Deployment to staging occurs automatically upon merging to the main branch. Production deployments are gated and require manual approval from the engineering lead. Rollback procedures are automated; in the event of a deployment failure, the system will immediately revert to the last stable container version."
        ]
    ),
    "Microservices Architecture Layout and Service Map": (
        "Engineering", 2, [
            "Our primary application relies on a decoupled microservices architecture designed to run on a local Kubernetes cluster. The main API gateway routes incoming public requests to internal downstream services. Inter-service communication is handled via lightweight gRPC endpoints to keep latency under 10ms.",
            "Each microservice manages its own isolated datastore, avoiding direct database sharing across service boundaries. Data synchronization is managed asynchronously using a RabbitMQ message broker. Eventual consistency is monitored through distributed tracing logs.",
            "All services must expose standard health and readiness endpoints (`/health` and `/ready`) for container orchestration. Metrics are collected by Prometheus and formatted for centralized visualization dashboards in Grafana."
        ]
    ),
    "Frontend State Management with Redux Toolkit": (
        "Engineering", 1, [
            "This document establishes the state management patterns for our client application. We utilize Redux Toolkit (RTK) to maintain a single, predictable source of truth across the web application. Ad-hoc React state should only be used for strictly localized UI components.",
            "Async data fetching must be handled using RTK Query (RTKQ) hooks to implement automated caching, request deduplication, and polling. Slice reducers should contain clear, pure functions to mutate state in response to user actions.",
            "To prevent performance bottlenecks, avoid storing massive raw JSON blocks in the Redux store. Normalize nested entity relationships and map state to selector functions to prevent unnecessary component re-renders."
        ]
    ),
    "PostgreSQL Database Migration Best Practices": (
        "Engineering", 2, [
            "Database schemas are managed using Alembic migration scripts. Any changes to database tables, indexes, or extensions must be committed to version control and reviewed by database engineers. Direct schema mutation in production environments is strictly prohibited.",
            "When writing migrations, always ensure they are backward-compatible to allow zero-downtime rolling updates. Avoid adding default constraints on massive tables in a single step, as this can lock tables and cause API request timeouts.",
            "Ensure that all newly introduced foreign keys have corresponding indexes to maintain search performance. Before running migrations on production, developers must test migration scripts against local copies of staging databases."
        ]
    ),
    "Redis Semantic Caching Implementation Details": (
        "Engineering", 2, [
            "This technical specification describes the integration of Redis as a semantic caching layer for our RAG system. The cache stores query vector embeddings alongside their matching documents. It prevents redundant LLM calls for repeated or semantically similar prompts.",
            "The cache utilizes cosine similarity calculations to locate cache hits. A threshold of 0.92 is established; any incoming query vector within this cosine distance to a cached query will return the cached response directly.",
            "Keys are configured with a Time-To-Live (TTL) of 24 hours. Cache invalidation is triggered automatically when a document in the main PostgreSQL table is updated or deleted, ensuring cache consistency."
        ]
    ),
    "API Design Principles and RESTful Standards": (
        "Engineering", 1, [
            "We adhere strictly to RESTful design principles for all public and internal web services. APIs must use standard HTTP methods such as GET, POST, PUT, and DELETE to denote semantic operations. Route URIs must use plural nouns and clear nested hierarchies.",
            "Responses should return standard JSON payloads accompanied by correct HTTP status codes (e.g., 200 OK, 201 Created, 400 Bad Request, 403 Forbidden, 404 Not Found). API documentation must be generated automatically using Swagger/OpenAPI.",
            "Authentication is enforced via JWT Bearer tokens passed in the Authorization header. Rate limiting is configured at the gateway level, restricting clients to 100 requests per minute to prevent service denial attacks."
        ]
    ),
    "Logging and Monitoring with Prometheus and Grafana": (
        "Engineering", 1, [
            "System observability is established using Prometheus for metric collection and Grafana for dashboard visualizations. Applications must expose metrics on `/metrics` in the standard Prometheus exposition format, tracking CPU, memory, and HTTP response latencies.",
            "Alerts are configured via Prometheus Alertmanager to notify the on-call engineering team of anomalies. Critical alerts include high error rates (>1%), database disk usage exceeding 85%, and container restarts.",
            "Dashboards are organized by microservice and environment (staging vs. production). Service-level objectives (SLOs) are tracked weekly to guarantee 99.9% uptime and ensure rapid incident response times."
        ]
    ),
    "Secure Password Hashing and Storage Policy": (
        "Engineering", 3, [
            "Confidential Security Policy: All user passwords must be hashed using the Argon2id algorithm before being stored in the database. Raw passwords must never be logged, cached, or transmitted in plain text across service boundaries.",
            "The hashing parameters must meet the OWASP guidelines: a minimum memory cost of 64MB, a time cost of 3 iterations, and a parallelism factor of 4. Unique, high-entropy cryptographic salts must be generated for each password.",
            "Legacy bcrypt passwords will be migrated automatically upon user login. Access to the cryptographic keys and salt generation variables is restricted to security administrators via Vault KMS."
        ]
    ),
    "Automated Unit Testing Guidelines": (
        "Engineering", 1, [
            "This document establishes the testing standards for our codebase. We require all new features to be accompanied by unit and integration tests. The repository is configured to block merges if test coverage falls below 85%.",
            "Tests must be isolated and should not depend on external live databases or third-party APIs. Mocking frameworks (such as unittest.mock or pytest-mock) must be used to simulate external HTTP services and database drivers.",
            "Run your test suite locally using `pytest` or `npm test` before pushing to remote branches. Integration tests should verify critical user journeys, including user authentication, checkout flows, and search engines."
        ]
    ),
    "Containerization and Docker Compose Orchestration": (
        "Engineering", 1, [
            "Our local development environment is orchestrated using Docker Compose. This configuration mirrors production services locally, including the FastAPI application, PostgreSQL database, Redis cache, and vLLM inference container.",
            "Containers are configured on a shared bridge network, enabling them to resolve each other by container name. Environment variables are managed using local `.env` files which are excluded from version control.",
            "Volume mounts are configured for data directories to ensure local state persists across container restarts. Run `docker compose up --build` to launch the full development suite with updated dependency files."
        ]
    ),
    "Git Branching Strategy and Pull Request Review Workflow": (
        "Engineering", 1, [
            "This workflow governs code changes in our repositories. We use a modified Git Flow strategy. All development occurs on feature branches branched from `main`. Direct commits to `main` are restricted.",
            "Pull requests (PRs) must be reviewed by at least one other engineer before merge. Reviewers should check for code readability, architectural alignment, test coverage, and security vulnerabilities.",
            "Once approved and verified by the CI/CD pipeline, PRs should be squashed and merged into `main`. Release branches are tagged with semantic version numbers (e.g., v1.4.2) and deployed to staging."
        ]
    ),
    "Multi-Agent System Communication Protocol": (
        "Engineering", 2, [
            "This document specifies the communication protocols between agents in our multi-agent RAG system. Agents interact asynchronously via message queues, exchanging JSON payloads containing task context, security claims, and execution parameters.",
            "The orchestrator agent delegates sub-tasks to specialized retrieval, tools, and synthesis agents. Each agent validates the incoming security context and drops messages if the requested action violates tenant constraints.",
            "A global correlation ID must accompany all inter-agent messages. This correlation ID is logged in central systems, allowing developers to trace the lifecycle of a query across the entire agent mesh."
        ]
    ),
    "Disaster Recovery and Backup Verification Plan": (
        "Engineering", 3, [
            "Highly Confidential: This plan details the disaster recovery protocols for our primary database cluster. Daily incremental backups and weekly full backups of the PostgreSQL database are encrypted and stored in offsite buckets.",
            "Backup integrity is verified automatically every Monday through a containerized restoration process. If restoration fails or checksums mismatch, immediate alerts are triggered to the DevOps on-call engineers.",
            "In the event of a catastrophic failure, our recovery time objective (RTO) is 2 hours, and our recovery point objective (RPO) is 4 hours. Regional failover protocols are documented in the runbooks."
        ]
    ),

    # --- HR (13 documents) ---
    "Corporate Employee Handbook & Leave Policies": (
        "HR", 1, [
            "Welcome to the corporate handbook. Standard annual leave is 20 days. Maternity leave is 12 weeks. All employees are required to submit timesheets by Friday 5 PM.",
            "Sick leave must be reported to managers by 9 AM on the day of absence. A medical certificate is required for absences exceeding 3 consecutive business days.",
            "Paid time off (PTO) does not roll over more than 5 unused days into the next calendar year. Any additional unused leave will expire on December 31st."
        ]
    ),
    "Employee Onboarding Checklist and Guide": (
        "HR", 1, [
            "This guide assists HR staff and hiring managers during the onboarding of new employees. The first week focuses on compliance, hardware setup, and basic security training.",
            "On Day 1, HR will coordinate the collection of signed contracts, tax documents, and emergency contact details. IT support will deliver the configured workstation.",
            "By the end of Week 1, new hires must complete the interactive Security Awareness training and attend the company culture orientation seminar."
        ]
    ),
    "Remote Work Agreement and Equipment Policy": (
        "HR", 1, [
            "This document establishes the guidelines for remote work. Employees are eligible for remote status subject to manager approval and role requirements.",
            "The company provides a standard remote office package, including a laptop, monitor, keyboard, and ergonomic mouse. High-speed internet is the responsibility of the employee.",
            "Remote employees must adhere to our security policies. Workstations must be locked when unattended, and public Wi-Fi networks must only be accessed through the secure company VPN."
        ]
    ),
    "Performance Review and Quarterly Feedback Process": (
        "HR", 2, [
            "Our performance review cycle operates quarterly. It consists of self-evaluations, peer feedback, and manager discussions to assess performance against goals.",
            "Key performance indicators (KPIs) are agreed upon at the start of each quarter. Mid-quarter reviews are encouraged to address blocking issues early.",
            "Final quarterly evaluations determine eligibility for performance bonuses and career advancement opportunities. Documentation must be submitted in the HR portal."
        ]
    ),
    "Health and Wellness Benefits Package Details": (
        "HR", 1, [
            "We offer comprehensive health and wellness benefits to all full-time employees. Coverage includes medical, dental, and vision care starting on the first day of employment.",
            "Additional benefits include a monthly wellness stipend of $50, which can be applied to gym memberships, fitness equipment, or mental health apps.",
            "An Employee Assistance Program (EAP) is available 24/7, providing free, confidential counseling and legal advice for personal or work-related issues."
        ]
    ),
    "Workplace Diversity, Equity, and Inclusion Guidelines": (
        "HR", 1, [
            "These guidelines reinforce our commitment to creating a diverse, equitable, and inclusive workplace. We believe diverse teams drive innovation and enrich our culture.",
            "Hiring panels must consist of diverse members, and job descriptions are screened to ensure inclusive language. Bi-annual bias training is mandatory for all hiring managers.",
            "Employee Resource Groups (ERGs) are funded and supported by leadership, providing community and advocacy for underrepresented groups within the company."
        ]
    ),
    "Internal Referral Program and Hiring Bonuses": (
        "HR", 1, [
            "We encourage employees to refer qualified candidates for open positions. If a referred candidate is hired and completes 90 days, the referring employee receives a bonus.",
            "Hiring bonuses vary by role seniority: $1,000 for junior roles, $2,500 for mid-level, and $5,000 for senior engineering or leadership positions.",
            "Referrals must be submitted through the internal HR portal before the candidate submits their application to be eligible for the bonus."
        ]
    ),
    "Professional Development and Training Budget Rules": (
        "HR", 2, [
            "All employees are allocated an annual professional development budget of $2,000. This budget can be used for conferences, courses, certifications, or books.",
            "Budget requests require manager approval and must align with the employee's career goals and role responsibilities. Receipts must be submitted for reimbursement.",
            "Upon completion of training, employees are encouraged to share key takeaways with their team during weekly syncs or lunch-and-learn presentations."
        ]
    ),
    "Relocation Assistance and Housing Support Guidelines": (
        "HR", 2, [
            "This policy outlines relocation assistance for new hires or internal transfers moving over 50 miles for their role. Support is provided on a case-by-case basis.",
            "Assistance packages include a lump-sum relocation allowance, covered packing and moving services, and up to 30 days of temporary housing.",
            "All relocation expenses must be pre-approved by the HR director. Relocated employees must sign a repayment agreement if they leave the company within 12 months."
        ]
    ),
    "Anti-Harassment and Workplace Conduct Policies": (
        "HR", 1, [
            "We maintain a zero-tolerance policy for harassment, discrimination, or retaliation of any kind. All employees are entitled to a safe, respectful working environment.",
            "Reports of misconduct can be submitted to HR, a manager, or through our anonymous reporting hotline. All complaints are investigated promptly and confidentially.",
            "Violations of these conduct policies will result in disciplinary action up to and including immediate termination of employment."
        ]
    ),
    "Maternity and Paternity Family Leave Options": (
        "HR", 1, [
            "We provide paid family leave to support new parents. Biological, adoptive, and foster parents are eligible for up to 12 weeks of fully paid leave.",
            "Leave can be taken concurrently or intermittently within the first 12 months following the birth or placement of the child, subject to coordination with the manager.",
            "Employees must submit a leave request at least 30 days in advance of the anticipated start date to ensure smooth transition of responsibilities."
        ]
    ),
    "Security Awareness Training Requirements": (
        "HR", 1, [
            "All employees must complete security awareness training annually. This training covers phishing detection, password management, social engineering, and secure data handling.",
            "New hires must complete the training within their first 30 days. Failure to complete the training within the deadline will result in restricted network access.",
            "Monthly simulated phishing campaigns are conducted to reinforce learning. Employees who repeatedly fall for simulated emails will receive follow-up training."
        ]
    ),
    "Standard Retirement and 401k Matching Guidelines": (
        "HR", 1, [
            "We offer a retirement savings plan with company matching. Employees can contribute a percentage of their pre-tax salary to their 401k account.",
            "The company matches 100% of the first 3% of contributions, and 50% of the next 2% of contributions. Company matches are immediately 100% vested.",
            "Financial advisors are available quarterly to provide free, objective investment advice to help employees plan for their retirement goals."
        ]
    ),

    # --- MARKETING (12 documents) ---
    "Marketing Campaign Roadmap - Q3": (
        "Marketing", 1, [
            "The Q3 marketing campaign focuses on social media expansions. The budget is $150,000. Target demographics include tech professionals aged 25-45. Creative assets are due in August.",
            "Key performance indicators (KPIs) include a 15% increase in brand engagement, 10,000 new sign-ups, and a return on ad spend (ROAS) of 3:1.",
            "We will partner with micro-influencers in the tech space and run targeted campaigns on LinkedIn, YouTube, and Twitter to reach our audience."
        ]
    ),
    "Search Engine Optimization (SEO) Strategy Guide": (
        "Marketing", 1, [
            "This strategy guide outlines our approach to organic search growth. Our goal is to double organic traffic over the next 12 months by targeting high-intent keywords.",
            "On-page optimization involves updating meta titles, improving site speed, and ensuring mobile responsiveness. Content marketing will focus on long-form guides.",
            "Link building efforts will target high-authority tech blogs and industry publications. Monthly reports will track keyword rankings and organic traffic growth."
        ]
    ),
    "Product Launch Press Release Templates": (
        "Marketing", 1, [
            "These templates are pre-approved for public relations releases. They provide a structured format for announcing new product features or business partnerships.",
            "Press releases must include a compelling headline, a strong opening hook, key product benefits, quotes from leadership, and a boilerplate about the company.",
            "Drafts must be reviewed by the marketing director and public relations team before distribution to wire services and media outlets."
        ]
    ),
    "Brand Identity and Logo Usage Guidelines": (
        "Marketing", 1, [
            "This document defines our brand identity, including logo usage, typography, and color palettes. Consistency in brand presentation builds trust and recognition.",
            "The primary logo should be used on white backgrounds. A minimum clear space must be maintained around the logo, and modifications to colors are prohibited.",
            "Our brand colors are Hex #E30613 (Primary Red) and Hex #1A1A1A (Charcoal). Approved typography includes 'Inter' for body copy and 'Outfit' for headings."
        ]
    ),
    "Customer Persona Analysis for Enterprise Clients": (
        "Marketing", 2, [
            "This analysis identifies the primary personas for our enterprise tier. Understanding our buyers helps customize marketing messages and product development.",
            "Our primary persona is 'Director Dave' (IT Decision Maker, budget holder, focused on security/scalability) and 'Developer Dan' (End-user, values developer experience and API design).",
            "Marketing campaigns should address Dave's security concerns (RAG security, RBAC) and highlight Dan's ease of integration (FastMCP, OpenAI compat)."
        ]
    ),
    "Social Media Editorial Calendar and Rules": (
        "Marketing", 1, [
            "This editorial calendar schedules social media content across Twitter, LinkedIn, and YouTube. Consistency in posting builds audience engagement.",
            "LinkedIn content focuses on thought leadership and company updates, posted thrice weekly. Twitter posts are daily, focusing on product tips and tech discussions.",
            "All posts must align with our brand voice: professional, informative, and engaging. Avoid controversial topics or unauthorized product leaks."
        ]
    ),
    "Email Newsletter Segmentation and Copywriting Best Practices": (
        "Marketing", 1, [
            "Our newsletter strategy segmentations maximize open rates. We partition our list into developers, enterprise buyers, and general subscribers.",
            "Copywriting should be clear, action-oriented, and include a single call-to-action (CTA). Subject lines should be concise and spark curiosity.",
            "A/B testing must be performed on subject lines and CTA placement for all major campaigns. Deliverability metrics must be monitored weekly."
        ]
    ),
    "Competitor Analysis and Market Positioning Report": (
        "Marketing", 2, [
            "This report analyzes our top competitors in the secure RAG space. We evaluate feature sets, pricing models, and marketing positioning.",
            "Our competitive advantage is our native zero-trust RBAC integration and FastMCP local server mesh. Competitors lack granular row-level database filtering.",
            "Marketing materials should emphasize our security compliance and local offline capabilities to differentiate us from cloud-only competitors."
        ]
    ),
    "Event Planning Checklist for Corporate Conferences": (
        "Marketing", 1, [
            "This checklist assists the marketing team in planning and executing corporate conferences. Timelines start 6 months prior to the event date.",
            "Key tasks include venue selection, catering, speaker invitations, sponsor packages, registration setup, and promotional campaign launch.",
            "Post-event follow-up involves sending attendee surveys, processing lead lists for sales, and publishing recorded sessions on our YouTube channel."
        ]
    ),
    "Conversion Rate Optimization (CRO) Strategy": (
        "Marketing", 2, [
            "This strategy aims to increase the percentage of website visitors who sign up for a trial. We will perform A/B tests on key landing pages.",
            "Tests include simplifying sign-up forms, adding customer testimonials, implementing exit-intent popups, and testing different CTA button colors.",
            "Analytics tools will track user behavior, heatmaps, and funnel drop-offs. Successful variations will be implemented sitewide."
        ]
    ),
    "Affiliate and Partner Marketing Guidelines": (
        "Marketing", 1, [
            "These guidelines govern our affiliate program. Affiliates earn a commission for referring paying customers to our platform.",
            "Affiliates must use pre-approved creative assets and tracking links. Self-referrals and bidding on trademarked search terms are strictly prohibited.",
            "Commission payouts are processed monthly, subject to a minimum threshold. Violation of guidelines results in immediate termination from the program."
        ]
    ),
    "Paid Advertising Budget Allocation Recommendations": (
        "Marketing", 3, [
            "Highly Confidential: This document recommends our paid ad budget allocation for the next fiscal year. The proposed budget is $500,000.",
            "We recommend allocating 50% to Google Search Ads (targeting high-intent keywords), 30% to LinkedIn (targeting enterprise buyers), and 20% to retargeting.",
            "Performance will be monitored weekly, shifting budget from low-performing campaigns to maximize conversion efficiency and return on ad spend."
        ]
    ),

    # --- FINANCE (12 documents) ---
    "Annual Budget Planning Guidelines": (
        "Finance", 2, [
            "This guide assists department heads in preparing their annual budget requests. Requests must align with company strategic objectives.",
            "Budgets must itemize personnel costs, software licenses, travel, and operational expenses. Growth projections must be supported by historical data.",
            "Completed budget templates must be submitted to the finance department by October 31st for consolidation and executive board review."
        ]
    ),
    "Employee Expense Reporting and Reimbursement Rules": (
        "Finance", 1, [
            "This policy outlines rules for business expense reimbursement. Expenses must be business-related, reasonable, and pre-approved when required.",
            "Receipts are mandatory for all transactions. Expense reports must be submitted through the finance portal within 30 days of the transaction date.",
            "Non-reimbursable items include personal expenses, fine upgrades, and alcohol (except for approved client entertainment events)."
        ]
    ),
    "Travel Policy and Accommodation Allowances": (
        "Finance", 1, [
            "Our travel policy establishes guidelines for business travel. Travel must be booked through the company's approved booking tool.",
            "Daily accommodation allowances are capped by city tier: $150/night for Tier 2 and $250/night for Tier 1 cities (e.g., New York, London).",
            "Flights under 6 hours must be booked in economy class. Upgrades are allowed at the employee's personal expense."
        ]
    ),
    "Revenue Forecast and Q3 Financial Planning": (
        "Finance", 3, [
            "Highly Confidential: This forecast estimates our Q3 revenue and financial performance. We project a 12% quarter-over-quarter revenue growth.",
            "Growth is driven by expansion in our enterprise client base and upsells from existing customers. Operating margins are expected to improve by 3%.",
            "Risks to our forecast include delayed product features and competitive pricing pressure. Mitigation strategies are detailed in the appendix."
        ]
    ),
    "External Audit Preparations and Checklists": (
        "Finance", 2, [
            "This checklist prepares the finance team for the upcoming annual external audit. Organization of documentation ensures a smooth process.",
            "Key tasks include reconciling all bank accounts, preparing tax provisions, compiling asset registers, and documenting internal control reviews.",
            "Auditors will be provided workspace access. All audit queries must be routed through the finance controller to ensure consistent responses."
        ]
    ),
    "Monthly Payroll Processing Schedule": (
        "Finance", 2, [
            "This document establishes the monthly payroll processing timeline. Payroll is processed on the 25th of each month (or prior Friday if weekend).",
            "Managers must approve timesheets and commission calculations by the 20th. HR must submit employee change data by the 18th.",
            "Direct deposits are initiated on the 23rd. Pay slips are available in the employee self-service portal on payment day."
        ]
    ),
    "Procurement Workflow and Vendor Approvals": (
        "Finance", 2, [
            "All purchases exceeding $5,000 must follow the formal procurement process. This workflow ensures compliance and cost management.",
            "A purchase request must be submitted with three competitive bids. Once approved, a formal purchase order (PO) is issued to the vendor.",
            "Invoices must reference the PO number and be verified by the purchasing department before finance processes payment."
        ]
    ),
    "Corporate Tax Filing Instructions": (
        "Finance", 3, [
            "Highly Confidential: This manual outlines the procedures for preparing and filing corporate tax returns. We comply with all federal and state tax laws.",
            "Key filing steps include determining taxable income, calculating R&D tax credits, completing tax schedules, and obtaining executive sign-off.",
            "Returns must be submitted to the IRS by the statutory deadline. Electronic filing confirmations must be archived securely in the finance vault."
        ]
    ),
    "Equity Grant and Stock Option Guidelines": (
        "Finance", 3, [
            "Highly Confidential: This document outlines the equity compensation guidelines for new hires and promotion grants.",
            "Stock options vest over 4 years with a 1-year cliff. Options expire 10 years from the grant date or 90 days after termination of service.",
            "Board approval is required for all equity grants. Valuations are based on the latest independent 409A appraisal."
        ]
    ),
    "Strategic Capital Investment Opportunities": (
        "Finance", 3, [
            "Highly Confidential: This report evaluates three strategic capital investment opportunities to expand our database infrastructure.",
            "Options include expanding local data centers (high initial cost, full control), migrating to bare-metal cloud host (moderate cost), or hybrid setup.",
            "We recommend the hybrid setup due to optimal ROI, low risk, and scalability. Financial models are detailed in the attached spreadsheet."
        ]
    ),
    "Cost Optimization and Cloud Resource Savings": (
        "Finance", 2, [
            "This strategy aims to reduce cloud infrastructure costs by 15% without impacting application reliability.",
            "Key recommendations include purchasing reserved instances, configuring autoscaling to match demand patterns, and shutting down unused staging resources.",
            "Monthly reports will track cloud spend by department. Savings will be reinvested in product research and development."
        ]
    ),
    "Vendor Payment Procedures and Wire Transfers": (
        "Finance", 2, [
            "This procedure details the steps for processing vendor payments and wire transfers. Security checks prevent unauthorized disbursements.",
            "Dual authorization is required for all wire transfers exceeding $10,000. Banking details must be verified directly with the vendor.",
            "Payments are processed on a weekly schedule (Thursdays). Exception requests require written authorization from the CFO."
        ]
    )
}

def seed():
    print("Initializing database...")
    init_db()
    
    print("Seeding mock Confluence documents (50 total)...")
    count = 0
    for title, (dept, clearance, paragraphs) in MOCK_CONFLUENCE_DATA.items():
        doc = {
            "source": "confluence",
            "title": title,
            "content": "\n\n".join(paragraphs),
            "department": dept,
            "clearance_level": clearance
        }
        try:
            insert_document(doc)
            count += 1
            print(f"[{count}/50] Indexed: '{title}' (Dept: {dept}, Clearance: {clearance})")
        except Exception as e:
            print(f"Error seeding doc '{title}': {e}")
            sys.exit(1)
            
    print("\nDatabase seeding completed successfully.")

if __name__ == "__main__":
    seed()
