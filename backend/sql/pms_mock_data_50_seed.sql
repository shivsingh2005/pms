-- PMS realistic mock data seed (50 users) for dashboard testing
-- Target: PostgreSQL
-- Safe to rerun: this script deletes only prior seeded records under mockpms.local

BEGIN;

-- 1) Organization
INSERT INTO organizations (id, name, domain, created_at, updated_at)
VALUES (
  '90000000-0000-0000-0000-000000000000'::uuid,
  'Mock PMS Corp',
  'mockpms.local',
  now(),
  now()
)
ON CONFLICT (domain) DO UPDATE
SET name = EXCLUDED.name, updated_at = now();

-- Active performance cycle for analytics and lifecycle testing
INSERT INTO performance_cycles (
  id, organization_id, name, cycle_type, framework,
  start_date, end_date, goal_setting_deadline, self_review_deadline,
  checkin_cap_per_quarter, ai_usage_cap_per_quarter, is_active,
  created_at, updated_at
)
SELECT
  '90000000-0000-0000-0000-000000000050'::uuid,
  '90000000-0000-0000-0000-000000000000'::uuid,
  'FY2026 Q2',
  'quarterly',
  'OKR',
  DATE '2026-04-01',
  DATE '2026-06-30',
  DATE '2026-04-20',
  DATE '2026-06-25',
  8,
  20,
  TRUE,
  now(),
  now()
WHERE NOT EXISTS (
  SELECT 1
  FROM performance_cycles pc
  WHERE pc.id = '90000000-0000-0000-0000-000000000050'::uuid
);

-- 2) Cleanup previous seeded data (domain-scoped)
WITH seeded_users AS (
  SELECT id
  FROM users
  WHERE organization_id = '90000000-0000-0000-0000-000000000000'::uuid
    AND email LIKE '%@mockpms.local'
)
DELETE FROM ai_usage_logs WHERE user_id IN (SELECT id FROM seeded_users);

WITH seeded_users AS (
  SELECT id
  FROM users
  WHERE organization_id = '90000000-0000-0000-0000-000000000000'::uuid
    AND email LIKE '%@mockpms.local'
)
DELETE FROM ai_usage WHERE user_id IN (SELECT id FROM seeded_users);

WITH seeded_users AS (
  SELECT id
  FROM users
  WHERE organization_id = '90000000-0000-0000-0000-000000000000'::uuid
    AND email LIKE '%@mockpms.local'
), seeded_goals AS (
  SELECT id FROM goals WHERE user_id IN (SELECT id FROM seeded_users)
)
DELETE FROM ratings WHERE goal_id IN (SELECT id FROM seeded_goals);

WITH seeded_users AS (
  SELECT id
  FROM users
  WHERE organization_id = '90000000-0000-0000-0000-000000000000'::uuid
    AND email LIKE '%@mockpms.local'
), seeded_goals AS (
  SELECT id FROM goals WHERE user_id IN (SELECT id FROM seeded_users)
)
DELETE FROM checkins WHERE goal_id IN (SELECT id FROM seeded_goals);

WITH seeded_users AS (
  SELECT id
  FROM users
  WHERE organization_id = '90000000-0000-0000-0000-000000000000'::uuid
    AND email LIKE '%@mockpms.local'
)
DELETE FROM performance_reviews WHERE employee_id IN (SELECT id FROM seeded_users);

WITH seeded_users AS (
  SELECT id
  FROM users
  WHERE organization_id = '90000000-0000-0000-0000-000000000000'::uuid
    AND email LIKE '%@mockpms.local'
)
DELETE FROM goals WHERE user_id IN (SELECT id FROM seeded_users);

DELETE FROM employees WHERE email LIKE '%@mockpms.local';
DELETE FROM users WHERE email LIKE '%@mockpms.local';

-- 3) Insert users
-- Distribution:
-- 1 Admin, 3 HR, 6 Managers, 40 Employees

-- 3a) Admin
INSERT INTO users (
  id, google_id, email, name, profile_picture, role, roles,
  organization_id, manager_id, department, title, is_active,
  created_at, updated_at
)
VALUES (
  '90000000-0000-0000-0000-000000000001'::uuid,
  'mock-google-admin-001',
  'admin@mockpms.local',
  'Arjun Mehta',
  NULL,
  'admin',
  ARRAY['admin']::text[],
  '90000000-0000-0000-0000-000000000000'::uuid,
  NULL,
  'HR',
  'Admin',
  TRUE,
  now(),
  now()
);

-- 3b) HR (3)
INSERT INTO users (
  id, google_id, email, name, profile_picture, role, roles,
  organization_id, manager_id, department, title, is_active,
  created_at, updated_at
)
VALUES
(
  '90000000-0000-0000-0000-000000000010'::uuid,
  'mock-google-hr-010', 'nisha.verma@mockpms.local', 'Nisha Verma', NULL,
  'hr', ARRAY['hr']::text[],
  '90000000-0000-0000-0000-000000000000'::uuid,
  '90000000-0000-0000-0000-000000000001'::uuid,
  'HR', 'HR Executive', TRUE, now(), now()
),
(
  '90000000-0000-0000-0000-000000000011'::uuid,
  'mock-google-hr-011', 'rahul.kapoor@mockpms.local', 'Rahul Kapoor', NULL,
  'hr', ARRAY['hr']::text[],
  '90000000-0000-0000-0000-000000000000'::uuid,
  '90000000-0000-0000-0000-000000000001'::uuid,
  'HR', 'HR Executive', TRUE, now(), now()
),
(
  '90000000-0000-0000-0000-000000000012'::uuid,
  'mock-google-hr-012', 'aisha.khan@mockpms.local', 'Aisha Khan', NULL,
  'hr', ARRAY['hr']::text[],
  '90000000-0000-0000-0000-000000000000'::uuid,
  '90000000-0000-0000-0000-000000000001'::uuid,
  'HR', 'HR Executive', TRUE, now(), now()
);

-- 3c) Managers (6)
INSERT INTO users (
  id, google_id, email, name, profile_picture, role, roles,
  organization_id, manager_id, department, title, is_active,
  created_at, updated_at
)
VALUES
(
  '90000000-0000-0000-0000-000000000101'::uuid,
  'mock-google-mgr-101', 'priya.iyer@mockpms.local', 'Priya Iyer', NULL,
  'manager', ARRAY['employee','manager']::text[],
  '90000000-0000-0000-0000-000000000000'::uuid,
  '90000000-0000-0000-0000-000000000001'::uuid,
  'Engineering', 'Engineering Manager', TRUE, now(), now()
),
(
  '90000000-0000-0000-0000-000000000102'::uuid,
  'mock-google-mgr-102', 'karan.shah@mockpms.local', 'Karan Shah', NULL,
  'manager', ARRAY['employee','manager']::text[],
  '90000000-0000-0000-0000-000000000000'::uuid,
  '90000000-0000-0000-0000-000000000001'::uuid,
  'Engineering', 'Engineering Manager', TRUE, now(), now()
),
(
  '90000000-0000-0000-0000-000000000103'::uuid,
  'mock-google-mgr-103', 'meera.nair@mockpms.local', 'Meera Nair', NULL,
  'manager', ARRAY['employee','manager']::text[],
  '90000000-0000-0000-0000-000000000000'::uuid,
  '90000000-0000-0000-0000-000000000001'::uuid,
  'Sales', 'Sales Manager', TRUE, now(), now()
),
(
  '90000000-0000-0000-0000-000000000104'::uuid,
  'mock-google-mgr-104', 'vikram.sethi@mockpms.local', 'Vikram Sethi', NULL,
  'manager', ARRAY['employee','manager']::text[],
  '90000000-0000-0000-0000-000000000000'::uuid,
  '90000000-0000-0000-0000-000000000001'::uuid,
  'Sales', 'Sales Manager', TRUE, now(), now()
),
(
  '90000000-0000-0000-0000-000000000105'::uuid,
  'mock-google-mgr-105', 'ananya.roy@mockpms.local', 'Ananya Roy', NULL,
  'manager', ARRAY['employee','manager']::text[],
  '90000000-0000-0000-0000-000000000000'::uuid,
  '90000000-0000-0000-0000-000000000001'::uuid,
  'Product', 'Product Manager', TRUE, now(), now()
),
(
  '90000000-0000-0000-0000-000000000106'::uuid,
  'mock-google-mgr-106', 'harshit.tandon@mockpms.local', 'Harshit Tandon', NULL,
  'manager', ARRAY['employee','manager']::text[],
  '90000000-0000-0000-0000-000000000000'::uuid,
  '90000000-0000-0000-0000-000000000001'::uuid,
  'HR', 'HR Operations Manager', TRUE, now(), now()
);

-- 3d) Employees (40)
-- Manager allocation: 7,7,7,7,6,6
WITH employee_seed AS (
  SELECT *
  FROM (
    VALUES
      (1,  'Shiv Menon'), (2,  'Ritika Das'), (3,  'Ankit Jain'), (4,  'Pooja Rana'), (5,  'Neha Kulkarni'),
      (6,  'Rohan Batra'), (7,  'Isha Chawla'), (8,  'Tarun Arora'), (9,  'Aayushi Gupta'), (10, 'Yash Patil'),
      (11, 'Kavya Sen'), (12, 'Gaurav Khanna'), (13, 'Simran Kaur'), (14, 'Aditya Joshi'), (15, 'Shruti Mishra'),
      (16, 'Manav Ahuja'), (17, 'Tanvi Rao'), (18, 'Armaan Gill'), (19, 'Devansh Malhotra'), (20, 'Sana Qureshi'),
      (21, 'Amit Bhosale'), (22, 'Preeti Nanda'), (23, 'Sakshi Arora'), (24, 'Ritesh Kumar'), (25, 'Vani Shetty'),
      (26, 'Kunal Grover'), (27, 'Mihir Anand'), (28, 'Diya Narang'), (29, 'Nitin Suri'), (30, 'Pallavi Joshi'),
      (31, 'Radhika Iyer'), (32, 'Karthik Rao'), (33, 'Sonia Bhatia'), (34, 'Pranav Reddy'), (35, 'Esha Malhotra'),
      (36, 'Naveen Pillai'), (37, 'Bhavna Kapur'), (38, 'Arpit Verma'), (39, 'Irfan Sheikh'), (40, 'Mona Luthra')
  ) AS t(emp_no, full_name)
), mapped AS (
  SELECT
    emp_no,
    full_name,
    CASE
      WHEN emp_no BETWEEN 1  AND 7  THEN '90000000-0000-0000-0000-000000000101'::uuid
      WHEN emp_no BETWEEN 8  AND 14 THEN '90000000-0000-0000-0000-000000000102'::uuid
      WHEN emp_no BETWEEN 15 AND 21 THEN '90000000-0000-0000-0000-000000000103'::uuid
      WHEN emp_no BETWEEN 22 AND 28 THEN '90000000-0000-0000-0000-000000000104'::uuid
      WHEN emp_no BETWEEN 29 AND 34 THEN '90000000-0000-0000-0000-000000000105'::uuid
      ELSE                                 '90000000-0000-0000-0000-000000000106'::uuid
    END AS manager_id,
    CASE
      WHEN emp_no BETWEEN 1  AND 14 THEN 'Engineering'
      WHEN emp_no BETWEEN 15 AND 28 THEN 'Sales'
      WHEN emp_no BETWEEN 29 AND 34 THEN 'Product'
      ELSE                                 'HR'
    END AS department,
    CASE
      WHEN emp_no % 5 = 0 THEN 'QA Engineer'
      WHEN emp_no % 5 = 1 THEN 'Backend Developer'
      WHEN emp_no % 5 = 2 THEN 'Frontend Developer'
      WHEN emp_no % 5 = 3 THEN 'Sales Executive'
      ELSE                    'HR Executive'
    END AS title
  FROM employee_seed
)
INSERT INTO users (
  id, google_id, email, name, profile_picture, role, roles,
  organization_id, manager_id, department, title, is_active,
  created_at, updated_at
)
SELECT
  ('90000000-0000-0000-0000-' || lpad((200 + emp_no)::text, 12, '0'))::uuid,
  'mock-google-emp-' || lpad(emp_no::text, 3, '0'),
  'emp' || lpad(emp_no::text, 2, '0') || '@mockpms.local',
  full_name,
  NULL,
  'employee',
  ARRAY['employee']::text[],
  '90000000-0000-0000-0000-000000000000'::uuid,
  manager_id,
  department,
  title,
  TRUE,
  now(),
  now()
FROM mapped;

-- 4) Mirror into employees table (same 50 records)
INSERT INTO employees (
  id, employee_code, name, email, role, title, department, manager_id, is_active, created_at, updated_at
)
SELECT
  u.id,
  'EMP' || lpad(row_number() OVER (ORDER BY u.email)::text, 3, '0') AS employee_code,
  u.name,
  u.email,
  u.role,
  u.title,
  u.department,
  u.manager_id,
  u.is_active,
  now(),
  now()
FROM users u
WHERE u.organization_id = '90000000-0000-0000-0000-000000000000'::uuid
  AND u.email LIKE '%@mockpms.local';

-- 5) Goals: 3-5 per employee (40 employees)
WITH employee_users AS (
  SELECT id AS employee_id, manager_id, department, title
  FROM users
  WHERE organization_id = '90000000-0000-0000-0000-000000000000'::uuid
    AND role = 'employee'
), goal_seed AS (
  SELECT
    eu.employee_id,
    eu.manager_id,
    eu.department,
    eu.title,
    gs.goal_idx,
    row_number() OVER (ORDER BY eu.employee_id, gs.goal_idx) AS seq,
    random() AS r_progress,
    random() AS r_framework,
    random() AS r_weight
  FROM employee_users eu
  CROSS JOIN LATERAL generate_series(1, 3 + floor(random() * 3)::int) AS gs(goal_idx)
), goal_rows AS (
  SELECT
    seq,
    employee_id,
    manager_id,
    (ARRAY[
      'Improve delivery quality',
      'Increase customer impact',
      'Strengthen execution speed',
      'Improve collaboration outcomes',
      'Raise operational reliability'
    ])[1 + (seq % 5)] || ' - ' || department AS title,
    'Role: ' || coalesce(title, 'Contributor') || '. Goal index ' || goal_idx || ' with measurable KPI targets.' AS description,
    round((10 + floor(r_weight * 31))::numeric, 1)::float AS weightage,
    CASE
      WHEN r_progress < 0.20 THEN 100.0
      WHEN r_progress < 0.70 THEN round((40 + random() * 59)::numeric, 1)::float
      ELSE round((random() * 35)::numeric, 1)::float
    END AS progress,
    CASE
      WHEN r_framework < 0.34 THEN 'OKR'
      WHEN r_framework < 0.67 THEN 'MBO'
      ELSE 'Hybrid'
    END AS framework,
    (random() < 0.35) AS is_ai_generated
  FROM goal_seed
)
INSERT INTO goals (
  id, user_id, assigned_by, assigned_to, title, description,
  weightage, status, progress, framework, is_ai_generated,
  created_at, updated_at
)
SELECT
  ('91000000-0000-0000-0000-' || lpad(seq::text, 12, '0'))::uuid,
  employee_id,
  manager_id,
  employee_id,
  title,
  description,
  weightage,
  CASE
    WHEN progress = 100.0 THEN 'approved'::goal_status
    WHEN progress < 20.0 THEN 'draft'::goal_status
    WHEN progress < 70.0 THEN 'submitted'::goal_status
    ELSE 'approved'::goal_status
  END,
  progress,
  framework::goal_framework,
  is_ai_generated,
  now() - ((seq % 120) || ' days')::interval,
  now() - ((seq % 30) || ' days')::interval
FROM goal_rows;

-- 6) Check-ins: 5-10 per employee, all completed
WITH employee_users AS (
  SELECT id AS employee_id, manager_id
  FROM users
  WHERE organization_id = '90000000-0000-0000-0000-000000000000'::uuid
    AND role = 'employee'
), checkin_seed AS (
  SELECT
    eu.employee_id,
    eu.manager_id,
    gs.idx,
    row_number() OVER (ORDER BY eu.employee_id, gs.idx) AS seq
  FROM employee_users eu
  CROSS JOIN LATERAL generate_series(1, 5 + floor(random() * 6)::int) AS gs(idx)
), checkin_rows AS (
  SELECT
    cs.seq,
    cs.employee_id,
    cs.manager_id,
    (
      SELECT g.id
      FROM goals g
      WHERE g.user_id = cs.employee_id
      ORDER BY random()
      LIMIT 1
    ) AS goal_id,
    now() - ((5 + cs.idx * 7 + floor(random() * 15))::text || ' days')::interval AS meeting_date
  FROM checkin_seed cs
)
INSERT INTO checkins (
  id, goal_id, employee_id, manager_id, meeting_date,
  status, meeting_link, transcript, summary, created_at
)
SELECT
  ('92000000-0000-0000-0000-' || lpad(seq::text, 12, '0'))::uuid,
  goal_id,
  employee_id,
  manager_id,
  meeting_date,
  'completed'::checkin_status,
  NULL,
  NULL,
  'Completed check-in covering blockers, progress updates, and next-week actions.',
  meeting_date
FROM checkin_rows;

-- 7) Ratings: 5 per employee with mixed labels
--    Entries 1-3: manager ratings
--    Entries 4-5: peer feedback (stored in comments)
WITH employee_users AS (
  SELECT
    e.id AS employee_id,
    e.manager_id,
    ARRAY(
      SELECT p.id
      FROM users p
      WHERE p.organization_id = e.organization_id
        AND p.role = 'employee'
        AND p.manager_id = e.manager_id
        AND p.id <> e.id
    ) AS peer_ids
  FROM users e
  WHERE e.organization_id = '90000000-0000-0000-0000-000000000000'::uuid
    AND e.role = 'employee'
), rating_seed AS (
  SELECT
    eu.employee_id,
    eu.manager_id,
    eu.peer_ids,
    gs.idx,
    row_number() OVER (ORDER BY eu.employee_id, gs.idx) AS seq,
    random() AS rv
  FROM employee_users eu
  CROSS JOIN generate_series(1, 5) AS gs(idx)
), rating_rows AS (
  SELECT
    rs.seq,
    rs.employee_id,
    CASE
      WHEN rs.idx <= 3 THEN rs.manager_id
      ELSE coalesce(
        rs.peer_ids[1 + floor(random() * greatest(cardinality(rs.peer_ids), 1))::int],
        rs.manager_id
      )
    END AS rater_id,
    (
      SELECT g.id
      FROM goals g
      WHERE g.user_id = rs.employee_id
      ORDER BY random()
      LIMIT 1
    ) AS goal_id,
    CASE
      WHEN rs.rv < 0.12 THEN 1
      WHEN rs.rv < 0.30 THEN 2
      WHEN rs.rv < 0.62 THEN 3
      WHEN rs.rv < 0.88 THEN 4
      ELSE 5
    END AS rating_value,
    rs.idx
  FROM rating_seed rs
)
INSERT INTO ratings (
  id, goal_id, manager_id, employee_id, rating, rating_label, comments, created_at
)
SELECT
  ('93000000-0000-0000-0000-' || lpad(seq::text, 12, '0'))::uuid,
  goal_id,
  rater_id,
  employee_id,
  rating_value,
  CASE rating_value
    WHEN 5 THEN 'EE'::rating_label
    WHEN 4 THEN 'DE'::rating_label
    WHEN 3 THEN 'ME'::rating_label
    WHEN 2 THEN 'SME'::rating_label
    ELSE 'NI'::rating_label
  END,
  CASE
    WHEN idx <= 3 THEN 'Manager feedback: Performance aligned with current cycle goals and delivery expectations.'
    ELSE 'Peer feedback: Strong collaboration signal with useful communication and support behavior.'
  END,
  now() - ((seq % 180) || ' days')::interval
FROM rating_rows;

-- 8) Performance reviews (4 quarters per employee)
WITH employee_users AS (
  SELECT id AS employee_id, manager_id
  FROM users
  WHERE organization_id = '90000000-0000-0000-0000-000000000000'::uuid
    AND role = 'employee'
), review_seed AS (
  SELECT
    eu.employee_id,
    eu.manager_id,
    q.quarter,
    row_number() OVER (ORDER BY eu.employee_id, q.quarter) AS seq,
    round((2.0 + random() * 3.0)::numeric, 2)::float AS overall_rating
  FROM employee_users eu
  CROSS JOIN (VALUES (1), (2), (3), (4)) AS q(quarter)
)
INSERT INTO performance_reviews (
  id, employee_id, manager_id, cycle_year, cycle_quarter,
  overall_rating, summary, strengths, weaknesses, growth_areas, created_at
)
SELECT
  ('94000000-0000-0000-0000-' || lpad(seq::text, 12, '0'))::uuid,
  employee_id,
  manager_id,
  2026,
  quarter,
  overall_rating,
  'Quarterly review summary with measurable performance outcomes.',
  'Execution discipline, ownership, and delivery consistency.',
  'Scope balancing and escalation timing under pressure.',
  'Improve prioritization and proactive risk communication.',
  now() - ((seq % 250) || ' days')::interval
FROM review_seed;

-- 9) AI usage logs: random logs per user
WITH seeded_users AS (
  SELECT id
  FROM users
  WHERE organization_id = '90000000-0000-0000-0000-000000000000'::uuid
    AND email LIKE '%@mockpms.local'
), usage_seed AS (
  SELECT
    su.id AS user_id,
    gs.idx,
    row_number() OVER (ORDER BY su.id, gs.idx) AS seq,
    (ARRAY[
      'goal_suggestions',
      'role_based_goal_generation',
      'team_goal_allotment',
      'checkin_summary',
      'feedback_coaching',
      'review_generation',
      'decision_intelligence'
    ])[1 + floor(random() * 7)::int] AS feature_name
  FROM seeded_users su
  CROSS JOIN LATERAL generate_series(1, 1 + floor(random() * 5)::int) AS gs(idx)
)
INSERT INTO ai_usage_logs (
  id, user_id, feature_name, prompt_tokens, response_tokens, created_at
)
SELECT
  ('95000000-0000-0000-0000-' || lpad(seq::text, 12, '0'))::uuid,
  user_id,
  feature_name,
  (80 + floor(random() * 700))::int,
  (40 + floor(random() * 500))::int,
  now() - ((seq % 120) || ' days')::interval
FROM usage_seed;

-- 10) AI usage aggregate table from logs
WITH agg AS (
  SELECT
    user_id,
    feature_name,
    EXTRACT(QUARTER FROM created_at)::int AS quarter,
    EXTRACT(YEAR FROM created_at)::int AS year,
    count(*)::int AS usage_count,
    row_number() OVER (ORDER BY user_id, feature_name, EXTRACT(YEAR FROM created_at), EXTRACT(QUARTER FROM created_at)) AS seq
  FROM ai_usage_logs
  WHERE user_id IN (
    SELECT id
    FROM users
    WHERE organization_id = '90000000-0000-0000-0000-000000000000'::uuid
      AND email LIKE '%@mockpms.local'
  )
  GROUP BY user_id, feature_name, EXTRACT(YEAR FROM created_at), EXTRACT(QUARTER FROM created_at)
)
INSERT INTO ai_usage (
  id, user_id, feature_name, usage_count, quarter, year
)
SELECT
  ('96000000-0000-0000-0000-' || lpad(seq::text, 12, '0'))::uuid,
  user_id,
  feature_name,
  usage_count,
  quarter,
  year
FROM agg;

COMMIT;

-- Validation snippets (optional)
-- SELECT role, count(*) FROM users WHERE email LIKE '%@mockpms.local' GROUP BY role ORDER BY role;
-- SELECT manager_id, count(*) AS direct_reports FROM users WHERE role='employee' AND email LIKE '%@mockpms.local' GROUP BY manager_id ORDER BY direct_reports DESC;
-- SELECT min(progress), max(progress), avg(progress) FROM goals g JOIN users u ON u.id=g.user_id WHERE u.email LIKE '%@mockpms.local';
-- SELECT rating_label, count(*) FROM ratings r JOIN users u ON u.id=r.employee_id WHERE u.email LIKE '%@mockpms.local' GROUP BY rating_label ORDER BY rating_label;
