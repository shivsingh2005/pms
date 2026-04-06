from __future__ import annotations

import random
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.checkin import Checkin
from app.models.checkin_rating import CheckinRating
from app.models.employee import Employee
from app.models.enums import (
    CheckinStatus,
    GoalFramework,
    GoalStatus,
    MeetingStatus,
    MeetingType,
    PerformanceCycleStatus,
    RatingLabel,
    UserRole,
)
from app.models.goal import Goal
from app.models.meeting import Meeting
from app.models.performance_cycle import PerformanceCycle
from app.models.rating import Rating
from app.models.user import User


class ManagerSeedService:
    @staticmethod
    async def _ensure_employee_mirror_for_user(
        user: User,
        db: AsyncSession,
        *,
        manager_id=None,
        employee_code_prefix: str = "AUTO",
    ) -> None:
        existing_employee_result = await db.execute(select(Employee).where(Employee.id == user.id).limit(1))
        existing_employee = existing_employee_result.scalar_one_or_none()
        if existing_employee is not None:
            return

        db.add(
            Employee(
                id=user.id,
                employee_code=f"{employee_code_prefix}-{str(user.id)[:8]}",
                name=user.name,
                email=user.email,
                role=user.role,
                title=user.title,
                department=user.department,
                manager_id=manager_id,
                is_active=True,
            )
        )
        await db.flush()

    @staticmethod
    async def seed_manager_data(current_user: User, db: AsyncSession, team_size: int = 10) -> int:
        existing_team_result = await db.execute(
            select(User.id).where(
                User.manager_id == current_user.id,
                User.organization_id == current_user.organization_id,
                User.is_active.is_(True),
            )
        )
        existing_team_ids = list(existing_team_result.scalars().all())
        if existing_team_ids:
            return len(existing_team_ids)

        rng = random.Random(str(current_user.id))
        now = datetime.now(timezone.utc)

        cycle_result = await db.execute(
            select(PerformanceCycle)
            .where(
                PerformanceCycle.organization_id == current_user.organization_id,
                PerformanceCycle.is_active.is_(True),
            )
            .order_by(PerformanceCycle.start_date.desc())
            .limit(1)
        )
        cycle = cycle_result.scalar_one_or_none()
        if cycle is None:
            cycle = PerformanceCycle(
                organization_id=current_user.organization_id,
                name="Demo Manager Cycle",
                cycle_type="quarterly",
                framework="OKR",
                start_date=date.today().replace(day=1),
                end_date=date.today() + timedelta(days=90),
                goal_setting_deadline=date.today() + timedelta(days=10),
                self_review_deadline=date.today() + timedelta(days=80),
                checkin_cap_per_quarter=5,
                ai_usage_cap_per_quarter=3,
                is_active=True,
                status=PerformanceCycleStatus.active,
            )
            db.add(cycle)
            await db.flush()

        created_users: list[User] = []
        created_employee_rows: list[Employee] = []

        await ManagerSeedService._ensure_employee_mirror_for_user(
            current_user,
            db,
            manager_id=None,
            employee_code_prefix="MGR",
        )

        for idx in range(team_size):
            user = User(
                google_id=f"seed-mgr-{current_user.id}-{idx}-{uuid4()}",
                email=f"team{idx + 1}.{str(current_user.id)[:8]}@demo.pms",
                name=f"Team Member {idx + 1}",
                profile_picture=None,
                role=UserRole.employee,
                roles=[UserRole.employee.value],
                organization_id=current_user.organization_id,
                manager_id=current_user.id,
                department=current_user.department or "General",
                title="Software Engineer",
                is_active=True,
            )
            db.add(user)
            await db.flush()
            created_users.append(user)

            created_employee_rows.append(
                Employee(
                    id=user.id,
                    employee_code=f"DM{idx + 1:03d}",
                    name=user.name,
                    email=user.email,
                    role=user.role,
                    title=user.title,
                    department=user.department,
                    manager_id=current_user.id,
                    is_active=True,
                )
            )

        if created_employee_rows:
            db.add_all(created_employee_rows)
            await db.flush()

        for idx, employee in enumerate(created_users):
            progress = float(rng.randint(40, 100))
            consistency = float(rng.randint(50, 100))
            rating_score = int(rng.randint(1, 5))

            rating_label = RatingLabel.ME
            if rating_score >= 5:
                rating_label = RatingLabel.EE
            elif rating_score == 4:
                rating_label = RatingLabel.DE
            elif rating_score == 3:
                rating_label = RatingLabel.ME
            elif rating_score == 2:
                rating_label = RatingLabel.SME
            else:
                rating_label = RatingLabel.NI

            goal = Goal(
                cycle_id=cycle.id,
                user_id=employee.id,
                assigned_by=current_user.id,
                assigned_to=employee.id,
                title=f"Demo goal for {employee.name}",
                description="Seeded manager dashboard goal",
                weightage=round(100.0 / max(team_size, 1), 1),
                status=GoalStatus.approved,
                progress=progress,
                framework=GoalFramework.OKR,
                is_ai_generated=False,
            )
            db.add(goal)
            await db.flush()

            checkin = Checkin(
                cycle_id=cycle.id,
                goal_ids=[goal.id],
                goal_updates=[{"goal_id": str(goal.id), "progress": int(progress), "note": "Seeded update"}],
                employee_id=employee.id,
                manager_id=current_user.id,
                overall_progress=int(progress),
                status=CheckinStatus.reviewed if consistency >= 60 else CheckinStatus.submitted,
                meeting_link="https://meet.google.com/demo-seeded-meeting",
                meeting_date=now - timedelta(days=idx + 1),
                transcript="Seeded transcript",
                summary="Seeded check-in summary",
                achievements="Seeded achievements",
                blockers=None,
                confidence_level=4,
                manager_feedback="Keep up the momentum",
                created_at=now - timedelta(days=idx + 1),
            )
            db.add(checkin)
            await db.flush()

            meeting_start = now - timedelta(days=idx + 1, hours=1)
            meeting_end = meeting_start + timedelta(minutes=30)
            participants = [email for email in [employee.email, current_user.email] if email]
            meeting = Meeting(
                title=f"Weekly 1:1 - {employee.name}",
                cycle_id=cycle.id,
                description="Seeded manager dashboard meeting",
                organizer_id=current_user.id,
                checkin_id=checkin.id,
                employee_id=employee.id,
                manager_id=current_user.id,
                meeting_type=MeetingType.CHECKIN,
                goal_id=goal.id,
                start_time=meeting_start,
                end_time=meeting_end,
                google_event_id=f"seeded-{uuid4()}",
                meet_link="https://meet.google.com/demo-seeded-meeting",
                google_meet_link="https://meet.google.com/demo-seeded-meeting",
                participants=participants,
                status=MeetingStatus.completed,
            )
            db.add(meeting)

            rating = Rating(
                cycle_id=cycle.id,
                goal_id=goal.id,
                manager_id=current_user.id,
                employee_id=employee.id,
                rating=rating_score,
                rating_label=rating_label,
                comments="Seeded rating",
                created_at=now - timedelta(days=idx + 1),
            )
            db.add(rating)
            await db.flush()

            checkin_rating = CheckinRating(
                cycle_id=cycle.id,
                checkin_id=checkin.id,
                employee_id=employee.id,
                manager_id=current_user.id,
                rating=rating_score,
                feedback="Seeded check-in rating",
                created_at=now - timedelta(days=idx + 1),
            )
            db.add(checkin_rating)

        await db.commit()
        return len(created_users)

    @staticmethod
    async def seed_activity_for_existing_team(current_user: User, db: AsyncSession) -> int:
        rng = random.Random(f"activity-{current_user.id}")
        now = datetime.now(timezone.utc)

        team_result = await db.execute(
            select(User)
            .where(
                User.manager_id == current_user.id,
                User.organization_id == current_user.organization_id,
                User.is_active.is_(True),
            )
            .order_by(User.created_at.asc())
        )
        team_members = list(team_result.scalars().all())
        if not team_members:
            return 0

        await ManagerSeedService._ensure_employee_mirror_for_user(
            current_user,
            db,
            manager_id=None,
            employee_code_prefix="MGR",
        )

        for employee in team_members:
            await ManagerSeedService._ensure_employee_mirror_for_user(
                employee,
                db,
                manager_id=current_user.id,
                employee_code_prefix="EMP",
            )

        cycle_result = await db.execute(
            select(PerformanceCycle)
            .where(
                PerformanceCycle.organization_id == current_user.organization_id,
                PerformanceCycle.is_active.is_(True),
            )
            .order_by(PerformanceCycle.start_date.desc())
            .limit(1)
        )
        cycle = cycle_result.scalar_one_or_none()
        if cycle is None:
            cycle = PerformanceCycle(
                organization_id=current_user.organization_id,
                name="Demo Manager Cycle",
                cycle_type="quarterly",
                framework="OKR",
                start_date=date.today().replace(day=1),
                end_date=date.today() + timedelta(days=90),
                goal_setting_deadline=date.today() + timedelta(days=10),
                self_review_deadline=date.today() + timedelta(days=80),
                checkin_cap_per_quarter=5,
                ai_usage_cap_per_quarter=3,
                is_active=True,
                status=PerformanceCycleStatus.active,
            )
            db.add(cycle)
            await db.flush()

        seeded_count = 0
        for idx, employee in enumerate(team_members):
            goal_result = await db.execute(select(Goal).where(Goal.user_id == employee.id).limit(1))
            goal = goal_result.scalar_one_or_none()
            if goal is None:
                progress = float(rng.randint(40, 100))
                goal = Goal(
                    cycle_id=cycle.id,
                    user_id=employee.id,
                    assigned_by=current_user.id,
                    assigned_to=employee.id,
                    title=f"Seeded goal for {employee.name}",
                    description="Auto-seeded goal for manager dashboard consistency",
                    weightage=round(100.0 / max(len(team_members), 1), 1),
                    status=GoalStatus.approved,
                    progress=progress,
                    framework=GoalFramework.OKR,
                    is_ai_generated=False,
                )
                db.add(goal)
                await db.flush()
                seeded_count += 1

            checkin_result = await db.execute(select(Checkin).where(Checkin.employee_id == employee.id).limit(1))
            checkin = checkin_result.scalar_one_or_none()
            if checkin is None:
                progress = int(goal.progress if goal.progress else rng.randint(40, 100))
                checkin = Checkin(
                    cycle_id=cycle.id,
                    goal_ids=[goal.id],
                    goal_updates=[{"goal_id": str(goal.id), "progress": progress, "note": "Auto-seeded"}],
                    employee_id=employee.id,
                    manager_id=current_user.id,
                    overall_progress=progress,
                    status=CheckinStatus.reviewed,
                    meeting_link="https://meet.google.com/demo-seeded-meeting",
                    meeting_date=now - timedelta(days=idx + 1),
                    transcript="Seeded transcript",
                    summary="Seeded check-in summary",
                    achievements="Auto-seeded achievements",
                    blockers=None,
                    confidence_level=4,
                    manager_feedback="Keep up the momentum",
                    created_at=now - timedelta(days=idx + 1),
                )
                db.add(checkin)
                await db.flush()
                seeded_count += 1

            rating_result = await db.execute(select(Rating).where(Rating.employee_id == employee.id).limit(1))
            rating = rating_result.scalar_one_or_none()
            if rating is None:
                rating_score = int(rng.randint(1, 5))
                rating_label = RatingLabel.ME
                if rating_score >= 5:
                    rating_label = RatingLabel.EE
                elif rating_score == 4:
                    rating_label = RatingLabel.DE
                elif rating_score == 2:
                    rating_label = RatingLabel.SME
                elif rating_score == 1:
                    rating_label = RatingLabel.NI

                rating = Rating(
                    cycle_id=cycle.id,
                    goal_id=goal.id,
                    manager_id=current_user.id,
                    employee_id=employee.id,
                    rating=rating_score,
                    rating_label=rating_label,
                    comments="Auto-seeded rating",
                    created_at=now - timedelta(days=idx + 1),
                )
                db.add(rating)
                await db.flush()
                seeded_count += 1

            checkin_rating_result = await db.execute(select(CheckinRating).where(CheckinRating.employee_id == employee.id).limit(1))
            checkin_rating = checkin_rating_result.scalar_one_or_none()
            if checkin_rating is None:
                checkin_rating = CheckinRating(
                    cycle_id=cycle.id,
                    checkin_id=checkin.id,
                    employee_id=employee.id,
                    manager_id=current_user.id,
                    rating=rating.rating,
                    feedback="Auto-seeded check-in rating",
                    created_at=now - timedelta(days=idx + 1),
                )
                db.add(checkin_rating)
                seeded_count += 1

            meeting_result = await db.execute(select(Meeting).where(Meeting.employee_id == employee.id).limit(1))
            meeting = meeting_result.scalar_one_or_none()
            if meeting is None:
                start_time = now - timedelta(days=idx + 1, hours=1)
                end_time = start_time + timedelta(minutes=30)
                participants = [email for email in [employee.email, current_user.email] if email]
                meeting = Meeting(
                    title=f"Weekly 1:1 - {employee.name}",
                    cycle_id=cycle.id,
                    description="Auto-seeded manager dashboard meeting",
                    organizer_id=current_user.id,
                    checkin_id=checkin.id,
                    employee_id=employee.id,
                    manager_id=current_user.id,
                    meeting_type=MeetingType.CHECKIN,
                    goal_id=goal.id,
                    start_time=start_time,
                    end_time=end_time,
                    google_event_id=f"seeded-{uuid4()}",
                    meet_link="https://meet.google.com/demo-seeded-meeting",
                    google_meet_link="https://meet.google.com/demo-seeded-meeting",
                    participants=participants,
                    status=MeetingStatus.completed,
                )
                db.add(meeting)
                seeded_count += 1

        await db.commit()
        return seeded_count
