-- Manager Team Dashboard metric queries

-- Per-employee progress percentage
SELECT COALESCE(AVG(progress), 0) AS overall_progress
FROM goals
WHERE user_id = :employee_id;

-- Per-employee completed goals
SELECT COUNT(*) AS goals_completed
FROM goals
WHERE user_id = :employee_id
  AND progress = 100;

-- Per-employee check-in count
SELECT COUNT(*) AS checkin_count
FROM checkins
WHERE employee_id = :employee_id;
