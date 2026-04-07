from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.services.manager_seed_service import ManagerSeedService
from app.services.manager_service import ManagerService


class _ScalarListResult:
    def __init__(self, values: list):
        self._values = values

    def all(self):
        return list(self._values)


class _Result:
    def __init__(self, *, scalar_value=None, scalars_values=None, rowcount=None):
        self._scalar_value = scalar_value
        self._scalars_values = scalars_values
        self.rowcount = rowcount

    def scalar(self):
        return self._scalar_value

    def scalars(self):
        return _ScalarListResult(self._scalars_values or [])


class _StubSession:
    def __init__(self, results: list[_Result]):
        self._results = list(results)
        self.commit = AsyncMock()

    async def execute(self, _statement):
        if not self._results:
            raise AssertionError("Unexpected execute call in test")
        return self._results.pop(0)


def _manager():
    return SimpleNamespace(
        id=uuid4(),
        organization_id=uuid4(),
    )


@pytest.mark.asyncio
async def test_repair_relationships_syncs_mirrored_employee_rows(monkeypatch):
    db = _StubSession(
        [
            _Result(scalars_values=[uuid4()]),
            _Result(rowcount=1),
        ]
    )
    current_user = _manager()

    monkeypatch.setattr(ManagerService, "_team_count", AsyncMock(return_value=1))

    repaired = await ManagerService._repair_manager_relationships(current_user, db)

    assert repaired == 1


@pytest.mark.asyncio
async def test_repair_relationships_auto_assigns_orphan_employees_when_team_empty(monkeypatch):
    adopted_user_1 = uuid4()
    adopted_user_2 = uuid4()
    db = _StubSession(
        [
            _Result(scalars_values=[]),
            _Result(rowcount=2),
            _Result(scalars_values=[adopted_user_1, adopted_user_2]),
            _Result(rowcount=1),
        ]
    )
    current_user = _manager()

    monkeypatch.setattr(ManagerService, "_team_count", AsyncMock(return_value=0))

    repaired = await ManagerService._repair_manager_relationships(current_user, db)

    assert repaired == 3


@pytest.mark.asyncio
async def test_ensure_team_data_seeds_when_no_team_exists(monkeypatch):
    db = _StubSession([_Result(scalar_value=0)])
    current_user = _manager()

    monkeypatch.setattr(ManagerService, "_repair_manager_relationships", AsyncMock(return_value=0))
    monkeypatch.setattr(ManagerService, "_team_count", AsyncMock(return_value=0))
    seed_mock = AsyncMock(return_value=10)
    monkeypatch.setattr(ManagerSeedService, "seed_manager_data", seed_mock)

    await ManagerService._ensure_team_data(current_user, db)

    seed_mock.assert_awaited_once_with(current_user, db, team_size=10)


@pytest.mark.asyncio
async def test_ensure_team_data_commits_when_relationships_are_repaired(monkeypatch):
    db = _StubSession([_Result(scalar_value=0)])
    current_user = _manager()

    monkeypatch.setattr(ManagerService, "_repair_manager_relationships", AsyncMock(return_value=2))
    monkeypatch.setattr(ManagerService, "_team_count", AsyncMock(return_value=0))
    monkeypatch.setattr(ManagerSeedService, "seed_manager_data", AsyncMock(return_value=10))

    await ManagerService._ensure_team_data(current_user, db)

    db.commit.assert_awaited_once()
