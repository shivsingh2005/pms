from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.rbac import require_roles
from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.employee import EmployeeCreate, EmployeeOut, EmployeeUpdate
from app.services.employee_service import EmployeeService
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/employees", tags=["Employees"])


@router.get("", response_model=list[EmployeeOut])
async def list_employees(
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[EmployeeOut]:
    employees = await EmployeeService.list_employees(db)
    return [EmployeeOut.model_validate(employee) for employee in employees]


@router.get("/manager/{manager_id}", response_model=list[EmployeeOut])
async def list_employees_by_manager(
    manager_id: str,
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[EmployeeOut]:
    employees = await EmployeeService.get_by_manager(manager_id, db)
    return [EmployeeOut.model_validate(employee) for employee in employees]


@router.get("/{employee_id}", response_model=EmployeeOut)
async def get_employee(
    employee_id: str,
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EmployeeOut:
    employee = await EmployeeService.get_employee(employee_id, db)
    return EmployeeOut.model_validate(employee)


@router.post("", response_model=EmployeeOut)
async def create_employee(
    payload: EmployeeCreate,
    _: User = Depends(require_roles(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
) -> EmployeeOut:
    employee = await EmployeeService.create_employee(payload, db)
    payload_out = await EmployeeService.get_employee(str(employee.id), db)
    return EmployeeOut.model_validate(payload_out)


@router.patch("/{employee_id}", response_model=EmployeeOut)
async def update_employee(
    employee_id: str,
    payload: EmployeeUpdate,
    _: User = Depends(require_roles(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
) -> EmployeeOut:
    employee = await EmployeeService.update_employee(employee_id, payload, db)
    payload_out = await EmployeeService.get_employee(str(employee.id), db)
    return EmployeeOut.model_validate(payload_out)


@router.delete("/{employee_id}")
async def delete_employee(
    employee_id: str,
    _: User = Depends(require_roles(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await EmployeeService.delete_employee(employee_id, db)
    return {"deleted": True, "employee_id": employee_id}
