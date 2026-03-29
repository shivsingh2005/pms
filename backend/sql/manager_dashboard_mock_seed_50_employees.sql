-- Manager Team Dashboard mock seed
-- Creates 50 employees with 3-5 goals, 5-10 check-ins, and 2-4 ratings each.
-- Safe to rerun by domain scope cleanup.

BEGIN;

-- 1) Organization
INSERT INTO organizations (id, name, domain, created_at, updated_at)
VALUES (
  '98000000-0000-0000-0000-000000000000'::uuid,
  'Manager Dashboard Test Org',
  'managerdash.local',
  now(),
  now()
)
ON CONFLICT (domain) DO UPDATE
SET name = EXCLUDED.name, updated_at = now();

-- 2) Cleanup previously seeded manager dashboard records
WITH seeded_users AS (
  SELECT id
  FROM users
  WHERE organization_id = '98000000-0000-0000-0000-000000000000'::uuid
    AND email LIKE '%@managerdash.local'
), seeded_goals AS (
  SELECT id FROM goals WHERE user_id IN (SELECT id FROM seeded_users)
)
DELETE FROM ratings WHERE goal_id IN (SELECT id FROM seeded_goals);

WITH seeded_users AS (
  SELECT id
  FROM users
  WHERE organization_id = '98000000-0000-0000-0000-000000000000'::uuid
    AND email LIKE '%@managerdash.local'
), seeded_goals AS (
  SELECT id FROM goals WHERE user_id IN (SELECT id FROM seeded_users)
)
DELETE FROM checkins WHERE goal_id IN (SELECT id FROM seeded_goals);

WITH seeded_users AS (
  SELECT id
  FROM users
  WHERE organization_id = '98000000-0000-0000-0000-000000000000'::uuid
    AND email LIKE '%@managerdash.local'
)
DELETE FROM performance_reviews WHERE employee_id IN (SELECT id FROM seeded_users);

WITH seeded_users AS (
  SELECT id
  FROM users
  WHERE organization_id = '98000000-0000-0000-0000-000000000000'::uuid
    AND email LIKE '%@managerdash.local'
)
DELETE FROM goals WHERE user_id IN (SELECT id FROM seeded_users);

DELETE FROM employees WHERE email LIKE '%@managerdash.local';
DELETE FROM users WHERE email LIKE '%@managerdash.local';

-- 3) Seed one manager (plus role access as manager + employee)
INSERT INTO users (
  id, google_id, email, name, profile_picture, role, roles,
  organization_id, manager_id, department, title, is_active,
  created_at, updated_at
)
VALUES (
  '98000000-0000-0000-0000-000000000001'::uuid,
  'mgr-seed-001',
  'manager@managerdash.local',
  'Manager Seed',
  NULL,
  'manager',
  ARRAY['employee','manager']::text[],
  '98000000-0000-0000-0000-000000000000'::uuid,
  NULL,
  'Engineering',
  'Engineering Manager',
  TRUE,
  now(),
  now()
);

-- 4) Seed 50 employees under the manager
WITH employee_seed AS (
  SELECT generate_series(1, 50) AS idx
)
INSERT INTO users (
  id, google_id, email, name, profile_picture, role, roles,
  organization_id, manager_id, department, title, is_active,
  created_at, updated_at
)
SELECT
  ('98000000-0000-0000-0000-' || lpad((1000 + idx)::text, 12, '0'))::uuid,
  'mgr-emp-seed-' || lpad(idx::text, 3, '0'),
  'employee' || lpad(idx::text, 2, '0') || '@managerdash.local',
  'Employee ' || lpad(idx::text, 2, '0'),
  NULL,
  'employee',
  ARRAY['employee']::text[],
  '98000000-0000-0000-0000-000000000000'::uuid,
  '98000000-0000-0000-0000-000000000001'::uuid,
  CASE
    WHEN idx % 4 = 0 THEN 'Engineering'
    WHEN idx % 4 = 1 THEN 'Product'
    WHEN idx % 4 = 2 THEN 'Sales'
    ELSE 'HR'
  END,
  CASE
    WHEN idx % 5 = 0 THEN 'QA Engineer'
    WHEN idx % 5 = 1 THEN 'Backend Developer'
    WHEN idx % 5 = 2 THEN 'Frontend Developer'
    WHEN idx % 5 = 3 THEN 'Sales Executive'
    ELSE 'HR Executive'
  END,
  TRUE,
  now(),
  now()
FROM employee_seed;

-- 5) Goals: 3-5 per employee
WITH employee_users AS (
  SELECT id AS employee_id, manager_id, department, title
  FROM users
  WHERE organization_id = '98000000-0000-0000-0000-000000000000'::uuid
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
      'Improve execution quality',
      'Increase customer outcomes',
      'Strengthen delivery speed',
      'Improve reliability posture',
      'Scale collaboration impact'
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
  ('98100000-0000-0000-0000-' || lpad(seq::text, 12, '0'))::uuid,
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

-- 6) Check-ins: 5-10 per employee
WITH employee_users AS (
  SELECT id AS employee_id, manager_id
  FROM users
  WHERE organization_id = '98000000-0000-0000-0000-000000000000'::uuid
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
    now() - ((5 + cs.idx * 6 + floor(random() * 20))::text || ' days')::interval AS meeting_date
  FROM checkin_seed cs
)
INSERT INTO checkins (
  id, goal_id, employee_id, manager_id, meeting_date,
  status, meeting_link, transcript, summary, created_at
)
SELECT
  ('98200000-0000-0000-0000-' || lpad(seq::text, 12, '0'))::uuid,
  goal_id,
  employee_id,
  manager_id,
  meeting_date,
  'completed'::checkin_status,
  NULL,
  'Discussed execution updates, blockers, and next actions.',
  'Check-in completed with actionable follow-ups.',
  meeting_date
FROM checkin_rows;

-- 7) Ratings: 2-4 per employee
WITH employee_users AS (
  SELECT
    e.id AS employee_id,
    e.manager_id,
    ARRAY(
      SELECT p.id
      FROM users p
      WHERE p.organization_id = e.organization_id
        AND p.role = 'employee'
        AND p.id <> e.id
      LIMIT 10
    ) AS peer_ids
  FROM users e
  WHERE e.organization_id = '98000000-0000-0000-0000-000000000000'::uuid
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
  CROSS JOIN LATERAL generate_series(1, 2 + floor(random() * 3)::int) AS gs(idx)
), rating_rows AS (
  SELECT
    rs.seq,
    rs.employee_id,
    CASE
      WHEN rs.idx <= 2 THEN rs.manager_id
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
  ('98300000-0000-0000-0000-' || lpad(seq::text, 12, '0'))::uuid,
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
    WHEN idx <= 2 THEN 'Manager feedback: Performance aligned with cycle expectations.'
    ELSE 'Peer feedback: Positive collaboration and delivery partnership.'
  END,
  now() - ((seq % 180) || ' days')::interval
FROM rating_rows;

COMMIT;

-- Optional checks
-- SELECT count(*) FROM users WHERE organization_id='98000000-0000-0000-0000-000000000000'::uuid AND role='employee';
-- SELECT min(cnt), max(cnt) FROM (SELECT user_id, count(*) cnt FROM goals GROUP BY user_id) x;
-- SELECT min(cnt), max(cnt) FROM (SELECT employee_id, count(*) cnt FROM checkins GROUP BY employee_id) x;
-- SELECT min(cnt), max(cnt) FROM (SELECT employee_id, count(*) cnt FROM ratings GROUP BY employee_id) x;
