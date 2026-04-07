def goal_suggestion_prompt(role: str, department: str, objective: str) -> str:
    return f"""
Generate SMART goals for an employee.
Role: {role}
Department: {department}
Company objective: {objective}

Return JSON only in this shape:
{{
  "goals": [
    {{"title": "", "description": "", "kpi": "", "weightage": 25}}
  ]
}}
Include exactly 4 goals and weightage values that total 100.
""".strip()


def role_based_goal_generation_prompt(
    role_title: str,
    role: str,
    department: str,
    team_size: int,
    member_index: int,
    focus_area: str,
    objective: str | None,
    grounding_context: str | None,
    role_intelligence: list[str] | None,
    allotted_goals_context: str | None,
) -> str:
    company_objective = objective.strip() if objective else "Not provided"
    grounding = grounding_context.strip() if grounding_context else "Not provided"
    allotted_context = allotted_goals_context.strip() if allotted_goals_context else "Not provided"
    role_benchmarks = "\n".join(f"- {row}" for row in (role_intelligence or [])) or "- Not provided"
    return f"""
Generate SMART goals for an employee.

Role title: {role_title}
Role type: {role}
Department: {department}
Team size in this role: {team_size}
Employee index inside role team: {member_index} of {team_size}
Assigned focus area: {focus_area}
Organization objectives: {company_objective}
Grounding context from AOP and KPI library:
{grounding}

Allotted goal context from manager:
{allotted_context}

External role intelligence:
{role_benchmarks}

Constraints:
- Goals must be realistic and measurable
- Goals must align with team contribution
- Avoid duplication across employees with the same role
- Prioritize this employee's assigned focus area while keeping one collaboration goal
- Prefer KPIs that align with provided AOP and KPI context
- If allotted manager goals are provided, recommendations MUST be primarily based on those allotted goals
- Convert allotted goals into actionable employee-level goals with measurable outcomes and KPIs
- Do not repeat allotted goals verbatim; generate supportive, non-duplicative goals that clearly map to allotted-goal intent

Return JSON only in this shape:
{{
  "goals": [
    {{"title": "", "description": "", "kpi": "", "weightage": 25}}
  ]
}}
Include exactly 4 goals and weightage values that total 100.
""".strip()


def team_goal_generation_prompt(
    manager_name: str,
    team_structure: list[str],
    employee_lines: list[str],
    objective: str | None,
    grounding_context: str | None,
    role_intelligence: list[str] | None,
) -> str:
    org_objective = objective.strip() if objective else "Not provided"
    grounding = grounding_context.strip() if grounding_context else "Not provided"
    role_benchmarks = "\n".join(f"- {row}" for row in (role_intelligence or [])) or "- Not provided"
    structure = "\n".join(f"- {line}" for line in team_structure)
    employees = "\n".join(f"- {line}" for line in employee_lines)
    return f"""
Generate team goals.

Manager: {manager_name}
Team structure:
{structure}

Employees:
{employees}

Organization objectives: {org_objective}
Grounding context from AOP and KPI library:
{grounding}

External role intelligence:
{role_benchmarks}

Distribute goals such that:
- No duplication
- Each employee has unique responsibility
- Goals align with role
- Goals are SMART
- Goals cover different areas (performance, testing, optimization, delivery)
- Keep individual workload balanced

Return JSON only in this shape:
{{
  "employees": [
    {{
      "employee_id": "",
      "goals": [
        {{"title": "", "description": "", "kpi": "", "weightage": 25}}
      ]
    }}
  ]
}}
""".strip()


def checkin_summary_prompt(meeting_transcript: str) -> str:
    return f"""
Summarize this check-in transcript.
Transcript:
{meeting_transcript}

Return JSON only in this shape:
{{
  "summary": "",
  "key_points": [""],
  "action_items": [""]
}}
""".strip()


def performance_review_prompt(employee_goals: list[str], checkin_notes: list[str], manager_comments: str) -> str:
    goals = "\n".join(f"- {goal}" for goal in employee_goals)
    notes = "\n".join(f"- {note}" for note in checkin_notes)
    return f"""
Generate a concise performance review based on the following context.
Employee goals:
{goals}

Check-in notes:
{notes}

Manager comments:
{manager_comments}

Return JSON only in this shape:
{{
  "performance_summary": "",
  "strengths": [""],
  "weaknesses": [""],
  "growth_plan": [""]
}}
""".strip()


def feedback_coaching_prompt(manager_feedback: str) -> str:
    return f"""
Coach this feedback to be constructive, specific, and respectful.
Original feedback:
{manager_feedback}

Return JSON only in this shape:
{{
  "improved_feedback": "",
  "tone_score": 0,
  "suggested_version": ""
}}
Tone score must be between 1 and 10.
""".strip()


def career_growth_prompt(role: str, department: str, current_skills: list[str], target_role: str) -> str:
    skills = ", ".join(current_skills)
    return f"""
Create career growth suggestions.
Current role: {role}
Department: {department}
Current skills: {skills}
Target role: {target_role}

Return JSON only in this shape:
{{
  "growth_suggestions": [""],
  "next_quarter_plan": [""],
  "recommended_training": [""]
}}
""".strip()


def training_program_prompt(department: str, skill_gaps: list[str]) -> str:
    gaps = ", ".join(skill_gaps)
    return f"""
Suggest training programs for this department.
Department: {department}
Skill gaps: {gaps}

Return JSON only in this shape:
{{
  "programs": [
    {{"name": "", "duration_weeks": 0, "outcome": ""}}
  ]
}}
""".strip()


def decision_intelligence_prompt(context: str, questions: list[str]) -> str:
    question_block = "\n".join(f"- {question}" for question in questions)
    return f"""
Provide decision intelligence insights for managers and leadership.
Business context:
{context}

Questions:
{question_block}

Return JSON only in this shape:
{{
  "insights": [""],
  "risks": [""],
  "recommended_actions": [""]
}}
""".strip()


def rating_suggestion_prompt(
    overall_progress: int,
    confidence_level: int,
    blockers: str | None,
    achievements: str | None,
) -> str:
    blockers_text = blockers.strip() if blockers else "None"
    achievements_text = achievements.strip() if achievements else "None"
    return f"""
Suggest a check-in rating for a manager with rationale.

Overall progress: {overall_progress}
Employee confidence level (1-5): {confidence_level}
Blockers: {blockers_text}
Achievements: {achievements_text}

Return JSON only in this shape:
{{
  "suggested_rating": 1,
  "confidence": 0.0,
  "rationale": [""]
}}
Constraints:
- suggested_rating must be integer from 1 to 5
- confidence must be between 0 and 1
- rationale must include 2-4 concise bullets
""".strip()


def goal_cluster_detection_prompt(
    goal_title: str,
    goal_description: str,
    goal_kpi: str,
    employee_role: str,
    employee_department: str,
    employee_function: str,
) -> str:
    return f"""
Analyze this goal and determine which universal performance cluster it belongs to.
Do NOT limit to engineering roles. Consider all business functions.

Goal Title: {goal_title}
Goal Description: {goal_description}
Goal KPI: {goal_kpi}
Employee Role: {employee_role}
Employee Department: {employee_department}
Employee Function: {employee_function}

Universal cluster options:
- Revenue Growth (Sales, Business Dev, Account Management, Leadership)
- Talent Acquisition (HR, Recruiting, Operations, Leadership)
- Product Delivery (Product, Engineering, Design, Leadership)
- Customer Success (Customer Success, Support, Sales, Product)
- Content & Marketing (Marketing, Editorial, Social Media, Communications)
- Technical Excellence (Engineering, DevOps, QA, Data Science)
- Process Optimization (Operations, Finance, Admin, Data Science)
- Compliance & Risk (Legal, Finance, Security, Admin)
- Employee Development (HR, Management, Leadership, Education)
- User Engagement (Product, Engineering, Data Science, Analytics)
- Strategic Planning (Leadership, Strategy, Product, Finance)

Determine and return JSON ONLY:
{{
  "cluster_name": "Revenue Growth",
  "cluster_category": "Business Performance",
  "sub_category": "New Business Acquisition",
  "applicable_functions": ["Sales", "Business Development"],
  "goal_nature": "quantitative|qualitative|behavioral",
  "confidence": "High|Medium|Low",
  "reasoning": "Why this cluster was selected"
}}
""".strip()


def employee_recommendation_prompt(
    goal_title: str,
    goal_description: str,
    goal_kpi: str,
    goal_cluster: str,
    goal_nature: str,
    team_members_json: str,
) -> str:
    return f"""
A manager wants to assign this goal to their team.
Analyze the goal and recommend which team members are best suited for it.

Goal: {goal_title}
Goal Description: {goal_description}
Goal KPI: {goal_kpi}
Goal Cluster: {goal_cluster}
Goal Nature: {goal_nature}

Team members data (JSON):
{team_members_json}

Rules:
1. Match based on GOAL NATURE and SKILLS, not just job title
2. Consider current workload — don't overload people
3. Consider historical performance in similar goal types
4. A sales goal may go to anyone with client-facing experience
5. A technical goal may go to any engineer with relevant skills
6. Return 3-5 recommendations, ranked by match score
7. Provide clear reasoning for each recommendation
8. Mark workload risk if assigning would exceed 85% capacity

Return JSON ONLY:
{{
  "recommended_employees": [
    {{
      "employee_id": "...",
      "name": "...",
      "role": "...",
      "match_score": 85,
      "match_reason": "Strong client relationship history",
      "current_workload": 65,
      "workload_after_assignment": 78,
      "fit_confidence": "High|Medium|Low",
      "risk_flag": null
    }}
  ],
  "not_recommended": [
    {{
      "employee_id": "...",
      "reason": "Already at 90% workload"
    }}
  ],
  "cluster_insight": "This is a revenue-focused goal. Best suited for team members with client-facing experience."
}}
""".strip()


def next_action_prompt(
    user_id: str,
    cycle_status: str,
    goals_count: int,
    goals_submitted_count: int,
    goals_approved_count: int,
    checkins_count: int,
    days_since_last_checkin: int,
    pending_approvals: int,
) -> str:
    return f"""
Analyze the user's current state in their performance cycle and determine
the most important action they should take right now.

User ID: {user_id}
Cycle Status: {cycle_status}
Total Goals: {goals_count}
Goals Submitted: {goals_submitted_count}
Goals Approved: {goals_approved_count}
Check-ins Submitted: {checkins_count}
Days Since Last Check-in: {days_since_last_checkin}
Pending Approvals Waiting for User: {pending_approvals}

Priority Logic (in order):
1. If no goals → "create_goals"
2. If goals not submitted → "submit_goals"
3. If goals not approved → "wait_approval"
4. If check-in due (>21 days) → "submit_checkin"
5. If pending approvals → "review_pending"
6. If on track → "on_track"

Return JSON ONLY:
{{
  "action": "create_goals|submit_goals|wait_approval|submit_checkin|review_pending|on_track",
  "message": "User-friendly message about what to do next",
  "priority": "high|medium|low",
  "cta": "Call-to-action button text",
  "url": "URL to navigate to or null"
}}
""".strip()
