from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.enums import GoalFramework, UserRole
from app.services.goal_service import GoalService
from app.schemas.goal import GoalCreate


class FakeResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class FakeDB:
    def __init__(self, cycle_id=None):
        self.cycle_id = cycle_id
        self.added = []
        self.committed = 0
        self.refreshed = []

    async def execute(self, stmt):
        return FakeResult(self.cycle_id)

    def add(self, model):
        self.added.append(model)

    async def commit(self):
        self.committed += 1

    async def refresh(self, model):
        self.refreshed.append(model)


@pytest.mark.asyncio
async def test_create_goal_marks_leadership_goal_as_self_created():
    db = FakeDB(cycle_id=uuid4())
    leadership_user = SimpleNamespace(id=uuid4(), organization_id=uuid4(), role=UserRole.leadership)

    goal = await GoalService.create_goal(
        leadership_user,
        GoalCreate(title="Launch leadership initiative", description="Build a strategic plan", weightage=25, progress=0, framework=GoalFramework.OKR),
        db,
    )

    assert goal.source_type == "self_created"
    assert goal.user_id == leadership_user.id
    assert db.committed == 2
    assert len(db.added) == 1