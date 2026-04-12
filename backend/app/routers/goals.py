from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.rbac import require_roles
from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.goal import (
    GoalApprovalHistoryOut,
    GoalAssignRequest,
    GoalAssignmentCandidateOut,
    GoalAssignmentOneRequest,
    GoalAssignmentOneResponse,
    GoalAssignmentRecommendationRequest,
    GoalAssignmentRecommendationResponse,
    GoalCascadeRequest,
    GoalCascadeResponse,
    GoalChangeLogOut,
    GoalCreate,
    GoalDriftOut,
    GoalLineageResponse,
    GoalSubmitForApprovalRequest,
    GoalWithdrawRequest,
    GoalOut,
    GoalUpdate,
    ManagerGoalEditApproveRequest,
    ManagerGoalReviewRequest,
    ManagerPendingGoalOut,
    SelfCreateGoalRequest,
    SelfGoalSummaryOut,
)
from app.services.goal_service import GoalService
from app.utils.dependencies import get_current_user, get_user_mode

router = APIRouter(prefix="/goals", tags=["Goals"])


@router.post("", response_model=GoalOut)
async def create_goal(
    payload: GoalCreate,
    current_user: User = Depends(require_roles(UserRole.employee, UserRole.manager, UserRole.leadership)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> GoalOut:
    if current_user.role == UserRole.manager and mode != UserRole.manager:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Switch to manager mode to create goals as a manager",
        )
    goal = await GoalService.create_goal(current_user, payload, db)
    return GoalOut.model_validate(goal)


@router.get("", response_model=list[GoalOut])
async def list_goals(
    current_user: User = Depends(get_current_user),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> list[GoalOut]:
    goals = await GoalService.list_goals(current_user, mode, db)
    return [GoalOut.model_validate(goal) for goal in goals]


@router.post("/self-create", response_model=GoalOut)
async def self_create_goal(
    payload: SelfCreateGoalRequest,
    current_user: User = Depends(require_roles(UserRole.employee)),
    db: AsyncSession = Depends(get_db),
) -> GoalOut:
    goal = await GoalService.self_create_goal(current_user, GoalCreate(**payload.model_dump(), progress=0), db)
    return GoalOut.model_validate(goal)


@router.get("/self/summary", response_model=SelfGoalSummaryOut)
async def get_self_goal_summary(
    current_user: User = Depends(require_roles(UserRole.employee)),
    db: AsyncSession = Depends(get_db),
) -> SelfGoalSummaryOut:
    summary = await GoalService.get_self_goal_summary(current_user, db)
    return SelfGoalSummaryOut(**summary)


@router.post("/{goal_id}/request-approval", response_model=GoalOut)
async def request_goal_approval(
    goal_id: str,
    payload: GoalSubmitForApprovalRequest,
    current_user: User = Depends(require_roles(UserRole.employee)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> GoalOut:
    if mode != UserRole.employee:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Switch to employee mode to submit personal goals")
    goal = await GoalService.submit_self_goal_for_approval(goal_id, current_user, db, notes=payload.notes)
    return GoalOut.model_validate(goal)


@router.post("/{goal_id}/withdraw", response_model=GoalOut)
async def withdraw_goal(
    goal_id: str,
    payload: GoalWithdrawRequest,
    current_user: User = Depends(require_roles(UserRole.employee)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> GoalOut:
    if mode != UserRole.employee:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Switch to employee mode to withdraw personal goals")
    goal = await GoalService.withdraw_goal_request(goal_id, current_user, db, reason=payload.reason)
    return GoalOut.model_validate(goal)


@router.get("/manager/pending", response_model=list[ManagerPendingGoalOut])
async def list_manager_pending_goals(
    current_user: User = Depends(require_roles(UserRole.manager)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> list[ManagerPendingGoalOut]:
    if mode != UserRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Switch to manager mode to review pending goals")
    rows = await GoalService.list_manager_pending_goals(current_user, db)
    return [
        ManagerPendingGoalOut(
            goal=GoalOut.model_validate(goal),
            employee_name=employee.name,
            employee_email=employee.email,
            employee_role=employee.title or employee.role.value,
            employee_department=employee.department,
        )
        for goal, employee in rows
    ]


@router.post("/{goal_id}/manager/request-edit", response_model=GoalOut)
async def request_goal_edit(
    goal_id: str,
    payload: ManagerGoalReviewRequest,
    current_user: User = Depends(require_roles(UserRole.manager)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> GoalOut:
    if mode != UserRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Switch to manager mode to request edits")
    goal = await GoalService.request_goal_edit(goal_id, current_user, db, comment=payload.comment)
    return GoalOut.model_validate(goal)


@router.post("/{goal_id}/manager/approve", response_model=GoalOut)
async def manager_approve_goal(
    goal_id: str,
    payload: ManagerGoalReviewRequest,
    current_user: User = Depends(require_roles(UserRole.manager)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> GoalOut:
    if mode != UserRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Switch to manager mode to approve goals")
    goal = await GoalService.approve_goal(goal_id, current_user, db, manager_comment=payload.comment)
    return GoalOut.model_validate(goal)


@router.post("/{goal_id}/manager/reject", response_model=GoalOut)
async def manager_reject_goal(
    goal_id: str,
    payload: ManagerGoalReviewRequest,
    current_user: User = Depends(require_roles(UserRole.manager)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> GoalOut:
    if mode != UserRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Switch to manager mode to reject goals")
    goal = await GoalService.reject_goal(goal_id, current_user, db, manager_comment=payload.comment)
    return GoalOut.model_validate(goal)


@router.post("/{goal_id}/manager/edit-and-approve", response_model=GoalOut)
async def manager_edit_and_approve_goal(
    goal_id: str,
    payload: ManagerGoalEditApproveRequest,
    current_user: User = Depends(require_roles(UserRole.manager)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> GoalOut:
    if mode != UserRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Switch to manager mode to edit and approve goals")
    update_payload = GoalUpdate(
        title=payload.title,
        description=payload.description,
        weightage=payload.weightage,
        framework=payload.framework,
        progress=payload.progress,
    )
    goal = await GoalService.manager_edit_and_approve_goal(
        goal_id=goal_id,
        manager=current_user,
        payload=update_payload,
        db=db,
        comment=payload.comment,
    )
    return GoalOut.model_validate(goal)


@router.get("/{goal_id}/approval-history", response_model=list[GoalApprovalHistoryOut])
async def get_goal_approval_history(
    goal_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[GoalApprovalHistoryOut]:
    rows = await GoalService.get_goal_approval_history(goal_id, current_user, db)
    return [GoalApprovalHistoryOut.model_validate(row) for row in rows]


@router.patch("/{goal_id}", response_model=GoalOut)
async def update_goal(
    goal_id: str,
    payload: GoalUpdate,
    current_user: User = Depends(require_roles(UserRole.employee, UserRole.manager)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> GoalOut:
    if current_user.role == UserRole.manager and mode != UserRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Switch to manager mode to edit goals")
    goal = await GoalService.update_goal(goal_id, current_user, payload, db)
    return GoalOut.model_validate(goal)


@router.post("/{goal_id}/submit", response_model=GoalOut)
async def submit_goal(
    goal_id: str,
    current_user: User = Depends(require_roles(UserRole.employee, UserRole.manager)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> GoalOut:
    if mode == UserRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Switch to employee mode to submit personal goals")
    goal = await GoalService.submit_goal(goal_id, current_user, db)
    return GoalOut.model_validate(goal)


@router.post("/{goal_id}/approve", response_model=GoalOut)
async def approve_goal(
    goal_id: str,
    payload: ManagerGoalReviewRequest | None = None,
    current_user: User = Depends(require_roles(UserRole.manager)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> GoalOut:
    if current_user.role == UserRole.manager and mode != UserRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Switch to manager mode to approve goals")
    goal = await GoalService.approve_goal(goal_id, current_user, db, manager_comment=(payload.comment if payload else None))
    return GoalOut.model_validate(goal)


@router.post("/{goal_id}/reject", response_model=GoalOut)
async def reject_goal(
    goal_id: str,
    payload: ManagerGoalReviewRequest | None = None,
    current_user: User = Depends(require_roles(UserRole.manager)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> GoalOut:
    if current_user.role == UserRole.manager and mode != UserRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Switch to manager mode to reject goals")
    goal = await GoalService.reject_goal(goal_id, current_user, db, manager_comment=(payload.comment if payload else None))
    return GoalOut.model_validate(goal)


@router.post("/assign", response_model=list[GoalOut])
async def assign_goals(
    payload: GoalAssignRequest,
    current_user: User = Depends(require_roles(UserRole.manager)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> list[GoalOut]:
    if current_user.role == UserRole.manager and mode != UserRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Switch to manager mode to assign goals")
    goals = await GoalService.assign_goals(current_user, payload, db)
    return [GoalOut.model_validate(goal) for goal in goals]


@router.post("/assignment/recommendations", response_model=GoalAssignmentRecommendationResponse)
async def get_assignment_recommendations(
    payload: GoalAssignmentRecommendationRequest,
    current_user: User = Depends(require_roles(UserRole.manager)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> GoalAssignmentRecommendationResponse:
    if mode != UserRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Switch to manager mode to generate role recommendations")

    output = await GoalService.get_role_goal_recommendations(current_user, payload.organization_objectives, db)
    return GoalAssignmentRecommendationResponse(**output)


@router.get("/assignment/candidates/{role_key}", response_model=list[GoalAssignmentCandidateOut])
async def get_assignment_candidates(
    role_key: str,
    current_user: User = Depends(require_roles(UserRole.manager)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> list[GoalAssignmentCandidateOut]:
    if mode != UserRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Switch to manager mode to view candidates")

    rows = await GoalService.list_assignment_candidates(current_user, role_key, db)
    return [GoalAssignmentCandidateOut(**row) for row in rows]


@router.post("/assignment/one", response_model=GoalAssignmentOneResponse)
async def assign_single_goal(
    payload: GoalAssignmentOneRequest,
    current_user: User = Depends(require_roles(UserRole.manager)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> GoalAssignmentOneResponse:
    if mode != UserRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Switch to manager mode to assign goals")

    goal, workload, workload_status, warning = await GoalService.assign_single_goal(current_user, payload, db)
    return GoalAssignmentOneResponse(
        goal=GoalOut.model_validate(goal),
        employee_workload_percent=workload,
        employee_workload_status=workload_status,
        warning=warning,
    )


@router.post("/cascade", response_model=GoalCascadeResponse)
async def cascade_goal(
    payload: GoalCascadeRequest,
    current_user: User = Depends(require_roles(UserRole.manager, UserRole.hr, UserRole.leadership)),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> GoalCascadeResponse:
    if current_user.role == UserRole.manager and mode != UserRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Switch to manager mode to cascade goals")

    parent_goal_id, child_ids = await GoalService.cascade_goal(current_user, payload, db)
    return GoalCascadeResponse(parent_goal_id=parent_goal_id, children_created=len(child_ids), child_goal_ids=child_ids)


@router.get("/lineage/{goal_id}", response_model=GoalLineageResponse)
async def get_goal_lineage(
    goal_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GoalLineageResponse:
    output = await GoalService.get_goal_lineage(goal_id=goal_id, current_user=current_user, db=db)
    return GoalLineageResponse(**output)


@router.get("/changes/{goal_id}", response_model=list[GoalChangeLogOut])
async def get_goal_changes(
    goal_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[GoalChangeLogOut]:
    rows = await GoalService.get_goal_changes(goal_id=goal_id, current_user=current_user, db=db)
    return [GoalChangeLogOut.model_validate(row) for row in rows]


@router.get("/insights/drift", response_model=list[GoalDriftOut])
async def get_goal_drift(
    current_user: User = Depends(get_current_user),
    mode: UserRole = Depends(get_user_mode),
    db: AsyncSession = Depends(get_db),
) -> list[GoalDriftOut]:
    rows = await GoalService.get_goal_drift(current_user, mode, db)
    return [GoalDriftOut(**row) for row in rows]
