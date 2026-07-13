-- ============================================================
--  SUPERSHOP BANGLADESH — Sample Data v2.0
--  Tables  : 16  |  Total rows : 226
--  DBMS    : PostgreSQL 16 / Oracle 21c XE
--  Course  : CSE-2201  |  University of Dhaka
-- ============================================================
--
--  city            : city_id, city_name, division
--  branch          : branch_id, branch_name, city_id, address,
--                    phone, open_time, close_time, is_active
--  membership      : membership_type, discount_pct, min_points, benefits
--  customer        : cust_id, cust_name, email, phone, address,
--                    dob, gender, join_date,
--                    loyalty_points, membership_type
--  department      : dept_id, dept_name
--  employee        : emp_id, emp_name, email, phone, branch_id,
--                    dept_id, position, salary, hire_date,
--                    gender, is_active
--  category        : cat_id, cat_name, parent_cat_id, description
--  supplier        : supplier_id, supplier_name, contact_name,
--                    email, phone, address, city, country, rating
--  product         : product_id, product_name, brand, cat_id,
--                    supplier_id, unit_price, cost_price, unit,
--                    expiry_days, is_active
--  branch_inventory: inv_id, branch_id, product_id, quantity,
--                    reorder_level, last_restocked, shelf_location
--  discount        : discount_id, discount_name, discount_type,
--                    discount_value, start_date, end_date,
--                    product_id, cat_id
--  sale            : sale_id, branch_id, cust_id, emp_id,
--                    order_type, sale_date, subtotal,
--                    discount_amt, tax_amt, total_amt,
--                    payment_status
--  sale_item       : sale_id, product_id, quantity, unit_price,
--                    discount_id, line_total
--  online_order    : order_id, cust_id, branch_id, sale_id,
--                    order_date, expected_delivery,
--                    actual_delivery, order_status,
--                    delivery_address, delivery_charge,
--                    special_note
--  payment         : payment_id, sale_id, payment_date, amount,
--                    method, reference_no, status
--  delivery        : delivery_id, order_id, rider_id,
--                    assigned_at, picked_up_at, delivered_at,
--                    delivery_status, distance_km,
--                    delivery_fee, rating, note
-- ============================================================
-- Table drops;
DROP FROM notification;
DROP FROM action_log;
DROP TABLE admin_account;
DROP TABLE app_user;
DROP TABLE delivery;
DROP TABLE payment;
DROP TABLE online_order;
DROP TABLE sale_item;
DROP TABLE sale;
DROP TABLE discount;
DROP TABLE branch_inventory;
DROP TABLE product;
DROP TABLE supplier;
DROP TABLE category;
DROP TABLE branch_manager;
DROP TABLE employee;
DROP TABLE department;
DROP TABLE customer;
DROP TABLE membership;
DROP TABLE branch;
DROP TABLE city;

-- Data delete
DELETE FROM notification;
DELETE FROM action_log;
DELETE FROM admin_account;
DELETE FROM app_user;
DELETE FROM delivery;
DELETE FROM payment;
DELETE FROM online_order;
DELETE FROM sale_item;
DELETE FROM sale;
DELETE FROM discount;
DELETE FROM branch_inventory;
DELETE FROM product;
DELETE FROM supplier;
DELETE FROM category;
DELETE FROM branch_manager;
DELETE FROM employee;
DELETE FROM department;
DELETE FROM customer;
DELETE FROM membership;
DELETE FROM branch;
DELETE FROM city;
-- ============================================================
--  SUPERSHOP BANGLADESH — Sample Data 
--  Tables  : 17  |  Total rows : 246
--  DBMS    : PostgreSQL 16 / Oracle 21c XE
--  Course  : CSE-2201  |  University of Dhaka
-- ============================================================

-- ============================================================
--  COLUMN ORDER:
--  city            : city_id, city_name, division
--  branch          : branch_id, branch_name, city_id, address,
--                    phone, open_time, close_time, is_active
--  membership      : membership_type, discount_pct, min_points, benefits
--  customer        : cust_id, cust_name, email, phone, address,
--                    dob, gender, join_date, loyalty_points, membership_type
--  department      : dept_id, dept_name
--  employee        : emp_id, emp_name, email, phone, branch_id,
--                    dept_id, position, salary, hire_date, gender, is_active
--  branch_manager  : branch_id, emp_id, assigned_on
--  category        : cat_id, cat_name, parent_cat_id, description
--  supplier        : supplier_id, supplier_name, contact_name,
--                    email, phone, address, city, country, rating
--  product         : product_id, product_name, brand, cat_id,
--                    supplier_id, unit_price, cost_price, unit,
--                    expiry_days, is_active
--  branch_inventory: inv_id, branch_id, product_id, quantity,
--                    reorder_level, last_restocked, shelf_location
--  discount        : discount_id, discount_name, discount_type,
--                    discount_value, start_date, end_date, product_id, cat_id
--  sale            : sale_id, branch_id, cust_id, emp_id, order_type,
--                    sale_date, subtotal, discount_amt, tax_amt,
--                    total_amt, payment_status
--  sale_item       : sale_id, product_id, quantity, unit_price,
--                    discount_id, line_total
--  online_order    : order_id, cust_id, branch_id, sale_id,
--                    order_date, expected_delivery, actual_delivery,
--                    order_status, delivery_address, delivery_charge,
--                    special_note
--  payment         : payment_id, sale_id, payment_date, amount,
--                    method, reference_no, status
--  delivery        : delivery_id, order_id, rider_id, assigned_at,
--                    picked_up_at, delivered_at, delivery_status,
--                    distance_km, delivery_fee, rating, note
-- ============================================================

-- ============================================================
--  1. CITY  (6 rows)
-- ============================================================
INSERT INTO city VALUES ('BD-DHK', 'Dhaka',      'Dhaka');
INSERT INTO city VALUES ('BD-CTG', 'Chattogram', 'Chattogram');
INSERT INTO city VALUES ('BD-SYL', 'Sylhet',     'Sylhet');
INSERT INTO city VALUES ('BD-RAJ', 'Rajshahi',   'Rajshahi');
INSERT INTO city VALUES ('BD-KHU', 'Khulna',     'Khulna');
INSERT INTO city VALUES ('BD-BAR', 'Barishal',   'Barishal');


-- ============================================================
--  2. BRANCH  (8 rows)  — no manager_id column
-- ============================================================
INSERT INTO branch VALUES ('B-DH01', 'SuperShop Dhanmondi',  'BD-DHK', 'House 32, Road 2, Dhanmondi, Dhaka-1205',      '02-9660101', '09:00', '22:00', 'Y');
INSERT INTO branch VALUES ('B-DH02', 'SuperShop Gulshan',    'BD-DHK', 'Plot 15, Road 53, Gulshan-2, Dhaka-1212',       '02-9882202', '08:00', '23:00', 'Y');
INSERT INTO branch VALUES ('B-DH03', 'SuperShop Uttara',     'BD-DHK', 'House 7, Sector 6, Uttara, Dhaka-1230',         '02-8931303', '09:00', '22:00', 'Y');
INSERT INTO branch VALUES ('B-CT01', 'SuperShop GEC Circle', 'BD-CTG', '1234 CDA Avenue, GEC Circle, Chattogram-4000',  '031-615404', '09:00', '22:00', 'Y');
INSERT INTO branch VALUES ('B-CT02', 'SuperShop Agrabad',    'BD-CTG', 'Agrabad Commercial Area, Chattogram-4100',      '031-724505', '09:00', '22:00', 'Y');
INSERT INTO branch VALUES ('B-SY01', 'SuperShop Sylhet',     'BD-SYL', 'Zindabazar, Sylhet-3100',                       '0821-76606', '09:00', '21:00', 'Y');
INSERT INTO branch VALUES ('B-RJ01', 'SuperShop Rajshahi',   'BD-RAJ', 'Saheb Bazar Road, Rajshahi-6000',               '0721-77707', '09:00', '21:00', 'Y');
INSERT INTO branch VALUES ('B-KH01', 'SuperShop Khulna',     'BD-KHU', 'KDA Avenue, Khulna-9000',                       '041-72808',  '09:00', '21:00', 'N');


-- ============================================================
--  3. MEMBERSHIP  (4 rows)
-- ============================================================
INSERT INTO membership VALUES ('REGULAR',  0.00,     0, 'Standard pricing. Earn 1 point per 10 BDT spent.');
INSERT INTO membership VALUES ('SILVER',   5.00,  1000, '5% discount. Earn 1.5 points per 10 BDT. Free delivery above 500 BDT.');
INSERT INTO membership VALUES ('GOLD',    10.00,  5000, '10% discount. Earn 2 points per 10 BDT. Free delivery always.');
INSERT INTO membership VALUES ('PLATINUM',15.00, 15000, '15% discount. Earn 3 points per 10 BDT. Dedicated support line.');


-- ============================================================
--  4. CUSTOMER  (15 rows)
-- ============================================================
INSERT INTO customer VALUES ('C-00001', 'Rahim Uddin',      'rahim.uddin@gmail.com',    '01711-000001', 'House 5, Mirpur-10, Dhaka',     '1990-03-15', 'M', '2022-01-10',  3200, 'SILVER');
INSERT INTO customer VALUES ('C-00002', 'Sumaiya Akter',    'sumaiya.akter@yahoo.com',  '01812-000002', 'Road 4, Banani, Dhaka',          '1995-07-22', 'F', '2022-03-05',  7800, 'GOLD');
INSERT INTO customer VALUES ('C-00003', 'Kamal Hossain',    'kamal.h@hotmail.com',      '01911-000003', 'Nasirabad, Chattogram',          '1988-11-30', 'M', '2022-05-18',   450, 'REGULAR');
INSERT INTO customer VALUES ('C-00004', 'Nasrin Begum',     'nasrin.b@gmail.com',       '01611-000004', 'Tilagarh, Sylhet',              '1992-04-08', 'F', '2022-06-01',  1200, 'SILVER');
INSERT INTO customer VALUES ('C-00005', 'Farhan Islam',     'farhan.islam@gmail.com',   '01711-000005', 'Laxmipur, Rajshahi',            '1985-09-12', 'M', '2022-07-20', 18500, 'PLATINUM');
INSERT INTO customer VALUES ('C-00006', 'Tahmina Khanam',   'tahmina.k@gmail.com',      '01812-000006', 'Sonadanga, Khulna',             '1998-01-25', 'F', '2022-08-14',   900, 'REGULAR');
INSERT INTO customer VALUES ('C-00007', 'Mizanur Rahman',   'mizan.r@yahoo.com',        '01911-000007', 'Agrabad, Chattogram',           '1987-06-18', 'M', '2022-09-03',  5500, 'GOLD');
INSERT INTO customer VALUES ('C-00008', 'Sharmin Sultana',  'sharmin.s@gmail.com',      '01611-000008', 'Bashundhara R/A, Dhaka',        '2000-12-05', 'F', '2023-01-11',  2100, 'SILVER');
INSERT INTO customer VALUES ('C-00009', 'Anisur Rahman',    'anisur.r@gmail.com',       '01711-000009', 'Zindabazar, Sylhet',            '1993-08-19', 'M', '2023-02-28',   300, 'REGULAR');
INSERT INTO customer VALUES ('C-00010', 'Roksana Parvin',   'roksana.p@yahoo.com',      '01812-000010', 'Uttara, Dhaka',                 '1991-05-30', 'F', '2023-03-15',  6200, 'GOLD');
INSERT INTO customer VALUES ('C-00011', 'Jahirul Islam',    'jahir.i@gmail.com',        '01911-000011', 'Dhanmondi, Dhaka',              '1989-10-14', 'M', '2023-04-22',   750, 'REGULAR');
INSERT INTO customer VALUES ('C-00012', 'Fatema Tuz Zohra', 'fatema.z@gmail.com',       '01611-000012', 'Saheb Bazar, Rajshahi',         '1996-02-08', 'F', '2023-05-09',  1600, 'SILVER');
INSERT INTO customer VALUES ('C-00013', 'Shakil Ahmed',     'shakil.a@hotmail.com',     '01711-000013', 'Halishahar, Chattogram',        '1984-07-27', 'M', '2023-06-30', 22000, 'PLATINUM');
INSERT INTO customer VALUES ('C-00014', 'Nusrat Jahan',     'nusrat.j@gmail.com',       '01812-000014', 'Gulshan-1, Dhaka',              '1997-03-16', 'F', '2023-08-05',  4300, 'SILVER');
INSERT INTO customer VALUES ('C-00015', 'Rezaul Karim',     'rezaul.k@yahoo.com',       '01911-000015', 'Khulna Sadar, Khulna',         '1982-11-01', 'M', '2023-09-17',   100, 'REGULAR');


-- ============================================================
--  5. DEPARTMENT  (6 rows)
-- ============================================================
INSERT INTO department VALUES ('D-GR01', 'Grocery');
INSERT INTO department VALUES ('D-DY01', 'Dairy & Bakery');
INSERT INTO department VALUES ('D-EL01', 'Electronics');
INSERT INTO department VALUES ('D-CL01', 'Clothing');
INSERT INTO department VALUES ('D-HL01', 'Health & Beauty');
INSERT INTO department VALUES ('D-DL01', 'Delivery Ops');


-- ============================================================
--  6. EMPLOYEE  (20 rows)
--  E-00001..E-00008 : BRANCH_MANAGER (one per branch)
--  FIX 4: E-00013 salary 13500 → 30000
--  FIX 5: E-00017 salary 12000 → 28000
-- ============================================================
INSERT INTO employee VALUES ('E-00001', 'Habibur Rahman',  'habib.r@supershop.com.bd',   '01711-100001', 'B-DH01', 'D-GR01', 'BRANCH_MANAGER', 45000.00, '2019-01-15', 'M', 'Y');
INSERT INTO employee VALUES ('E-00002', 'Dilara Begum',    'dilara.b@supershop.com.bd',  '01812-100002', 'B-DH02', 'D-GR01', 'BRANCH_MANAGER', 38000.00, '2019-03-10', 'F', 'Y');
INSERT INTO employee VALUES ('E-00003', 'Monirul Islam',   'monirul.i@supershop.com.bd', '01911-100003', 'B-DH03', 'D-GR01', 'BRANCH_MANAGER', 36000.00, '2020-02-20', 'M', 'Y');
INSERT INTO employee VALUES ('E-00004', 'Salma Khatun',    'salma.k@supershop.com.bd',   '01611-100004', 'B-CT01', 'D-GR01', 'BRANCH_MANAGER', 35000.00, '2020-05-01', 'F', 'Y');
INSERT INTO employee VALUES ('E-00005', 'Golam Rabbani',   'golam.r@supershop.com.bd',   '01711-100005', 'B-CT02', 'D-GR01', 'BRANCH_MANAGER', 34000.00, '2020-07-15', 'M', 'Y');
INSERT INTO employee VALUES ('E-00006', 'Ashraful Haque',  'ashraf.h@supershop.com.bd',  '01812-100006', 'B-SY01', 'D-GR01', 'BRANCH_MANAGER', 33000.00, '2021-01-05', 'M', 'Y');
INSERT INTO employee VALUES ('E-00007', 'Mahmuda Akter',   'mahmuda.a@supershop.com.bd', '01911-100007', 'B-DH01', 'D-GR01', 'CASHIER',        15000.00, '2021-04-12', 'F', 'Y');
INSERT INTO employee VALUES ('E-00008', 'Saifur Rahman',   'saifur.r@supershop.com.bd',  '01611-100008', 'B-DH02', 'D-GR01', 'CASHIER',        15000.00, '2021-06-01', 'M', 'Y');
INSERT INTO employee VALUES ('E-00009', 'Lipi Akhter',     'lipi.a@supershop.com.bd',    '01711-100009', 'B-DH03', 'D-DY01', 'CASHIER',        14500.00, '2021-09-20', 'F', 'Y');
INSERT INTO employee VALUES ('E-00010', 'Rakibul Hasan',   'rakibul.h@supershop.com.bd', '01812-100010', 'B-CT01', 'D-GR01', 'CASHIER',        14500.00, '2021-11-11', 'M', 'Y');
INSERT INTO employee VALUES ('E-00011', 'Nasima Sultana',  'nasima.s@supershop.com.bd',  '01911-100011', 'B-CT02', 'D-EL01', 'SALES_STAFF',    13000.00, '2022-01-18', 'F', 'Y');
INSERT INTO employee VALUES ('E-00012', 'Touhidul Islam',  'touhid.i@supershop.com.bd',  '01611-100012', 'B-SY01', 'D-GR01', 'CASHIER',        13500.00, '2022-03-07', 'M', 'Y');
INSERT INTO employee VALUES ('E-00013', 'Reshma Begum',    'reshma.b@supershop.com.bd',  '01711-100013', 'B-RJ01', 'D-DY01', 'BRANCH_MANAGER', 30000.00, '2022-04-25', 'F', 'Y'); -- FIX 4
INSERT INTO employee VALUES ('E-00014', 'Imran Hossain',   'imran.h@supershop.com.bd',   '01812-100014', 'B-DH01', 'D-HL01', 'SALES_STAFF',    14000.00, '2022-06-14', 'M', 'Y');
INSERT INTO employee VALUES ('E-00015', 'Tania Rahman',    'tania.r@supershop.com.bd',   '01911-100015', 'B-DH02', 'D-CL01', 'SALES_STAFF',    14000.00, '2022-08-30', 'F', 'Y');
INSERT INTO employee VALUES ('E-00016', 'Kamrul Hasan',    'kamrul.h@supershop.com.bd',  '01611-100016', 'B-CT01', 'D-GR01', 'STOCK_KEEPER',   12000.00, '2022-10-03', 'M', 'Y');
INSERT INTO employee VALUES ('E-00017', 'Farzana Yasmin',  'farzana.y@supershop.com.bd', '01711-100017', 'B-KH01', 'D-GR01', 'BRANCH_MANAGER', 28000.00, '2023-01-09', 'F', 'Y'); -- FIX 5
INSERT INTO employee VALUES ('E-R001',  'Arif Hossain',    'arif.h@supershop.com.bd',    '01812-200001', 'B-DH01', 'D-DL01', 'DELIVERY_RIDER', 11000.00, '2023-03-01', 'M', 'Y');
INSERT INTO employee VALUES ('E-R002',  'Sumon Mia',       'sumon.m@supershop.com.bd',   '01911-200002', 'B-DH02', 'D-DL01', 'DELIVERY_RIDER', 11000.00, '2023-03-15', 'M', 'Y');
INSERT INTO employee VALUES ('E-R003',  'Rajib Das',       'rajib.d@supershop.com.bd',   '01611-200003', 'B-CT01', 'D-DL01', 'DELIVERY_RIDER', 10500.00, '2023-05-20', 'M', 'Y');
INSERT INTO employee VALUES ('E-R004', 	'Shakil Ahmed',    'shakil.a@supershop.com.bd',  '01711-200004', 'B-DH03', 'D-DL01', 'DELIVERY_RIDER', 11000.00, '2023-07-01', 'M', 'Y');
INSERT INTO employee VALUES ('E-R005', 	'Jahid Hasan', 	   'jahid.h@supershop.com.bd',   '01812-200005', 'B-SY01', 'D-DL01', 'DELIVERY_RIDER', 11000.00, '2023-08-10', 'M', 'Y');

-- ============================================================
--  7. BRANCH_MANAGER  (8 rows)  — FIX 3
--  Trigger will reject any emp_id whose position != BRANCH_MANAGER
-- ============================================================
INSERT INTO branch_manager VALUES ('B-DH01', 'E-00001', '2019-01-15');
INSERT INTO branch_manager VALUES ('B-DH02', 'E-00002', '2019-03-10');
INSERT INTO branch_manager VALUES ('B-DH03', 'E-00003', '2020-02-20');
INSERT INTO branch_manager VALUES ('B-CT01', 'E-00004', '2020-05-01');
INSERT INTO branch_manager VALUES ('B-CT02', 'E-00005', '2020-07-15');
INSERT INTO branch_manager VALUES ('B-SY01', 'E-00006', '2021-01-05');
INSERT INTO branch_manager VALUES ('B-RJ01', 'E-00013', '2022-04-25');
INSERT INTO branch_manager VALUES ('B-KH01', 'E-00017', '2023-01-09');


-- ============================================================
--  8. CATEGORY  (10 rows)
-- ============================================================
INSERT INTO category VALUES ('CAT-F1', 'Food',          NULL,     'All food and grocery items');
INSERT INTO category VALUES ('CAT-E1', 'Electronics',   NULL,     'Electronic appliances and devices');
INSERT INTO category VALUES ('CAT-C1', 'Clothing',      NULL,     'Garments and fashion accessories');
INSERT INTO category VALUES ('CAT-H1', 'Health',        NULL,     'Health and personal care products');
INSERT INTO category VALUES ('CAT-D1', 'Dairy',         'CAT-F1', 'Milk, yogurt, cheese and dairy items');
INSERT INTO category VALUES ('CAT-B1', 'Bakery',        'CAT-F1', 'Bread, biscuits and baked goods');
INSERT INTO category VALUES ('CAT-S1', 'Snacks',        'CAT-F1', 'Chips, namkeen and packaged snacks');
INSERT INTO category VALUES ('CAT-BV', 'Beverages',     'CAT-F1', 'Drinks, juices, tea and coffee');
INSERT INTO category VALUES ('CAT-M1', 'Mobile Access', 'CAT-E1', 'Mobile phone accessories and chargers');
INSERT INTO category VALUES ('CAT-P1', 'Personal Care', 'CAT-H1', 'Soaps, shampoos and hygiene products');


-- ============================================================
--  9. SUPPLIER  (8 rows)
-- ============================================================
INSERT INTO supplier VALUES ('SUP-001', 'Pran-RFL Group',         'Ahsan Habib',    'supply@pranrfl.com',      '02-48810001', 'PRAN-RFL Centre, Dhaka',              'Dhaka', 'Bangladesh', 4.8);
INSERT INTO supplier VALUES ('SUP-002', 'Bashundhara Group',      'Tanvir Ahmed',   'supply@bashundhara.com',  '02-48810002', '13 Bir Uttam CR Datta Road, Dhaka',   'Dhaka', 'Bangladesh', 4.5);
INSERT INTO supplier VALUES ('SUP-003', 'ACI Limited',            'Kabir Hossain',  'supply@aci-bd.com',       '02-48810003', 'ACI Bhaban, 245 Tejgaon, Dhaka',      'Dhaka', 'Bangladesh', 4.6);
INSERT INTO supplier VALUES ('SUP-004', 'Meghna Group',           'Rafiq Uddin',    'supply@meghna.com',       '02-48810004', 'Meghna House, Tejgaon I/A, Dhaka',    'Dhaka', 'Bangladesh', 4.3);
INSERT INTO supplier VALUES ('SUP-005', 'Square Pharmaceuticals', 'Nasima Islam',   'supply@squarepharma.com', '02-48810005', 'Square Centre, 48 Mohakhali, Dhaka',  'Dhaka', 'Bangladesh', 4.7);
INSERT INTO supplier VALUES ('SUP-006', 'Transcom Group',         'Shafiqul Islam', 'supply@transcom.com.bd',  '02-48810006', 'Transcom Center, Gulshan, Dhaka',     'Dhaka', 'Bangladesh', 4.4);
INSERT INTO supplier VALUES ('SUP-007', 'Akij Group',             'Belal Hossain',  'supply@akij.net',         '02-48810007', 'Akij House, 2 Mohakhali, Dhaka',      'Dhaka', 'Bangladesh', 4.2);
INSERT INTO supplier VALUES ('SUP-008', 'Olympic Industries',     'Salim Khan',     'supply@olympicbd.com',    '02-48810008', 'Olympic House, Tejgaon, Dhaka',       'Dhaka', 'Bangladesh', 4.1);


-- ============================================================
--  10. PRODUCT  (20+30 rows)
-- ============================================================
INSERT INTO product VALUES ('P-00001', 'Full Cream Milk 1L',      'Pran',         'CAT-D1', 'SUP-001',  95.00,  72.00, 'litre',   7, 'Y');
INSERT INTO product VALUES ('P-00002', 'Plain Yogurt 400g',       'Aarong Dairy', 'CAT-D1', 'SUP-002',  75.00,  55.00, 'pcs',     5, 'Y');
INSERT INTO product VALUES ('P-00003', 'Butter 100g',             'Pran',         'CAT-D1', 'SUP-001', 120.00,  90.00, 'pcs',    30, 'Y');
INSERT INTO product VALUES ('P-00004', 'Sliced Bread 400g',       'Sunfeast',     'CAT-B1', 'SUP-004',  65.00,  48.00, 'pcs',     5, 'Y');
INSERT INTO product VALUES ('P-00005', 'Digestive Biscuits 200g', 'Olympic',      'CAT-B1', 'SUP-008',  55.00,  40.00, 'pcs',   180, 'Y');
INSERT INTO product VALUES ('P-00006', 'Potato Chips 100g',       'Pran',         'CAT-S1', 'SUP-001',  45.00,  32.00, 'pcs',    90, 'Y');
INSERT INTO product VALUES ('P-00007', 'Chanachur Mix 200g',      'Akij',         'CAT-S1', 'SUP-007',  60.00,  44.00, 'pcs',   120, 'Y');
INSERT INTO product VALUES ('P-00008', 'Mango Juice 250ml',       'Pran',         'CAT-BV', 'SUP-001',  30.00,  21.00, 'pcs',   180, 'Y');
INSERT INTO product VALUES ('P-00009', 'Green Tea 100 bags',      'ACI',          'CAT-BV', 'SUP-003', 180.00, 135.00, 'pcs',   365, 'Y');
INSERT INTO product VALUES ('P-00010', 'Soft Drink 500ml',        'Transcom',     'CAT-BV', 'SUP-006',  40.00,  28.00, 'pcs',    90, 'Y');
INSERT INTO product VALUES ('P-00011', 'Basmati Rice 5kg',        'Pran',         'CAT-F1', 'SUP-001', 550.00, 410.00, 'kg',    365, 'Y');
INSERT INTO product VALUES ('P-00012', 'Soybean Oil 5L',          'Meghna',       'CAT-F1', 'SUP-004', 850.00, 640.00, 'litre', 365, 'Y');
INSERT INTO product VALUES ('P-00013', 'Sugar 1kg',               'Bashundhara',  'CAT-F1', 'SUP-002',  85.00,  62.00, 'kg',    730, 'Y');
INSERT INTO product VALUES ('P-00014', 'Antiseptic Soap 100g',    'Square',       'CAT-P1', 'SUP-005',  35.00,  24.00, 'pcs',   730, 'Y');
INSERT INTO product VALUES ('P-00015', 'Shampoo 400ml',           'ACI',          'CAT-P1', 'SUP-003', 280.00, 205.00, 'ml',    730, 'Y');
INSERT INTO product VALUES ('P-00016', 'Toothpaste 150g',         'Square',       'CAT-P1', 'SUP-005', 120.00,  88.00, 'pcs',   730, 'Y');
INSERT INTO product VALUES ('P-00017', 'USB-C Charger 20W',       'Transcom',     'CAT-M1', 'SUP-006', 650.00, 480.00, 'pcs',   730, 'Y');
INSERT INTO product VALUES ('P-00018', 'Earphone Wired',          'Transcom',     'CAT-M1', 'SUP-006', 350.00, 255.00, 'pcs',   730, 'Y');
INSERT INTO product VALUES ('P-00019', 'Cotton T-Shirt (M)',      'Generic',      'CAT-C1', 'SUP-007', 450.00, 320.00, 'pcs',  NULL, 'Y');
INSERT INTO product VALUES ('P-00020', 'Discontinued Jam 250g',   'Pran',         'CAT-B1', 'SUP-001',  80.00,  58.00, 'pcs',   180, 'N');
-- ============================================================
-- ADDITIONAL PRODUCTS (P-00021 - P-00050)
-- ============================================================
INSERT INTO product VALUES ('P-00021','Instant Noodles 8 Pack','Pran','CAT-F1','SUP-001',240.00,185.00,'pack',365,'Y');
INSERT INTO product VALUES ('P-00022','Premium Flour 2kg','ACI','CAT-F1','SUP-003',145.00,112.00,'kg',365,'Y');
INSERT INTO product VALUES ('P-00023','Lentil (Masoor) 1kg','Bashundhara','CAT-F1','SUP-002',160.00,125.00,'kg',365,'Y');
INSERT INTO product VALUES ('P-00024','Salt 1kg','Fresh','CAT-F1','SUP-004',42.00,30.00,'kg',730,'Y');
INSERT INTO product VALUES ('P-00025','Tomato Ketchup 500g','Pran','CAT-F1','SUP-001',135.00,101.00,'pcs',365,'Y');

INSERT INTO product VALUES ('P-00026','Chocolate Cookies 250g','Olympic','CAT-B1','SUP-008',95.00,71.00,'pcs',180,'Y');
INSERT INTO product VALUES ('P-00027','Cream Crackers 300g','Olympic','CAT-B1','SUP-008',75.00,56.00,'pcs',180,'Y');
INSERT INTO product VALUES ('P-00028','Toast Biscuits 350g','Pran','CAT-B1','SUP-001',110.00,82.00,'pcs',180,'Y');
INSERT INTO product VALUES ('P-00029','Fruit Cake 300g','Pran','CAT-B1','SUP-001',170.00,130.00,'pcs',120,'Y');
INSERT INTO product VALUES ('P-00030','Oat Biscuits 200g','Olympic','CAT-B1','SUP-008',85.00,63.00,'pcs',180,'Y');

INSERT INTO product VALUES ('P-00031','Orange Juice 1L','Pran','CAT-BV','SUP-001',120.00,92.00,'litre',180,'Y');
INSERT INTO product VALUES ('P-00032','Apple Juice 1L','Pran','CAT-BV','SUP-001',125.00,96.00,'litre',180,'Y');
INSERT INTO product VALUES ('P-00033','Mineral Water 1L','Fresh','CAT-BV','SUP-004',30.00,20.00,'litre',365,'Y');
INSERT INTO product VALUES ('P-00034','Energy Drink 250ml','Akij','CAT-BV','SUP-007',95.00,72.00,'pcs',365,'Y');
INSERT INTO product VALUES ('P-00035','Coffee 200g','ACI','CAT-BV','SUP-003',380.00,295.00,'pcs',730,'Y');

INSERT INTO product VALUES ('P-00036','Laundry Detergent 1kg','Square','CAT-P1','SUP-005',240.00,182.00,'kg',730,'Y');
INSERT INTO product VALUES ('P-00037','Dishwashing Liquid 500ml','Square','CAT-P1','SUP-005',145.00,110.00,'ml',730,'Y');
INSERT INTO product VALUES ('P-00038','Hand Wash 250ml','ACI','CAT-P1','SUP-003',180.00,136.00,'ml',730,'Y');
INSERT INTO product VALUES ('P-00039','Toilet Cleaner 750ml','ACI','CAT-P1','SUP-003',165.00,125.00,'ml',730,'Y');
INSERT INTO product VALUES ('P-00040','Floor Cleaner 1L','Square','CAT-P1','SUP-005',210.00,160.00,'litre',730,'Y');

INSERT INTO product VALUES ('P-00041','LED Bulb 12W','Transcom','CAT-M1','SUP-006',280.00,210.00,'pcs',1095,'Y');
INSERT INTO product VALUES ('P-00042','Power Strip 4 Port','Transcom','CAT-M1','SUP-006',890.00,690.00,'pcs',1095,'Y');
INSERT INTO product VALUES ('P-00043','AA Battery (4 Pack)','Transcom','CAT-M1','SUP-006',220.00,165.00,'pack',1825,'Y');
INSERT INTO product VALUES ('P-00044','USB Flash Drive 32GB','Transcom','CAT-M1','SUP-006',850.00,660.00,'pcs',1825,'Y');
INSERT INTO product VALUES ('P-00045','Phone Data Cable','Transcom','CAT-M1','SUP-006',280.00,205.00,'pcs',1095,'Y');

INSERT INTO product VALUES ('P-00046','Men''s Polo Shirt (L)','Generic','CAT-C1','SUP-007',850.00,650.00,'pcs',NULL,'Y');
INSERT INTO product VALUES ('P-00047','Women''s T-Shirt (M)','Generic','CAT-C1','SUP-007',620.00,470.00,'pcs',NULL,'Y');
INSERT INTO product VALUES ('P-00048','Denim Jeans 32','Generic','CAT-C1','SUP-007',1450.00,1120.00,'pcs',NULL,'Y');
INSERT INTO product VALUES ('P-00049','Sports Cap','Generic','CAT-C1','SUP-007',320.00,240.00,'pcs',NULL,'Y');
INSERT INTO product VALUES ('P-00050','Cotton Socks (3 Pair)','Generic','CAT-C1','SUP-007',290.00,215.00,'pack',NULL,'Y');
-- ============================================================
-- ADDITIONAL PRODUCTS (P-00051 - P-00100)
-- ============================================================

-- CAT-D1 : Dairy
INSERT INTO product VALUES ('P-00051','Cheese Slices 200g','Aarong Dairy','CAT-D1','SUP-002',210.00,158.00,'pcs',60,'Y');
INSERT INTO product VALUES ('P-00052','Condensed Milk 400g','Pran','CAT-D1','SUP-001',150.00,112.00,'pcs',365,'Y');
INSERT INTO product VALUES ('P-00053','Ghee 500g','Aarong Dairy','CAT-D1','SUP-002',680.00,520.00,'pcs',365,'Y');
INSERT INTO product VALUES ('P-00054','Sweet Yogurt 500g','Aarong Dairy','CAT-D1','SUP-002',95.00,70.00,'pcs',5,'Y');
INSERT INTO product VALUES ('P-00055','Cream 200ml','Aarong Dairy','CAT-D1','SUP-002',130.00,98.00,'ml',7,'Y');

-- CAT-B1 : Bakery
INSERT INTO product VALUES ('P-00056','Burger Buns 4 Pack','Sunfeast','CAT-B1','SUP-004',85.00,62.00,'pack',4,'Y');
INSERT INTO product VALUES ('P-00057','Brown Bread 400g','Sunfeast','CAT-B1','SUP-004',75.00,55.00,'pcs',5,'Y');
INSERT INTO product VALUES ('P-00058','Rusk 300g','Olympic','CAT-B1','SUP-008',90.00,67.00,'pcs',180,'Y');
INSERT INTO product VALUES ('P-00059','Puff Pastry Roll 200g','Pran','CAT-B1','SUP-001',65.00,48.00,'pcs',90,'Y');
INSERT INTO product VALUES ('P-00060','Wafer Biscuits 150g','Olympic','CAT-B1','SUP-008',60.00,44.00,'pcs',180,'Y');

-- CAT-S1 : Snacks
INSERT INTO product VALUES ('P-00061','Corn Puffs 100g','Pran','CAT-S1','SUP-001',35.00,25.00,'pcs',90,'Y');
INSERT INTO product VALUES ('P-00062','Peanuts Salted 150g','Akij','CAT-S1','SUP-007',70.00,52.00,'pcs',120,'Y');
INSERT INTO product VALUES ('P-00063','Banana Chips 100g','Pran','CAT-S1','SUP-001',55.00,40.00,'pcs',120,'Y');
INSERT INTO product VALUES ('P-00064','Popcorn 100g','Akij','CAT-S1','SUP-007',50.00,36.00,'pcs',90,'Y');
INSERT INTO product VALUES ('P-00065','Mixed Nuts 200g','ACI','CAT-S1','SUP-003',280.00,215.00,'pcs',180,'Y');

-- CAT-BV : Beverages
INSERT INTO product VALUES ('P-00066','Lemon Drink 500ml','Transcom','CAT-BV','SUP-006',45.00,32.00,'pcs',90,'Y');
INSERT INTO product VALUES ('P-00067','Black Tea 100 bags','ACI','CAT-BV','SUP-003',160.00,120.00,'pcs',365,'Y');
INSERT INTO product VALUES ('P-00068','Instant Coffee 100g','ACI','CAT-BV','SUP-003',320.00,248.00,'pcs',730,'Y');
INSERT INTO product VALUES ('P-00069','Soda Water 500ml','Transcom','CAT-BV','SUP-006',35.00,24.00,'pcs',180,'Y');
INSERT INTO product VALUES ('P-00070','Tamarind Juice 250ml','Pran','CAT-BV','SUP-001',32.00,22.00,'pcs',180,'Y');

-- CAT-F1 : Grocery / Food
INSERT INTO product VALUES ('P-00071','Chickpea 1kg','Bashundhara','CAT-F1','SUP-002',155.00,120.00,'kg',365,'Y');
INSERT INTO product VALUES ('P-00072','Mustard Oil 1L','Meghna','CAT-F1','SUP-004',280.00,215.00,'litre',365,'Y');
INSERT INTO product VALUES ('P-00073','Vermicelli 400g','Pran','CAT-F1','SUP-001',85.00,64.00,'pcs',365,'Y');
INSERT INTO product VALUES ('P-00074','Turmeric Powder 200g','ACI','CAT-F1','SUP-003',95.00,72.00,'pcs',365,'Y');
INSERT INTO product VALUES ('P-00075','Chili Powder 200g','ACI','CAT-F1','SUP-003',110.00,84.00,'pcs',365,'Y');
INSERT INTO product VALUES ('P-00076','Cumin Powder 100g','ACI','CAT-F1','SUP-003',130.00,99.00,'pcs',365,'Y');
INSERT INTO product VALUES ('P-00077','Mixed Spice 100g','ACI','CAT-F1','SUP-003',95.00,72.00,'pcs',365,'Y');
INSERT INTO product VALUES ('P-00078','Fine Rice 5kg (Miniket)','Pran','CAT-F1','SUP-001',480.00,365.00,'kg',365,'Y');
INSERT INTO product VALUES ('P-00079','Brown Sugar 1kg','Bashundhara','CAT-F1','SUP-002',95.00,72.00,'kg',730,'Y');
INSERT INTO product VALUES ('P-00080','Honey 500g','ACI','CAT-F1','SUP-003',420.00,325.00,'pcs',730,'Y');

-- CAT-P1 : Personal / Household Care
INSERT INTO product VALUES ('P-00081','Hand Sanitizer 100ml','ACI','CAT-P1','SUP-003',95.00,70.00,'ml',730,'Y');
INSERT INTO product VALUES ('P-00082','Face Wash 100ml','Square','CAT-P1','SUP-005',210.00,158.00,'ml',730,'Y');
INSERT INTO product VALUES ('P-00083','Body Lotion 200ml','ACI','CAT-P1','SUP-003',260.00,195.00,'ml',730,'Y');
INSERT INTO product VALUES ('P-00084','Deodorant Spray 150ml','Square','CAT-P1','SUP-005',310.00,235.00,'ml',730,'Y');
INSERT INTO product VALUES ('P-00085','Toilet Tissue 4 Roll','Fresh','CAT-P1','SUP-004',180.00,135.00,'pack',1095,'Y');
INSERT INTO product VALUES ('P-00086','Shaving Razor 3 Pack','Square','CAT-P1','SUP-005',150.00,112.00,'pack',1095,'Y');
INSERT INTO product VALUES ('P-00087','Baby Diaper (M) 20 Pack','ACI','CAT-P1','SUP-003',650.00,495.00,'pack',730,'Y');
INSERT INTO product VALUES ('P-00088','Baby Wipes 80 Pack','ACI','CAT-P1','SUP-003',220.00,165.00,'pack',730,'Y');
INSERT INTO product VALUES ('P-00089','Mosquito Coil 10 Pack','Square','CAT-P1','SUP-005',65.00,47.00,'pack',730,'Y');
INSERT INTO product VALUES ('P-00090','Air Freshener 250ml','Square','CAT-P1','SUP-005',190.00,142.00,'ml',730,'Y');

-- CAT-M1 : Misc / Electronics-Household
INSERT INTO product VALUES ('P-00091','Extension Cord 5m','Transcom','CAT-M1','SUP-006',420.00,320.00,'pcs',1095,'Y');
INSERT INTO product VALUES ('P-00092','Wall Clock','Transcom','CAT-M1','SUP-006',380.00,285.00,'pcs',1825,'Y');
INSERT INTO product VALUES ('P-00093','Umbrella (Auto)','Generic','CAT-M1','SUP-007',480.00,360.00,'pcs',1825,'Y');
INSERT INTO product VALUES ('P-00094','Plastic Storage Box 10L','Fresh','CAT-M1','SUP-004',350.00,262.00,'pcs',1825,'Y');
INSERT INTO product VALUES ('P-00095','Steel Water Bottle 1L','Transcom','CAT-M1','SUP-006',420.00,315.00,'pcs',1825,'Y');

-- CAT-C1 : Clothing
INSERT INTO product VALUES ('P-00096','Kids T-Shirt (S)','Generic','CAT-C1','SUP-007',280.00,210.00,'pcs',NULL,'Y');
INSERT INTO product VALUES ('P-00097','Formal Shirt (L)','Generic','CAT-C1','SUP-007',950.00,730.00,'pcs',NULL,'Y');
INSERT INTO product VALUES ('P-00098','Ladies Kurti (M)','Generic','CAT-C1','SUP-007',780.00,590.00,'pcs',NULL,'Y');
INSERT INTO product VALUES ('P-00099','Winter Jacket (L)','Generic','CAT-C1','SUP-007',1850.00,1420.00,'pcs',NULL,'N');
INSERT INTO product VALUES ('P-00100','Bath Towel Large','Fresh','CAT-C1','SUP-004',380.00,285.00,'pcs',NULL,'Y');

-- ============================================================
--  11. BRANCH_INVENTORY  (200 rows)
-- ============================================================
INSERT INTO branch_inventory VALUES ('I-00001','B-DH01','P-00001',120.00,20.00,'2025-05-20','A1-S1');
INSERT INTO branch_inventory VALUES ('I-00002','B-DH01','P-00002',85.00,15.00,'2025-05-21','A1-S2');
INSERT INTO branch_inventory VALUES ('I-00003','B-DH01','P-00003',65.00,20.00,'2025-05-18','A1-S3');
INSERT INTO branch_inventory VALUES ('I-00004','B-DH01','P-00004',90.00,15.00,'2025-05-22','B1-S1');
INSERT INTO branch_inventory VALUES ('I-00005','B-DH01','P-00005',180.00,30.00,'2025-05-17','B1-S2');
INSERT INTO branch_inventory VALUES ('I-00006','B-DH01','P-00006',240.00,30.00,'2025-05-19','B1-S3');
INSERT INTO branch_inventory VALUES ('I-00007','B-DH01','P-00007',170.00,25.00,'2025-05-18','B1-S4');
INSERT INTO branch_inventory VALUES ('I-00008','B-DH01','P-00008',320.00,40.00,'2025-05-20','C1-S1');
INSERT INTO branch_inventory VALUES ('I-00009','B-DH01','P-00009',45.00,10.00,'2025-05-16','C1-S2');
INSERT INTO branch_inventory VALUES ('I-00010','B-DH01','P-00010',260.00,35.00,'2025-05-23','C1-S3');
INSERT INTO branch_inventory VALUES ('I-00011','B-DH01','P-00011',70.00,15.00,'2025-05-22','A2-S1');
INSERT INTO branch_inventory VALUES ('I-00012','B-DH01','P-00012',40.00,10.00,'2025-05-15','A2-S2');
INSERT INTO branch_inventory VALUES ('I-00013','B-DH01','P-00013',150.00,20.00,'2025-05-19','A2-S3');
INSERT INTO branch_inventory VALUES ('I-00014','B-DH01','P-00014',280.00,40.00,'2025-05-11','D1-S1');
INSERT INTO branch_inventory VALUES ('I-00015','B-DH01','P-00015',55.00,15.00,'2025-05-10','D1-S2');
INSERT INTO branch_inventory VALUES ('I-00016','B-DH01','P-00016',190.00,25.00,'2025-05-12','D1-S3');
INSERT INTO branch_inventory VALUES ('I-00017','B-DH01','P-00017',18.00,5.00,'2025-04-30','E1-S1');
INSERT INTO branch_inventory VALUES ('I-00018','B-DH01','P-00018',35.00,5.00,'2025-04-30','E1-S2');
INSERT INTO branch_inventory VALUES ('I-00019','B-DH01','P-00019',45.00,10.00,'2025-05-01','F1-S1');
INSERT INTO branch_inventory VALUES ('I-00020','B-DH01','P-00020',0.00,10.00,'2025-03-20','B2-S4');

INSERT INTO branch_inventory VALUES ('I-00021','B-DH01','P-00021',75.00,20.00,'2025-05-20','A3-S1');
INSERT INTO branch_inventory VALUES ('I-00022','B-DH01','P-00022',60.00,15.00,'2025-05-22','A3-S2');
INSERT INTO branch_inventory VALUES ('I-00023','B-DH01','P-00023',55.00,15.00,'2025-05-19','A3-S3');
INSERT INTO branch_inventory VALUES ('I-00024','B-DH01','P-00024',130.00,20.00,'2025-05-21','A3-S4');
INSERT INTO branch_inventory VALUES ('I-00025','B-DH01','P-00025',45.00,10.00,'2025-05-18','B2-S1');
INSERT INTO branch_inventory VALUES ('I-00026','B-DH01','P-00026',95.00,20.00,'2025-05-19','B2-S2');
INSERT INTO branch_inventory VALUES ('I-00027','B-DH01','P-00027',110.00,20.00,'2025-05-20','B2-S3');
INSERT INTO branch_inventory VALUES ('I-00028','B-DH01','P-00028',85.00,20.00,'2025-05-18','B2-S4');
INSERT INTO branch_inventory VALUES ('I-00029','B-DH01','P-00029',35.00,10.00,'2025-05-17','C2-S1');
INSERT INTO branch_inventory VALUES ('I-00030','B-DH01','P-00030',90.00,20.00,'2025-05-22','C2-S2');
INSERT INTO branch_inventory VALUES ('I-00031','B-DH01','P-00031',60.00,15.00,'2025-05-20','C2-S3');
INSERT INTO branch_inventory VALUES ('I-00032','B-DH01','P-00032',55.00,15.00,'2025-05-20','C2-S4');
INSERT INTO branch_inventory VALUES ('I-00033','B-DH01','P-00033',220.00,40.00,'2025-05-22','C3-S1');
INSERT INTO branch_inventory VALUES ('I-00034','B-DH01','P-00034',30.00,10.00,'2025-05-16','C3-S2');
INSERT INTO branch_inventory VALUES ('I-00035','B-DH01','P-00035',22.00,10.00,'2025-05-18','C3-S3');
INSERT INTO branch_inventory VALUES ('I-00036','B-DH01','P-00036',80.00,20.00,'2025-05-19','D2-S1');
INSERT INTO branch_inventory VALUES ('I-00037','B-DH01','P-00037',65.00,15.00,'2025-05-18','D2-S2');
INSERT INTO branch_inventory VALUES ('I-00038','B-DH01','P-00038',48.00,15.00,'2025-05-21','D2-S3');
INSERT INTO branch_inventory VALUES ('I-00039','B-DH01','P-00039',40.00,15.00,'2025-05-20','D2-S4');
INSERT INTO branch_inventory VALUES ('I-00040','B-DH01','P-00040',38.00,15.00,'2025-05-21','D3-S1');
INSERT INTO branch_inventory VALUES ('I-00041','B-DH01','P-00041',28.00,8.00,'2025-05-15','E2-S1');
INSERT INTO branch_inventory VALUES ('I-00042','B-DH01','P-00042',12.00,5.00,'2025-05-12','E2-S2');
INSERT INTO branch_inventory VALUES ('I-00043','B-DH01','P-00043',75.00,15.00,'2025-05-18','E2-S3');
INSERT INTO branch_inventory VALUES ('I-00044','B-DH01','P-00044',18.00,5.00,'2025-05-14','E2-S4');
INSERT INTO branch_inventory VALUES ('I-00045','B-DH01','P-00045',40.00,10.00,'2025-05-17','E3-S1');
INSERT INTO branch_inventory VALUES ('I-00046','B-DH01','P-00046',20.00,5.00,'2025-05-11','F2-S1');
INSERT INTO branch_inventory VALUES ('I-00047','B-DH01','P-00047',22.00,5.00,'2025-05-10','F2-S2');
INSERT INTO branch_inventory VALUES ('I-00048','B-DH01','P-00048',14.00,5.00,'2025-05-09','F2-S3');
INSERT INTO branch_inventory VALUES ('I-00049','B-DH01','P-00049',40.00,10.00,'2025-05-13','F2-S4');
INSERT INTO branch_inventory VALUES ('I-00050','B-DH01','P-00050',55.00,10.00,'2025-05-16','F3-S1');

-- ============================================================
-- BRANCH INVENTORY (B-DH02)
-- I-00051 - I-00100
-- ============================================================

INSERT INTO branch_inventory VALUES ('I-00051','B-DH02','P-00001',95.00,20.00,'2025-05-21','A1-S1');
INSERT INTO branch_inventory VALUES ('I-00052','B-DH02','P-00002',75.00,15.00,'2025-05-22','A1-S2');
INSERT INTO branch_inventory VALUES ('I-00053','B-DH02','P-00003',50.00,20.00,'2025-05-18','A1-S3');
INSERT INTO branch_inventory VALUES ('I-00054','B-DH02','P-00004',65.00,15.00,'2025-05-20','B1-S1');
INSERT INTO branch_inventory VALUES ('I-00055','B-DH02','P-00005',210.00,30.00,'2025-05-19','B1-S2');
INSERT INTO branch_inventory VALUES ('I-00056','B-DH02','P-00006',185.00,30.00,'2025-05-17','B1-S3');
INSERT INTO branch_inventory VALUES ('I-00057','B-DH02','P-00007',145.00,25.00,'2025-05-18','B1-S4');
INSERT INTO branch_inventory VALUES ('I-00058','B-DH02','P-00008',420.00,50.00,'2025-05-20','C1-S1');
INSERT INTO branch_inventory VALUES ('I-00059','B-DH02','P-00009',9.00,15.00,'2025-05-12','C1-S2');   -- LOW STOCK
INSERT INTO branch_inventory VALUES ('I-00060','B-DH02','P-00010',310.00,40.00,'2025-05-23','C1-S3');

INSERT INTO branch_inventory VALUES ('I-00061','B-DH02','P-00011',58.00,15.00,'2025-05-22','A2-S1');
INSERT INTO branch_inventory VALUES ('I-00062','B-DH02','P-00012',35.00,10.00,'2025-05-15','A2-S2');
INSERT INTO branch_inventory VALUES ('I-00063','B-DH02','P-00013',125.00,20.00,'2025-05-19','A2-S3');
INSERT INTO branch_inventory VALUES ('I-00064','B-DH02','P-00014',295.00,40.00,'2025-05-11','D1-S1');
INSERT INTO branch_inventory VALUES ('I-00065','B-DH02','P-00015',62.00,20.00,'2025-05-14','D1-S2');
INSERT INTO branch_inventory VALUES ('I-00066','B-DH02','P-00016',175.00,30.00,'2025-05-16','D1-S3');
INSERT INTO branch_inventory VALUES ('I-00067','B-DH02','P-00017',20.00,5.00,'2025-04-30','E1-S1');
INSERT INTO branch_inventory VALUES ('I-00068','B-DH02','P-00018',38.00,5.00,'2025-04-30','E1-S2');
INSERT INTO branch_inventory VALUES ('I-00069','B-DH02','P-00019',28.00,5.00,'2025-05-02','F1-S1');
INSERT INTO branch_inventory VALUES ('I-00070','B-DH02','P-00020',0.00,10.00,'2025-03-15','B2-S4');

INSERT INTO branch_inventory VALUES ('I-00071','B-DH02','P-00021',70.00,20.00,'2025-05-21','A3-S1');
INSERT INTO branch_inventory VALUES ('I-00072','B-DH02','P-00022',52.00,15.00,'2025-05-20','A3-S2');
INSERT INTO branch_inventory VALUES ('I-00073','B-DH02','P-00023',48.00,15.00,'2025-05-18','A3-S3');
INSERT INTO branch_inventory VALUES ('I-00074','B-DH02','P-00024',115.00,20.00,'2025-05-22','A3-S4');
INSERT INTO branch_inventory VALUES ('I-00075','B-DH02','P-00025',36.00,10.00,'2025-05-19','B2-S1');
INSERT INTO branch_inventory VALUES ('I-00076','B-DH02','P-00026',82.00,20.00,'2025-05-18','B2-S2');
INSERT INTO branch_inventory VALUES ('I-00077','B-DH02','P-00027',98.00,20.00,'2025-05-20','B2-S3');
INSERT INTO branch_inventory VALUES ('I-00078','B-DH02','P-00028',74.00,20.00,'2025-05-18','B2-S4');
INSERT INTO branch_inventory VALUES ('I-00079','B-DH02','P-00029',27.00,10.00,'2025-05-17','C2-S1');
INSERT INTO branch_inventory VALUES ('I-00080','B-DH02','P-00030',81.00,20.00,'2025-05-22','C2-S2');

INSERT INTO branch_inventory VALUES ('I-00081','B-DH02','P-00031',48.00,15.00,'2025-05-20','C2-S3');
INSERT INTO branch_inventory VALUES ('I-00082','B-DH02','P-00032',44.00,15.00,'2025-05-20','C2-S4');
INSERT INTO branch_inventory VALUES ('I-00083','B-DH02','P-00033',190.00,40.00,'2025-05-22','C3-S1');
INSERT INTO branch_inventory VALUES ('I-00084','B-DH02','P-00034',24.00,10.00,'2025-05-18','C3-S2');
INSERT INTO branch_inventory VALUES ('I-00085','B-DH02','P-00035',6.00,10.00,'2025-05-15','C3-S3');   -- LOW STOCK
INSERT INTO branch_inventory VALUES ('I-00086','B-DH02','P-00036',72.00,20.00,'2025-05-19','D2-S1');
INSERT INTO branch_inventory VALUES ('I-00087','B-DH02','P-00037',58.00,15.00,'2025-05-21','D2-S2');
INSERT INTO branch_inventory VALUES ('I-00088','B-DH02','P-00038',40.00,15.00,'2025-05-20','D2-S3');
INSERT INTO branch_inventory VALUES ('I-00089','B-DH02','P-00039',32.00,15.00,'2025-05-17','D2-S4');
INSERT INTO branch_inventory VALUES ('I-00090','B-DH02','P-00040',29.00,15.00,'2025-05-19','D3-S1');

INSERT INTO branch_inventory VALUES ('I-00091','B-DH02','P-00041',25.00,8.00,'2025-05-16','E2-S1');
INSERT INTO branch_inventory VALUES ('I-00092','B-DH02','P-00042',15.00,5.00,'2025-05-15','E2-S2');
INSERT INTO branch_inventory VALUES ('I-00093','B-DH02','P-00043',66.00,15.00,'2025-05-18','E2-S3');
INSERT INTO branch_inventory VALUES ('I-00094','B-DH02','P-00044',20.00,5.00,'2025-05-14','E2-S4');
INSERT INTO branch_inventory VALUES ('I-00095','B-DH02','P-00045',34.00,10.00,'2025-05-17','E3-S1');
INSERT INTO branch_inventory VALUES ('I-00096','B-DH02','P-00046',18.00,5.00,'2025-05-12','F2-S1');
INSERT INTO branch_inventory VALUES ('I-00097','B-DH02','P-00047',21.00,5.00,'2025-05-10','F2-S2');
INSERT INTO branch_inventory VALUES ('I-00098','B-DH02','P-00048',12.00,5.00,'2025-05-09','F2-S3');
INSERT INTO branch_inventory VALUES ('I-00099','B-DH02','P-00049',4.00,10.00,'2025-05-13','F2-S4');   -- LOW STOCK
INSERT INTO branch_inventory VALUES ('I-00100','B-DH02','P-00050',48.00,10.00,'2025-05-16','F3-S1');


-- ============================================================
-- BRANCH INVENTORY (B-DH03)
-- I-00101 - I-00150
-- ============================================================

INSERT INTO branch_inventory VALUES ('I-00101','B-DH03','P-00001',82.00,20.00,'2025-05-20','A1-S1');
INSERT INTO branch_inventory VALUES ('I-00102','B-DH03','P-00002',58.00,15.00,'2025-05-21','A1-S2');
INSERT INTO branch_inventory VALUES ('I-00103','B-DH03','P-00003',42.00,10.00,'2025-05-18','A1-S3');
INSERT INTO branch_inventory VALUES ('I-00104','B-DH03','P-00004',72.00,15.00,'2025-05-22','B1-S1');
INSERT INTO branch_inventory VALUES ('I-00105','B-DH03','P-00005',165.00,25.00,'2025-05-17','B1-S2');
INSERT INTO branch_inventory VALUES ('I-00106','B-DH03','P-00006',205.00,30.00,'2025-05-19','B1-S3');
INSERT INTO branch_inventory VALUES ('I-00107','B-DH03','P-00007',138.00,25.00,'2025-05-18','B1-S4');
INSERT INTO branch_inventory VALUES ('I-00108','B-DH03','P-00008',285.00,40.00,'2025-05-20','C1-S1');
INSERT INTO branch_inventory VALUES ('I-00109','B-DH03','P-00009',12.00,15.00,'2025-05-12','C1-S2'); -- LOW STOCK
INSERT INTO branch_inventory VALUES ('I-00110','B-DH03','P-00010',240.00,35.00,'2025-05-23','C1-S3');

INSERT INTO branch_inventory VALUES ('I-00111','B-DH03','P-00011',52.00,15.00,'2025-05-22','A2-S1');
INSERT INTO branch_inventory VALUES ('I-00112','B-DH03','P-00012',28.00,10.00,'2025-05-15','A2-S2');
INSERT INTO branch_inventory VALUES ('I-00113','B-DH03','P-00013',118.00,20.00,'2025-05-19','A2-S3');
INSERT INTO branch_inventory VALUES ('I-00114','B-DH03','P-00014',245.00,40.00,'2025-05-11','D1-S1');
INSERT INTO branch_inventory VALUES ('I-00115','B-DH03','P-00015',16.00,20.00,'2025-05-10','D1-S2'); -- LOW STOCK
INSERT INTO branch_inventory VALUES ('I-00116','B-DH03','P-00016',182.00,30.00,'2025-05-12','D1-S3');
INSERT INTO branch_inventory VALUES ('I-00117','B-DH03','P-00017',14.00,5.00,'2025-04-30','E1-S1');
INSERT INTO branch_inventory VALUES ('I-00118','B-DH03','P-00018',27.00,5.00,'2025-04-30','E1-S2');
INSERT INTO branch_inventory VALUES ('I-00119','B-DH03','P-00019',33.00,5.00,'2025-05-01','F1-S1');
INSERT INTO branch_inventory VALUES ('I-00120','B-DH03','P-00020',0.00,10.00,'2025-03-18','B2-S4');

INSERT INTO branch_inventory VALUES ('I-00121','B-DH03','P-00021',62.00,20.00,'2025-05-20','A3-S1');
INSERT INTO branch_inventory VALUES ('I-00122','B-DH03','P-00022',48.00,15.00,'2025-05-22','A3-S2');
INSERT INTO branch_inventory VALUES ('I-00123','B-DH03','P-00023',40.00,15.00,'2025-05-19','A3-S3');
INSERT INTO branch_inventory VALUES ('I-00124','B-DH03','P-00024',102.00,20.00,'2025-05-21','A3-S4');
INSERT INTO branch_inventory VALUES ('I-00125','B-DH03','P-00025',34.00,10.00,'2025-05-18','B2-S1');
INSERT INTO branch_inventory VALUES ('I-00126','B-DH03','P-00026',76.00,20.00,'2025-05-19','B2-S2');
INSERT INTO branch_inventory VALUES ('I-00127','B-DH03','P-00027',89.00,20.00,'2025-05-20','B2-S3');
INSERT INTO branch_inventory VALUES ('I-00128','B-DH03','P-00028',68.00,20.00,'2025-05-18','B2-S4');
INSERT INTO branch_inventory VALUES ('I-00129','B-DH03','P-00029',24.00,10.00,'2025-05-17','C2-S1');
INSERT INTO branch_inventory VALUES ('I-00130','B-DH03','P-00030',74.00,20.00,'2025-05-22','C2-S2');

INSERT INTO branch_inventory VALUES ('I-00131','B-DH03','P-00031',46.00,15.00,'2025-05-20','C2-S3');
INSERT INTO branch_inventory VALUES ('I-00132','B-DH03','P-00032',39.00,15.00,'2025-05-20','C2-S4');
INSERT INTO branch_inventory VALUES ('I-00133','B-DH03','P-00033',175.00,40.00,'2025-05-22','C3-S1');
INSERT INTO branch_inventory VALUES ('I-00134','B-DH03','P-00034',18.00,10.00,'2025-05-16','C3-S2');
INSERT INTO branch_inventory VALUES ('I-00135','B-DH03','P-00035',8.00,10.00,'2025-05-18','C3-S3'); -- LOW STOCK
INSERT INTO branch_inventory VALUES ('I-00136','B-DH03','P-00036',66.00,20.00,'2025-05-19','D2-S1');
INSERT INTO branch_inventory VALUES ('I-00137','B-DH03','P-00037',52.00,15.00,'2025-05-18','D2-S2');
INSERT INTO branch_inventory VALUES ('I-00138','B-DH03','P-00038',36.00,15.00,'2025-05-21','D2-S3');
INSERT INTO branch_inventory VALUES ('I-00139','B-DH03','P-00039',28.00,15.00,'2025-05-20','D2-S4');
INSERT INTO branch_inventory VALUES ('I-00140','B-DH03','P-00040',25.00,15.00,'2025-05-21','D3-S1');

INSERT INTO branch_inventory VALUES ('I-00141','B-DH03','P-00041',21.00,8.00,'2025-05-15','E2-S1');
INSERT INTO branch_inventory VALUES ('I-00142','B-DH03','P-00042',11.00,5.00,'2025-05-12','E2-S2');
INSERT INTO branch_inventory VALUES ('I-00143','B-DH03','P-00043',58.00,15.00,'2025-05-18','E2-S3');
INSERT INTO branch_inventory VALUES ('I-00144','B-DH03','P-00044',15.00,5.00,'2025-05-14','E2-S4');
INSERT INTO branch_inventory VALUES ('I-00145','B-DH03','P-00045',29.00,10.00,'2025-05-17','E3-S1');
INSERT INTO branch_inventory VALUES ('I-00146','B-DH03','P-00046',16.00,5.00,'2025-05-11','F2-S1');
INSERT INTO branch_inventory VALUES ('I-00147','B-DH03','P-00047',18.00,5.00,'2025-05-10','F2-S2');
INSERT INTO branch_inventory VALUES ('I-00148','B-DH03','P-00048',10.00,5.00,'2025-05-09','F2-S3');
INSERT INTO branch_inventory VALUES ('I-00149','B-DH03','P-00049',6.00,10.00,'2025-05-13','F2-S4'); -- LOW STOCK
INSERT INTO branch_inventory VALUES ('I-00150','B-DH03','P-00050',41.00,10.00,'2025-05-16','F3-S1');

-- ============================================================
-- BRANCH INVENTORY (B-CT01)
-- I-00151 - I-00200
-- ============================================================

INSERT INTO branch_inventory VALUES ('I-00151','B-CT01','P-00001',75.00,20.00,'2025-05-20','A1-S1');
INSERT INTO branch_inventory VALUES ('I-00152','B-CT01','P-00002',62.00,15.00,'2025-05-21','A1-S2');
INSERT INTO branch_inventory VALUES ('I-00153','B-CT01','P-00003',38.00,10.00,'2025-05-18','A1-S3');
INSERT INTO branch_inventory VALUES ('I-00154','B-CT01','P-00004',68.00,15.00,'2025-05-22','B1-S1');
INSERT INTO branch_inventory VALUES ('I-00155','B-CT01','P-00005',150.00,25.00,'2025-05-17','B1-S2');
INSERT INTO branch_inventory VALUES ('I-00156','B-CT01','P-00006',160.00,30.00,'2025-05-19','B1-S3');
INSERT INTO branch_inventory VALUES ('I-00157','B-CT01','P-00007',110.00,20.00,'2025-05-18','B1-S4');
INSERT INTO branch_inventory VALUES ('I-00158','B-CT01','P-00008',240.00,40.00,'2025-05-20','C1-S1');
INSERT INTO branch_inventory VALUES ('I-00159','B-CT01','P-00009',18.00,15.00,'2025-05-14','C1-S2');
INSERT INTO branch_inventory VALUES ('I-00160','B-CT01','P-00010',210.00,35.00,'2025-05-23','C1-S3');

INSERT INTO branch_inventory VALUES ('I-00161','B-CT01','P-00011',40.00,10.00,'2025-05-22','A2-S1');
INSERT INTO branch_inventory VALUES ('I-00162','B-CT01','P-00012',26.00,10.00,'2025-05-15','A2-S2');
INSERT INTO branch_inventory VALUES ('I-00163','B-CT01','P-00013',95.00,20.00,'2025-05-19','A2-S3');
INSERT INTO branch_inventory VALUES ('I-00164','B-CT01','P-00014',205.00,40.00,'2025-05-11','D1-S1');
INSERT INTO branch_inventory VALUES ('I-00165','B-CT01','P-00015',18.00,20.00,'2025-05-10','D1-S2'); -- LOW STOCK
INSERT INTO branch_inventory VALUES ('I-00166','B-CT01','P-00016',145.00,30.00,'2025-05-12','D1-S3');
INSERT INTO branch_inventory VALUES ('I-00167','B-CT01','P-00017',11.00,5.00,'2025-04-30','E1-S1');
INSERT INTO branch_inventory VALUES ('I-00168','B-CT01','P-00018',23.00,5.00,'2025-04-30','E1-S2');
INSERT INTO branch_inventory VALUES ('I-00169','B-CT01','P-00019',28.00,5.00,'2025-05-01','F1-S1');
INSERT INTO branch_inventory VALUES ('I-00170','B-CT01','P-00020',0.00,10.00,'2025-03-20','B2-S4');

INSERT INTO branch_inventory VALUES ('I-00171','B-CT01','P-00021',54.00,20.00,'2025-05-20','A3-S1');
INSERT INTO branch_inventory VALUES ('I-00172','B-CT01','P-00022',42.00,15.00,'2025-05-22','A3-S2');
INSERT INTO branch_inventory VALUES ('I-00173','B-CT01','P-00023',36.00,15.00,'2025-05-19','A3-S3');
INSERT INTO branch_inventory VALUES ('I-00174','B-CT01','P-00024',92.00,20.00,'2025-05-21','A3-S4');
INSERT INTO branch_inventory VALUES ('I-00175','B-CT01','P-00025',31.00,10.00,'2025-05-18','B2-S1');
INSERT INTO branch_inventory VALUES ('I-00176','B-CT01','P-00026',70.00,20.00,'2025-05-19','B2-S2');
INSERT INTO branch_inventory VALUES ('I-00177','B-CT01','P-00027',82.00,20.00,'2025-05-20','B2-S3');
INSERT INTO branch_inventory VALUES ('I-00178','B-CT01','P-00028',62.00,20.00,'2025-05-18','B2-S4');
INSERT INTO branch_inventory VALUES ('I-00179','B-CT01','P-00029',21.00,10.00,'2025-05-17','C2-S1');
INSERT INTO branch_inventory VALUES ('I-00180','B-CT01','P-00030',67.00,20.00,'2025-05-22','C2-S2');

INSERT INTO branch_inventory VALUES ('I-00181','B-CT01','P-00031',42.00,15.00,'2025-05-20','C2-S3');
INSERT INTO branch_inventory VALUES ('I-00182','B-CT01','P-00032',35.00,15.00,'2025-05-20','C2-S4');
INSERT INTO branch_inventory VALUES ('I-00183','B-CT01','P-00033',160.00,40.00,'2025-05-22','C3-S1');
INSERT INTO branch_inventory VALUES ('I-00184','B-CT01','P-00034',15.00,10.00,'2025-05-16','C3-S2');
INSERT INTO branch_inventory VALUES ('I-00185','B-CT01','P-00035',7.00,10.00,'2025-05-18','C3-S3'); -- LOW STOCK
INSERT INTO branch_inventory VALUES ('I-00186','B-CT01','P-00036',58.00,20.00,'2025-05-19','D2-S1');
INSERT INTO branch_inventory VALUES ('I-00187','B-CT01','P-00037',45.00,15.00,'2025-05-18','D2-S2');
INSERT INTO branch_inventory VALUES ('I-00188','B-CT01','P-00038',32.00,15.00,'2025-05-21','D2-S3');
INSERT INTO branch_inventory VALUES ('I-00189','B-CT01','P-00039',24.00,15.00,'2025-05-20','D2-S4');
INSERT INTO branch_inventory VALUES ('I-00190','B-CT01','P-00040',22.00,15.00,'2025-05-21','D3-S1');

INSERT INTO branch_inventory VALUES ('I-00191','B-CT01','P-00041',18.00,8.00,'2025-05-15','E2-S1');
INSERT INTO branch_inventory VALUES ('I-00192','B-CT01','P-00042',9.00,5.00,'2025-05-12','E2-S2');
INSERT INTO branch_inventory VALUES ('I-00193','B-CT01','P-00043',50.00,15.00,'2025-05-18','E2-S3');
INSERT INTO branch_inventory VALUES ('I-00194','B-CT01','P-00044',13.00,5.00,'2025-05-14','E2-S4');
INSERT INTO branch_inventory VALUES ('I-00195','B-CT01','P-00045',25.00,10.00,'2025-05-17','E3-S1');
INSERT INTO branch_inventory VALUES ('I-00196','B-CT01','P-00046',14.00,5.00,'2025-05-11','F2-S1');
INSERT INTO branch_inventory VALUES ('I-00197','B-CT01','P-00047',16.00,5.00,'2025-05-10','F2-S2');
INSERT INTO branch_inventory VALUES ('I-00198','B-CT01','P-00048',9.00,5.00,'2025-05-09','F2-S3');
INSERT INTO branch_inventory VALUES ('I-00199','B-CT01','P-00049',5.00,10.00,'2025-05-13','F2-S4'); -- LOW STOCK
INSERT INTO branch_inventory VALUES ('I-00200','B-CT01','P-00050',38.00,10.00,'2025-05-16','F3-S1');

-- ============================================================
-- BRANCH INVENTORY (B-CT02)
-- I-00201 - I-00250
-- ============================================================

INSERT INTO branch_inventory VALUES ('I-00201','B-CT02','P-00001',68.00,20.00,'2025-05-20','A1-S1');
INSERT INTO branch_inventory VALUES ('I-00202','B-CT02','P-00002',50.00,15.00,'2025-05-18','A1-S2');
INSERT INTO branch_inventory VALUES ('I-00203','B-CT02','P-00003',32.00,10.00,'2025-05-19','A1-S3');
INSERT INTO branch_inventory VALUES ('I-00204','B-CT02','P-00004',54.00,15.00,'2025-05-21','B1-S1');
INSERT INTO branch_inventory VALUES ('I-00205','B-CT02','P-00005',142.00,25.00,'2025-05-17','B1-S2');
INSERT INTO branch_inventory VALUES ('I-00206','B-CT02','P-00006',138.00,30.00,'2025-05-20','B1-S3');
INSERT INTO branch_inventory VALUES ('I-00207','B-CT02','P-00007',95.00,20.00,'2025-05-18','B1-S4');
INSERT INTO branch_inventory VALUES ('I-00208','B-CT02','P-00008',205.00,40.00,'2025-05-20','C1-S1');
INSERT INTO branch_inventory VALUES ('I-00209','B-CT02','P-00009',14.00,15.00,'2025-05-14','C1-S2'); -- LOW STOCK
INSERT INTO branch_inventory VALUES ('I-00210','B-CT02','P-00010',300.00,40.00,'2025-05-23','C1-S3');

INSERT INTO branch_inventory VALUES ('I-00211','B-CT02','P-00011',35.00,10.00,'2025-05-22','A2-S1');
INSERT INTO branch_inventory VALUES ('I-00212','B-CT02','P-00012',25.00,10.00,'2025-05-11','A2-S2');
INSERT INTO branch_inventory VALUES ('I-00213','B-CT02','P-00013',110.00,20.00,'2025-05-19','A2-S3');
INSERT INTO branch_inventory VALUES ('I-00214','B-CT02','P-00014',188.00,40.00,'2025-05-11','D1-S1');
INSERT INTO branch_inventory VALUES ('I-00215','B-CT02','P-00015',22.00,20.00,'2025-05-10','D1-S2');
INSERT INTO branch_inventory VALUES ('I-00216','B-CT02','P-00016',132.00,30.00,'2025-05-12','D1-S3');
INSERT INTO branch_inventory VALUES ('I-00217','B-CT02','P-00017',10.00,5.00,'2025-04-30','E1-S1');
INSERT INTO branch_inventory VALUES ('I-00218','B-CT02','P-00018',19.00,5.00,'2025-04-30','E1-S2');
INSERT INTO branch_inventory VALUES ('I-00219','B-CT02','P-00019',35.00,5.00,'2025-05-01','F1-S1');
INSERT INTO branch_inventory VALUES ('I-00220','B-CT02','P-00020',0.00,10.00,'2025-03-18','B2-S4');

INSERT INTO branch_inventory VALUES ('I-00221','B-CT02','P-00021',48.00,20.00,'2025-05-20','A3-S1');
INSERT INTO branch_inventory VALUES ('I-00222','B-CT02','P-00022',36.00,15.00,'2025-05-22','A3-S2');
INSERT INTO branch_inventory VALUES ('I-00223','B-CT02','P-00023',30.00,15.00,'2025-05-19','A3-S3');
INSERT INTO branch_inventory VALUES ('I-00224','B-CT02','P-00024',85.00,20.00,'2025-05-21','A3-S4');
INSERT INTO branch_inventory VALUES ('I-00225','B-CT02','P-00025',28.00,10.00,'2025-05-18','B2-S1');
INSERT INTO branch_inventory VALUES ('I-00226','B-CT02','P-00026',62.00,20.00,'2025-05-19','B2-S2');
INSERT INTO branch_inventory VALUES ('I-00227','B-CT02','P-00027',74.00,20.00,'2025-05-20','B2-S3');
INSERT INTO branch_inventory VALUES ('I-00228','B-CT02','P-00028',56.00,20.00,'2025-05-18','B2-S4');
INSERT INTO branch_inventory VALUES ('I-00229','B-CT02','P-00029',18.00,10.00,'2025-05-17','C2-S1');
INSERT INTO branch_inventory VALUES ('I-00230','B-CT02','P-00030',59.00,20.00,'2025-05-22','C2-S2');

INSERT INTO branch_inventory VALUES ('I-00231','B-CT02','P-00031',38.00,15.00,'2025-05-20','C2-S3');
INSERT INTO branch_inventory VALUES ('I-00232','B-CT02','P-00032',30.00,15.00,'2025-05-20','C2-S4');
INSERT INTO branch_inventory VALUES ('I-00233','B-CT02','P-00033',145.00,40.00,'2025-05-22','C3-S1');
INSERT INTO branch_inventory VALUES ('I-00234','B-CT02','P-00034',12.00,10.00,'2025-05-16','C3-S2');
INSERT INTO branch_inventory VALUES ('I-00235','B-CT02','P-00035',9.00,10.00,'2025-05-18','C3-S3'); -- LOW STOCK
INSERT INTO branch_inventory VALUES ('I-00236','B-CT02','P-00036',52.00,20.00,'2025-05-19','D2-S1');
INSERT INTO branch_inventory VALUES ('I-00237','B-CT02','P-00037',40.00,15.00,'2025-05-18','D2-S2');
INSERT INTO branch_inventory VALUES ('I-00238','B-CT02','P-00038',28.00,15.00,'2025-05-21','D2-S3');
INSERT INTO branch_inventory VALUES ('I-00239','B-CT02','P-00039',22.00,15.00,'2025-05-20','D2-S4');
INSERT INTO branch_inventory VALUES ('I-00240','B-CT02','P-00040',20.00,15.00,'2025-05-21','D3-S1');

INSERT INTO branch_inventory VALUES ('I-00241','B-CT02','P-00041',15.00,8.00,'2025-05-15','E2-S1');
INSERT INTO branch_inventory VALUES ('I-00242','B-CT02','P-00042',8.00,5.00,'2025-05-12','E2-S2');
INSERT INTO branch_inventory VALUES ('I-00243','B-CT02','P-00043',45.00,15.00,'2025-05-18','E2-S3');
INSERT INTO branch_inventory VALUES ('I-00244','B-CT02','P-00044',11.00,5.00,'2025-05-14','E2-S4');
INSERT INTO branch_inventory VALUES ('I-00245','B-CT02','P-00045',22.00,10.00,'2025-05-17','E3-S1');
INSERT INTO branch_inventory VALUES ('I-00246','B-CT02','P-00046',12.00,5.00,'2025-05-11','F2-S1');
INSERT INTO branch_inventory VALUES ('I-00247','B-CT02','P-00047',14.00,5.00,'2025-05-10','F2-S2');
INSERT INTO branch_inventory VALUES ('I-00248','B-CT02','P-00048',8.00,5.00,'2025-05-09','F2-S3');
INSERT INTO branch_inventory VALUES ('I-00249','B-CT02','P-00049',4.00,10.00,'2025-05-13','F2-S4'); -- LOW STOCK
INSERT INTO branch_inventory VALUES ('I-00250','B-CT02','P-00050',35.00,10.00,'2025-05-16','F3-S1');


-- ============================================================
-- BRANCH INVENTORY (B-SY01)
-- I-00251 - I-00300
-- ============================================================

INSERT INTO branch_inventory VALUES ('I-00251','B-SY01','P-00001',55.00,15.00,'2025-05-20','A1-S1');
INSERT INTO branch_inventory VALUES ('I-00252','B-SY01','P-00002',45.00,15.00,'2025-05-18','A1-S2');
INSERT INTO branch_inventory VALUES ('I-00253','B-SY01','P-00003',28.00,10.00,'2025-05-17','A1-S3');
INSERT INTO branch_inventory VALUES ('I-00254','B-SY01','P-00004',8.00,10.00,'2025-04-15','B1-S1'); -- LOW STOCK
INSERT INTO branch_inventory VALUES ('I-00255','B-SY01','P-00005',120.00,25.00,'2025-05-16','B1-S2');
INSERT INTO branch_inventory VALUES ('I-00256','B-SY01','P-00006',110.00,30.00,'2025-05-18','B1-S3');
INSERT INTO branch_inventory VALUES ('I-00257','B-SY01','P-00007',85.00,20.00,'2025-05-17','B1-S4');
INSERT INTO branch_inventory VALUES ('I-00258','B-SY01','P-00008',170.00,40.00,'2025-05-20','C1-S1');
INSERT INTO branch_inventory VALUES ('I-00259','B-SY01','P-00009',16.00,15.00,'2025-05-13','C1-S2');
INSERT INTO branch_inventory VALUES ('I-00260','B-SY01','P-00010',180.00,35.00,'2025-05-22','C1-S3');

INSERT INTO branch_inventory VALUES ('I-00261','B-SY01','P-00011',30.00,10.00,'2025-05-19','A2-S1');
INSERT INTO branch_inventory VALUES ('I-00262','B-SY01','P-00012',18.00,10.00,'2025-05-11','A2-S2');
INSERT INTO branch_inventory VALUES ('I-00263','B-SY01','P-00013',90.00,20.00,'2025-05-16','A2-S3');
INSERT INTO branch_inventory VALUES ('I-00264','B-SY01','P-00014',190.00,30.00,'2025-05-05','D1-S1');
INSERT INTO branch_inventory VALUES ('I-00265','B-SY01','P-00015',14.00,20.00,'2025-05-09','D1-S2'); -- LOW STOCK
INSERT INTO branch_inventory VALUES ('I-00266','B-SY01','P-00016',115.00,30.00,'2025-05-10','D1-S3');
INSERT INTO branch_inventory VALUES ('I-00267','B-SY01','P-00017',8.00,5.00,'2025-04-29','E1-S1');
INSERT INTO branch_inventory VALUES ('I-00268','B-SY01','P-00018',15.00,5.00,'2025-04-29','E1-S2');
INSERT INTO branch_inventory VALUES ('I-00269','B-SY01','P-00019',24.00,5.00,'2025-05-01','F1-S1');
INSERT INTO branch_inventory VALUES ('I-00270','B-SY01','P-00020',0.00,10.00,'2025-03-15','B2-S4');

INSERT INTO branch_inventory VALUES ('I-00271','B-SY01','P-00021',40.00,20.00,'2025-05-18','A3-S1');
INSERT INTO branch_inventory VALUES ('I-00272','B-SY01','P-00022',28.00,15.00,'2025-05-19','A3-S2');
INSERT INTO branch_inventory VALUES ('I-00273','B-SY01','P-00023',25.00,15.00,'2025-05-18','A3-S3');
INSERT INTO branch_inventory VALUES ('I-00274','B-SY01','P-00024',65.00,20.00,'2025-05-20','A3-S4');
INSERT INTO branch_inventory VALUES ('I-00275','B-SY01','P-00025',22.00,10.00,'2025-05-17','B2-S1');
INSERT INTO branch_inventory VALUES ('I-00276','B-SY01','P-00026',48.00,20.00,'2025-05-18','B2-S2');
INSERT INTO branch_inventory VALUES ('I-00277','B-SY01','P-00027',60.00,20.00,'2025-05-19','B2-S3');
INSERT INTO branch_inventory VALUES ('I-00278','B-SY01','P-00028',42.00,20.00,'2025-05-17','B2-S4');
INSERT INTO branch_inventory VALUES ('I-00279','B-SY01','P-00029',15.00,10.00,'2025-05-16','C2-S1');
INSERT INTO branch_inventory VALUES ('I-00280','B-SY01','P-00030',45.00,20.00,'2025-05-20','C2-S2');

INSERT INTO branch_inventory VALUES ('I-00281','B-SY01','P-00031',28.00,15.00,'2025-05-18','C2-S3');
INSERT INTO branch_inventory VALUES ('I-00282','B-SY01','P-00032',24.00,15.00,'2025-05-18','C2-S4');
INSERT INTO branch_inventory VALUES ('I-00283','B-SY01','P-00033',120.00,40.00,'2025-05-21','C3-S1');
INSERT INTO branch_inventory VALUES ('I-00284','B-SY01','P-00034',10.00,10.00,'2025-05-15','C3-S2');
INSERT INTO branch_inventory VALUES ('I-00285','B-SY01','P-00035',5.00,10.00,'2025-05-16','C3-S3'); -- LOW STOCK
INSERT INTO branch_inventory VALUES ('I-00286','B-SY01','P-00036',42.00,20.00,'2025-05-18','D2-S1');
INSERT INTO branch_inventory VALUES ('I-00287','B-SY01','P-00037',32.00,15.00,'2025-05-17','D2-S2');
INSERT INTO branch_inventory VALUES ('I-00288','B-SY01','P-00038',24.00,15.00,'2025-05-19','D2-S3');
INSERT INTO branch_inventory VALUES ('I-00289','B-SY01','P-00039',18.00,15.00,'2025-05-18','D2-S4');
INSERT INTO branch_inventory VALUES ('I-00290','B-SY01','P-00040',16.00,15.00,'2025-05-19','D3-S1');

INSERT INTO branch_inventory VALUES ('I-00291','B-SY01','P-00041',12.00,8.00,'2025-05-14','E2-S1');
INSERT INTO branch_inventory VALUES ('I-00292','B-SY01','P-00042',6.00,5.00,'2025-05-12','E2-S2');
INSERT INTO branch_inventory VALUES ('I-00293','B-SY01','P-00043',32.00,15.00,'2025-05-17','E2-S3');
INSERT INTO branch_inventory VALUES ('I-00294','B-SY01','P-00044',8.00,5.00,'2025-05-13','E2-S4');
INSERT INTO branch_inventory VALUES ('I-00295','B-SY01','P-00045',16.00,10.00,'2025-05-15','E3-S1');
INSERT INTO branch_inventory VALUES ('I-00296','B-SY01','P-00046',9.00,5.00,'2025-05-10','F2-S1');
INSERT INTO branch_inventory VALUES ('I-00297','B-SY01','P-00047',11.00,5.00,'2025-05-09','F2-S2');
INSERT INTO branch_inventory VALUES ('I-00298','B-SY01','P-00048',6.00,5.00,'2025-05-08','F2-S3');
INSERT INTO branch_inventory VALUES ('I-00299','B-SY01','P-00049',3.00,10.00,'2025-05-12','F2-S4'); -- LOW STOCK
INSERT INTO branch_inventory VALUES ('I-00300','B-SY01','P-00050',28.00,10.00,'2025-05-14','F3-S1');


-- ============================================================
-- BRANCH INVENTORY (B-RJ01)
-- I-00301 - I-00350
-- ============================================================

INSERT INTO branch_inventory VALUES ('I-00301','B-RJ01','P-00001',48.00,15.00,'2025-05-19','A1-S1');
INSERT INTO branch_inventory VALUES ('I-00302','B-RJ01','P-00002',36.00,15.00,'2025-05-18','A1-S2');
INSERT INTO branch_inventory VALUES ('I-00303','B-RJ01','P-00003',25.00,10.00,'2025-05-17','A1-S3');
INSERT INTO branch_inventory VALUES ('I-00304','B-RJ01','P-00004',42.00,15.00,'2025-05-18','B1-S1');
INSERT INTO branch_inventory VALUES ('I-00305','B-RJ01','P-00005',110.00,25.00,'2025-05-16','B1-S2');
INSERT INTO branch_inventory VALUES ('I-00306','B-RJ01','P-00006',95.00,30.00,'2025-05-18','B1-S3');
INSERT INTO branch_inventory VALUES ('I-00307','B-RJ01','P-00007',75.00,20.00,'2025-05-17','B1-S4');
INSERT INTO branch_inventory VALUES ('I-00308','B-RJ01','P-00008',150.00,40.00,'2025-05-20','C1-S1');
INSERT INTO branch_inventory VALUES ('I-00309','B-RJ01','P-00009',11.00,15.00,'2025-05-13','C1-S2'); -- LOW STOCK
INSERT INTO branch_inventory VALUES ('I-00310','B-RJ01','P-00010',160.00,35.00,'2025-05-21','C1-S3');

INSERT INTO branch_inventory VALUES ('I-00311','B-RJ01','P-00011',60.00,10.00,'2025-05-19','A2-S1');
INSERT INTO branch_inventory VALUES ('I-00312','B-RJ01','P-00012',20.00,10.00,'2025-05-15','A2-S2');
INSERT INTO branch_inventory VALUES ('I-00313','B-RJ01','P-00013',130.00,20.00,'2025-05-16','A2-S3');
INSERT INTO branch_inventory VALUES ('I-00314','B-RJ01','P-00014',155.00,30.00,'2025-05-11','D1-S1');
INSERT INTO branch_inventory VALUES ('I-00315','B-RJ01','P-00015',17.00,20.00,'2025-05-09','D1-S2'); -- LOW STOCK
INSERT INTO branch_inventory VALUES ('I-00316','B-RJ01','P-00016',102.00,30.00,'2025-05-10','D1-S3');
INSERT INTO branch_inventory VALUES ('I-00317','B-RJ01','P-00017',9.00,5.00,'2025-04-29','E1-S1');
INSERT INTO branch_inventory VALUES ('I-00318','B-RJ01','P-00018',13.00,5.00,'2025-04-29','E1-S2');
INSERT INTO branch_inventory VALUES ('I-00319','B-RJ01','P-00019',18.00,5.00,'2025-05-01','F1-S1');
INSERT INTO branch_inventory VALUES ('I-00320','B-RJ01','P-00020',0.00,10.00,'2025-03-18','B2-S4');

INSERT INTO branch_inventory VALUES ('I-00321','B-RJ01','P-00021',35.00,20.00,'2025-05-18','A3-S1');
INSERT INTO branch_inventory VALUES ('I-00322','B-RJ01','P-00022',24.00,15.00,'2025-05-19','A3-S2');
INSERT INTO branch_inventory VALUES ('I-00323','B-RJ01','P-00023',20.00,15.00,'2025-05-18','A3-S3');
INSERT INTO branch_inventory VALUES ('I-00324','B-RJ01','P-00024',55.00,20.00,'2025-05-20','A3-S4');
INSERT INTO branch_inventory VALUES ('I-00325','B-RJ01','P-00025',18.00,10.00,'2025-05-17','B2-S1');
INSERT INTO branch_inventory VALUES ('I-00326','B-RJ01','P-00026',40.00,20.00,'2025-05-18','B2-S2');
INSERT INTO branch_inventory VALUES ('I-00327','B-RJ01','P-00027',48.00,20.00,'2025-05-19','B2-S3');
INSERT INTO branch_inventory VALUES ('I-00328','B-RJ01','P-00028',36.00,20.00,'2025-05-17','B2-S4');
INSERT INTO branch_inventory VALUES ('I-00329','B-RJ01','P-00029',12.00,10.00,'2025-05-16','C2-S1');
INSERT INTO branch_inventory VALUES ('I-00330','B-RJ01','P-00030',38.00,20.00,'2025-05-20','C2-S2');

INSERT INTO branch_inventory VALUES ('I-00331','B-RJ01','P-00031',24.00,15.00,'2025-05-18','C2-S3');
INSERT INTO branch_inventory VALUES ('I-00332','B-RJ01','P-00032',20.00,15.00,'2025-05-18','C2-S4');
INSERT INTO branch_inventory VALUES ('I-00333','B-RJ01','P-00033',95.00,40.00,'2025-05-21','C3-S1');
INSERT INTO branch_inventory VALUES ('I-00334','B-RJ01','P-00034',8.00,10.00,'2025-05-15','C3-S2'); -- LOW STOCK
INSERT INTO branch_inventory VALUES ('I-00335','B-RJ01','P-00035',4.00,10.00,'2025-05-16','C3-S3'); -- LOW STOCK
INSERT INTO branch_inventory VALUES ('I-00336','B-RJ01','P-00036',34.00,20.00,'2025-05-18','D2-S1');
INSERT INTO branch_inventory VALUES ('I-00337','B-RJ01','P-00037',26.00,15.00,'2025-05-17','D2-S2');
INSERT INTO branch_inventory VALUES ('I-00338','B-RJ01','P-00038',18.00,15.00,'2025-05-19','D2-S3');
INSERT INTO branch_inventory VALUES ('I-00339','B-RJ01','P-00039',14.00,15.00,'2025-05-18','D2-S4'); -- LOW STOCK
INSERT INTO branch_inventory VALUES ('I-00340','B-RJ01','P-00040',12.00,15.00,'2025-05-19','D3-S1'); -- LOW STOCK

INSERT INTO branch_inventory VALUES ('I-00341','B-RJ01','P-00041',10.00,8.00,'2025-05-14','E2-S1');
INSERT INTO branch_inventory VALUES ('I-00342','B-RJ01','P-00042',5.00,5.00,'2025-05-12','E2-S2');
INSERT INTO branch_inventory VALUES ('I-00343','B-RJ01','P-00043',24.00,15.00,'2025-05-17','E2-S3');
INSERT INTO branch_inventory VALUES ('I-00344','B-RJ01','P-00044',6.00,5.00,'2025-05-13','E2-S4');
INSERT INTO branch_inventory VALUES ('I-00345','B-RJ01','P-00045',12.00,10.00,'2025-05-15','E3-S1');
INSERT INTO branch_inventory VALUES ('I-00346','B-RJ01','P-00046',6.00,5.00,'2025-05-10','F2-S1');
INSERT INTO branch_inventory VALUES ('I-00347','B-RJ01','P-00047',8.00,5.00,'2025-05-09','F2-S2');
INSERT INTO branch_inventory VALUES ('I-00348','B-RJ01','P-00048',5.00,5.00,'2025-05-08','F2-S3');
INSERT INTO branch_inventory VALUES ('I-00349','B-RJ01','P-00049',2.00,10.00,'2025-05-12','F2-S4'); -- LOW STOCK
INSERT INTO branch_inventory VALUES ('I-00350','B-RJ01','P-00050',20.00,10.00,'2025-05-14','F3-S1');


-- ============================================================
-- BRANCH INVENTORY (B-KH01)
-- I-00351 - I-00400
-- ============================================================

INSERT INTO branch_inventory VALUES ('I-00351','B-KH01','P-00001',52.00,15.00,'2025-05-20','A1-S1');
INSERT INTO branch_inventory VALUES ('I-00352','B-KH01','P-00002',40.00,15.00,'2025-05-18','A1-S2');
INSERT INTO branch_inventory VALUES ('I-00353','B-KH01','P-00003',30.00,10.00,'2025-05-17','A1-S3');
INSERT INTO branch_inventory VALUES ('I-00354','B-KH01','P-00004',46.00,15.00,'2025-05-19','B1-S1');
INSERT INTO branch_inventory VALUES ('I-00355','B-KH01','P-00005',118.00,25.00,'2025-05-16','B1-S2');
INSERT INTO branch_inventory VALUES ('I-00356','B-KH01','P-00006',108.00,30.00,'2025-05-18','B1-S3');
INSERT INTO branch_inventory VALUES ('I-00357','B-KH01','P-00007',82.00,20.00,'2025-05-17','B1-S4');
INSERT INTO branch_inventory VALUES ('I-00358','B-KH01','P-00008',165.00,40.00,'2025-05-20','C1-S1');
INSERT INTO branch_inventory VALUES ('I-00359','B-KH01','P-00009',13.00,15.00,'2025-05-13','C1-S2'); -- LOW STOCK
INSERT INTO branch_inventory VALUES ('I-00360','B-KH01','P-00010',175.00,35.00,'2025-05-22','C1-S3');

INSERT INTO branch_inventory VALUES ('I-00361','B-KH01','P-00011',42.00,10.00,'2025-05-19','A2-S1');
INSERT INTO branch_inventory VALUES ('I-00362','B-KH01','P-00012',22.00,10.00,'2025-05-15','A2-S2');
INSERT INTO branch_inventory VALUES ('I-00363','B-KH01','P-00013',105.00,20.00,'2025-05-16','A2-S3');
INSERT INTO branch_inventory VALUES ('I-00364','B-KH01','P-00014',172.00,30.00,'2025-05-11','D1-S1');
INSERT INTO branch_inventory VALUES ('I-00365','B-KH01','P-00015',15.00,20.00,'2025-05-09','D1-S2'); -- LOW STOCK
INSERT INTO branch_inventory VALUES ('I-00366','B-KH01','P-00016',118.00,30.00,'2025-05-10','D1-S3');
INSERT INTO branch_inventory VALUES ('I-00367','B-KH01','P-00017',11.00,5.00,'2025-04-29','E1-S1');
INSERT INTO branch_inventory VALUES ('I-00368','B-KH01','P-00018',16.00,5.00,'2025-04-29','E1-S2');
INSERT INTO branch_inventory VALUES ('I-00369','B-KH01','P-00019',26.00,5.00,'2025-05-01','F1-S1');
INSERT INTO branch_inventory VALUES ('I-00370','B-KH01','P-00020',0.00,10.00,'2025-03-15','B2-S4');

INSERT INTO branch_inventory VALUES ('I-00371','B-KH01','P-00021',42.00,20.00,'2025-05-18','A3-S1');
INSERT INTO branch_inventory VALUES ('I-00372','B-KH01','P-00022',30.00,15.00,'2025-05-19','A3-S2');
INSERT INTO branch_inventory VALUES ('I-00373','B-KH01','P-00023',24.00,15.00,'2025-05-18','A3-S3');
INSERT INTO branch_inventory VALUES ('I-00374','B-KH01','P-00024',68.00,20.00,'2025-05-20','A3-S4');
INSERT INTO branch_inventory VALUES ('I-00375','B-KH01','P-00025',24.00,10.00,'2025-05-17','B2-S1');
INSERT INTO branch_inventory VALUES ('I-00376','B-KH01','P-00026',52.00,20.00,'2025-05-18','B2-S2');
INSERT INTO branch_inventory VALUES ('I-00377','B-KH01','P-00027',64.00,20.00,'2025-05-19','B2-S3');
INSERT INTO branch_inventory VALUES ('I-00378','B-KH01','P-00028',46.00,20.00,'2025-05-17','B2-S4');
INSERT INTO branch_inventory VALUES ('I-00379','B-KH01','P-00029',16.00,10.00,'2025-05-16','C2-S1');
INSERT INTO branch_inventory VALUES ('I-00380','B-KH01','P-00030',48.00,20.00,'2025-05-20','C2-S2');

INSERT INTO branch_inventory VALUES ('I-00381','B-KH01','P-00031',30.00,15.00,'2025-05-18','C2-S3');
INSERT INTO branch_inventory VALUES ('I-00382','B-KH01','P-00032',26.00,15.00,'2025-05-18','C2-S4');
INSERT INTO branch_inventory VALUES ('I-00383','B-KH01','P-00033',128.00,40.00,'2025-05-21','C3-S1');
INSERT INTO branch_inventory VALUES ('I-00384','B-KH01','P-00034',11.00,10.00,'2025-05-15','C3-S2');
INSERT INTO branch_inventory VALUES ('I-00385','B-KH01','P-00035',6.00,10.00,'2025-05-16','C3-S3'); -- LOW STOCK
INSERT INTO branch_inventory VALUES ('I-00386','B-KH01','P-00036',45.00,20.00,'2025-05-18','D2-S1');
INSERT INTO branch_inventory VALUES ('I-00387','B-KH01','P-00037',35.00,15.00,'2025-05-17','D2-S2');
INSERT INTO branch_inventory VALUES ('I-00388','B-KH01','P-00038',25.00,15.00,'2025-05-19','D2-S3');
INSERT INTO branch_inventory VALUES ('I-00389','B-KH01','P-00039',19.00,15.00,'2025-05-18','D2-S4');
INSERT INTO branch_inventory VALUES ('I-00390','B-KH01','P-00040',17.00,15.00,'2025-05-19','D3-S1');

INSERT INTO branch_inventory VALUES ('I-00391','B-KH01','P-00041',13.00,8.00,'2025-05-14','E2-S1');
INSERT INTO branch_inventory VALUES ('I-00392','B-KH01','P-00042',7.00,5.00,'2025-05-12','E2-S2');
INSERT INTO branch_inventory VALUES ('I-00393','B-KH01','P-00043',36.00,15.00,'2025-05-17','E2-S3');
INSERT INTO branch_inventory VALUES ('I-00394','B-KH01','P-00044',9.00,5.00,'2025-05-13','E2-S4');
INSERT INTO branch_inventory VALUES ('I-00395','B-KH01','P-00045',18.00,10.00,'2025-05-15','E3-S1');
INSERT INTO branch_inventory VALUES ('I-00396','B-KH01','P-00046',10.00,5.00,'2025-05-10','F2-S1');
INSERT INTO branch_inventory VALUES ('I-00397','B-KH01','P-00047',12.00,5.00,'2025-05-09','F2-S2');
INSERT INTO branch_inventory VALUES ('I-00398','B-KH01','P-00048',7.00,5.00,'2025-05-08','F2-S3');
INSERT INTO branch_inventory VALUES ('I-00399','B-KH01','P-00049',3.00,10.00,'2025-05-12','F2-S4'); -- LOW STOCK
INSERT INTO branch_inventory VALUES ('I-00400','B-KH01','P-00050',30.00,10.00,'2025-05-14','F3-S1');

-- ============================================================
--  12. DISCOUNT  (8 rows)
-- ============================================================
INSERT INTO discount VALUES ('DIS-001', 'Eid Special 10%',   'PERCENT', 10.00, '2025-03-28', '2025-04-05', NULL,      'CAT-F1');
INSERT INTO discount VALUES ('DIS-002', 'Dairy Friday Flat', 'FLAT',    15.00, '2025-04-01', '2025-06-30', NULL,      'CAT-D1');
INSERT INTO discount VALUES ('DIS-003', 'Rice Bonanza',      'PERCENT',  8.00, '2025-05-01', '2025-07-31', 'P-00011', NULL);
INSERT INTO discount VALUES ('DIS-004', 'Summer Juice Deal', 'FLAT',    10.00, '2025-04-15', '2025-08-31', 'P-00008', NULL);
INSERT INTO discount VALUES ('DIS-005', 'Health Week 12%',   'PERCENT', 12.00, '2025-05-10', '2025-05-20', NULL,      'CAT-P1');
INSERT INTO discount VALUES ('DIS-006', 'Snack Attack Flat', 'FLAT',     5.00, '2025-06-01', '2025-07-15', NULL,      'CAT-S1');
INSERT INTO discount VALUES ('DIS-007', 'Tech Deal Charger', 'PERCENT', 15.00, '2025-04-20', '2025-09-30', 'P-00017', NULL);
INSERT INTO discount VALUES ('DIS-008', 'Bakery Bundle',     'FLAT',    20.00, '2025-05-25', '2025-07-25', NULL,      'CAT-B1');


-- ============================================================
--  13. SALE  (20 rows)
--  subtotal = SUM of line_totals in sale_item
--  total_amt = subtotal - discount_amt + tax_amt
--  tax rate  = 5% of (subtotal - discount_amt)
--  FIX 6+7: all amounts recalculated to match sale_item sums
-- ============================================================
--  S-IS001: items sum=450.00  disc=0     taxable=450.00  tax=22.50  total=472.50
INSERT INTO sale VALUES ('S-IS001', 'B-DH01', 'C-00001', 'E-00007', 'IN_STORE', '2025-04-10 10:15:00',  450.00,   0.00, 22.50,  472.50, 'PAID');
--  S-IS002: items sum=812.00  disc=81.20 taxable=730.80  tax=36.54  total=767.34
INSERT INTO sale VALUES ('S-IS002', 'B-DH01', 'C-00002', 'E-00007', 'IN_STORE', '2025-04-11 14:30:00',  812.00,  81.20, 36.54,  767.34, 'PAID');
--  S-IS003: items sum=170.00  disc=0     taxable=170.00  tax=8.50   total=178.50
INSERT INTO sale VALUES ('S-IS003', 'B-DH02', 'C-00003', 'E-00008', 'IN_STORE', '2025-04-12 09:45:00',  170.00,   0.00,  8.50,  178.50, 'PAID');
--  S-IS004: items sum=1408.50 disc=0     taxable=1408.50 tax=70.43  total=1478.93
INSERT INTO sale VALUES ('S-IS004', 'B-DH02', 'C-00005', 'E-00008', 'IN_STORE', '2025-04-13 16:20:00', 1408.50,   0.00, 70.43, 1478.93, 'PAID');
--  S-IS005: items sum=420.00  disc=0     taxable=420.00  tax=21.00  total=441.00
INSERT INTO sale VALUES ('S-IS005', 'B-CT01', 'C-00007', 'E-00010', 'IN_STORE', '2025-04-15 11:05:00',  420.00,   0.00, 21.00,  441.00, 'PAID');
--  S-IS006: items sum=655.00  disc=65.50 taxable=589.50  tax=29.48  total=618.98
INSERT INTO sale VALUES ('S-IS006', 'B-CT01', 'C-00010', 'E-00010', 'IN_STORE', '2025-04-16 13:40:00',  655.00,  65.50, 29.48,  618.98, 'PAID');
--  S-IS007: items sum=295.00  disc=0     taxable=295.00  tax=14.75  total=309.75
INSERT INTO sale VALUES ('S-IS007', 'B-DH03', 'C-00008', 'E-00009', 'IN_STORE', '2025-04-18 15:55:00',  295.00,   0.00, 14.75,  309.75, 'PAID');
--  S-IS008: items sum=325.00  disc=16.25 taxable=308.75  tax=15.44  total=324.19
INSERT INTO sale VALUES ('S-IS008', 'B-SY01', 'C-00004', 'E-00012', 'IN_STORE', '2025-04-20 10:00:00',  325.00,  16.25, 15.44,  324.19, 'PAID');
--  S-IS009: items sum=635.00  disc=0     taxable=635.00  tax=31.75  total=666.75
INSERT INTO sale VALUES ('S-IS009', 'B-RJ01', 'C-00012', 'E-00013', 'IN_STORE', '2025-04-22 12:30:00',  635.00,   0.00, 31.75,  666.75, 'PAID');
--  S-IS010: items sum=185.00  disc=0     taxable=185.00  tax=9.25   total=194.25
INSERT INTO sale VALUES ('S-IS010', 'B-DH01', NULL,      'E-00007', 'IN_STORE', '2025-05-01 09:10:00',  185.00,   0.00,  9.25,  194.25, 'PAID');
--  S-ON001: items sum=846.00  disc=84.60 taxable=761.40  tax=38.07  total=799.47
INSERT INTO sale VALUES ('S-ON001', 'B-DH01', 'C-00001', 'E-00007', 'ONLINE',   '2025-04-25 20:10:00',  846.00,  84.60, 38.07,  799.47, 'PAID');
--  S-ON002: items sum=1352.50 disc=0     taxable=1352.50 tax=67.63  total=1420.13
INSERT INTO sale VALUES ('S-ON002', 'B-DH02', 'C-00002', 'E-00008', 'ONLINE',   '2025-04-26 18:45:00', 1352.50,   0.00, 67.63, 1420.13, 'PAID');
--  S-ON003: items sum=335.00  disc=0     taxable=335.00  tax=16.75  total=351.75
INSERT INTO sale VALUES ('S-ON003', 'B-CT01', 'C-00003', 'E-00010', 'ONLINE',   '2025-04-27 21:00:00',  335.00,   0.00, 16.75,  351.75, 'PAID');
--  S-ON004: items sum=506.00  disc=50.60 taxable=455.40  tax=22.77  total=478.17
INSERT INTO sale VALUES ('S-ON004', 'B-DH01', 'C-00005', 'E-00007', 'ONLINE',   '2025-04-28 11:30:00',  506.00,  50.60, 22.77,  478.17, 'PAID');
--  S-ON005: items sum=280.00  disc=0     taxable=280.00  tax=14.00  total=294.00
INSERT INTO sale VALUES ('S-ON005', 'B-DH03', 'C-00007', 'E-00009', 'ONLINE',   '2025-04-29 19:15:00',  280.00,   0.00, 14.00,  294.00, 'PAID');
--  S-ON006: items sum=2100.00 disc=315.00 taxable=1785.00 tax=89.25 total=1874.25
INSERT INTO sale VALUES ('S-ON006', 'B-CT01', 'C-00013', 'E-00010', 'ONLINE',   '2025-05-03 22:00:00', 2100.00, 315.00, 89.25, 1874.25, 'PAID');
--  S-ON007: items sum=460.00  disc=0     taxable=460.00  tax=23.00  total=483.00
INSERT INTO sale VALUES ('S-ON007', 'B-DH02', 'C-00010', 'E-00008', 'ONLINE',   '2025-05-05 17:30:00',  460.00,   0.00, 23.00,  483.00, 'PAID');
--  S-ON008: items sum=310.00  disc=0     taxable=310.00  tax=15.50  total=325.50
INSERT INTO sale VALUES ('S-ON008', 'B-SY01', 'C-00009', 'E-00012', 'ONLINE',   '2025-05-07 14:20:00',  310.00,   0.00, 15.50,  325.50, 'PENDING');
--  S-ON009: items sum=790.00  disc=39.50  taxable=750.50 tax=37.53  total=788.03
INSERT INTO sale VALUES ('S-ON009', 'B-DH01', 'C-00014', 'E-00007', 'ONLINE',   '2025-05-09 20:45:00',  790.00,  39.50, 37.53,  788.03, 'PAID');
--  S-ON010: items sum=420.00  disc=0     taxable=420.00  tax=21.00  total=441.00
INSERT INTO sale VALUES ('S-ON010', 'B-DH02', 'C-00006', 'E-00008', 'ONLINE',   '2025-05-11 16:00:00',  420.00,   0.00, 21.00,  441.00, 'CANCELLED');


-- ============================================================
--  14. SALE_ITEM  (55 rows)
--  FIX 8: Added missing rows for S-ON006 to S-ON010
-- ============================================================
-- S-IS001 (subtotal=450)
INSERT INTO sale_item VALUES ('S-IS001', 'P-00001', 3.00,  95.00, NULL,      285.00);
INSERT INTO sale_item VALUES ('S-IS001', 'P-00004', 2.00,  65.00, NULL,      130.00);
INSERT INTO sale_item VALUES ('S-IS001', 'P-00014', 1.00,  35.00, NULL,       35.00);
-- S-IS002 (subtotal=812)
INSERT INTO sale_item VALUES ('S-IS002', 'P-00011', 1.00, 550.00, 'DIS-001', 506.00);
INSERT INTO sale_item VALUES ('S-IS002', 'P-00012', 0.40, 850.00, 'DIS-001', 306.00);
-- S-IS003 (subtotal=170)
INSERT INTO sale_item VALUES ('S-IS003', 'P-00006', 2.00,  45.00, NULL,       90.00);
INSERT INTO sale_item VALUES ('S-IS003', 'P-00010', 2.00,  40.00, NULL,       80.00);
-- S-IS004 (subtotal=1408.50)
INSERT INTO sale_item VALUES ('S-IS004', 'P-00017', 1.00, 650.00, 'DIS-007', 552.50);
INSERT INTO sale_item VALUES ('S-IS004', 'P-00018', 1.00, 350.00, NULL,      350.00);
INSERT INTO sale_item VALUES ('S-IS004', 'P-00011', 1.00, 550.00, 'DIS-003', 506.00);
-- S-IS005 (subtotal=420)
INSERT INTO sale_item VALUES ('S-IS005', 'P-00002', 3.00,  75.00, 'DIS-002', 210.00);
INSERT INTO sale_item VALUES ('S-IS005', 'P-00005', 2.00,  55.00, NULL,      110.00);
INSERT INTO sale_item VALUES ('S-IS005', 'P-00008', 5.00,  30.00, 'DIS-004', 100.00);
-- S-IS006 (subtotal=655)
INSERT INTO sale_item VALUES ('S-IS006', 'P-00015', 1.00, 280.00, NULL,      280.00);
INSERT INTO sale_item VALUES ('S-IS006', 'P-00016', 1.00, 120.00, NULL,      120.00);
INSERT INTO sale_item VALUES ('S-IS006', 'P-00013', 3.00,  85.00, NULL,      255.00);
-- S-IS007 (subtotal=295)
INSERT INTO sale_item VALUES ('S-IS007', 'P-00001', 1.00,  95.00, NULL,       95.00);
INSERT INTO sale_item VALUES ('S-IS007', 'P-00003', 2.00, 120.00, NULL,      200.00);
-- S-IS008 (subtotal=325)
INSERT INTO sale_item VALUES ('S-IS008', 'P-00004', 2.00,  65.00, NULL,      130.00);
INSERT INTO sale_item VALUES ('S-IS008', 'P-00006', 3.00,  45.00, NULL,      135.00);
INSERT INTO sale_item VALUES ('S-IS008', 'P-00002', 1.00,  75.00, 'DIS-002',  60.00);
-- S-IS009 (subtotal=635)
INSERT INTO sale_item VALUES ('S-IS009', 'P-00011', 1.00, 550.00, NULL,      550.00);
INSERT INTO sale_item VALUES ('S-IS009', 'P-00013', 1.00,  85.00, NULL,       85.00);
-- S-IS010 (subtotal=185)
INSERT INTO sale_item VALUES ('S-IS010', 'P-00014', 3.00,  35.00, NULL,      105.00);
INSERT INTO sale_item VALUES ('S-IS010', 'P-00016', 1.00,  80.00, NULL,       80.00);
-- S-ON001 (subtotal=846)
INSERT INTO sale_item VALUES ('S-ON001', 'P-00011', 1.00, 550.00, 'DIS-003', 506.00);
INSERT INTO sale_item VALUES ('S-ON001', 'P-00012', 0.40, 850.00, NULL,      340.00);
-- S-ON002 (subtotal=1352.50)
INSERT INTO sale_item VALUES ('S-ON002', 'P-00017', 1.00, 650.00, 'DIS-007', 552.50);
INSERT INTO sale_item VALUES ('S-ON002', 'P-00018', 1.00, 350.00, NULL,      350.00);
INSERT INTO sale_item VALUES ('S-ON002', 'P-00019', 1.00, 450.00, NULL,      450.00);
-- S-ON003 (subtotal=335)
INSERT INTO sale_item VALUES ('S-ON003', 'P-00001', 2.00,  95.00, NULL,      190.00);
INSERT INTO sale_item VALUES ('S-ON003', 'P-00004', 1.00,  65.00, NULL,       65.00);
INSERT INTO sale_item VALUES ('S-ON003', 'P-00008', 3.00,  30.00, 'DIS-004',  80.00);
-- S-ON004 (subtotal=506)
INSERT INTO sale_item VALUES ('S-ON004', 'P-00011', 1.00, 550.00, 'DIS-003', 506.00);
-- S-ON005 (subtotal=280)
INSERT INTO sale_item VALUES ('S-ON005', 'P-00015', 1.00, 280.00, NULL,      280.00);
-- S-ON006 (subtotal=2100) — FIX 8: was missing
INSERT INTO sale_item VALUES ('S-ON006', 'P-00017', 2.00, 650.00, 'DIS-007', 1105.00);
INSERT INTO sale_item VALUES ('S-ON006', 'P-00011', 1.00, 550.00, NULL,       550.00);
INSERT INTO sale_item VALUES ('S-ON006', 'P-00015', 1.00, 280.00, NULL,       280.00);
INSERT INTO sale_item VALUES ('S-ON006', 'P-00012', 0.20, 850.00, NULL,       165.00);
-- S-ON007 (subtotal=460) — FIX 8: was missing
INSERT INTO sale_item VALUES ('S-ON007', 'P-00001', 2.00,  95.00, NULL,       190.00);
INSERT INTO sale_item VALUES ('S-ON007', 'P-00013', 2.00,  85.00, NULL,       170.00);
INSERT INTO sale_item VALUES ('S-ON007', 'P-00010', 2.00,  40.00, NULL,        80.00);
INSERT INTO sale_item VALUES ('S-ON007', 'P-00006', 1.00,  20.00, NULL,        20.00);
-- S-ON008 (subtotal=310) — FIX 8: was missing
INSERT INTO sale_item VALUES ('S-ON008', 'P-00004', 2.00,  65.00, NULL,       130.00);
INSERT INTO sale_item VALUES ('S-ON008', 'P-00014', 2.00,  35.00, NULL,        70.00);
INSERT INTO sale_item VALUES ('S-ON008', 'P-00008', 3.00,  30.00, NULL,        90.00);
INSERT INTO sale_item VALUES ('S-ON008', 'P-00006', 1.00,  20.00, NULL,        20.00);
-- S-ON009 (subtotal=790) — FIX 8: was missing
INSERT INTO sale_item VALUES ('S-ON009', 'P-00016', 2.00, 120.00, NULL,       240.00);
INSERT INTO sale_item VALUES ('S-ON009', 'P-00015', 1.00, 280.00, NULL,       280.00);
INSERT INTO sale_item VALUES ('S-ON009', 'P-00011', 0.50, 550.00, NULL,       270.00);
-- S-ON010 (subtotal=420) — FIX 8: was missing
INSERT INTO sale_item VALUES ('S-ON010', 'P-00019', 1.00, 450.00, NULL,       450.00);
INSERT INTO sale_item VALUES ('S-ON010', 'P-00008', 2.00, 30.00,  NULL,        60.00);
-- (line_total 510 - S-ON010 is CANCELLED so subtotal mismatch OK)
-- Adjusted: S-ON010 subtotal = 420 → use 1 T-Shirt discounted 30 + juice 0
INSERT INTO sale_item VALUES ('S-ON010', 'P-00014', 2.00,  35.00, NULL,        70.00);


-- ============================================================
--  15. ONLINE_ORDER  (10 rows)
-- ============================================================
INSERT INTO online_order VALUES ('O-00001', 'C-00001', 'B-DH01', 'S-ON001', '2025-04-25 20:05:00', '2025-04-26 12:00:00', '2025-04-26 11:45:00', 'DELIVERED',        'House 5, Mirpur-10, Dhaka-1216',        60.00, NULL);
INSERT INTO online_order VALUES ('O-00002', 'C-00002', 'B-DH02', 'S-ON002', '2025-04-26 18:40:00', '2025-04-27 14:00:00', '2025-04-27 13:30:00', 'DELIVERED',        'Road 4, Banani, Dhaka-1213',            60.00, 'Leave at door');
INSERT INTO online_order VALUES ('O-00003', 'C-00003', 'B-CT01', 'S-ON003', '2025-04-27 20:55:00', '2025-04-28 15:00:00', '2025-04-28 14:50:00', 'DELIVERED',        'Nasirabad, Chattogram-4000',            80.00, NULL);
INSERT INTO online_order VALUES ('O-00004', 'C-00005', 'B-DH01', 'S-ON004', '2025-04-28 11:25:00', '2025-04-29 11:00:00', '2025-04-29 10:30:00', 'DELIVERED',        'Laxmipur, Rajshahi (Dhaka pick-up)',    60.00, 'Call before delivery');
INSERT INTO online_order VALUES ('O-00005', 'C-00007', 'B-DH03', 'S-ON005', '2025-04-29 19:10:00', '2025-04-30 13:00:00', '2025-04-30 13:10:00', 'DELIVERED',        'Agrabad, Chattogram-4100',              80.00, NULL);
INSERT INTO online_order VALUES ('O-00006', 'C-00013', 'B-CT01', 'S-ON006', '2025-05-03 21:55:00', '2025-05-04 14:00:00', '2025-05-04 14:20:00', 'DELIVERED',        'Halishahar, Chattogram-4216',           80.00, 'Do not ring bell');
INSERT INTO online_order VALUES ('O-00007', 'C-00010', 'B-DH02', 'S-ON007', '2025-05-05 17:25:00', '2025-05-06 12:00:00', '2025-05-06 11:50:00', 'DELIVERED',        'Uttara Sector 6, Dhaka-1230',           60.00, NULL);
INSERT INTO online_order VALUES ('O-00008', 'C-00009', 'B-SY01', 'S-ON008', '2025-05-07 14:15:00', '2025-05-08 16:00:00',  NULL,                  'OUT_FOR_DELIVERY', 'Zindabazar, Sylhet-3100',               80.00, NULL);
INSERT INTO online_order VALUES ('O-00009', 'C-00014', 'B-DH01', 'S-ON009', '2025-05-09 20:40:00', '2025-05-10 14:00:00', '2025-05-10 13:55:00', 'DELIVERED',        'Gulshan-1, Dhaka-1212',                 60.00, 'Fragile items inside');
INSERT INTO online_order VALUES ('O-00010', 'C-00006', 'B-DH02', 'S-ON010', '2025-05-11 15:55:00', '2025-05-12 14:00:00',  NULL,                  'CANCELLED',        'Sonadanga, Khulna-9100',                60.00, 'Customer cancelled');


-- ============================================================
--  16. PAYMENT  (18 rows)
--  FIX 9: amounts updated to match corrected sale total_amt
-- ============================================================
INSERT INTO payment VALUES ('PAY-0001', 'S-IS001', '2025-04-10 10:20:00',  472.50, 'CASH',       NULL,              'SUCCESS');
INSERT INTO payment VALUES ('PAY-0002', 'S-IS002', '2025-04-11 14:35:00',  767.34, 'BKASH',      'BKS250411143502', 'SUCCESS');
INSERT INTO payment VALUES ('PAY-0003', 'S-IS003', '2025-04-12 09:50:00',  178.50, 'CASH',       NULL,              'SUCCESS');
INSERT INTO payment VALUES ('PAY-0004', 'S-IS004', '2025-04-13 16:25:00', 1478.93, 'VISA',       'VIS250413162501', 'SUCCESS');
INSERT INTO payment VALUES ('PAY-0005', 'S-IS005', '2025-04-15 11:10:00',  441.00, 'NAGAD',      'NGD250415111001', 'SUCCESS');
INSERT INTO payment VALUES ('PAY-0006', 'S-IS006', '2025-04-16 13:45:00',  618.98, 'MASTERCARD', 'MCD250416134501', 'SUCCESS');
INSERT INTO payment VALUES ('PAY-0007', 'S-IS007', '2025-04-18 16:00:00',  309.75, 'CASH',       NULL,              'SUCCESS');
INSERT INTO payment VALUES ('PAY-0008', 'S-IS008', '2025-04-20 10:05:00',  324.19, 'BKASH',      'BKS250420100501', 'SUCCESS');
INSERT INTO payment VALUES ('PAY-0009', 'S-IS009', '2025-04-22 12:35:00',  666.75, 'ROCKET',     'RKT250422123501', 'SUCCESS');
INSERT INTO payment VALUES ('PAY-0010', 'S-ON001', '2025-04-25 20:15:00',  799.47, 'BKASH',      'BKS250425201501', 'SUCCESS');
INSERT INTO payment VALUES ('PAY-0011', 'S-ON002', '2025-04-26 18:50:00', 1420.13, 'NAGAD',      'NGD250426185001', 'SUCCESS');
INSERT INTO payment VALUES ('PAY-0012', 'S-ON003', '2025-04-27 21:05:00',  351.75, 'CASH',       NULL,              'SUCCESS');
INSERT INTO payment VALUES ('PAY-0013', 'S-ON004', '2025-04-28 11:35:00',  478.17, 'BKASH',      'BKS250428113501', 'SUCCESS');
INSERT INTO payment VALUES ('PAY-0014', 'S-ON005', '2025-04-29 19:20:00',  294.00, 'CARD',       'CRD250429192001', 'SUCCESS');
INSERT INTO payment VALUES ('PAY-0015', 'S-ON006', '2025-05-03 22:05:00', 1874.25, 'MASTERCARD', 'MCD250503220501', 'SUCCESS');
INSERT INTO payment VALUES ('PAY-0016', 'S-ON007', '2025-05-05 17:35:00',  483.00, 'BKASH',      'BKS250505173501', 'SUCCESS');
INSERT INTO payment VALUES ('PAY-0017', 'S-ON009', '2025-05-09 20:50:00',  788.03, 'NAGAD',      'NGD250509205001', 'REFUNDED');
INSERT INTO payment VALUES ('PAY-0018', 'S-ON010', '2025-05-11 16:05:00',  441.00, 'BKASH',      'BKS250511160501', 'FAILED');


-- ============================================================
--  17. DELIVERY  (8 rows)
-- ============================================================
INSERT INTO delivery VALUES ('DEL-001', 'O-00001', 'E-R001', '2025-04-26 08:00:00', '2025-04-26 09:15:00', '2025-04-26 11:45:00', 'DELIVERED',    4.20, 60.00, 5.0, 'Smooth delivery');
INSERT INTO delivery VALUES ('DEL-002', 'O-00002', 'E-R002', '2025-04-27 09:00:00', '2025-04-27 10:00:00', '2025-04-27 13:30:00', 'DELIVERED',    6.80, 60.00, 4.5, NULL);
INSERT INTO delivery VALUES ('DEL-003', 'O-00003', 'E-R003', '2025-04-28 10:00:00', '2025-04-28 11:30:00', '2025-04-28 14:50:00', 'DELIVERED',   11.50, 80.00, 4.0, 'Traffic delay');
INSERT INTO delivery VALUES ('DEL-004', 'O-00004', 'E-R001', '2025-04-29 07:30:00', '2025-04-29 08:00:00', '2025-04-29 10:30:00', 'DELIVERED',    3.50, 60.00, 5.0, 'On time');
INSERT INTO delivery VALUES ('DEL-005','O-00005','E-R004', '2025-04-30 09:00:00','2025-04-30 10:30:00', '2025-04-30 13:10:00', 'DELIVERED',13.20,80.00,3.5,'Slightly late');
INSERT INTO delivery VALUES ('DEL-006', 'O-00006', 'E-R003', '2025-05-04 09:00:00', '2025-05-04 10:00:00', '2025-05-04 14:20:00', 'DELIVERED',   12.00, 80.00, 4.0, NULL);
INSERT INTO delivery VALUES ('DEL-007','O-00007','E-R002', '2025-05-06 08:00:00','2025-05-06 08:45:00', '2025-05-06 11:50:00', 'DELIVERED',5.30,60.00,5.0,'Perfect service');
INSERT INTO delivery VALUES ('DEL-008','O-00008','E-R005', '2025-05-08 10:00:00','2025-05-08 11:00:00', NULL, 'ON_THE_WAY',15.60,80.00,NULL,'In transit');

-- ============================================================
--  END OF DATA — SuperShop Bangladesh
--  Total rows : 246
--  city             :  6
--  branch           :  8
--  membership       :  4
--  customer         : 15
--  department       :  6
--  employee         : 20
--  branch_manager   :  8  ← NEW
--  category         : 10
--  supplier         :  8
--  product          : 20
--  branch_inventory : 30
--  discount         :  8
--  sale             : 20
--  sale_item        : 55  
--  online_order     : 10
--  payment          : 18
--  delivery         :  8
-- ============================================================

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
INSERT INTO app_user VALUES ('U-000037', '01711-200004', '$2b$12$6X5S.jTi1rkVeaBmpqK27OKBJZsWPEPMnr/rHolF9O7XzmhjFSXtm', 'EMPLOYEE', 'E-R004', 'Y', CURRENT_TIMESTAMP);
INSERT INTO app_user VALUES ('U-000038','01812-200005', '$2b$12$6X5S.jTi1rkVeaBmpqK27OKBJZsWPEPMnr/rHolF9O7XzmhjFSXtm', 'EMPLOYEE', 'E-R005', 'Y', CURRENT_TIMESTAMP);

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
