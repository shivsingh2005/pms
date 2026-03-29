-- Employees table schema + 30-row seed with hierarchy
-- Run after migration 20260320_0005 has been applied.

-- Optional standalone schema SQL (for direct SQL setups)
CREATE TABLE IF NOT EXISTS employees (
    id UUID PRIMARY KEY,
    employee_code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    role user_role NOT NULL,
    title TEXT,
    department TEXT,
    manager_id UUID REFERENCES employees(id) ON DELETE SET NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO employees (id, employee_code, name, email, role, title, department, manager_id, is_active) VALUES
('00000000-0000-0000-0000-000000000001','EMP001','Arjun Mehta','arjun.mehta@acmepms.com','admin','Chief Admin','Executive',NULL,TRUE),
('00000000-0000-0000-0000-000000000002','EMP002','Nisha Verma','nisha.verma@acmepms.com','hr','HR Business Partner','HR','00000000-0000-0000-0000-000000000001',TRUE),
('00000000-0000-0000-0000-000000000003','EMP003','Rahul Kapoor','rahul.kapoor@acmepms.com','hr','Talent Operations Specialist','HR','00000000-0000-0000-0000-000000000001',TRUE),
('00000000-0000-0000-0000-000000000010','EMP004','Priya Iyer','priya.iyer@acmepms.com','manager','Engineering Manager I','Engineering','00000000-0000-0000-0000-000000000001',TRUE),
('00000000-0000-0000-0000-000000000011','EMP005','Karan Shah','karan.shah@acmepms.com','manager','Engineering Manager II','Engineering','00000000-0000-0000-0000-000000000001',TRUE),
('00000000-0000-0000-0000-000000000012','EMP006','Meera Nair','meera.nair@acmepms.com','manager','Sales Manager','Sales','00000000-0000-0000-0000-000000000001',TRUE),
('00000000-0000-0000-0000-000000000013','EMP007','Vikram Sethi','vikram.sethi@acmepms.com','manager','HR Operations Manager','HR Ops','00000000-0000-0000-0000-000000000001',TRUE),
('00000000-0000-0000-0000-000000000020','EMP008','Devansh Malhotra','devansh.malhotra@acmepms.com','leadership','Team Lead - Backend','Engineering','00000000-0000-0000-0000-000000000010',TRUE),
('00000000-0000-0000-0000-000000000021','EMP009','Sana Qureshi','sana.qureshi@acmepms.com','leadership','Team Lead - Frontend','Engineering','00000000-0000-0000-0000-000000000010',TRUE),
('00000000-0000-0000-0000-000000000022','EMP010','Amit Bhosale','amit.bhosale@acmepms.com','leadership','Team Lead - Sales','Sales','00000000-0000-0000-0000-000000000012',TRUE),
('00000000-0000-0000-0000-000000000101','EMP011','Shiv Menon','shiv.menon@acmepms.com','employee','Backend Developer','Engineering','00000000-0000-0000-0000-000000000020',TRUE),
('00000000-0000-0000-0000-000000000102','EMP012','Ritika Das','ritika.das@acmepms.com','employee','Backend Developer','Engineering','00000000-0000-0000-0000-000000000020',TRUE),
('00000000-0000-0000-0000-000000000103','EMP013','Ankit Jain','ankit.jain@acmepms.com','employee','Backend Developer','Engineering','00000000-0000-0000-0000-000000000020',TRUE),
('00000000-0000-0000-0000-000000000104','EMP014','Pooja Rana','pooja.rana@acmepms.com','employee','Backend Developer','Engineering','00000000-0000-0000-0000-000000000020',TRUE),
('00000000-0000-0000-0000-000000000105','EMP015','Neha Kulkarni','neha.kulkarni@acmepms.com','employee','Frontend Developer','Engineering','00000000-0000-0000-0000-000000000021',TRUE),
('00000000-0000-0000-0000-000000000106','EMP016','Rohan Batra','rohan.batra@acmepms.com','employee','Frontend Developer','Engineering','00000000-0000-0000-0000-000000000021',TRUE),
('00000000-0000-0000-0000-000000000107','EMP017','Isha Chawla','isha.chawla@acmepms.com','employee','Frontend Developer','Engineering','00000000-0000-0000-0000-000000000021',TRUE),
('00000000-0000-0000-0000-000000000108','EMP018','Tarun Arora','tarun.arora@acmepms.com','employee','Frontend Developer','Engineering','00000000-0000-0000-0000-000000000021',TRUE),
('00000000-0000-0000-0000-000000000109','EMP019','Aayushi Gupta','aayushi.gupta@acmepms.com','employee','QA Engineer','Engineering','00000000-0000-0000-0000-000000000011',TRUE),
('00000000-0000-0000-0000-000000000110','EMP020','Harshit Tandon','harshit.tandon@acmepms.com','employee','QA Engineer','Engineering','00000000-0000-0000-0000-000000000011',TRUE),
('00000000-0000-0000-0000-000000000111','EMP021','Nupur Khandelwal','nupur.khandelwal@acmepms.com','employee','DevOps Engineer','Engineering','00000000-0000-0000-0000-000000000011',TRUE),
('00000000-0000-0000-0000-000000000112','EMP022','Yash Patil','yash.patil@acmepms.com','employee','DevOps Engineer','Engineering','00000000-0000-0000-0000-000000000011',TRUE),
('00000000-0000-0000-0000-000000000113','EMP023','Kavya Sen','kavya.sen@acmepms.com','employee','Sales Executive','Sales','00000000-0000-0000-0000-000000000022',TRUE),
('00000000-0000-0000-0000-000000000114','EMP024','Gaurav Khanna','gaurav.khanna@acmepms.com','employee','Sales Executive','Sales','00000000-0000-0000-0000-000000000022',TRUE),
('00000000-0000-0000-0000-000000000115','EMP025','Simran Kaur','simran.kaur@acmepms.com','employee','Sales Executive','Sales','00000000-0000-0000-0000-000000000022',TRUE),
('00000000-0000-0000-0000-000000000116','EMP026','Aditya Joshi','aditya.joshi@acmepms.com','employee','Sales Executive','Sales','00000000-0000-0000-0000-000000000022',TRUE),
('00000000-0000-0000-0000-000000000117','EMP027','Shruti Mishra','shruti.mishra@acmepms.com','employee','HR Executive','HR Ops','00000000-0000-0000-0000-000000000013',TRUE),
('00000000-0000-0000-0000-000000000118','EMP028','Manav Ahuja','manav.ahuja@acmepms.com','employee','HR Executive','HR Ops','00000000-0000-0000-0000-000000000013',TRUE),
('00000000-0000-0000-0000-000000000119','EMP029','Tanvi Rao','tanvi.rao@acmepms.com','employee','Data Analyst','Engineering','00000000-0000-0000-0000-000000000011',TRUE),
('00000000-0000-0000-0000-000000000120','EMP030','Armaan Gill','armaan.gill@acmepms.com','employee','Customer Support Specialist','Sales','00000000-0000-0000-0000-000000000012',TRUE)
ON CONFLICT (employee_code) DO NOTHING;
