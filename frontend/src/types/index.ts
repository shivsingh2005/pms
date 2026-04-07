export type UserRole = "employee" | "manager" | "hr" | "leadership";

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  roles: UserRole[];
  organization_id: string;
  manager_id?: string | null;
  domain?: string | null;
  business_unit?: string | null;
  department?: string | null;
  title?: string | null;
  first_login?: boolean;
  onboarding_complete?: boolean;
  last_active?: string | null;
  is_active?: boolean;
}

export interface DashboardNextAction {
  title: string;
  detail: string;
  action_url: string;
  action_label: string;
  level: "info" | "warning" | "critical" | string;
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
  cycle_id?: string | null;
  goal_ids: string[];
  goal_updates: Array<{ goal_id: string; progress?: number | null; note?: string | null }>;
  employee_id: string;
  manager_id: string;
  overall_progress: number;
  status: "draft" | "submitted" | "reviewed";
  summary: string;
  achievements?: string | null;
  blockers?: string | null;
  confidence_level?: number | null;
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

export interface CheckinTranscriptGoalSummary {
  goal_id: string;
  goal_title: string;
  summary_note: string;
}

export interface CheckinTranscriptIngestResult {
  checkin: Checkin;
  summary: string;
  key_points: string[];
  action_items: string[];
  goal_summaries: CheckinTranscriptGoalSummary[];
}

export interface CheckinRatingRecommendation {
  checkin_id: string;
  suggested_rating: number;
  confidence: number;
  rationale: string[];
  factors: Record<string, number | boolean | null>;
  override_allowed: boolean;
}

export interface AIFeedbackCoachingResult {
  improved_feedback: string;
  tone_score: number;
  suggested_version: string;
}

export interface ManagerPendingCheckin {
  id: string;
  employee_id: string;
  employee_name: string;
  goal_ids: string[];
  goal_titles: string[];
  overall_progress: number;
  summary?: string | null;
  achievements?: string | null;
  blockers?: string | null;
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

export interface ReviewNarrativeRequest {
  period?: "quarter" | "year";
  cycle_year?: number;
  cycle_quarter?: number;
  manager_comments?: string;
}

export interface ReviewNarrative {
  period: "quarter" | "year";
  cycle_year?: number | null;
  cycle_quarter?: number | null;
  performance_summary: string;
  strengths: string[];
  weaknesses: string[];
  growth_plan: string[];
  explainability: {
    scope: "employee" | "team" | "organization";
    review_count: number;
    source_review_ids: string[];
    filters: {
      period: "quarter" | "year";
      cycle_year?: number | null;
      cycle_quarter?: number | null;
    };
  };
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

export interface RoleGoalRecommendation {
  title: string;
  description: string;
  difficulty: "easy" | "medium" | "hard";
  suggested_weight: number;
  kpi?: string | null;
}

export interface RoleGoalCluster {
  role: "frontend" | "backend" | "others";
  goals: RoleGoalRecommendation[];
}

export interface GoalAssignmentRecommendationsPayload {
  manager_id: string;
  clusters: RoleGoalCluster[];
}

export interface GoalAssignmentCandidate {
  employee_id: string;
  employee_name: string;
  role: string;
  role_key: "frontend" | "backend" | "others";
  goal_count: number;
  total_weightage: number;
  active_checkins: number;
  workload_percent: number;
  workload_status: "low" | "medium" | "high";
}

export interface GoalAssignmentSingleResult {
  goal: Goal;
  employee_workload_percent: number;
  employee_workload_status: "low" | "medium" | "high";
  warning?: string | null;
}

export interface GoalCascadeChildPayload {
  employee_id: string;
  title: string;
  description?: string;
  kpi?: string;
  framework: "OKR" | "MBO" | "Hybrid";
  weightage: number;
  progress: number;
}

export interface GoalCascadeResult {
  parent_goal_id: string;
  children_created: number;
  child_goal_ids: string[];
}

export interface GoalLineageNode {
  goal_id: string;
  user_id: string;
  title: string;
  framework: "OKR" | "MBO" | "Hybrid";
  weightage: number;
  progress: number;
  status: Goal["status"];
}

export interface GoalLineageEdge {
  parent_goal_id: string;
  child_goal_id: string;
  contribution_percentage: number;
}

export interface GoalLineage {
  root_goal_id: string;
  nodes: GoalLineageNode[];
  edges: GoalLineageEdge[];
}

export interface GoalChangeLog {
  id: string;
  goal_id: string;
  changed_by?: string | null;
  change_type: string;
  before_state?: Record<string, unknown> | null;
  after_state?: Record<string, unknown> | null;
  note?: string | null;
  created_at: string;
}

export interface GoalDriftInsight {
  goal_id: string;
  user_id: string;
  title: string;
  weightage: number;
  progress: number;
  drift_score: number;
  reason: string;
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

export interface GeneratedReportSection {
  heading: string;
  content: string[];
}

export interface GeneratedReportPayload {
  report_type: "individual" | "team" | "business";
  generated_at: string;
  summary: string;
  sections: GeneratedReportSection[];
  metadata: Record<string, string | number | null>;
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
  created_by_role?: "manager" | "hr" | "employee" | "leadership";
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

export interface FrameworkRecommendation {
  recommended_framework: string;
  rationale: string;
}

export interface FrameworkSelection {
  user_id: string;
  selected_framework: string;
  cycle_type: string;
  recommendation_reason?: string | null;
}

export interface DepartmentFrameworkPolicy {
  id: string;
  department: string;
  allowed_frameworks: string[];
  cycle_type: string;
  is_active: boolean;
}

export interface KPILibraryItem {
  id: string;
  role: string;
  domain?: string | null;
  department?: string | null;
  goal_title: string;
  goal_description: string;
  suggested_kpi: string;
  suggested_weight: number;
  framework: string;
}

export interface AnnualOperatingPlanItem {
  id: string;
  organization_id: string;
  year: number;
  objective: string;
  target_value?: string | null;
  department?: string | null;
  created_by?: string | null;
}

export interface LeadershipAOPTarget {
  id: string;
  organization_id: string;
  cycle_id?: string | null;
  title: string;
  description?: string | null;
  year: number;
  quarter?: number | null;
  total_target_value: number;
  target_unit: string;
  target_metric: string;
  department?: string | null;
  status: string;
  created_by?: string | null;
  created_at: string;
  updated_at: string;
  assigned_target_value: number;
  assigned_percentage: number;
  manager_count: number;
}

export interface AOPManagerAssignment {
  id: string;
  aop_id: string;
  manager_id: string;
  manager_name: string;
  manager_department?: string | null;
  assigned_target_value: number;
  assigned_percentage: number;
  target_unit?: string | null;
  description?: string | null;
  status: string;
  acknowledged_at?: string | null;
}

export interface AOPProgressManager {
  manager_id: string;
  manager_name: string;
  manager_department?: string | null;
  target_value: number;
  achieved_value: number;
  achieved_percentage: number;
  status_label: string;
}

export interface AOPProgress {
  aop_id: string;
  title: string;
  total_target_value: number;
  achieved_value: number;
  achieved_percentage: number;
  managers: AOPProgressManager[];
}

export interface CascadedManagerGoal {
  goal_id: string;
  aop_id?: string | null;
  assignment_id?: string | null;
  title: string;
  description?: string | null;
  target_value?: number | null;
  target_unit?: string | null;
  status: string;
  assigned_by?: string | null;
}

export interface CascadedEmployeeGoal {
  goal_id: string;
  manager_goal_id?: string | null;
  aop_id?: string | null;
  title: string;
  description?: string | null;
  target_value?: number | null;
  target_unit?: string | null;
  target_percentage?: number | null;
  status: string;
  contribution_level?: string | null;
}

export interface GoalLineageImpact {
  employee_goal_id: string;
  employee_title: string;
  employee_target_value?: number | null;
  employee_target_percentage?: number | null;
  employee_progress: number;
  manager_goal_id?: string | null;
  manager_title?: string | null;
  manager_target_value?: number | null;
  manager_progress?: number | null;
  aop_id?: string | null;
  aop_title?: string | null;
  aop_total_value?: number | null;
  aop_progress?: number | null;
  contribution_level?: string | null;
  business_context?: string | null;
}

export interface EmployeeCascadeSuggestionRequest {
  manager_name: string;
  total_target_value: number;
  target_unit: string;
  target_metric: string;
  employees: Array<{
    employee_id: string;
    name: string;
    role: string;
    current_workload_percentage: number;
    historical_performance_score?: number;
  }>;
}

export interface EmployeeCascadeSuggestion {
  employee_id: string;
  suggested_value: number;
  suggested_percentage: number;
  rationale: string;
  workload_after: number;
}

export interface EmployeeCascadeSuggestionResponse {
  assignments: EmployeeCascadeSuggestion[];
  total_check: number;
  warnings: string[];
}

export interface AIUsageFeatureStatus {
  feature_name: string;
  used: number;
  limit: number;
  remaining: number;
}

export interface AIQuarterlyUsage {
  quarter: number;
  year: number;
  features: AIUsageFeatureStatus[];
}

export interface AIGrowthSuggestionResult {
  growth_suggestions: string[];
  next_quarter_plan: string[];
  recommended_training: string[];
}

export interface CycleTimelineNode {
  id: string;
  node_name: string;
  status: string;
  completed_at?: string | null;
  locked_at?: string | null;
  notes?: string | null;
}

export interface CycleTimelineState {
  employee_id: string;
  cycle_id: string;
  items: CycleTimelineNode[];
}

export interface NotificationItem {
  id: string;
  user_id: string;
  type: string;
  title: string;
  message: string;
  action_url?: string | null;
  is_read: boolean;
  created_at: string;
}

export interface NotificationsPayload {
  unread_count: number;
  items: NotificationItem[];
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
  rating: number;
  consistency: number;
}

export interface ManagerDashboardTeamItem {
  employee_id: string;
  employee_name: string;
  progress: number;
  rating: number;
  consistency: number;
}

export interface ManagerTeamPerformancePayload {
  team_size: number;
  avg_performance: number;
  avg_progress: number;
  completed_goals: number;
  consistency: number;
  at_risk: number;
  message?: string | null;
  trend: ManagerTeamPerformanceTrendPoint[];
  distribution: ManagerTeamPerformanceDistributionItem[];
  workload: ManagerTeamPerformanceWorkloadItem[];
  performers: {
    top: ManagerTeamPerformancePerformerItem[];
    low: ManagerTeamPerformancePerformerItem[];
  };
  top_performers: ManagerTeamPerformancePerformerItem[];
  low_performers: ManagerTeamPerformancePerformerItem[];
  team: ManagerDashboardTeamItem[];
  insights: string[];
}

export interface ManagerStackRankingItem {
  rank: number;
  employee_id: string;
  employee_name: string;
  progress: number;
  rating: number;
  consistency: number;
  risk_level: "low" | "medium" | "high";
}

export interface ManagerStackRankingPayload {
  sort_by: "progress" | "rating" | "consistency";
  order: "asc" | "desc";
  at_risk_only: boolean;
  total_considered: number;
  items: ManagerStackRankingItem[];
}
