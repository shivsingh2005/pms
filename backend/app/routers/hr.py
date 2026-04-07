from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.rbac import require_roles
from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.hr import (
    HRCalibrationOut,
    HREmployeeDirectoryItem,
    HREmployeePerformance,
    HREmployeeProfileOut,
    HRManagerOption,
    HRManagerTeamSummaryOut,
    HRMeetingOut,
    HRMeetingSummaryOut,
    HRMeetingSummaryRequest,
    HRNineBoxOut,
    HROrgAnalyticsOut,
    HROverviewOut,
    HRReportResponseOut,
    HRSuccessionOut,
    HRTeamInsights,
)
from app.services.hr_service import HRService

router = APIRouter(prefix="/hr", tags=["HR Dashboard"])


@router.get("/overview", response_model=HROverviewOut)
async def hr_overview(
    current_user: User = Depends(require_roles(UserRole.hr, UserRole.leadership)),
    db: AsyncSession = Depends(get_db),
) -> HROverviewOut:
    payload = await HRService.get_overview(current_user, db)
    return HROverviewOut(**payload)


@router.get("/managers", response_model=list[HRManagerOption])
async def list_managers(
    department: str | None = Query(default=None),
    current_user: User = Depends(require_roles(UserRole.hr, UserRole.leadership)),
    db: AsyncSession = Depends(get_db),
) -> list[HRManagerOption]:
    managers = await HRService.list_managers(current_user, db, department)
    return [
        HRManagerOption(
            id=str(manager.id),
            name=manager.name,
            email=manager.email,
            department=manager.department,
            title=manager.title,
        )
        for manager in managers
    ]


@router.get("/employees", response_model=list[HREmployeeDirectoryItem])
async def list_employees(
    department: str | None = Query(default=None),
    manager_id: str | None = Query(default=None),
    needs_training: bool | None = Query(default=None),
    current_user: User = Depends(require_roles(UserRole.hr, UserRole.leadership)),
    db: AsyncSession = Depends(get_db),
) -> list[HREmployeeDirectoryItem]:
    rows = await HRService.list_employee_directory(
        current_user=current_user,
        db=db,
        department=department,
        manager_id=manager_id,
        needs_training=needs_training,
    )
    return [HREmployeeDirectoryItem(**row) for row in rows]


@router.get("/employees/{employee_id}", response_model=HREmployeeProfileOut)
async def get_employee_profile(
    employee_id: str,
    current_user: User = Depends(require_roles(UserRole.hr, UserRole.leadership)),
    db: AsyncSession = Depends(get_db),
) -> HREmployeeProfileOut:
    payload = await HRService.get_employee_profile(current_user=current_user, employee_id=employee_id, db=db)
    if not payload:
        return HREmployeeProfileOut(
            id=employee_id,
            name="Unknown",
            role="Unknown",
            department="Unknown",
            manager_name=None,
            progress=0,
            consistency=0,
            avg_rating=0,
            needs_training=False,
            ai_training_reason="Profile not found",
            goals=[],
            checkins=[],
            ratings=[],
            performance_trend=[],
        )
    return HREmployeeProfileOut(**payload)


@router.get("/team/{manager_id}", response_model=list[HREmployeePerformance])
async def get_team_by_manager(
    manager_id: str,
    department: str | None = Query(default=None),
    role: str | None = Query(default=None),
    performance: str | None = Query(default=None, pattern="^(on_track|needs_attention|at_risk)$"),
    current_user: User = Depends(require_roles(UserRole.hr, UserRole.leadership)),
    db: AsyncSession = Depends(get_db),
) -> list[HREmployeePerformance]:
    team_rows = await HRService.get_team_performance(
        current_user=current_user,
        manager_id=manager_id,
        db=db,
        department=department,
        role=role,
        performance=performance,
    )
    return [HREmployeePerformance(**row) for row in team_rows]


@router.get("/manager-team/{manager_id}", response_model=HRManagerTeamSummaryOut)
async def get_manager_team_analytics(
    manager_id: str,
    current_user: User = Depends(require_roles(UserRole.hr, UserRole.leadership)),
    db: AsyncSession = Depends(get_db),
) -> HRManagerTeamSummaryOut:
    payload = await HRService.get_manager_team_analytics(current_user=current_user, manager_id=manager_id, db=db)
    if not payload:
        return HRManagerTeamSummaryOut(
            manager_id=manager_id,
            manager_name="Unknown",
            team_size=0,
            avg_performance=0,
            consistency=0,
            at_risk_employees=0,
            top_performers=[],
            low_performers=[],
            workload_distribution=[],
            rating_distribution=[],
            members=[],
        )
    return HRManagerTeamSummaryOut(**payload)


@router.get("/team/{manager_id}/insights", response_model=HRTeamInsights)
async def get_team_insights(
    manager_id: str,
    department: str | None = Query(default=None),
    role: str | None = Query(default=None),
    performance: str | None = Query(default=None, pattern="^(on_track|needs_attention|at_risk)$"),
    current_user: User = Depends(require_roles(UserRole.hr, UserRole.leadership)),
    db: AsyncSession = Depends(get_db),
) -> HRTeamInsights:
    team_rows = await HRService.get_team_performance(
        current_user=current_user,
        manager_id=manager_id,
        db=db,
        department=department,
        role=role,
        performance=performance,
    )
    return HRTeamInsights(summary=HRService.build_team_insights(team_rows))


@router.get("/analytics", response_model=HROrgAnalyticsOut)
async def get_org_analytics(
    current_user: User = Depends(require_roles(UserRole.hr, UserRole.leadership)),
    db: AsyncSession = Depends(get_db),
) -> HROrgAnalyticsOut:
    payload = await HRService.get_org_analytics(current_user, db)
    return HROrgAnalyticsOut(**payload)


@router.get("/calibration", response_model=HRCalibrationOut)
async def get_calibration(
    current_user: User = Depends(require_roles(UserRole.hr, UserRole.leadership)),
    db: AsyncSession = Depends(get_db),
) -> HRCalibrationOut:
    payload = await HRService.get_calibration(current_user, db)
    return HRCalibrationOut(**payload)


@router.get("/reports", response_model=HRReportResponseOut)
async def generate_report(
    report_type: str = Query(default="org", pattern="^(employee|team|org)$"),
    current_user: User = Depends(require_roles(UserRole.hr, UserRole.leadership)),
    db: AsyncSession = Depends(get_db),
) -> HRReportResponseOut:
    payload = await HRService.generate_report(current_user=current_user, report_type=report_type, db=db)
    return HRReportResponseOut(**payload)


@router.get("/meetings", response_model=list[HRMeetingOut])
async def list_hr_meetings(
    employee_id: str | None = Query(default=None),
    manager_id: str | None = Query(default=None),
    current_user: User = Depends(require_roles(UserRole.hr, UserRole.leadership)),
    db: AsyncSession = Depends(get_db),
) -> list[HRMeetingOut]:
    rows = await HRService.list_meetings(current_user=current_user, db=db, employee_id=employee_id, manager_id=manager_id)
    return [HRMeetingOut(**row) for row in rows]


@router.post("/meetings/{meeting_id}/summarize", response_model=HRMeetingSummaryOut)
async def summarize_hr_meeting(
    meeting_id: str,
    payload: HRMeetingSummaryRequest,
    current_user: User = Depends(require_roles(UserRole.hr, UserRole.leadership)),
    db: AsyncSession = Depends(get_db),
) -> HRMeetingSummaryOut:
    result = await HRService.summarize_meeting(current_user=current_user, meeting_id=meeting_id, transcript=payload.transcript, db=db)
    if not result:
        return HRMeetingSummaryOut(meeting_id=meeting_id, summary="Meeting not found")
    return HRMeetingSummaryOut(**result)


@router.get("/9box", response_model=HRNineBoxOut)
async def get_9box(
    current_user: User = Depends(require_roles(UserRole.hr, UserRole.leadership)),
    db: AsyncSession = Depends(get_db),
) -> HRNineBoxOut:
    payload = await HRService.compute_9box(current_user=current_user, db=db)
    return HRNineBoxOut(**payload)


@router.get("/succession", response_model=list[HRSuccessionOut])
async def get_succession(
    target_role: str | None = Query(default=None),
    current_user: User = Depends(require_roles(UserRole.hr, UserRole.leadership)),
    db: AsyncSession = Depends(get_db),
) -> list[HRSuccessionOut]:
    rows = await HRService.get_succession(current_user=current_user, db=db, target_role=target_role)
    return [HRSuccessionOut(**row) for row in rows]
