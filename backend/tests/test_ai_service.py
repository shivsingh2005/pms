from types import SimpleNamespace
from uuid import uuid4
import pytest
from app.ai.ai_service import AIService
from app.ai.gemini_client import GeminiClientError
from app.models.enums import UserRole


class FakeResult:
    def __init__(self, value: int):
        self._value = value

    def scalar(self):
        return self._value


class FakeDB:
    def __init__(self, count: int = 0):
        self.count = count
        self.added = []
        self.committed = 0

    async def execute(self, stmt):
        return FakeResult(self.count)

    def add(self, model):
        self.added.append(model)

    async def commit(self):
        self.committed += 1


class FakeClientOk:
    async def generate_json(self, prompt: str):
        return ({"goals": []}, SimpleNamespace(prompt_tokens=11, response_tokens=22))


class FakeClientError:
    async def generate_json(self, prompt: str):
        raise GeminiClientError("failure")


class FakeTeamMembersResult:
    def __init__(self, members):
        self._members = members

    def scalars(self):
        return self

    def all(self):
        return self._members


class FakeWorkloadResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class FakeTeamDB:
    def __init__(self, manager, members, workloads):
        self.manager = manager
        self.members = members
        self.workloads = workloads
        self.exec_count = 0

    async def get(self, model, key):
        return self.manager

    async def execute(self, stmt):
        self.exec_count += 1
        if self.exec_count == 1:
            return FakeTeamMembersResult(self.members)
        return FakeWorkloadResult(self.workloads)


@pytest.mark.asyncio
async def test_rbac_blocks_unauthorized_feature():
    service = AIService(client=FakeClientOk())
    manager = SimpleNamespace(id="u1", role=UserRole.manager)

    with pytest.raises(PermissionError):
        await service._check_rbac("career_growth", manager)


@pytest.mark.asyncio
async def test_quarter_limit_allows_when_under_feature_cap():
    service = AIService(client=FakeClientOk())
    employee = SimpleNamespace(id="u1", role=UserRole.employee)
    db = FakeDB(count=3)

    await service._enforce_quarter_limit(employee, "goal_suggestions", db)


@pytest.mark.asyncio
async def test_execute_returns_fallback_on_gemini_error_and_logs_usage():
    service = AIService(client=FakeClientError())
    hr_user = SimpleNamespace(id="u1", role=UserRole.hr)
    db = FakeDB(count=0)
    fallback = {"summary": "fallback"}

    result = await service._execute(
        hr_user,
        "decision_intelligence",
        "prompt",
        fallback,
        db,
    )

    assert result == fallback
    assert db.committed == 1
    assert len(db.added) == 1


@pytest.mark.asyncio
async def test_generate_team_goals_sanitizes_ai_goals_and_uses_fallback_for_invalid_items():
    service = AIService(client=FakeClientOk())

    org_id = uuid4()
    manager_id = uuid4()
    member_1_id = uuid4()
    member_2_id = uuid4()

    requester = SimpleNamespace(
        id=manager_id,
        role=UserRole.manager,
        organization_id=org_id,
        is_active=True,
    )
    manager = SimpleNamespace(
        id=manager_id,
        role=UserRole.manager,
        organization_id=org_id,
        is_active=True,
        name="Manager One",
    )

    members = [
        SimpleNamespace(
            id=member_1_id,
            name="Alice",
            title="Backend Engineer",
            role=UserRole.employee,
            department="Engineering",
            manager_id=manager_id,
            organization_id=org_id,
            is_active=True,
        ),
        SimpleNamespace(
            id=member_2_id,
            name="Bob",
            title="Backend Engineer",
            role=UserRole.employee,
            department="Engineering",
            manager_id=manager_id,
            organization_id=org_id,
            is_active=True,
        ),
    ]
    workloads = [
        (member_1_id, 40.0, 2),
        (member_2_id, 20.0, 1),
    ]

    db = FakeTeamDB(manager=manager, members=members, workloads=workloads)

    async def fake_execute(user, feature_name, prompt, fallback, _db):
        return {
            "employees": [
                {
                    "employee_id": str(member_1_id),
                    "goals": ["bad", {"title": "missing fields"}],
                },
                {
                    "employee_id": str(member_2_id),
                    "goals": [
                        {
                            "title": "Stabilize APIs",
                            "description": "Improve backend reliability.",
                            "kpi": "Reduce incidents by 20%",
                            "weightage": "40",
                        }
                    ],
                },
            ]
        }

    service._execute = fake_execute

    result = await service.generate_team_goals(
        requester=requester,
        manager_id=str(manager_id),
        organization_objectives="Improve delivery quality",
        db=db,
    )

    employees = {row["employee_id"]: row for row in result["employees"]}

    # Member 1 had only malformed goals from AI; fallback goals should be preserved.
    assert len(employees[str(member_1_id)]["goals"]) == 3

    # Member 2 should keep sanitized AI goal item with numeric weightage.
    goals_member_2 = employees[str(member_2_id)]["goals"]
    assert len(goals_member_2) == 1
    assert goals_member_2[0]["title"] == "Stabilize APIs"
    assert goals_member_2[0]["weightage"] == 40.0
