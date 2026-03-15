from enum import Enum


class UserRole(str, Enum):
    employee = "employee"
    manager = "manager"
    hr = "hr"
    leadership = "leadership"
    admin = "admin"


class GoalStatus(str, Enum):
    draft = "draft"
    submitted = "submitted"
    approved = "approved"
    rejected = "rejected"


class GoalFramework(str, Enum):
    OKR = "OKR"
    MBO = "MBO"
    Hybrid = "Hybrid"


class CheckinStatus(str, Enum):
    scheduled = "scheduled"
    completed = "completed"


class RatingLabel(str, Enum):
    EE = "EE"
    DE = "DE"
    ME = "ME"
    SME = "SME"
    NI = "NI"


class MeetingStatus(str, Enum):
    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"
