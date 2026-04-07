from datetime import datetime, timezone
from collections import Counter
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.ai_service import AIService
from app.core.cache import cache_get, cache_set
from app.models.checkin import Checkin
from app.models.enums import UserRole
from app.models.goal import Goal
from app.models.performance_review import PerformanceReview
from app.models.user import User
from app.schemas.review import ReviewGenerateRequest, ReviewNarrativeRequest
from app.services.rating_service import RatingService


class ReviewService:
    @staticmethod
    def _split_insights(value: str | None) -> list[str]:
        if not value:
            return []
        items = [item.strip(" -\n\t") for item in value.replace("\n", ";").split(";")]
        return [item for item in items if item]

    @staticmethod
    def _dominant_scope_for_reviews(current_user: User) -> str:
        if current_user.role == UserRole.employee:
            return "employee"
        if current_user.role == UserRole.manager:
            return "team"
        return "organization"

    @staticmethod
    async def list_reviews(current_user: User, db: AsyncSession) -> list[PerformanceReview]:
        stmt = select(PerformanceReview)
        if current_user.role == UserRole.employee:
            stmt = stmt.where(PerformanceReview.employee_id == current_user.id)
        elif current_user.role == UserRole.manager:
            stmt = stmt.where(PerformanceReview.manager_id == current_user.id)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def generate_review(manager: User, payload: ReviewGenerateRequest, db: AsyncSession) -> PerformanceReview:
        weighted_score = await RatingService.weighted_score(payload.employee_id, db)
        summary = f"Performance review generated with weighted score {weighted_score:.2f}"

        review = PerformanceReview(
            employee_id=payload.employee_id,
            manager_id=manager.id,
            cycle_year=payload.cycle_year,
            cycle_quarter=payload.cycle_quarter,
            overall_rating=weighted_score,
            summary=summary,
            strengths="Consistent contribution against goals",
            weaknesses="Needs improvement in low-progress goals",
            growth_areas="Strategic planning and ownership",
            created_at=datetime.now(timezone.utc),
        )
        db.add(review)
        await db.commit()
        await db.refresh(review)
        return review

    @staticmethod
    async def analytics(db: AsyncSession) -> dict:
        cache_key = "reviews:analytics"
        cached = await cache_get(cache_key)
        if cached:
            return cached

        result = await db.execute(
            select(func.count(PerformanceReview.id), func.avg(PerformanceReview.overall_rating))
        )
        total_reviews, avg_rating = result.one()
        payload = {
            "total_reviews": int(total_reviews or 0),
            "avg_rating": float(avg_rating or 0),
        }
        await cache_set(cache_key, payload)
        return payload

    @staticmethod
    async def narrative(current_user: User, payload: ReviewNarrativeRequest, db: AsyncSession) -> dict:
        reviews_stmt = select(PerformanceReview)
        if current_user.role == UserRole.employee:
            reviews_stmt = reviews_stmt.where(PerformanceReview.employee_id == current_user.id)
        elif current_user.role == UserRole.manager:
            reviews_stmt = reviews_stmt.where(PerformanceReview.manager_id == current_user.id)

        if payload.cycle_year is not None:
            reviews_stmt = reviews_stmt.where(PerformanceReview.cycle_year == payload.cycle_year)
        if payload.period == "quarter":
            if payload.cycle_quarter is not None:
                reviews_stmt = reviews_stmt.where(PerformanceReview.cycle_quarter == payload.cycle_quarter)
            elif payload.cycle_year is not None:
                # Prevent mixed-quarter quarter narratives when year is selected.
                latest_q_stmt = (
                    select(func.max(PerformanceReview.cycle_quarter))
                    .where(PerformanceReview.cycle_year == payload.cycle_year)
                )
                latest_q_result = await db.execute(latest_q_stmt)
                latest_quarter = latest_q_result.scalar_one_or_none()
                if latest_quarter is not None:
                    reviews_stmt = reviews_stmt.where(PerformanceReview.cycle_quarter == int(latest_quarter))

        reviews_stmt = reviews_stmt.order_by(PerformanceReview.created_at.desc()).limit(40)
        reviews_result = await db.execute(reviews_stmt)
        reviews = list(reviews_result.scalars().all())

        if not reviews:
            return {
                "period": payload.period,
                "cycle_year": payload.cycle_year,
                "cycle_quarter": payload.cycle_quarter,
                "performance_summary": "No reviews are available for the selected period.",
                "strengths": ["Collect check-ins and complete at least one review cycle."],
                "weaknesses": ["Insufficient review evidence in the selected scope."],
                "growth_plan": ["Run quarterly review generation after manager check-ins."],
                "explainability": {
                    "scope": ReviewService._dominant_scope_for_reviews(current_user),
                    "review_count": 0,
                    "source_review_ids": [],
                    "filters": {
                        "period": payload.period,
                        "cycle_year": payload.cycle_year,
                        "cycle_quarter": payload.cycle_quarter,
                    },
                },
            }

        source_review_ids = [review.id for review in reviews]
        employee_ids = sorted({str(review.employee_id) for review in reviews})

        if current_user.role == UserRole.employee:
            latest = reviews[0]
            return {
                "period": payload.period,
                "cycle_year": payload.cycle_year or latest.cycle_year,
                "cycle_quarter": payload.cycle_quarter or latest.cycle_quarter,
                "performance_summary": latest.summary or "Performance narrative is currently unavailable.",
                "strengths": ReviewService._split_insights(latest.strengths) or ["Consistent contribution against assigned goals"],
                "weaknesses": ReviewService._split_insights(latest.weaknesses) or ["Maintain momentum on lower-progress goals"],
                "growth_plan": ReviewService._split_insights(latest.growth_areas) or ["Define one measurable growth outcome for next cycle"],
                "explainability": {
                    "scope": "employee",
                    "review_count": len(reviews),
                    "source_review_ids": source_review_ids,
                    "filters": {
                        "period": payload.period,
                        "cycle_year": payload.cycle_year,
                        "cycle_quarter": payload.cycle_quarter,
                    },
                },
            }

        ai_service = AIService()

        goal_stmt = (
            select(Goal.title)
            .where(Goal.user_id.in_(employee_ids))
            .order_by(Goal.updated_at.desc())
            .limit(30)
        )
        checkin_stmt = (
            select(Checkin.summary)
            .where(Checkin.employee_id.in_(employee_ids))
            .order_by(Checkin.updated_at.desc())
            .limit(30)
        )
        goals_result = await db.execute(goal_stmt)
        checkins_result = await db.execute(checkin_stmt)
        goal_titles = [row for row in goals_result.scalars().all() if row]
        checkin_notes = [row for row in checkins_result.scalars().all() if row]

        combined_comments = []
        if payload.manager_comments.strip():
            combined_comments.append(payload.manager_comments.strip())
        summary_counter = Counter(
            item.strip() for item in [review.summary or "" for review in reviews] if item and item.strip()
        )
        if summary_counter:
            top_summary, _ = summary_counter.most_common(1)[0]
            combined_comments.append(f"Dominant review theme: {top_summary}")

        narrative = await ai_service.generate_performance_review(
            user=current_user,
            employee_goals=goal_titles or ["No goal catalog found for selected scope"],
            checkin_notes=checkin_notes or ["No check-in notes found for selected scope"],
            manager_comments=" | ".join(combined_comments) or "Generate a concise executive narrative.",
            db=db,
        )

        return {
            "period": payload.period,
            "cycle_year": payload.cycle_year,
            "cycle_quarter": payload.cycle_quarter,
            "performance_summary": narrative.get("performance_summary", "Performance narrative unavailable."),
            "strengths": narrative.get("strengths", []),
            "weaknesses": narrative.get("weaknesses", []),
            "growth_plan": narrative.get("growth_plan", []),
            "explainability": {
                "scope": ReviewService._dominant_scope_for_reviews(current_user),
                "review_count": len(reviews),
                "source_review_ids": source_review_ids,
                "filters": {
                    "period": payload.period,
                    "cycle_year": payload.cycle_year,
                    "cycle_quarter": payload.cycle_quarter,
                },
            },
        }
