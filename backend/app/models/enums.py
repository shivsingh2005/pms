from enum import Enum


class UserRole(str, Enum):
    employee = "employee"
    manager = "manager"
    hr = "hr"
    leadership = "leadership"


class GoalStatus(str, Enum):
    draft = "draft"
    submitted = "submitted"
    pending_approval = "submitted"
    edit_requested = "edit_requested"
    withdrawn = "withdrawn"
    approved = "approved"
    rejected = "rejected"


class GoalFramework(str, Enum):
    OKR = "OKR"
    MBO = "MBO"
    Hybrid = "Hybrid"


class CheckinStatus(str, Enum):
    draft = "draft"
    submitted = "submitted"
    reviewed = "reviewed"


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


class MeetingType(str, Enum):
    CHECKIN = "CHECKIN"
    GENERAL = "GENERAL"
    HR = "HR"
    REVIEW = "REVIEW"


class MeetingProposalStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class PerformanceCycleStatus(str, Enum):
    planning = "planning"
    active = "active"
    closed = "closed"
    locked = "locked"
