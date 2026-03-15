export type UserRole = "employee" | "manager" | "hr" | "leadership" | "admin";

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  organization_id: string;
  manager_id?: string | null;
  department?: string | null;
  title?: string | null;
  is_active?: boolean;
}

export interface Goal {
  id: string;
  user_id: string;
  title: string;
  description?: string | null;
  weightage: number;
  status: "draft" | "submitted" | "approved" | "rejected";
  progress: number;
  framework: "OKR" | "MBO" | "Hybrid";
  created_at: string;
}

export interface Checkin {
  id: string;
  goal_id: string;
  employee_id: string;
  manager_id: string;
  meeting_date: string;
  status: "scheduled" | "completed";
  meeting_link?: string | null;
  transcript?: string | null;
  summary?: string | null;
}

export interface Meeting {
  id: string;
  title: string;
  description?: string | null;
  organizer_id: string;
  goal_id: string;
  start_time: string;
  end_time: string;
  google_event_id: string;
  google_meet_link?: string | null;
  participants: string[];
  status: "scheduled" | "completed" | "cancelled";
  created_at: string;
}

export interface Review {
  id: string;
  employee_id: string;
  manager_id: string;
  cycle_year: number;
  cycle_quarter: number;
  overall_rating?: number | null;
  summary?: string | null;
  strengths?: string | null;
  weaknesses?: string | null;
  growth_areas?: string | null;
  created_at: string;
}

export interface AIChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  createdAt: number;
}

export interface ApiErrorResponse {
  detail?: string;
  message?: string;
}
