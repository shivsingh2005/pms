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
