-- ============================================================
--  SUPERSHOP  BANGLADESH
--  Database : Multi-City, Multi-Branch Retail + Online Orders
--  Tables   : 17
--  DBMS     : PostgreSQL 16 / Oracle 21c XE
--  Course   : CSE-2201  Database Management System
--  Semester : 2nd Year 2nd Semester 2025
--  University of Dhaka — Department of CSE
-- ============================================================


--  CHANGES vs previous version:
--  FIX 1 : branch — removed manager_id column entirely
--  FIX 2 : branch — removed ALTER TABLE branch_manager_fk
--  FIX 3 : customer — removed stray ALTER TABLE DROP COLUMN city_id
--           (city_id was already absent from the CREATE TABLE body)
--  NEW   : branch_manager table added (TABLE 6) to enforce that
--           only BRANCH_MANAGER employees can manage a branch,
--           enforced via a trigger
--  ORDER : city → branch → membership → customer →
--           department → employee → branch_manager (+ trigger) →
--           category → supplier → product →
--           branch_inventory → discount →
--           sale → sale_item → online_order → payment → delivery
-- ============================================================


-- ============================================================
--  TABLE 1: CITY
-- ============================================================
CREATE TABLE city (
    city_id     CHAR(6)         NOT NULL,
    city_name   VARCHAR(50)     NOT NULL,
    division    VARCHAR(30)     NOT NULL,

    CONSTRAINT  city_id_pk      PRIMARY KEY (city_id),
    CONSTRAINT  check_city_id   CHECK (city_id LIKE 'BD-___')
);


-- ============================================================
--  TABLE 2: BRANCH
-- ============================================================
CREATE TABLE branch (
    branch_id   CHAR(6)         NOT NULL,
    branch_name VARCHAR(50)     NOT NULL,
    city_id     CHAR(6)         NOT NULL,
    address     VARCHAR(150)    NOT NULL,
    phone       VARCHAR(15),
    open_time   VARCHAR(5)      DEFAULT '09:00',
    close_time  VARCHAR(5)      DEFAULT '22:00',
    is_active   CHAR(1)         DEFAULT 'Y',

    CONSTRAINT  b_id_pk         PRIMARY KEY (branch_id),
    CONSTRAINT  check_b_id      CHECK (branch_id LIKE 'B-____'),
    CONSTRAINT  b_unique_phone  UNIQUE (phone),
    CONSTRAINT  b_fk            FOREIGN KEY (city_id) REFERENCES city(city_id)
                                ON DELETE RESTRICT,
    CONSTRAINT  check_b_isAct   CHECK (is_active IN ('Y', 'N'))
);


-- ============================================================
--  TABLE 3: MEMBERSHIP
-- ============================================================
CREATE TABLE membership (
    membership_type VARCHAR(10)     NOT NULL,
    discount_pct    NUMERIC(5,2)    DEFAULT 0,
    min_points      NUMERIC(8,0)    DEFAULT 0,
    benefits        VARCHAR(200),

    CONSTRAINT  mem_pk          PRIMARY KEY (membership_type),
    CONSTRAINT  check_mem_dis   CHECK (discount_pct >= 0 AND discount_pct <= 100),
    CONSTRAINT  check_mem_pt    CHECK (min_points >= 0)
);


-- ============================================================
--  TABLE 4: CUSTOMER
-- ============================================================
CREATE TABLE customer (
    cust_id         VARCHAR(8)      NOT NULL,
    cust_name       VARCHAR(60)     NOT NULL,
    email           VARCHAR(100),
    phone           VARCHAR(15)     NOT NULL,
    address         VARCHAR(200),
    dob             DATE,
    gender          CHAR(1),
    join_date       DATE            DEFAULT CURRENT_DATE,
    loyalty_points  NUMERIC(10,0)   DEFAULT 0,
    membership_type VARCHAR(10)     DEFAULT 'REGULAR',

    CONSTRAINT  cust_id_pk      PRIMARY KEY (cust_id),
    CONSTRAINT  check_cust_id   CHECK (cust_id LIKE 'C-%'),
    CONSTRAINT  check_cust_mail UNIQUE (email),
    CONSTRAINT  check_cust_phn  UNIQUE (phone),
    CONSTRAINT  cust_mem_tpe_fk FOREIGN KEY (membership_type)
                                REFERENCES membership(membership_type)
                                ON DELETE SET NULL,
    CONSTRAINT  cust_gender     CHECK (gender IN ('M', 'F'))
);


-- ============================================================
--  TABLE 5: DEPARTMENT
-- ============================================================
CREATE TABLE department (
    dept_id     CHAR(6)         NOT NULL,
    dept_name   VARCHAR(50)     NOT NULL,

    CONSTRAINT  dept_id_pk      PRIMARY KEY (dept_id),
    CONSTRAINT  check_dept_id   CHECK (dept_id LIKE 'D-____')
);


-- ============================================================
--  TABLE 6: EMPLOYEE
--  position = 'BRANCH_MANAGER' → eligible for branch_manager
--  position = 'DELIVERY_RIDER' → eligible for delivery
-- ============================================================
CREATE TABLE employee (
    emp_id      VARCHAR(8)      NOT NULL,
    emp_name    VARCHAR(60)     NOT NULL,
    email       VARCHAR(100),
    phone       VARCHAR(15),
    branch_id   CHAR(6),         
    dept_id     CHAR(6),
    position    VARCHAR(30)     NOT NULL,
    salary      NUMERIC(10,2),
    hire_date   DATE            NOT NULL,
    gender      CHAR(1),
    is_active   CHAR(1)         DEFAULT 'Y',

    CONSTRAINT  emp_id_pk       PRIMARY KEY (emp_id),
    CONSTRAINT  check_emp_id    CHECK (emp_id LIKE 'E-%'),
    CONSTRAINT  check_emp_email UNIQUE (email),
    CONSTRAINT  check_emp_phn   UNIQUE (phone),
    CONSTRAINT  emp_bran_id_fk  FOREIGN KEY (branch_id) REFERENCES branch(branch_id)
                                ON DELETE RESTRICT,
    CONSTRAINT  emp_dept_id_fk  FOREIGN KEY (dept_id) REFERENCES department(dept_id)
                                ON DELETE SET NULL,
    CONSTRAINT  emp_gender      CHECK (gender IN ('M', 'F')),
    CONSTRAINT  check_emp_isAct CHECK (is_active IN ('Y', 'N')),
    CONSTRAINT  check_emp_sal   CHECK (salary >= 10000)
);
-- ALTER TABLE employee ALTER COLUMN branch_id DROP NOT NULL;

-- ============================================================
--  TABLE 7: BRANCH_MANAGER  
--  PRIMARY KEY (branch_id) enforces one manager per branch.
--  emp_id must be an employee with position = 'BRANCH_MANAGER',
--  enforced by the trigger below.
-- ============================================================
CREATE TABLE branch_manager (
    branch_id   CHAR(6)         NOT NULL,
    emp_id      VARCHAR(8)      NOT NULL,
    assigned_on DATE            NOT NULL DEFAULT CURRENT_DATE,

    CONSTRAINT  bm_pk           PRIMARY KEY (branch_id),
    CONSTRAINT  bm_emp_uniq     UNIQUE (emp_id),
    CONSTRAINT  bm_branch_fk    FOREIGN KEY (branch_id) REFERENCES branch(branch_id)
                                ON DELETE CASCADE,
    CONSTRAINT  bm_emp_fk       FOREIGN KEY (emp_id) REFERENCES employee(emp_id)
                                ON DELETE RESTRICT
);

-- ── Trigger: reject INSERT/UPDATE if employee is not BRANCH_MANAGER ──────────
-- CREATE OR REPLACE FUNCTION fn_check_branch_manager_role()
-- RETURNS TRIGGER AS $$
-- BEGIN
--     IF (SELECT position FROM employee WHERE emp_id = NEW.emp_id)
--        != 'BRANCH_MANAGER' THEN
--         RAISE EXCEPTION
--             'Employee % cannot manage a branch — position is %, not BRANCH_MANAGER.',
--             NEW.emp_id,
--             (SELECT position FROM employee WHERE emp_id = NEW.emp_id);
--     END IF;
--     RETURN NEW;
-- END;
-- $$ LANGUAGE plpgsql;
-- 
-- CREATE TRIGGER trg_branch_manager_role
-- BEFORE INSERT OR UPDATE ON branch_manager
-- FOR EACH ROW EXECUTE FUNCTION fn_check_branch_manager_role();


-- ============================================================
--  TABLE 8: CATEGORY  (self-referencing)
-- ============================================================
CREATE TABLE category (
    cat_id          CHAR(6)         NOT NULL,
    cat_name        VARCHAR(50)     NOT NULL,
    parent_cat_id   CHAR(6),
    description     VARCHAR(200),

    CONSTRAINT  cat_id_pk       PRIMARY KEY (cat_id),
    CONSTRAINT  check_cat_id    CHECK (cat_id LIKE 'CAT-__'),
    CONSTRAINT  par_cat_id_fk   FOREIGN KEY (parent_cat_id) REFERENCES category(cat_id)
                                ON DELETE SET NULL
);


-- ============================================================
--  TABLE 9: SUPPLIER
-- ============================================================
CREATE TABLE supplier (
    supplier_id     VARCHAR(8)      NOT NULL,
    supplier_name   VARCHAR(80)     NOT NULL,
    contact_name    VARCHAR(60),
    email           VARCHAR(100),
    phone           VARCHAR(15)     NOT NULL,
    address         VARCHAR(150),
    city            VARCHAR(40)     DEFAULT 'Dhaka',
    country         VARCHAR(30)     DEFAULT 'Bangladesh',
    rating          NUMERIC(3,1)    DEFAULT 0,

    CONSTRAINT  sup_id_pk       PRIMARY KEY (supplier_id),
    CONSTRAINT  check_sup_id    CHECK (supplier_id LIKE 'SUP-%'),
    CONSTRAINT  check_sup_mail  UNIQUE (email),
    CONSTRAINT  check_sup_rat   CHECK (rating >= 0 AND rating <= 5)
);


-- ============================================================
--  TABLE 10: PRODUCT
-- ============================================================
CREATE TABLE product (
    product_id      VARCHAR(8)      NOT NULL,
    product_name    VARCHAR(100)    NOT NULL,
    brand           VARCHAR(50),
    cat_id          CHAR(6),
    supplier_id     VARCHAR(8),
    unit_price      NUMERIC(10,2)   NOT NULL,
    cost_price      NUMERIC(10,2),
    unit            VARCHAR(20)     NOT NULL,
    expiry_days     NUMERIC(5,0),
    is_active       CHAR(1)         DEFAULT 'Y',
    image_url       VARCHAR(500),
    
    CONSTRAINT  p_id_pk         PRIMARY KEY (product_id),
    CONSTRAINT  check_p_id      CHECK (product_id LIKE 'P-%'),
    CONSTRAINT  check_p_u_price CHECK (unit_price > 0),
    CONSTRAINT  check_p_c_price CHECK (cost_price > 0),
    CONSTRAINT  check_p_exp_dys CHECK (expiry_days > 0),
    CONSTRAINT  check_p_is_act  CHECK (is_active IN ('Y', 'N')),
    CONSTRAINT  p_cat_id_fk     FOREIGN KEY (cat_id) REFERENCES category(cat_id)
                                ON DELETE SET NULL,
    CONSTRAINT  p_sup_id_fk     FOREIGN KEY (supplier_id) REFERENCES supplier(supplier_id)
                                ON DELETE SET NULL
);


-- ============================================================
--  TABLE 11: BRANCH_INVENTORY
-- ============================================================
CREATE TABLE branch_inventory (
    inv_id          VARCHAR(8)      NOT NULL,
    branch_id       CHAR(6)         NOT NULL,
    product_id      VARCHAR(8)      NOT NULL,
    quantity        NUMERIC(10,2)   DEFAULT 0,
    reorder_level   NUMERIC(10,2)   DEFAULT 10,
    last_restocked  DATE,
    shelf_location  VARCHAR(20),

    CONSTRAINT  bi_inv_id_pk    PRIMARY KEY (inv_id),
    CONSTRAINT  check_bi_inv_id CHECK (inv_id LIKE 'I-%'),
    CONSTRAINT  bi_unique       UNIQUE (branch_id, product_id),
    CONSTRAINT  bi_quantity     CHECK (quantity >= 0),
    CONSTRAINT  bi_reorder_lvl  CHECK (reorder_level >= 0),
    CONSTRAINT  bi_branch_id_fk FOREIGN KEY (branch_id) REFERENCES branch(branch_id)
                                ON DELETE CASCADE,
    CONSTRAINT  bi_p_id_fk      FOREIGN KEY (product_id) REFERENCES product(product_id)
                                ON DELETE CASCADE
);


-- ============================================================
--  TABLE 12: DISCOUNT
-- ============================================================
CREATE TABLE discount (
    discount_id     VARCHAR(8)      NOT NULL,
    discount_name   VARCHAR(60)     NOT NULL,
    discount_type   VARCHAR(10)     NOT NULL,
    discount_value  NUMERIC(10,2)   NOT NULL,
    start_date      DATE            NOT NULL,
    end_date        DATE            NOT NULL,
    product_id      VARCHAR(8),
    cat_id          CHAR(6),

    CONSTRAINT  dis_id_pk       PRIMARY KEY (discount_id),
    CONSTRAINT  check_dis_id    CHECK (discount_id LIKE 'DIS-%'),
    CONSTRAINT  check_dis_tp    CHECK (discount_type IN ('PERCENT', 'FLAT')),
    CONSTRAINT  check_dis_val   CHECK (discount_value > 0),
    CONSTRAINT  check_dis       CHECK (end_date >= start_date),
    CONSTRAINT  dis_p_id_fk     FOREIGN KEY (product_id) REFERENCES product(product_id)
                                ON DELETE CASCADE,
    CONSTRAINT  dis_c_id_fk     FOREIGN KEY (cat_id) REFERENCES category(cat_id)
                                ON DELETE SET NULL
);


-- ============================================================
--  TABLE 13: SALE
-- ============================================================
CREATE TABLE sale (
    sale_id         VARCHAR(8)      NOT NULL,
    branch_id       CHAR(6)         NOT NULL,
    cust_id         VARCHAR(8),
    emp_id          VARCHAR(8)      NOT NULL,
    order_type      VARCHAR(10)     DEFAULT 'IN_STORE',
    sale_date       TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    subtotal        NUMERIC(12,2),
    discount_amt    NUMERIC(10,2)   DEFAULT 0,
    tax_amt         NUMERIC(10,2)   DEFAULT 0,
    total_amt       NUMERIC(12,2),
    payment_status  VARCHAR(10)     DEFAULT 'PENDING',

    CONSTRAINT  sale_id_pk      PRIMARY KEY (sale_id),
    CONSTRAINT  check_sale_id   CHECK (sale_id LIKE 'S-%'),
    CONSTRAINT  sale_ord_typ    CHECK (order_type IN ('IN_STORE', 'ONLINE')),
    CONSTRAINT  sale_subtotal   CHECK (subtotal >= 0),
    CONSTRAINT  sale_dis_amt    CHECK (discount_amt >= 0),
    CONSTRAINT  sale_tax_amt    CHECK (tax_amt >= 0),
    CONSTRAINT  sale_total      CHECK (total_amt >= 0),
    CONSTRAINT  sale_stat       CHECK (payment_status IN ('PAID', 'PENDING', 'CANCELLED')),
    CONSTRAINT  sale_b_id_fk    FOREIGN KEY (branch_id) REFERENCES branch(branch_id)
                                ON DELETE RESTRICT,
    CONSTRAINT  sale_c_id_fk    FOREIGN KEY (cust_id) REFERENCES customer(cust_id)
                                ON DELETE SET NULL,
    CONSTRAINT  sale_emp_id_fk  FOREIGN KEY (emp_id) REFERENCES employee(emp_id)
                                ON DELETE RESTRICT
);


-- ============================================================
--  TABLE 14: SALE_ITEM
-- ============================================================
CREATE TABLE sale_item (
    sale_id         VARCHAR(8)      NOT NULL,
    product_id      VARCHAR(8)      NOT NULL,
    quantity        NUMERIC(10,2)   NOT NULL,
    unit_price      NUMERIC(10,2)   NOT NULL,
    discount_id     VARCHAR(8),
    line_total      NUMERIC(12,2),

    CONSTRAINT  sale_itm_pk     PRIMARY KEY (sale_id, product_id),
    CONSTRAINT  sale_itm_qty    CHECK (quantity > 0),
    CONSTRAINT  sale_itm_price  CHECK (unit_price > 0),
    CONSTRAINT  sale_itm_total  CHECK (line_total >= 0),
    CONSTRAINT  sale_itm_sid_fk FOREIGN KEY (sale_id) REFERENCES sale(sale_id)
                                ON DELETE CASCADE,
    CONSTRAINT  sale_itm_pid_fk FOREIGN KEY (product_id) REFERENCES product(product_id)
                                ON DELETE RESTRICT,
    CONSTRAINT  sale_itm_dis_fk FOREIGN KEY (discount_id) REFERENCES discount(discount_id)
                                ON DELETE SET NULL
);


-- ============================================================
--  TABLE 15: ONLINE_ORDER
-- ============================================================
CREATE TABLE online_order (
    order_id            VARCHAR(8)      NOT NULL,
    cust_id             VARCHAR(8)      NOT NULL,
    branch_id           CHAR(6)         NOT NULL,
    sale_id             VARCHAR(8),
    order_date          TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    expected_delivery   TIMESTAMP,
    actual_delivery     TIMESTAMP,
    order_status        VARCHAR(18)     DEFAULT 'PLACED',
    delivery_address    VARCHAR(200)    NOT NULL,
    delivery_charge     NUMERIC(8,2)    DEFAULT 0,
    special_note        VARCHAR(200),

    CONSTRAINT  oo_id_pk        PRIMARY KEY (order_id),
    CONSTRAINT  check_oo_id     CHECK (order_id LIKE 'O-%'),
    CONSTRAINT  oo_sale_uniq    UNIQUE (sale_id),
    CONSTRAINT  oo_status       CHECK (order_status IN
                                ('PLACED', 'CONFIRMED', 'PACKED',
                                 'OUT_FOR_DELIVERY', 'DELIVERED', 'CANCELLED')),
    CONSTRAINT  oo_del_charge   CHECK (delivery_charge >= 0),
    CONSTRAINT  oo_cust_fk      FOREIGN KEY (cust_id) REFERENCES customer(cust_id)
                                ON DELETE RESTRICT,
    CONSTRAINT  oo_branch_fk    FOREIGN KEY (branch_id) REFERENCES branch(branch_id)
                                ON DELETE RESTRICT,
    CONSTRAINT  oo_sale_fk      FOREIGN KEY (sale_id) REFERENCES sale(sale_id)
                                ON DELETE SET NULL
);


-- ============================================================
--  TABLE 16: PAYMENT
-- ============================================================
CREATE TABLE payment (
    payment_id      VARCHAR(8)      NOT NULL,
    sale_id         VARCHAR(8)      NOT NULL,
    payment_date    TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    amount          NUMERIC(12,2)   NOT NULL,
    method          VARCHAR(20)     NOT NULL,
    reference_no    VARCHAR(40),
    status          VARCHAR(10)     DEFAULT 'SUCCESS',

    CONSTRAINT  pay_id_pk       PRIMARY KEY (payment_id),
    CONSTRAINT  check_pay_id    CHECK (payment_id LIKE 'PAY-%'),
    CONSTRAINT  pay_ref_uniq    UNIQUE (reference_no),
    CONSTRAINT  pay_amount      CHECK (amount > 0),
    CONSTRAINT  pay_method      CHECK (method IN
                                ('CASH', 'CARD', 'BKASH',
                                 'NAGAD', 'ROCKET',
                                 'VISA', 'MASTERCARD')),
    CONSTRAINT  pay_status      CHECK (status IN ('SUCCESS', 'FAILED', 'REFUNDED')),
    CONSTRAINT  pay_sale_fk     FOREIGN KEY (sale_id) REFERENCES sale(sale_id)
                                ON DELETE CASCADE
);


-- ============================================================
--  TABLE 17: DELIVERY
-- ============================================================
CREATE TABLE delivery (
    delivery_id     VARCHAR(8)      NOT NULL,
    order_id        VARCHAR(8)      NOT NULL,
    rider_id        VARCHAR(8)      NOT NULL,
    assigned_at     TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    picked_up_at    TIMESTAMP,
    delivered_at    TIMESTAMP,
    delivery_status VARCHAR(15)     DEFAULT 'ASSIGNED',
    distance_km     NUMERIC(6,2),
    delivery_fee    NUMERIC(8,2)    DEFAULT 0,
    rating          NUMERIC(3,1),
    note            VARCHAR(200),

    CONSTRAINT  del_id_pk       PRIMARY KEY (delivery_id),
    CONSTRAINT  check_del_id    CHECK (delivery_id LIKE 'DEL-%'),
    CONSTRAINT  del_ord_uniq    UNIQUE (order_id),
    CONSTRAINT  del_status      CHECK (delivery_status IN
                                ('ASSIGNED', 'PICKED_UP',
                                 'ON_THE_WAY', 'DELIVERED', 'FAILED')),
    CONSTRAINT  del_distance    CHECK (distance_km > 0),
    CONSTRAINT  del_fee         CHECK (delivery_fee >= 0),
    CONSTRAINT  del_rating      CHECK (rating >= 1 AND rating <= 5),
    CONSTRAINT  del_order_fk    FOREIGN KEY (order_id) REFERENCES online_order(order_id)
                                ON DELETE RESTRICT,
    CONSTRAINT  del_rider_fk    FOREIGN KEY (rider_id) REFERENCES employee(emp_id)
                                ON DELETE RESTRICT
);


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
--  END OF DDL — SuperShop Bangladesh
--  Total tables : 17
--
--  CREATION ORDER (dependency-safe):
--    city → branch → membership → customer →
--    department → employee → branch_manager (+ trigger) →
--    category → supplier → product →
--    branch_inventory → discount →
--    sale → sale_item → online_order → payment → delivery
--
--  BILL RECEIPT QUERY (sale + sale_item):
--    SELECT
--        s.sale_id, s.sale_date, s.order_type,
--        b.branch_name,
--        c.cust_name, c.membership_type,
--        p.product_name, si.quantity, si.unit_price,
--        d.discount_name, d.discount_type, d.discount_value,
--        si.line_total,
--        s.subtotal, s.discount_amt, s.tax_amt, s.total_amt,
--        py.method AS payment_method, py.status AS payment_status
--    FROM sale s
--    JOIN branch b        ON s.branch_id  = b.branch_id
--    LEFT JOIN customer c ON s.cust_id    = c.cust_id
--    JOIN sale_item si    ON s.sale_id    = si.sale_id
--    JOIN product p       ON si.product_id= p.product_id
--    LEFT JOIN discount d ON si.discount_id = d.discount_id
--    LEFT JOIN payment py ON s.sale_id    = py.sale_id
--    WHERE s.sale_id = 'S-IS001'
--    ORDER BY p.product_name;
-- ============================================================

-- ============================================================
--  TABLE 20: NOTIFICATION
--  Generic, polymorphic — works for EMPLOYEE, ADMIN, CUSTOMER.
--  recipient_id maps to emp_id / admin_id / cust_id depending
--  on recipient_type (same pattern as app_user.ref_id).
-- ============================================================
CREATE TABLE notification (
    notif_id        VARCHAR(10)     NOT NULL,
    recipient_type  VARCHAR(10)     NOT NULL,   -- 'EMPLOYEE' | 'ADMIN' | 'CUSTOMER'
    recipient_id    VARCHAR(12)     NOT NULL,   -- emp_id / admin_id / cust_id
    branch_id       CHAR(6),                     -- optional, lets you filter/broadcast by branch
    notif_type      VARCHAR(30)     NOT NULL,   -- 'LOW_STOCK', 'NEW_PRODUCT', 'ORDER_PLACED', ...
    title           VARCHAR(100)    NOT NULL,
    message         VARCHAR(300)    NOT NULL,
    link_url        VARCHAR(200),                -- where the click should land
    ref_table       VARCHAR(30),                 -- e.g. 'branch_inventory', 'product'
    ref_id          VARCHAR(20),                 -- inv_id / product_id this notif is about
    is_read         CHAR(1)         DEFAULT 'N',
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    read_at         TIMESTAMP,

    CONSTRAINT notif_pk         PRIMARY KEY (notif_id),
    CONSTRAINT check_notif_id   CHECK (notif_id LIKE 'N-%'),
    CONSTRAINT notif_recip_type CHECK (recipient_type IN ('EMPLOYEE','ADMIN','CUSTOMER')),
    CONSTRAINT notif_is_read    CHECK (is_read IN ('Y','N')),
    CONSTRAINT notif_branch_fk  FOREIGN KEY (branch_id) REFERENCES branch(branch_id)
                                ON DELETE CASCADE
);

-- CREATE INDEX idx_notif_recipient ON notification (recipient_type, recipient_id, is_read);
-- CREATE INDEX idx_notif_ref       ON notification (ref_table, ref_id, notif_type);


-- ============================================================
--  TABLE 21: ACTION_LOG
--  Records every CREATE/UPDATE/DELETE done by an admin or
--  employee through the app. old_values/new_values store a
--  JSON snapshot so you can see exactly what changed.
-- ============================================================
CREATE TABLE action_log (
    log_id          VARCHAR(10)     NOT NULL,
    actor_type      VARCHAR(10)     NOT NULL,   -- 'ADMIN' | 'EMPLOYEE' | 'SYSTEM'
    actor_id        VARCHAR(12)     NOT NULL,   -- admin_id / emp_id
    actor_name      VARCHAR(60)     NOT NULL,   -- snapshot, survives account deletion
    action          VARCHAR(10)     NOT NULL,   -- 'CREATE' | 'UPDATE' | 'DELETE'
    table_name      VARCHAR(30)     NOT NULL,   -- 'product', 'employee', ...
    record_id       VARCHAR(20)     NOT NULL,   -- product_id / emp_id / discount_id ...
    description     VARCHAR(300)    NOT NULL,   -- human-readable summary
    old_values      JSONB,
    new_values      JSONB,
    ip_address      VARCHAR(45),
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT log_pk           PRIMARY KEY (log_id),
    CONSTRAINT check_log_id     CHECK (log_id LIKE 'LOG-%'),
    CONSTRAINT log_actor_type   CHECK (actor_type IN ('ADMIN','EMPLOYEE','SYSTEM')),
    CONSTRAINT log_action_type  CHECK (action IN ('CREATE','UPDATE','DELETE'))
);

-- CREATE INDEX idx_log_table_record ON action_log (table_name, record_id);
-- CREATE INDEX idx_log_actor        ON action_log (actor_type, actor_id);
-- CREATE INDEX idx_log_created      ON action_log (created_at DESC);

CREATE TABLE customer_message (
    msg_id       VARCHAR(10)  NOT NULL,
    cust_id      VARCHAR(10)  NOT NULL,
    branch_id    VARCHAR(10)  NOT NULL,
    sender_role  VARCHAR(10)  NOT NULL,   -- 'CUSTOMER' | 'MANAGER'
    message      VARCHAR(500) NOT NULL,
    is_read      CHAR(1)      DEFAULT 'N',
    created_at   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT msg_pk           PRIMARY KEY (msg_id),
    CONSTRAINT check_msg_id     CHECK (msg_id LIKE 'MSG-%'),
    CONSTRAINT msg_sender_role  CHECK (sender_role IN ('CUSTOMER','MANAGER')),
    CONSTRAINT msg_is_read      CHECK (is_read IN ('Y','N')),
    CONSTRAINT msg_cust_fk      FOREIGN KEY (cust_id)   REFERENCES customer(cust_id)
                                ON DELETE CASCADE,
    CONSTRAINT msg_branch_fk    FOREIGN KEY (branch_id) REFERENCES branch(branch_id)
                                ON DELETE CASCADE
);
