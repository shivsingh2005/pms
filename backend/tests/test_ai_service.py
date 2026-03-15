from types import SimpleNamespace
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


@pytest.mark.asyncio
async def test_rbac_blocks_unauthorized_feature():
    service = AIService(client=FakeClientOk())
    manager = SimpleNamespace(id="u1", role=UserRole.manager)

    with pytest.raises(PermissionError):
        await service._check_rbac("career_growth", manager)


@pytest.mark.asyncio
async def test_quarter_limit_is_unlimited_for_employee():
    service = AIService(client=FakeClientOk())
    employee = SimpleNamespace(id="u1", role=UserRole.employee)
    db = FakeDB(count=3)

    await service._enforce_quarter_limit(employee, db)


@pytest.mark.asyncio
async def test_execute_returns_fallback_on_gemini_error_and_logs_usage():
    service = AIService(client=FakeClientError())
    admin = SimpleNamespace(id="u1", role=UserRole.admin)
    db = FakeDB(count=0)
    fallback = {"summary": "fallback"}

    result = await service._execute(
        admin,
        "decision_intelligence",
        "prompt",
        fallback,
        db,
    )

    assert result == fallback
    assert db.committed == 1
    assert len(db.added) == 1
