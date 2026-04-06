from __future__ import annotations

import asyncio
import random
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.checkin import Checkin
from app.models.employee import Employee
from app.models.enums import CheckinStatus, GoalFramework, GoalStatus, RatingLabel, UserRole
from app.models.goal import Goal
from app.models.organization import Organization
from app.models.performance_review import PerformanceReview
from app.models.rating import Rating
from app.models.user import User

SEED = 42042
ORG_DOMAIN = "structured.mock"
ORG_NAME = "Structured Mock Organization"

FEEDBACK_COMMENTS = [
    "Great collaboration",
    "Needs improvement in deadlines",
    "Excellent problem solving",
    "Very proactive during sprint execution",
    "Could improve communication clarity",
]

CHECKIN_SNIPPETS = [
    "Discussed progress and unblocked current sprint items.",
    "Reviewed delivery quality and aligned on next-week priorities.",
    "Captured dependency risks and mitigation actions.",
    "Validated milestone completion and updated execution plan.",
]

GOAL_TEMPLATES = [
    "Improve delivery quality",
    "Reduce production defects",
    "Increase sprint predictability",
    "Improve stakeholder communication",
    "Strengthen testing coverage",
    "Optimize workflow efficiency",
]


def _roles_for_user(role: UserRole) -> list[str]:
    if role == UserRole.manager:
        return [UserRole.employee.value, UserRole.manager.value]
    return [role.value]


def _rating_label_from_roll(roll: float) -> RatingLabel:
    # Distribution target:
    # EE 10%, DE 25%, ME 40%, SME 15%, NI 10%
    if roll < 0.10:
        return RatingLabel.EE
    if roll < 0.35:
        return RatingLabel.DE
    if roll < 0.75:
        return RatingLabel.ME
    if roll < 0.90:
        return RatingLabel.SME
    return RatingLabel.NI


def _rating_score(label: RatingLabel) -> int:
    if label == RatingLabel.EE:
        return 5
    if label == RatingLabel.DE:
        return 4
    if label == RatingLabel.ME:
        return 3
    if label == RatingLabel.SME:
        return 2
    return 1


def _progress_value(rng: random.Random) -> float:
    # Ensure low/medium/high spread.
    bucket = rng.choices(
        population=["high", "medium", "low"],
        weights=[0.30, 0.40, 0.30],
        k=1,
    )[0]
    if bucket == "high":
        return round(rng.uniform(80, 100), 1)
    if bucket == "medium":
        return round(rng.uniform(40, 70), 1)
    return round(rng.uniform(0, 39), 1)


async def _table_exists(db: AsyncSession, table_name: str) -> bool:
    q = text(
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = :table_name
        )
        """
    )
    result = await db.execute(q, {"table_name": table_name})
    return bool(result.scalar())


async def _truncate_for_reseed(db: AsyncSession) -> bool:
    # Requested clear order, plus additional related tables present in this schema.
    ordered_tables = [
        "peer_feedback",
        "ratings",
        "checkins",
        "goals",
        "goal_contributions",
        "performance_reviews",
        "meetings",
        "ai_usage_logs",
        "ai_usage",
        "employees",
        "users",
        "performance_cycles",
        "organizations",
    ]

    existing_tables: list[str] = []
    peer_feedback_exists = False
    for table_name in ordered_tables:
        exists = await _table_exists(db, table_name)
        if exists:
            existing_tables.append(table_name)
        if table_name == "peer_feedback":
            peer_feedback_exists = exists

    for table_name in existing_tables:
        await db.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))

    return peer_feedback_exists


async def reseed() -> None:
    rng = random.Random(SEED)

    async with AsyncSessionLocal() as db:
        peer_feedback_exists = await _truncate_for_reseed(db)

        org = Organization(id=uuid4(), name=ORG_NAME, domain=ORG_DOMAIN)
        db.add(org)
        await db.flush()

        # Core users
        executive_lead = User(
            id=uuid4(),
            google_id=f"seed-leadership-root-{uuid4()}",
            email="executive@structured.mock",
            name="Arjun Mehta",
            profile_picture=None,
            role=UserRole.leadership,
            roles=_roles_for_user(UserRole.leadership),
            organization_id=org.id,
            manager_id=None,
            department="Executive",
            title="Executive Director",
            is_active=True,
        )
        db.add(executive_lead)
        await db.flush()

        leadership = User(
            id=uuid4(),
            google_id=f"seed-leadership-{uuid4()}",
            email="leadership@structured.mock",
            name="Devansh Malhotra",
            profile_picture=None,
            role=UserRole.leadership,
            roles=_roles_for_user(UserRole.leadership),
            organization_id=org.id,
            manager_id=executive_lead.id,
            department="Executive",
            title="Business Head",
            is_active=True,
        )
        db.add(leadership)

        hr = User(
            id=uuid4(),
            google_id=f"seed-hr-{uuid4()}",
            email="hr@structured.mock",
            name="Nisha Verma",
            profile_picture=None,
            role=UserRole.hr,
            roles=_roles_for_user(UserRole.hr),
            organization_id=org.id,
            manager_id=executive_lead.id,
            department="HR",
            title="HRBP",
            is_active=True,
        )
        db.add(hr)
        await db.flush()

        # 5 managers under leadership
        manager_specs = [
            ("Priya Iyer", "Engineering", "Engineering Manager I"),
            ("Karan Shah", "Engineering", "Engineering Manager II"),
            ("Meera Nair", "Sales", "Sales Manager"),
            ("Vikram Sethi", "HR Ops", "HR Ops Manager"),
            ("Ananya Roy", "Product", "Product Manager"),
        ]

        managers: list[User] = []
        for idx, (name, department, title) in enumerate(manager_specs, start=1):
            manager = User(
                id=uuid4(),
                google_id=f"seed-manager-{idx}-{uuid4()}",
                email=f"manager{idx:02d}@structured.mock",
                name=name,
                profile_picture=None,
                role=UserRole.manager,
                roles=_roles_for_user(UserRole.manager),
                organization_id=org.id,
                manager_id=leadership.id,
                department=department,
                title=title,
                is_active=True,
            )
            db.add(manager)
            managers.append(manager)
        await db.flush()

        # 50 employees: 10 per manager
        role_titles = [
            "Backend Developer",
            "Frontend Developer",
            "QA Engineer",
            "Sales Executive",
        ]
        first_names = [
            "Shiv", "Ritika", "Ankit", "Pooja", "Neha", "Rohan", "Isha", "Tarun", "Aayushi", "Yash",
            "Kavya", "Gaurav", "Simran", "Aditya", "Shruti", "Manav", "Tanvi", "Armaan", "Sana", "Amit",
            "Preeti", "Sakshi", "Ritesh", "Vani", "Kunal", "Mihir", "Diya", "Nitin", "Pallavi", "Radhika",
            "Karthik", "Sonia", "Pranav", "Esha", "Naveen", "Bhavna", "Arpit", "Irfan", "Mona", "Harshit",
            "Rahul", "Aisha", "Dev", "Manya", "Vikas", "Reema", "Alok", "Nisha", "Kabir", "Sneha",
        ]
        last_names = [
            "Menon", "Das", "Jain", "Rana", "Kulkarni", "Batra", "Chawla", "Arora", "Gupta", "Patil",
            "Sen", "Khanna", "Kaur", "Joshi", "Mishra", "Ahuja", "Rao", "Gill", "Qureshi", "Bhosale",
            "Nanda", "Sethi", "Kumar", "Shetty", "Grover", "Anand", "Narang", "Suri", "Iyer", "Reddy",
            "Malhotra", "Pillai", "Kapur", "Verma", "Sheikh", "Luthra", "Kapoor", "Khan", "Roy", "Tandon",
            "Bhatia", "Shah", "Naik", "Basu", "Yadav", "Chopra", "Agrawal", "Tripathi", "Singh", "Pandey",
        ]

        employees: list[User] = []
        employee_counter = 1
        for manager in managers:
            for _ in range(10):
                full_name = f"{first_names[employee_counter - 1]} {last_names[employee_counter - 1]}"
                title = role_titles[(employee_counter - 1) % len(role_titles)]

                # Keep department mostly aligned to manager's domain.
                if manager.department == "Sales":
                    title = "Sales Executive"
                elif manager.department == "HR Ops":
                    title = "QA Engineer" if employee_counter % 2 == 0 else "Frontend Developer"
                elif manager.department == "Product":
                    title = "Frontend Developer" if employee_counter % 2 == 0 else "Backend Developer"

                employee = User(
                    id=uuid4(),
                    google_id=f"seed-employee-{employee_counter:03d}-{uuid4()}",
                    email=f"employee{employee_counter:02d}@structured.mock",
                    name=full_name,
                    profile_picture=None,
                    role=UserRole.employee,
                    roles=_roles_for_user(UserRole.employee),
                    organization_id=org.id,
                    manager_id=manager.id,
                    department=manager.department,
                    title=title,
                    is_active=True,
                )
                db.add(employee)
                employees.append(employee)
                employee_counter += 1
        await db.flush()

        # Mirror users to employees table for employee-directory style modules.
        all_people = [executive_lead, leadership, hr, *managers, *employees]
        employee_rows: list[Employee] = []
        for idx, person in enumerate(all_people, start=1):
            employee_rows.append(
                Employee(
                    id=person.id,
                    employee_code=f"EMP{idx:03d}",
                    name=person.name,
                    email=person.email,
                    role=person.role,
                    title=person.title,
                    department=person.department,
                    manager_id=person.manager_id,
                    is_active=True,
                )
            )
        db.add_all(employee_rows)
        await db.flush()

        goals_by_employee: dict[str, list[Goal]] = defaultdict(list)

        # Goals: 3-5 per employee
        for employee in employees:
            total_goals = rng.randint(3, 5)
            for _ in range(total_goals):
                progress = _progress_value(rng)
                goal = Goal(
                    id=uuid4(),
                    user_id=employee.id,
                    assigned_by=employee.manager_id,
                    assigned_to=employee.id,
                    title=f"{rng.choice(GOAL_TEMPLATES)} - {employee.department}",
                    description="Deliver measurable improvements against quarterly priorities.",
                    weightage=round(rng.uniform(10, 40), 1),
                    status=GoalStatus.approved,
                    progress=progress,
                    framework=rng.choice([GoalFramework.OKR, GoalFramework.MBO, GoalFramework.Hybrid]),
                    is_ai_generated=rng.random() < 0.4,
                )
                db.add(goal)
                goals_by_employee[str(employee.id)].append(goal)
        await db.flush()

        # Unified check-ins: one per employee for the active seeded cycle
        now = datetime.now(timezone.utc)
        for employee in employees:
            employee_goals = goals_by_employee[str(employee.id)]
            average_progress = int(sum(float(goal.progress or 0) for goal in employee_goals) / max(len(employee_goals), 1))
            checkin = Checkin(
                id=uuid4(),
                cycle_id=None,
                goal_ids=[goal.id for goal in employee_goals],
                goal_updates=[
                    {
                        "goal_id": str(goal.id),
                        "progress": int(goal.progress or 0),
                        "note": "Seeded consolidated update",
                    }
                    for goal in employee_goals
                ],
                employee_id=employee.id,
                manager_id=employee.manager_id,
                meeting_date=now - timedelta(days=rng.randint(0, 14), hours=rng.randint(0, 23)),
                status=CheckinStatus.reviewed,
                meeting_link=None,
                transcript="Discussed weekly execution blockers and follow-up actions.",
                summary=rng.choice(CHECKIN_SNIPPETS),
                achievements="Delivered sprint milestones for assigned goals.",
                created_at=now - timedelta(days=rng.randint(0, 14)),
                overall_progress=average_progress,
                blockers="",
                confidence_level=rng.randint(3, 5),
            )
            db.add(checkin)
        await db.flush()

        # Ratings: 2-4 manager ratings per employee
        for employee in employees:
            total_ratings = rng.randint(2, 4)
            employee_goals = goals_by_employee[str(employee.id)]
            for _ in range(total_ratings):
                label = _rating_label_from_roll(rng.random())
                rating = Rating(
                    id=uuid4(),
                    goal_id=rng.choice(employee_goals).id,
                    manager_id=employee.manager_id,
                    employee_id=employee.id,
                    rating=_rating_score(label),
                    rating_label=label,
                    comments="Manager feedback: performance reviewed against agreed outcomes.",
                    created_at=now - timedelta(days=rng.randint(0, 90)),
                )
                db.add(rating)

        # Peer feedback: no dedicated table in current schema; store as additional ratings comments from peers.
        for manager in managers:
            team_members = [member for member in employees if member.manager_id == manager.id]
            for employee in team_members:
                total_peer_feedback = rng.randint(2, 5)
                peers = [peer for peer in team_members if peer.id != employee.id]
                if not peers:
                    continue
                employee_goals = goals_by_employee[str(employee.id)]
                for _ in range(total_peer_feedback):
                    peer_user = rng.choice(peers)
                    label = _rating_label_from_roll(rng.random())
                    db.add(
                        Rating(
                            id=uuid4(),
                            goal_id=rng.choice(employee_goals).id,
                            manager_id=peer_user.id,
                            employee_id=employee.id,
                            rating=_rating_score(label),
                            rating_label=label,
                            comments=f"Peer feedback: {rng.choice(FEEDBACK_COMMENTS)}",
                            created_at=now - timedelta(days=rng.randint(0, 90)),
                        )
                    )

        # Add one performance review row for each employee to improve analytics depth.
        for employee in employees:
            db.add(
                PerformanceReview(
                    id=uuid4(),
                    employee_id=employee.id,
                    manager_id=employee.manager_id,
                    cycle_year=2026,
                    cycle_quarter=1,
                    overall_rating=round(rng.uniform(2.0, 4.8), 2),
                    summary="Quarterly review summary with goal and behavior assessment.",
                    strengths="Collaboration, Ownership",
                    weaknesses="Prioritization under pressure",
                    growth_areas="Stakeholder communication, Risk management",
                    created_at=now - timedelta(days=rng.randint(0, 120)),
                )
            )

        await db.commit()

        # Validation queries requested by user.
        total_employees = (await db.execute(text("SELECT COUNT(*) FROM employees"))).scalar_one()
        manager_team_sizes = (
            await db.execute(
                text(
                    """
                    SELECT manager_id, COUNT(*) AS team_size
                    FROM employees
                    WHERE manager_id IS NOT NULL
                    GROUP BY manager_id
                    ORDER BY team_size DESC
                    """
                )
            )
        ).all()
        total_goals = (await db.execute(text("SELECT COUNT(*) FROM goals"))).scalar_one()

        print("Structured reseed complete.")
        print(f"peer_feedback_table_exists={peer_feedback_exists}")
        if not peer_feedback_exists:
            print("peer_feedback table not found; peer feedback stored in ratings.comments with 'Peer feedback:' prefix.")
        print(f"employees_count={total_employees}")
        print(f"goals_count={total_goals}")
        print("manager_team_distribution:")
        for manager_id, team_size in manager_team_sizes:
            print(f"  manager_id={manager_id} team_size={team_size}")


if __name__ == "__main__":
    asyncio.run(reseed())
