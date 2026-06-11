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
--  10. PRODUCT  (20 rows)
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
--  11. BRANCH_INVENTORY  (30 rows)
-- ============================================================
INSERT INTO branch_inventory VALUES ('I-00001', 'B-DH01', 'P-00001', 120.00, 20.00, '2025-05-20', 'A1-S1');
INSERT INTO branch_inventory VALUES ('I-00002', 'B-DH01', 'P-00004',  80.00, 15.00, '2025-05-22', 'B2-S3');
INSERT INTO branch_inventory VALUES ('I-00003', 'B-DH01', 'P-00006', 200.00, 30.00, '2025-05-18', 'C3-S2');
INSERT INTO branch_inventory VALUES ('I-00004', 'B-DH01', 'P-00011',  55.00, 10.00, '2025-05-25', 'A2-S1');
INSERT INTO branch_inventory VALUES ('I-00005', 'B-DH01', 'P-00012',  30.00, 10.00, '2025-05-15', 'A2-S2');
INSERT INTO branch_inventory VALUES ('I-00006', 'B-DH01', 'P-00014', 350.00, 50.00, '2025-05-10', 'D1-S1');
INSERT INTO branch_inventory VALUES ('I-00007', 'B-DH02', 'P-00001',  90.00, 20.00, '2025-05-21', 'A1-S1');
INSERT INTO branch_inventory VALUES ('I-00008', 'B-DH02', 'P-00002',  60.00, 15.00, '2025-05-23', 'A1-S2');
INSERT INTO branch_inventory VALUES ('I-00009', 'B-DH02', 'P-00008', 500.00, 50.00, '2025-05-20', 'B1-S4');
INSERT INTO branch_inventory VALUES ('I-00010', 'B-DH02', 'P-00017',  25.00,  5.00, '2025-04-30', 'E1-S1');
INSERT INTO branch_inventory VALUES ('I-00011', 'B-DH02', 'P-00018',  40.00,  5.00, '2025-04-30', 'E1-S2');
INSERT INTO branch_inventory VALUES ('I-00012', 'B-DH02', 'P-00013', 150.00, 20.00, '2025-05-19', 'A3-S1');
INSERT INTO branch_inventory VALUES ('I-00013', 'B-DH03', 'P-00003',  45.00, 10.00, '2025-05-12', 'A1-S3');
INSERT INTO branch_inventory VALUES ('I-00014', 'B-DH03', 'P-00005', 180.00, 25.00, '2025-05-17', 'B2-S1');
INSERT INTO branch_inventory VALUES ('I-00015', 'B-DH03', 'P-00009',  12.00, 15.00, '2025-04-25', 'B3-S2'); -- LOW STOCK
INSERT INTO branch_inventory VALUES ('I-00016', 'B-DH03', 'P-00016', 220.00, 30.00, '2025-05-08', 'D2-S3');
INSERT INTO branch_inventory VALUES ('I-00017', 'B-CT01', 'P-00001',  75.00, 20.00, '2025-05-20', 'A1-S1');
INSERT INTO branch_inventory VALUES ('I-00018', 'B-CT01', 'P-00006', 160.00, 30.00, '2025-05-19', 'C2-S1');
INSERT INTO branch_inventory VALUES ('I-00019', 'B-CT01', 'P-00007', 110.00, 20.00, '2025-05-14', 'C2-S2');
INSERT INTO branch_inventory VALUES ('I-00020', 'B-CT01', 'P-00011',  40.00, 10.00, '2025-05-22', 'A2-S1');
INSERT INTO branch_inventory VALUES ('I-00021', 'B-CT01', 'P-00015',  18.00, 20.00, '2025-04-20', 'D1-S4'); -- LOW STOCK
INSERT INTO branch_inventory VALUES ('I-00022', 'B-CT02', 'P-00002',  50.00, 15.00, '2025-05-18', 'A1-S2');
INSERT INTO branch_inventory VALUES ('I-00023', 'B-CT02', 'P-00010', 300.00, 40.00, '2025-05-23', 'B1-S3');
INSERT INTO branch_inventory VALUES ('I-00024', 'B-CT02', 'P-00012',  25.00, 10.00, '2025-05-11', 'A2-S2');
INSERT INTO branch_inventory VALUES ('I-00025', 'B-CT02', 'P-00019',  35.00,  5.00, '2025-04-28', 'F1-S1');
INSERT INTO branch_inventory VALUES ('I-00026', 'B-SY01', 'P-00001',  55.00, 15.00, '2025-05-20', 'A1-S1');
INSERT INTO branch_inventory VALUES ('I-00027', 'B-SY01', 'P-00004',   8.00, 10.00, '2025-04-15', 'B1-S2'); -- LOW STOCK
INSERT INTO branch_inventory VALUES ('I-00028', 'B-SY01', 'P-00014', 190.00, 30.00, '2025-05-05', 'D1-S1');
INSERT INTO branch_inventory VALUES ('I-00029', 'B-RJ01', 'P-00011',  60.00, 10.00, '2025-05-19', 'A1-S1');
INSERT INTO branch_inventory VALUES ('I-00030', 'B-RJ01', 'P-00013', 130.00, 20.00, '2025-05-16', 'A3-S2');


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
INSERT INTO delivery VALUES ('DEL-005', 'O-00005', 'E-R002', '2025-04-30 09:00:00', '2025-04-30 10:30:00', '2025-04-30 13:10:00', 'DELIVERED',   13.20, 80.00, 3.5, 'Slightly late');
INSERT INTO delivery VALUES ('DEL-006', 'O-00006', 'E-R003', '2025-05-04 09:00:00', '2025-05-04 10:00:00', '2025-05-04 14:20:00', 'DELIVERED',   12.00, 80.00, 4.0, NULL);
INSERT INTO delivery VALUES ('DEL-007', 'O-00007', 'E-R001', '2025-05-06 08:00:00', '2025-05-06 08:45:00', '2025-05-06 11:50:00', 'DELIVERED',    5.30, 60.00, 5.0, 'Perfect service');
INSERT INTO delivery VALUES ('DEL-008', 'O-00008', 'E-R002', '2025-05-08 10:00:00', '2025-05-08 11:00:00',  NULL,                  'ON_THE_WAY',  15.60, 80.00, NULL, 'In transit');


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

