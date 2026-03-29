from types import SimpleNamespace
from uuid import uuid4
import pytest
from fastapi import HTTPException
from app.integrations.google.meet_service import MeetService
from app.models.enums import UserRole


def test_validate_create_role_allows_employee_manager_and_hr():
    employee = SimpleNamespace(role=UserRole.employee)
    manager = SimpleNamespace(role=UserRole.manager)
    hr_user = SimpleNamespace(role=UserRole.hr)

    MeetService._validate_create_role(employee)
    MeetService._validate_create_role(manager)
    MeetService._validate_create_role(hr_user)


def test_validate_create_role_blocks_leadership():
    leadership_user = SimpleNamespace(role=UserRole.leadership)

    with pytest.raises(HTTPException) as exc:
        MeetService._validate_create_role(leadership_user)

    assert exc.value.status_code == 403


def test_ensure_meeting_access_blocks_other_employee():
    meeting = SimpleNamespace(organizer_id=uuid4())
    user = SimpleNamespace(role=UserRole.employee, id=uuid4())

    with pytest.raises(HTTPException) as exc:
        MeetService._ensure_meeting_access(user, meeting)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_get_meeting_invalid_uuid_returns_400():
    service = MeetService.__new__(MeetService)
    fake_db = SimpleNamespace()
    fake_user = SimpleNamespace(role=UserRole.admin)

    with pytest.raises(HTTPException) as exc:
        await service.get_meeting("not-a-uuid", fake_user, fake_db)

    assert exc.value.status_code == 400
