from sqlalchemy import String, Text, Boolean
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class GoalCluster(Base, UUIDMixin, TimestampMixin):
    """AI-detected goal clusters that work across all business functions.
    
    Examples: Revenue Growth, Talent Acquisition, Product Delivery, etc.
    Not hardcoded by role — dynamically determined by AI based on goal content + employee context.
    """
    __tablename__ = "goal_clusters"

    cluster_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    cluster_category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    applicable_functions: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list
    )
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    __table_args__ = (
        {"comment": "Universal goal clusters for all business functions (Sales, HR, Engineering, Product, etc.)"},
    )
