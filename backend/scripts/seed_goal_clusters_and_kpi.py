"""
Seed script: Goal Clusters and Universal KPI Library

This script populates goal_clusters and extends kpi_library with
cross-functional templates for all business functions:
- Sales, HR, Product, Editorial, Operations, Finance, 
- Marketing, Customer Success, Engineering, Legal, Data/Analytics

Run: PYTHONPATH=. python scripts/seed_goal_clusters_and_kpi.py
"""

import asyncio
from uuid import uuid4
from sqlalchemy import select, delete
from app.database import async_session_maker
from app.models import GoalCluster, KPILibrary


# Universal goal clusters (not hardcoded by role)
GOAL_CLUSTERS = [
    {
        "cluster_name": "Revenue Growth",
        "cluster_category": "Business Performance",
        "description": "Goals focused on increasing revenue, ARR, or deal size",
        "applicable_functions": ["Sales", "Business Development", "Account Management", "Leadership"],
    },
    {
        "cluster_name": "Talent Acquisition",
        "cluster_category": "People Management",
        "description": "Goals for hiring, recruiting, and building teams",
        "applicable_functions": ["HR", "Recruiting", "Operations", "Leadership"],
    },
    {
        "cluster_name": "Product Delivery",
        "cluster_category": "Execution",
        "description": "Goals for shipping features, roadmap execution, and releases",
        "applicable_functions": ["Product", "Engineering", "Design", "Leadership"],
    },
    {
        "cluster_name": "Customer Success",
        "cluster_category": "Customer Experience",
        "description": "Goals for customer satisfaction, retention, and NPS",
        "applicable_functions": ["Customer Success", "Support", "Sales", "Product"],
    },
    {
        "cluster_name": "Content & Marketing",
        "cluster_category": "Brand & Awareness",
        "description": "Goals for content creation, campaigns, and brand building",
        "applicable_functions": ["Marketing", "Editorial", "Social Media", "Communications"],
    },
    {
        "cluster_name": "Technical Excellence",
        "cluster_category": "Quality & Performance",
        "description": "Goals for code quality, reliability, performance, and architecture",
        "applicable_functions": ["Engineering", "DevOps", "QA", "Data Science"],
    },
    {
        "cluster_name": "Process Optimization",
        "cluster_category": "Operations",
        "description": "Goals for efficiency, automation, and cost reduction",
        "applicable_functions": ["Operations", "Finance", "Admin", "Data Science"],
    },
    {
        "cluster_name": "Compliance & Risk",
        "cluster_category": "Governance",
        "description": "Goals for legal, compliance, security, and audit",
        "applicable_functions": ["Legal", "Finance", "Security", "Admin"],
    },
    {
        "cluster_name": "Employee Development",
        "cluster_category": "People Management",
        "description": "Goals for training, mentoring, and skill development",
        "applicable_functions": ["HR", "Management", "Leadership", "Education"],
    },
    {
        "cluster_name": "User Engagement",
        "cluster_category": "Product Metrics",
        "description": "Goals for DAU, MAU, engagement, and user retention",
        "applicable_functions": ["Product", "Engineering", "Data Science", "Analytics"],
    },
    {
        "cluster_name": "Strategic Planning",
        "cluster_category": "Strategic Direction",
        "description": "Goals for planning, roadmaps, and strategic initiatives",
        "applicable_functions": ["Leadership", "Strategy", "Product", "Finance"],
    },
]


# Universal KPI Library (all 11 functions)
KPI_LIBRARY_ENTRIES = [
    # SALES FUNCTION (6 goals)
    ("Sales Executive", "Sales", "Revenue Growth", "Achieve quarterly revenue target", "Meet or exceed assigned revenue quota", "Revenue closed", "₹X Cr per quarter", 25.0, "MBO"),
    ("Sales Executive", "Sales", "Pipeline Management", "Build qualified sales pipeline", "Maintain 3x pipeline coverage ratio", "Pipeline value", "3x quota", 20.0, "MBO"),
    ("Account Manager", "Sales", "Customer Retention", "Achieve client retention rate", "Retain existing clients and reduce churn", "Retention rate", "95%+", 30.0, "MBO"),
    ("Sales Executive", "Sales", "Deal Velocity", "Reduce sales cycle length", "Close deals faster than target", "Average deal cycle", "< 45 days", 15.0, "OKR"),
    ("Business Development", "Sales", "Partner Expansion", "Develop strategic partnerships", "Build new revenue channels via partnerships", "New partners enabled", "X partners per quarter", 20.0, "OKR"),
    ("Sales Manager", "Sales", "Team Performance", "Manage team quota achievement", "Ensure team meets monthly/quarterly targets", "Team quota %", "100%+ attainment", 25.0, "MBO"),

    # HR FUNCTION (7 goals)
    ("HR Business Partner", "HR", "Talent Acquisition", "Meet hiring targets for BU", "Close open positions within SLA", "Positions closed", "X hires per quarter", 25.0, "OKR"),
    ("Recruiter", "HR", "Quality of Hire", "Hire top-quality candidates", "Focus on retention and performance of new hires", "QoH score", "8/10+ average", 30.0, "OKR"),
    ("HR Executive", "HR", "Engagement & Culture", "Improve employee engagement", "Drive engagement programs and survey scores", "eNPS score", "> 50", 20.0, "OKR"),
    ("HR Business Partner", "HR", "Attrition Management", "Reduce voluntary attrition", "Implement retention initiatives", "Attrition rate", "< 12% annually", 20.0, "OKR"),
    ("L&D Manager", "HR", "Learning & Development", "Deploy training programs", "Increase skill adoption and employee growth", "Training hours per employee", "> 40 hours/year", 25.0, "OKR"),
    ("HR Analyst", "HR", "Data & Reporting", "Deliver accurate HR metrics", "Provide timely insights for business decisions", "Reports delivered on-time %", "100%", 15.0, "MBO"),
    ("People Manager", "HR", "Team Development", "Develop direct reports", "Give feedback, coaching, and growth opportunities", "Promotion/growth rate", "> 20% per year", 25.0, "OKR"),

    # PRODUCT FUNCTION (6 goals)
    ("Product Manager", "Product", "Product Delivery", "Ship product roadmap on time", "Deliver committed features each sprint", "Features shipped", "X per quarter", 30.0, "OKR"),
    ("Product Manager", "Product", "User Metrics", "Improve product engagement metrics", "Drive DAU, retention, NPS", "DAU/MAU ratio", "> 40%", 25.0, "OKR"),
    ("Product Designer", "Product", "Design Quality", "Deliver high-quality designs", "Create intuitive, accessible user interfaces", "Design QA score", "> 9/10", 25.0, "MBO"),
    ("Product Manager", "Product", "Roadmap Planning", "Align roadmap with strategy", "Ensure features map to business goals", "Alignment score", "100%", 20.0, "OKR"),
    ("UX Researcher", "Product", "User Research", "Gather user insights", "Conduct research that informs product decisions", "Research insights delivered", "X per quarter", 25.0, "MBO"),
    ("Product Analyst", "Product", "Analytics & Insights", "Provide product analytics", "Track KPIs and provide actionable insights", "Dashboard accuracy", "100%", 20.0, "MBO"),

    # EDITORIAL / CONTENT FUNCTION (5 goals)
    ("Content Writer", "Editorial", "Content Output", "Publish high-quality content pieces", "Meet content calendar targets", "Articles published", "X per month", 25.0, "MBO"),
    ("Editor", "Editorial", "Content Quality", "Maintain content quality standards", "Ensure zero factual errors, strong engagement", "Quality score", "> 8/10 peer review", 20.0, "MBO"),
    ("Content Manager", "Editorial", "Content Strategy", "Execute content strategy", "Align content with business objectives", "Strategy alignment %", "100%", 25.0, "OKR"),
    ("Copywriter", "Editorial", "Copywriting Excellence", "Create compelling copy", "Maximize engagement and conversions", "Engagement rate", "> 5%", 20.0, "MBO"),
    ("Content Producer", "Editorial", "Multimedia Production", "Produce multimedia content", "Create videos, graphics, and interactive content", "Assets produced", "X per quarter", 25.0, "MBO"),

    # OPERATIONS FUNCTION (6 goals)
    ("Operations Manager", "Operations", "Process Efficiency", "Improve operational efficiency", "Reduce manual effort and processing time", "Process cycle time reduction", "30% reduction", 25.0, "OKR"),
    ("Operations Analyst", "Operations", "SLA Compliance", "Meet service level agreements", "Ensure all processes meet defined SLAs", "SLA compliance rate", "> 98%", 25.0, "MBO"),
    ("Operations Lead", "Operations", "Cost Optimization", "Optimize operational costs", "Identify and implement cost-saving initiatives", "Cost savings", "₹X per quarter", 20.0, "OKR"),
    ("Office Manager", "Operations", "Vendor Management", "Manage vendor relationships", "Maintain vendor quality and SLAs", "Vendor satisfaction score", "> 8/10", 15.0, "MBO"),
    ("Operations Engineer", "Operations", "Systems Reliability", "Ensure infrastructure reliability", "Maintain uptime and system performance", "Uptime %", "> 99.5%", 30.0, "OKR"),
    ("Process Analyst", "Operations", "Process Optimization", "Streamline business processes", "Identify bottlenecks and implement improvements", "Process improvements", "X per quarter", 20.0, "MBO"),

    # FINANCE FUNCTION (6 goals)
    ("Finance Manager", "Finance", "Budget Control", "Manage departmental budget", "Control costs and optimize spending", "Budget variance", "< 5%", 30.0, "MBO"),
    ("Finance Analyst", "Finance", "Financial Reporting", "Deliver accurate financial reports on time", "Zero errors in financial reporting", "Report accuracy %", "100%", 20.0, "MBO"),
    ("Accountant", "Finance", "Accounts Reconciliation", "Reconcile accounts accurately", "Maintain accurate financial records", "Reconciliation variance %", "< 1%", 25.0, "MBO"),
    ("Finance Manager", "Finance", "Cash Flow Management", "Optimize cash flow", "Maintain healthy liquidity and cash reserves", "Cash conversion cycle", "X days", 25.0, "OKR"),
    ("Tax Specialist", "Finance", "Tax Compliance", "Ensure tax compliance", "File accurate tax returns and manage tax risks", "Compliance rate %", "100%", 20.0, "MBO"),
    ("Finance Director", "Finance", "Financial Planning", "Drive financial planning initiatives", "Support strategic planning with financial insights", "Planning accuracy %", "> 90%", 25.0, "OKR"),

    # MARKETING FUNCTION (6 goals)
    ("Marketing Manager", "Marketing", "Lead Generation", "Generate qualified leads for sales", "Drive MQL targets through campaigns", "MQLs generated", "X per quarter", 25.0, "OKR"),
    ("Marketing Analyst", "Marketing", "Campaign ROI", "Achieve positive campaign ROI", "Optimize marketing spend efficiency", "Campaign ROAS", "> 3x", 20.0, "OKR"),
    ("Content Marketing Manager", "Marketing", "Content Marketing", "Drive content marketing initiatives", "Create content that generates leads and engagement", "Website traffic from content", "X% growth", 25.0, "OKR"),
    ("Social Media Manager", "Marketing", "Social Engagement", "Grow social media presence", "Increase followers, engagement, and brand awareness", "Social engagement rate", "> 3%", 20.0, "MBO"),
    ("Marketing Operations", "Marketing", "Marketing Automation", "Implement marketing automation", "Streamline marketing processes and improve efficiency", "Process automation %", "X%", 20.0, "OKR"),
    ("Brand Manager", "Marketing", "Brand Building", "Build brand equity", "Execute brand initiatives and increase brand value", "Brand awareness %", "X% growth", 25.0, "OKR"),

    # CUSTOMER SUCCESS FUNCTION (6 goals)
    ("Customer Success Manager", "Customer Success", "Customer NPS", "Improve Net Promoter Score", "Drive customer satisfaction initiatives", "NPS score", "> 50", 25.0, "OKR"),
    ("Customer Success Manager", "Customer Success", "Account Expansion", "Drive account expansion revenue", "Upsell and cross-sell to existing customers", "Expansion ARR", "₹X per quarter", 20.0, "MBO"),
    ("Support Manager", "Customer Success", "Support Quality", "Maintain high support quality", "Ensure customer issues resolved quickly and satisfactorily", "CSAT score", "> 90%", 25.0, "MBO"),
    ("Customer Success Manager", "Customer Success", "Churn Reduction", "Reduce customer churn", "Implement retention initiatives", "Churn rate", "< 5%", 30.0, "OKR"),
    ("Onboarding Specialist", "Customer Success", "Customer Onboarding", "Deliver successful customer onboarding", "Ensure smooth customer activation and time-to-value", "Onboarding completion %", "> 95%", 20.0, "MBO"),
    ("CS Manager", "Customer Success", "Customer Health", "Maintain healthy customer base", "Proactively manage customer relationships", "Health score average", "> 8/10", 25.0, "OKR"),

    # ENGINEERING FUNCTION (7 goals - balanced with other functions)
    ("Software Engineer", "Engineering", "Technical Delivery", "Complete sprint commitments", "Deliver assigned stories on time with quality", "Sprint velocity", "> 85% completion", 25.0, "OKR"),
    ("Software Engineer", "Engineering", "Code Quality", "Maintain high code quality", "Reduce technical debt and bugs", "Bug rate", "< 2 critical per sprint", 20.0, "OKR"),
    ("Senior Engineer", "Engineering", "System Design", "Design scalable systems", "Create robust architecture for growth", "Design quality score", "> 9/10", 25.0, "OKR"),
    ("Engineering Manager", "Engineering", "Engineering Velocity", "Improve team velocity", "Increase delivery capacity and efficiency", "Velocity trend", "X% growth", 20.0, "OKR"),
    ("QA Engineer", "Engineering", "Test Coverage", "Maintain high test coverage", "Ensure comprehensive test automation", "Test coverage %", "> 85%", 25.0, "OKR"),
    ("DevOps Engineer", "Engineering", "Infrastructure Reliability", "Ensure infrastructure uptime", "Maintain stable, scalable infrastructure", "Uptime %", "> 99.9%", 30.0, "OKR"),
    ("Tech Lead", "Engineering", "Technical Leadership", "Lead engineering initiatives", "Mentor engineers and drive technical excellence", "Team growth", "X engineers developed", 25.0, "MBO"),

    # LEGAL FUNCTION (4 goals)
    ("Legal Counsel", "Legal", "Compliance Management", "Ensure legal compliance", "Maintain company compliance with regulations", "Compliance rate %", "100%", 25.0, "MBO"),
    ("Contracts Manager", "Legal", "Contract Management", "Manage legal contracts", "Negotiate and execute contracts efficiently", "Contracts processed", "X per quarter", 20.0, "MBO"),
    ("Legal Director", "Legal", "Risk Management", "Manage legal risks", "Identify and mitigate legal risks", "Risk mitigation %", "> 95%", 25.0, "OKR"),
    ("Paralegal", "Legal", "Legal Documentation", "Maintain accurate legal records", "Ensure all documentation is accurate and complete", "Documentation accuracy %", "100%", 15.0, "MBO"),

    # DATA & ANALYTICS FUNCTION (6 goals)
    ("Data Scientist", "Analytics", "Model Development", "Build predictive models", "Create models that drive business insights", "Model accuracy", "> 85%", 25.0, "OKR"),
    ("Data Analyst", "Analytics", "Data Pipeline", "Build and maintain data pipelines", "Ensure data quality and accessibility", "Pipeline uptime %", "> 99%", 25.0, "OKR"),
    ("Analytics Engineer", "Analytics", "Analytics Infrastructure", "Develop analytics infrastructure", "Build tools and systems for analytics", "Infrastructure reliability %", "> 99%", 25.0, "OKR"),
    ("BI Manager", "Analytics", "Business Intelligence", "Drive BI initiatives", "Create dashboards and reports that drive decisions", "Dashboard accuracy %", "100%", 20.0, "OKR"),
    ("Data Scientist", "Analytics", "Data Insights", "Generate actionable data insights", "Provide insights that drive business decisions", "Insights delivered", "X per quarter", 25.0, "MBO"),
    ("Analytics Manager", "Analytics", "Analytics Quality", "Maintain analytics quality standards", "Ensure accuracy and reliability of all analytics", "Quality score", "> 9/10", 20.0, "MBO"),

    # DESIGN FUNCTION (5 goals)
    ("UX/UI Designer", "Design", "Design Excellence", "Create excellent user experiences", "Build intuitive, accessible interfaces", "Design quality score", "> 9/10", 25.0, "MBO"),
    ("Design Manager", "Design", "Design System", "Develop and maintain design system", "Create consistent design standards and components", "System coverage %", "> 90%", 25.0, "OKR"),
    ("Product Designer", "Design", "User-Centric Design", "Ensure user-centric design approach", "Conduct user research and testing", "User satisfaction %", "> 85%", 25.0, "OKR"),
    ("Interaction Designer", "Design", "Interaction Design", "Create smooth interactions", "Design intuitive user interactions and flows", "Interaction quality score", "> 8/10", 20.0, "MBO"),
    ("Design Researcher", "Design", "Design Research", "Conduct design research", "Gather user insights for design decisions", "Research insights delivered", "X per quarter", 20.0, "MBO"),
]


async def seed_goal_clusters():
    """Seed goal_clusters table with universal clusters."""
    async with async_session_maker() as session:
        # Check if already seeded
        existing = await session.execute(select(GoalCluster).limit(1))
        if existing.scalars().first():
            print("✓ Goal clusters already seeded")
            return

        for cluster_data in GOAL_CLUSTERS:
            cluster = GoalCluster(
                id=str(uuid4()),
                cluster_name=cluster_data["cluster_name"],
                cluster_category=cluster_data["cluster_category"],
                description=cluster_data["description"],
                applicable_functions=cluster_data["applicable_functions"],
                is_ai_generated=True,
            )
            session.add(cluster)

        await session.commit()
        print(f"✓ Seeded {len(GOAL_CLUSTERS)} goal clusters")


async def seed_kpi_library():
    """Seed kpi_library table with universal KPI entries."""
    async with async_session_maker() as session:
        # Count existing entries
        existing = await session.execute(select(KPILibrary).limit(1))
        existing_count = len(existing.scalars().all())
        
        # If we have very few entries, reseed
        if existing_count > 50:
            print(f"✓ KPI library already seeded with {existing_count} entries")
            return

        # Clear old entries if less than expected
        if existing_count > 0:
            await session.execute(delete(KPILibrary))
            print("Cleared old KPI library entries")

        # Insert all KPI entries
        for entry in KPI_LIBRARY_ENTRIES:
            kpi = KPILibrary(
                id=str(uuid4()),
                role=entry[0],
                domain=entry[1],
                department=entry[2],
                goal_title=entry[3],
                goal_description=entry[4],
                suggested_kpi=entry[5],
                suggested_weight=entry[7],
                framework=entry[8],
            )
            session.add(kpi)

        await session.commit()
        print(f"✓ Seeded {len(KPI_LIBRARY_ENTRIES)} KPI library entries across 11 functions")


async def main():
    print("🌱 Seeding goal clusters and universal KPI library...")
    await seed_goal_clusters()
    await seed_kpi_library()
    print("\n✨ Seed complete!")


if __name__ == "__main__":
    asyncio.run(main())
