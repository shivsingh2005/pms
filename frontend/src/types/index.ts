export type UserRole = "employee" | "manager" | "hr" | "leadership" | "admin";

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  roles: UserRole[];
  organization_id: string;
  manager_id?: string | null;
  department?: string | null;
  title?: string | null;
  is_active?: boolean;
}

export interface Goal {
  id: string;
  user_id: string;
  assigned_by?: string | null;
  assigned_to?: string | null;
  title: string;
  description?: string | null;
  weightage: number;
  status: "draft" | "submitted" | "approved" | "rejected";
  progress: number;
  framework: "OKR" | "MBO" | "Hybrid";
  is_ai_generated?: boolean;
  created_at: string;
}

export interface Checkin {
  id: string;
  goal_id: string;
  employee_id: string;
  manager_id: string;
  progress: number;
  status: "draft" | "submitted" | "reviewed";
  summary?: string | null;
  blockers?: string | null;
  next_steps?: string | null;
  manager_feedback?: string | null;
  meeting_date?: string | null;
  meeting_link?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CheckinRating {
  id: string;
  checkin_id: string;
  employee_id: string;
  manager_id: string;
  rating: number;
  feedback?: string | null;
  created_at: string;
}

export interface ManagerPendingCheckin {
  id: string;
  employee_id: string;
  employee_name: string;
  goal_id: string;
  goal_title: string;
  progress: number;
  summary?: string | null;
  blockers?: string | null;
  next_steps?: string | null;
  status: "submitted";
  created_at: string;
}

export interface Meeting {
  id: string;
  title: string;
  meeting_type: "CHECKIN" | "GENERAL" | "HR" | "REVIEW";
  description?: string | null;
  organizer_id: string;
  checkin_id?: string | null;
  employee_id?: string | null;
  manager_id?: string | null;
  goal_id?: string | null;
  start_time: string;
  end_time: string;
  google_event_id: string;
  meet_link?: string | null;
  google_meet_link?: string | null;
  participants: string[];
  status: "scheduled" | "completed" | "cancelled";
  created_at: string;
}

export interface MeetingProposal {
  id: string;
  checkin_id: string;
  employee_id: string;
  manager_id: string;
  proposed_start_time: string;
  proposed_end_time: string;
  status: "pending" | "approved" | "rejected";
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

export interface AIGeneratedGoal {
  title: string;
  description: string;
  kpi: string;
  weightage: number;
}

export interface AIGoalGenerationResponse {
  user_id: string;
  title: string;
  department: string;
  team_size: number;
  focus_area: string;
  goals: AIGeneratedGoal[];
}

export interface HRManagerOption {
  id: string;
  name: string;
  email?: string | null;
  department?: string | null;
  title?: string | null;
}

export interface HREmployeePerformance {
  id: string;
  name: string;
  role: string;
  department: string;
  progress: number;
  consistency: number;
  last_checkin_status: string;
  rating?: number | null;
  status: "On Track" | "Needs Attention" | "At Risk";
}

export interface HRTeamInsights {
  summary: string[];
}

export interface HRHeatmapCell {
  employee_id: string;
  employee_name: string;
  progress: number;
  consistency: number;
  rating?: number | null;
  intensity: number;
  training_need_level: "No Need" | "Low" | "Medium" | "High" | "Critical";
  needs_training: boolean;
}

export interface HROverview {
  total_employees: number;
  total_managers: number;
  at_risk_employees: number;
  avg_org_performance: number;
  training_heatmap: HRHeatmapCell[];
}

export interface HREmployeeDirectoryItem {
  id: string;
  name: string;
  email?: string | null;
  role: string;
  department: string;
  manager_name?: string | null;
  manager_email?: string | null;
  progress: number;
  rating?: number | null;
  consistency: number;
  needs_training: boolean;
}

export interface HREmployeeProfile {
  id: string;
  name: string;
  role: string;
  department: string;
  manager_name?: string | null;
  progress: number;
  consistency: number;
  avg_rating: number;
  needs_training: boolean;
  ai_training_reason: string;
  goals: Array<{ id: string; title: string; progress: number; status: string }>;
  checkins: Array<{ id: string; progress: number; status: string; summary?: string | null; manager_feedback?: string | null; created_at: string }>;
  ratings: Array<{ id: string; rating: number; rating_label: string; comments?: string | null; created_at: string }>;
  performance_trend: Array<{ week: string; progress: number }>;
}

export interface HRManagerTeamSummary {
  manager_id: string;
  manager_name: string;
  team_size: number;
  avg_performance: number;
  consistency: number;
  at_risk_employees: number;
  top_performers: Array<{ employee: string; score: number }>;
  low_performers: Array<{ employee: string; score: number }>;
  workload_distribution: Array<{ employee: string; weightage: number }>;
  rating_distribution: Array<{ label: string; count: number }>;
  members: HREmployeePerformance[];
}

export interface HROrgAnalytics {
  performance_trend: Array<{ week: string; value: number }>;
  department_comparison: Array<{ department: string; value: number }>;
  rating_distribution: Array<{ label: string; count: number }>;
  checkin_consistency: Array<{ week: string; value: number }>;
}

export interface HRCalibrationManager {
  manager_id: string;
  manager_name: string;
  avg_rating: number;
  org_avg_rating: number;
  bias_direction: string;
  delta: number;
}

export interface HRCalibrationPayload {
  managers: HRCalibrationManager[];
}

export interface HRReportPayload {
  report_type: string;
  generated_at: string;
  rows: Record<string, unknown>[];
}

export interface HRMeeting {
  id: string;
  title?: string;
  description?: string | null;
  employee_id?: string | null;
  employee_name?: string | null;
  manager_id?: string | null;
  manager_name?: string | null;
  start_time: string;
  end_time: string;
  duration_minutes: number;
  meeting_type: string;
  mode: string;
  notes?: string | null;
  participants?: string[];
  meet_link?: string | null;
  google_event_id?: string | null;
  summary?: string | null;
  status: string;
  created_by_role?: "manager" | "hr" | "employee" | "admin";
  created_from_checkin: boolean;
  rating_given: boolean;
}

export interface TeamGoalEmployeeBundle {
  employee_id: string;
  employee_name: string;
  role: string;
  department: string;
  current_workload: number;
  goals: AIGeneratedGoal[];
}

export interface TeamGoalGenerationResponse {
  manager_id: string;
  team_structure: string[];
  employees: TeamGoalEmployeeBundle[];
}

export interface ManagerTeamMember {
  id: string;
  name: string;
  role: string;
  department: string;
  profile_avatar?: string | null;
  goal_progress_percent: number;
  status: "On Track" | "At Risk";
  current_workload: number;
  current_goals_count: number;
  consistency_percent: number;
  avg_final_rating: number;
}

export interface ManagerInspectionCheckin {
  id: string;
  meeting_date: string;
  summary?: string | null;
  notes?: string | null;
}

export interface ManagerInspectionPerformanceItem {
  cycle_year: number;
  cycle_quarter: number;
  overall_rating?: number | null;
  summary?: string | null;
  comments?: string | null;
}

export interface ManagerInspectionGoalItem {
  id: string;
  title: string;
  progress: number;
  status: string;
}

export interface ManagerInspectionRatingItem {
  id: string;
  rating: "EE" | "DE" | "ME" | "SME" | "NI";
  comments?: string | null;
  created_at: string;
}

export interface ManagerInspectionAIInsights {
  strengths: string[];
  weaknesses: string[];
  growth_areas: string[];
}

export interface ManagerEmployeeInspection {
  employee_id: string;
  name: string;
  employee_name?: string;
  role: string;
  department: string;
  email: string;
  progress: number;
  goals_completed: number;
  consistency: number;
  last_checkin?: string | null;
  current_workload: number;
  goals: ManagerInspectionGoalItem[];
  checkins: ManagerInspectionCheckin[];
  ratings: ManagerInspectionRatingItem[];
  performance_history: ManagerInspectionPerformanceItem[];
  ai_insights: ManagerInspectionAIInsights;
}

export interface ManagerTeamPerformanceTrendPoint {
  week: string;
  progress: number;
}

export interface ManagerTeamPerformanceDistributionItem {
  label: "EE" | "DE" | "ME" | "SME" | "NI";
  count: number;
}

export interface ManagerTeamPerformanceWorkloadItem {
  employee_id: string;
  employee_name: string;
  total_weightage: number;
}

export interface ManagerTeamPerformancePerformerItem {
  employee_id: string;
  employee_name: string;
  progress: number;
}

export interface ManagerTeamPerformancePayload {
  avg_progress: number;
  completed_goals: number;
  consistency: number;
  at_risk: number;
  trend: ManagerTeamPerformanceTrendPoint[];
  distribution: ManagerTeamPerformanceDistributionItem[];
  workload: ManagerTeamPerformanceWorkloadItem[];
  performers: {
    top: ManagerTeamPerformancePerformerItem[];
    low: ManagerTeamPerformancePerformerItem[];
  };
  insights: string[];
}

export interface AdminDashboardMetric {
  total_employees: number;
  total_managers: number;
  active_users: number;
  total_goals: number;
  active_checkins: number;
  meetings_scheduled: number;
  avg_rating: number;
}

export interface AdminDashboardPayload {
  metrics: AdminDashboardMetric;
  employee_growth: Array<{ month: string; count: number }>;
  role_distribution: Array<{ role: string; count: number }>;
  rating_distribution: Array<{ label: string; count: number }>;
}

export interface AdminUser {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  manager_id?: string | null;
  manager_name?: string | null;
  department?: string | null;
  title?: string | null;
  is_active: boolean;
  created_at: string;
}

export interface AdminUsersListPayload {
  users: AdminUser[];
  managers: Array<{ id: string; name: string }>;
  departments: string[];
}

export interface AdminCreateUserPayload {
  name: string;
  email: string;
  role: UserRole;
  manager_id?: string | null;
  department?: string | null;
  title?: string | null;
  password?: string;
}

export interface AdminUpdateUserPayload {
  name?: string;
  email?: string;
  role?: UserRole;
  manager_id?: string | null;
  department?: string | null;
  title?: string | null;
  is_active?: boolean;
}

export interface AdminRolePermission {
  role_key: string;
  display_name: string;
  permissions: string[];
  is_system: boolean;
  updated_at: string;
}

export interface AdminUpsertRolePayload {
  role_key: string;
  display_name: string;
  permissions: string[];
}

export interface AdminOrgManagerNode {
  manager_id: string;
  manager_name: string;
  department?: string | null;
  team_size: number;
  avg_team_rating: number;
  members: AdminUser[];
}

export interface AdminOrgStructurePayload {
  leaders: AdminUser[];
  managers: AdminOrgManagerNode[];
}

export interface AdminSystemSettings {
  working_hours: Record<string, unknown>;
  rating_scale: Record<string, unknown>;
  checkin_frequency: Record<string, unknown>;
  ai_settings: Record<string, unknown>;
}

export interface AdminAuditLog {
  id: string;
  actor_user_id: string;
  action: string;
  target_type: string;
  target_id?: string | null;
  message: string;
  details: Record<string, unknown>;
  created_at: string;
}

export interface AdminBulkUploadResult {
  created: number;
  failed: number;
  errors: string[];
}
