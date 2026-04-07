from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.employee import Employee
from app.schemas.employee import EmployeeCreate, EmployeeUpdate


class EmployeeService:
    @staticmethod
    async def _load_team_sizes(db: AsyncSession) -> dict[UUID, int]:
        result = await db.execute(
            select(Employee.manager_id, func.count(Employee.id))
            .where(Employee.manager_id.is_not(None))
            .group_by(Employee.manager_id)
        )
        return {manager_id: int(count) for manager_id, count in result.all() if manager_id is not None}

    @staticmethod
    async def list_employees(db: AsyncSession) -> list[dict]:
        result = await db.execute(select(Employee).order_by(Employee.employee_code.asc()))
        employees = list(result.scalars().all())
        team_sizes = await EmployeeService._load_team_sizes(db)
        return [{**employee.__dict__, "team_size": team_sizes.get(employee.id, 0)} for employee in employees]

    @staticmethod
    async def get_employee(employee_id: str, db: AsyncSession) -> dict:
        try:
            employee_uuid = UUID(employee_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid employee id") from exc

        employee = await db.get(Employee, employee_uuid)
        if not employee:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

        team_sizes = await EmployeeService._load_team_sizes(db)
        return {**employee.__dict__, "team_size": team_sizes.get(employee.id, 0)}

    @staticmethod
    async def get_by_manager(manager_id: str, db: AsyncSession) -> list[dict]:
        try:
            manager_uuid = UUID(manager_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid manager id") from exc

        result = await db.execute(
            select(Employee)
            .where(Employee.manager_id == manager_uuid)
            .order_by(Employee.employee_code.asc())
        )
        employees = list(result.scalars().all())
        team_sizes = await EmployeeService._load_team_sizes(db)
        return [{**employee.__dict__, "team_size": team_sizes.get(employee.id, 0)} for employee in employees]

    @staticmethod
    async def create_employee(payload: EmployeeCreate, db: AsyncSession) -> Employee:
        code_exists = await db.execute(select(Employee).where(Employee.employee_code == payload.employee_code.strip()))
        if code_exists.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Employee code already exists")

        email_exists = await db.execute(select(Employee).where(Employee.email == payload.email.strip().lower()))
        if email_exists.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

        manager_uuid = None
        if payload.manager_id:
            try:
                manager_uuid = UUID(payload.manager_id)
            except ValueError as exc:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid manager id") from exc

            manager = await db.get(Employee, manager_uuid)
            if not manager:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manager not found")

        employee = Employee(
            employee_code=payload.employee_code.strip().upper(),
            name=payload.name.strip(),
            email=payload.email.strip().lower(),
            role=payload.role,
            title=payload.title.strip() if payload.title else None,
            department=payload.department.strip() if payload.department else None,
            manager_id=manager_uuid,
            is_active=payload.is_active,
        )
        db.add(employee)
        await db.commit()
        await db.refresh(employee)
        return employee

    @staticmethod
    async def update_employee(employee_id: str, payload: EmployeeUpdate, db: AsyncSession) -> Employee:
        try:
            employee_uuid = UUID(employee_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid employee id") from exc

        employee = await db.get(Employee, employee_uuid)
        if not employee:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

        update_data = payload.model_dump(exclude_unset=True)

        if "employee_code" in update_data and update_data["employee_code"]:
            code = update_data["employee_code"].strip().upper()
            duplicate_code = await db.execute(select(Employee).where(Employee.employee_code == code, Employee.id != employee.id))
            if duplicate_code.scalar_one_or_none():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Employee code already exists")
            update_data["employee_code"] = code

        if "email" in update_data and update_data["email"]:
            email = str(update_data["email"]).strip().lower()
            duplicate_email = await db.execute(select(Employee).where(Employee.email == email, Employee.id != employee.id))
            if duplicate_email.scalar_one_or_none():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")
            update_data["email"] = email

        if "manager_id" in update_data:
            manager_id = update_data["manager_id"]
            if manager_id is None:
                update_data["manager_id"] = None
            else:
                try:
                    manager_uuid = UUID(manager_id)
                except ValueError as exc:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid manager id") from exc

                if manager_uuid == employee.id:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Employee cannot be their own manager")

                manager = await db.get(Employee, manager_uuid)
                if not manager:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manager not found")

                update_data["manager_id"] = manager_uuid

        for key, value in update_data.items():
            if isinstance(value, str) and key in {"name", "title", "department"}:
                setattr(employee, key, value.strip())
            else:
                setattr(employee, key, value)

        await db.commit()
        await db.refresh(employee)
        return employee

    @staticmethod
    async def delete_employee(employee_id: str, db: AsyncSession) -> None:
        try:
            employee_uuid = UUID(employee_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid employee id") from exc

        employee = await db.get(Employee, employee_uuid)
        if not employee:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

        reports_result = await db.execute(select(Employee).where(Employee.manager_id == employee.id))
        reports = list(reports_result.scalars().all())
        for report in reports:
            report.manager_id = employee.manager_id

        await db.delete(employee)
        await db.commit()
