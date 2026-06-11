-- ============================================================
--  SUPERSHOP BANGLADESH — Auth DDL + Seed
--  Adds TABLE 18: app_user  and  TABLE 19: admin_account
--  Run AFTER the main Supershop DDL
-- ============================================================


-- ============================================================
--  TABLE 18: APP_USER
--  Single auth table for EMPLOYEE and CUSTOMER login.
--  Admin uses admin_account directly (different credential type).
--
--  role  : 'EMPLOYEE' → ref_id = employee.emp_id
--          'CUSTOMER' → ref_id = customer.cust_id
--
--  phone UNIQUE — employees and customers cannot share a phone
--  (they are stored in different domain tables, but the login
--   portal disambiguates by the role chosen on the login page)
-- ============================================================
CREATE TABLE app_user (
    user_id         VARCHAR(12)     NOT NULL,
    phone           VARCHAR(15)     NOT NULL,
    password_hash   VARCHAR(255)    NOT NULL,
    role            VARCHAR(10)     NOT NULL,
    ref_id          VARCHAR(12)     NOT NULL,
    is_active       CHAR(1)         DEFAULT 'Y',
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT  au_pk       PRIMARY KEY (user_id),
    CONSTRAINT  check_au_id CHECK (user_id LIKE 'U-%'),
    CONSTRAINT  au_phone    UNIQUE (phone),
    CONSTRAINT  au_role     CHECK (role IN ('EMPLOYEE', 'CUSTOMER')),
    CONSTRAINT  au_active   CHECK (is_active IN ('Y', 'N'))
);


-- ============================================================
--  TABLE 19: ADMIN_ACCOUNT
--  Separate table for super-admin credentials.
--  Uses admin_id + password (not phone).
--  Not linked to employee table — admins are head-office users
--  who may not be branch staff.
-- ============================================================
CREATE TABLE admin_account (
    admin_id        VARCHAR(10)     NOT NULL,
    admin_name      VARCHAR(60)     NOT NULL,
    email           VARCHAR(100)    NOT NULL,
    password_hash   VARCHAR(255)    NOT NULL,
    is_active       CHAR(1)         DEFAULT 'Y',
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT  adm_pk      PRIMARY KEY (admin_id),
    CONSTRAINT  check_adm   CHECK (admin_id LIKE 'ADM-%'),
    CONSTRAINT  adm_email   UNIQUE (email),
    CONSTRAINT  adm_active  CHECK (is_active IN ('Y', 'N'))
);


-- ============================================================
--  SEED: admin_account  (1 super-admin)
--
--  Password: admin123  (bcrypt hash below)
--  Generate a fresh hash in Python:
--      import bcrypt
--      bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode()
-- ============================================================
INSERT INTO admin_account VALUES (
    'ADM-001',
    'Super Admin',
    'admin@supershop.com.bd',
    '$2b$12$PHWcyxLINm22a4/uNYqysOG8tugMdTcqL/LVlZZoqFuB0GHHebu9S',
    'Y',
    CURRENT_TIMESTAMP
);


-- ============================================================
--  SEED: app_user for EMPLOYEES  (20 rows)
--  Password for all: employee123  (replace hash in production)
--
--  Each row links to an emp_id from the employee table.
--  The phone here MUST match employee.phone exactly.
-- ============================================================
INSERT INTO app_user VALUES ('U-000001', '01711-100001', '$2b$12$6X5S.jTi1rkVeaBmpqK27OKBJZsWPEPMnr/rHolF9O7XzmhjFSXtm', 'EMPLOYEE', 'E-00001', 'Y', CURRENT_TIMESTAMP);
INSERT INTO app_user VALUES ('U-000002', '01812-100002', '$2b$12$6X5S.jTi1rkVeaBmpqK27OKBJZsWPEPMnr/rHolF9O7XzmhjFSXtm', 'EMPLOYEE', 'E-00002', 'Y', CURRENT_TIMESTAMP);
INSERT INTO app_user VALUES ('U-000003', '01911-100003', '$2b$12$6X5S.jTi1rkVeaBmpqK27OKBJZsWPEPMnr/rHolF9O7XzmhjFSXtm', 'EMPLOYEE', 'E-00003', 'Y', CURRENT_TIMESTAMP);
INSERT INTO app_user VALUES ('U-000004', '01611-100004', '$2b$12$6X5S.jTi1rkVeaBmpqK27OKBJZsWPEPMnr/rHolF9O7XzmhjFSXtm', 'EMPLOYEE', 'E-00004', 'Y', CURRENT_TIMESTAMP);
INSERT INTO app_user VALUES ('U-000005', '01711-100005', '$2b$12$6X5S.jTi1rkVeaBmpqK27OKBJZsWPEPMnr/rHolF9O7XzmhjFSXtm', 'EMPLOYEE', 'E-00005', 'Y', CURRENT_TIMESTAMP);
INSERT INTO app_user VALUES ('U-000006', '01812-100006', '$2b$12$6X5S.jTi1rkVeaBmpqK27OKBJZsWPEPMnr/rHolF9O7XzmhjFSXtm', 'EMPLOYEE', 'E-00006', 'Y', CURRENT_TIMESTAMP);
INSERT INTO app_user VALUES ('U-000007', '01911-100007', '$2b$12$6X5S.jTi1rkVeaBmpqK27OKBJZsWPEPMnr/rHolF9O7XzmhjFSXtm', 'EMPLOYEE', 'E-00007', 'Y', CURRENT_TIMESTAMP);
INSERT INTO app_user VALUES ('U-000008', '01611-100008', '$2b$12$6X5S.jTi1rkVeaBmpqK27OKBJZsWPEPMnr/rHolF9O7XzmhjFSXtm', 'EMPLOYEE', 'E-00008', 'Y', CURRENT_TIMESTAMP);
INSERT INTO app_user VALUES ('U-000009', '01711-100009', '$2b$12$6X5S.jTi1rkVeaBmpqK27OKBJZsWPEPMnr/rHolF9O7XzmhjFSXtm', 'EMPLOYEE', 'E-00009', 'Y', CURRENT_TIMESTAMP);
INSERT INTO app_user VALUES ('U-000010', '01812-100010', '$2b$12$6X5S.jTi1rkVeaBmpqK27OKBJZsWPEPMnr/rHolF9O7XzmhjFSXtm', 'EMPLOYEE', 'E-00010', 'Y', CURRENT_TIMESTAMP);
INSERT INTO app_user VALUES ('U-000011', '01911-100011', '$2b$12$6X5S.jTi1rkVeaBmpqK27OKBJZsWPEPMnr/rHolF9O7XzmhjFSXtm', 'EMPLOYEE', 'E-00011', 'Y', CURRENT_TIMESTAMP);
INSERT INTO app_user VALUES ('U-000012', '01611-100012', '$2b$12$6X5S.jTi1rkVeaBmpqK27OKBJZsWPEPMnr/rHolF9O7XzmhjFSXtm', 'EMPLOYEE', 'E-00012', 'Y', CURRENT_TIMESTAMP);
INSERT INTO app_user VALUES ('U-000013', '01711-100013', '$2b$12$6X5S.jTi1rkVeaBmpqK27OKBJZsWPEPMnr/rHolF9O7XzmhjFSXtm', 'EMPLOYEE', 'E-00013', 'Y', CURRENT_TIMESTAMP);
INSERT INTO app_user VALUES ('U-000014', '01812-100014', '$2b$12$6X5S.jTi1rkVeaBmpqK27OKBJZsWPEPMnr/rHolF9O7XzmhjFSXtm', 'EMPLOYEE', 'E-00014', 'Y', CURRENT_TIMESTAMP);
INSERT INTO app_user VALUES ('U-000015', '01911-100015', '$2b$12$6X5S.jTi1rkVeaBmpqK27OKBJZsWPEPMnr/rHolF9O7XzmhjFSXtm', 'EMPLOYEE', 'E-00015', 'Y', CURRENT_TIMESTAMP);
INSERT INTO app_user VALUES ('U-000016', '01611-100016', '$2b$12$6X5S.jTi1rkVeaBmpqK27OKBJZsWPEPMnr/rHolF9O7XzmhjFSXtm', 'EMPLOYEE', 'E-00016', 'Y', CURRENT_TIMESTAMP);
INSERT INTO app_user VALUES ('U-000017', '01711-100017', '$2b$12$6X5S.jTi1rkVeaBmpqK27OKBJZsWPEPMnr/rHolF9O7XzmhjFSXtm', 'EMPLOYEE', 'E-00017', 'Y', CURRENT_TIMESTAMP);
INSERT INTO app_user VALUES ('U-000018', '01812-200001', '$2b$12$6X5S.jTi1rkVeaBmpqK27OKBJZsWPEPMnr/rHolF9O7XzmhjFSXtm', 'EMPLOYEE', 'E-R001',  'Y', CURRENT_TIMESTAMP);
INSERT INTO app_user VALUES ('U-000019', '01911-200002', '$2b$12$6X5S.jTi1rkVeaBmpqK27OKBJZsWPEPMnr/rHolF9O7XzmhjFSXtm', 'EMPLOYEE', 'E-R002',  'Y', CURRENT_TIMESTAMP);
INSERT INTO app_user VALUES ('U-000020', '01611-200003', '$2b$12$6X5S.jTi1rkVeaBmpqK27OKBJZsWPEPMnr/rHolF9O7XzmhjFSXtm', 'EMPLOYEE', 'E-R003',  'Y', CURRENT_TIMESTAMP);


-- ============================================================
--  SEED: app_user for CUSTOMERS  (15 rows)
--  Password for all sample customers: customer123
-- ============================================================
INSERT INTO app_user VALUES ('U-000021', '01711-000001', '$2b$12$PHWcyxLINm22a4/uNYqysOG8tugMdTcqL/LVlZZoqFuB0GHHebu9S', 'CUSTOMER', 'C-00001', 'Y', CURRENT_TIMESTAMP);
INSERT INTO app_user VALUES ('U-000022', '01812-000002', '$2b$12$PHWcyxLINm22a4/uNYqysOG8tugMdTcqL/LVlZZoqFuB0GHHebu9S', 'CUSTOMER', 'C-00002', 'Y', CURRENT_TIMESTAMP);
INSERT INTO app_user VALUES ('U-000023', '01911-000003', '$2b$12$PHWcyxLINm22a4/uNYqysOG8tugMdTcqL/LVlZZoqFuB0GHHebu9S', 'CUSTOMER', 'C-00003', 'Y', CURRENT_TIMESTAMP);
INSERT INTO app_user VALUES ('U-000024', '01611-000004', '$2b$12$PHWcyxLINm22a4/uNYqysOG8tugMdTcqL/LVlZZoqFuB0GHHebu9S', 'CUSTOMER', 'C-00004', 'Y', CURRENT_TIMESTAMP);
INSERT INTO app_user VALUES ('U-000026', '01812-000006', '$2b$12$PHWcyxLINm22a4/uNYqysOG8tugMdTcqL/LVlZZoqFuB0GHHebu9S', 'CUSTOMER', 'C-00006', 'Y', CURRENT_TIMESTAMP);
INSERT INTO app_user VALUES ('U-000025', '01711-000005', '$2b$12$PHWcyxLINm22a4/uNYqysOG8tugMdTcqL/LVlZZoqFuB0GHHebu9S', 'CUSTOMER', 'C-00005', 'Y', CURRENT_TIMESTAMP);
INSERT INTO app_user VALUES ('U-000027', '01911-000007', '$2b$12$PHWcyxLINm22a4/uNYqysOG8tugMdTcqL/LVlZZoqFuB0GHHebu9S', 'CUSTOMER', 'C-00007', 'Y', CURRENT_TIMESTAMP);
INSERT INTO app_user VALUES ('U-000028', '01611-000008', '$2b$12$PHWcyxLINm22a4/uNYqysOG8tugMdTcqL/LVlZZoqFuB0GHHebu9S', 'CUSTOMER', 'C-00008', 'Y', CURRENT_TIMESTAMP);
INSERT INTO app_user VALUES ('U-000029', '01711-000009', '$2b$12$PHWcyxLINm22a4/uNYqysOG8tugMdTcqL/LVlZZoqFuB0GHHebu9S', 'CUSTOMER', 'C-00009', 'Y', CURRENT_TIMESTAMP);
INSERT INTO app_user VALUES ('U-000030', '01812-000010', '$2b$12$PHWcyxLINm22a4/uNYqysOG8tugMdTcqL/LVlZZoqFuB0GHHebu9S', 'CUSTOMER', 'C-00010', 'Y', CURRENT_TIMESTAMP);
INSERT INTO app_user VALUES ('U-000031', '01911-000011', '$2b$12$PHWcyxLINm22a4/uNYqysOG8tugMdTcqL/LVlZZoqFuB0GHHebu9S', 'CUSTOMER', 'C-00011', 'Y', CURRENT_TIMESTAMP);
INSERT INTO app_user VALUES ('U-000032', '01611-000012', '$2b$12$PHWcyxLINm22a4/uNYqysOG8tugMdTcqL/LVlZZoqFuB0GHHebu9S', 'CUSTOMER', 'C-00012', 'Y', CURRENT_TIMESTAMP);
INSERT INTO app_user VALUES ('U-000033', '01711-000013', '$2b$12$PHWcyxLINm22a4/uNYqysOG8tugMdTcqL/LVlZZoqFuB0GHHebu9S', 'CUSTOMER', 'C-00013', 'Y', CURRENT_TIMESTAMP);
INSERT INTO app_user VALUES ('U-000034', '01812-000014', '$2b$12$PHWcyxLINm22a4/uNYqysOG8tugMdTcqL/LVlZZoqFuB0GHHebu9S', 'CUSTOMER', 'C-00014', 'Y', CURRENT_TIMESTAMP);
INSERT INTO app_user VALUES ('U-000035', '01911-000015', '$2b$12$PHWcyxLINm22a4/uNYqysOG8tugMdTcqL/LVlZZoqFuB0GHHebu9S', 'CUSTOMER', 'C-00015', 'Y', CURRENT_TIMESTAMP);

-- ============================================================
--  HOW TO GENERATE REAL HASHES FOR SEED DATA
--  Run this Python script once before importing:
--
--  import bcrypt
--
--  emp_hash  = bcrypt.hashpw(b'employee123', bcrypt.gensalt()).decode()
--  cust_hash = bcrypt.hashpw(b'customer123', bcrypt.gensalt()).decode()
--  adm_hash  = bcrypt.hashpw(b'admin123',    bcrypt.gensalt()).decode()
--
--  print("Employee hash:", emp_hash)
--  print("Customer hash:", cust_hash)
--  print("Admin hash:   ", adm_hash)
--
--  Then replace the placeholder $2b$12$emphashreplaceXXX...
--  values above with the real hashes.
-- ============================================================