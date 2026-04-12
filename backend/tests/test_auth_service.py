from app.models.enums import UserRole
from app.services.auth_service import AuthService


def test_infer_role_from_leadership_demo_email() -> None:
    assert AuthService._infer_role_from_email("leadership@structured.mock") == UserRole.leadership


def test_infer_role_from_manager_email_still_maps_to_manager() -> None:
    assert AuthService._infer_role_from_email("manager@structured.mock") == UserRole.manager