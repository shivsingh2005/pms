import asyncio
from sqlalchemy import func, select
from app.database import AsyncSessionLocal
from app.models.checkin import Checkin
from app.models.goal import Goal
from app.models.performance_review import PerformanceReview
from app.models.rating import Rating
from app.models.user import User


async def verify() -> None:
    async with AsyncSessionLocal() as db:
        models = [
            ("users", User),
            ("goals", Goal),
            ("checkins", Checkin),
            ("ratings", Rating),
            ("reviews", PerformanceReview),
        ]
        for name, model in models:
            result = await db.execute(select(func.count()).select_from(model))
            print(f"{name}: {result.scalar()}")


if __name__ == "__main__":
    asyncio.run(verify())
