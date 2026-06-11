-- ============================================================
--  SUPERSHOP BANGLADESH — Lab Queries
--  Course : CSE-2201  |  University of Dhaka
-- ============================================================


-- ============================================================
--  Q1 – JOIN with ON
--  List all employees along with the branch and city they work in.
-- ============================================================
SELECT  e.emp_id,
        e.emp_name,
        e.position,
        b.branch_id,
        b.branch_name,
        c.city_name
FROM    employee e
        JOIN branch b ON (e.branch_id = b.branch_id)
        JOIN city   c ON (b.city_id   = c.city_id);


-- ============================================================
--  Q2 – JOIN with USING
--  List all products with their category names.
-- ============================================================
SELECT  p.product_id,
        p.product_name,
        p.unit_price,
        c.cat_id,
        c.cat_name
FROM    product p
        JOIN category c USING (cat_id);


-- ============================================================
--  Q3 (A) – CROSS JOIN
--  Show all possible (branch, membership) combinations.
--  (Demonstrates CROSS PRODUCT / CROSS JOIN)
-- ============================================================
SELECT  b.branch_id,
        b.branch_name,
        m.membership_type,
        m.discount_pct
FROM    branch b , membership m
ORDER BY b.branch_id, m.membership_type;

-- ============================================================
--  Q3 (B) – CROSS JOIN
-- While generating every possible pairing of branch names and membership types, 
-- how many total combinations are there?
-- ============================================================
SELECT	count(*)
FROM	branch CROSS JOIN membership;

-- ============================================================
--  Q4 – NATURAL LEFT OUTER JOIN
--  Show all products and the quantity sold.
--  Products never sold should also appear (quantity will be NULL).
-- ============================================================
SELECT  p.product_id,
        p.product_name,
        p.unit_price,
        si.quantity
FROM    product p
        NATURAL LEFT OUTER JOIN sale_item si;


-- ============================================================
--  Q5 – Multiple JOINs with ON
--  For every sale display: Sale ID, Sale Date, Branch Name,
--  Customer Name (NULL if walk-in), Employee Name, Total Amount.
-- ============================================================
SELECT  s.sale_id,
        s.sale_date,
        b.branch_name,
        c.cust_name,          -- NULL for walk-in customers
        e.emp_name,
        s.total_amt
FROM    sale     s
        JOIN      branch   b ON (s.branch_id = b.branch_id)
        LEFT JOIN customer c ON (s.cust_id   = c.cust_id)  
        JOIN      employee e ON (s.emp_id    = e.emp_id);


-- ============================================================
--  Q6 – EXISTS Subquery
--  Find customers who have placed at least one online order.
-- ============================================================
SELECT  *
FROM    customer c
WHERE   EXISTS (
            SELECT  *
            FROM    online_order o
            WHERE   o.cust_id = c.cust_id
        );


-- ============================================================
--  Q7 – NOT EXISTS Subquery
--  Find products that were never sold.
-- ============================================================
SELECT  *
FROM    product p
WHERE   NOT EXISTS (
            SELECT  *
            FROM    sale_item si
            WHERE   si.product_id = p.product_id
        );


-- ============================================================
--  Q8 – ALL Operator
--  Find employees whose salary is greater than ALL delivery riders.
-- ============================================================
SELECT  *
FROM    employee
WHERE   salary > ALL (
            SELECT  salary
            FROM    employee
            WHERE   position = 'DELIVERY_RIDER'
        );


-- ============================================================
--  Q9 – ANY Operator
--  Find products whose price is greater than ANY Bakery product.
-- ============================================================
SELECT  *
FROM    product
WHERE   unit_price > ANY (
            SELECT  unit_price
            FROM    product
                    NATURAL JOIN category
            WHERE   cat_name = 'Bakery'
        );


-- ============================================================
--  Q10 – IN Operator (with UNIQUE demonstration)
--  Find customers who made purchases from Branch B-DH01.
-- ============================================================

-- Version A: using IN 
SELECT  *
FROM    customer
WHERE   cust_id IN (
            SELECT  cust_id
            FROM    sale
            WHERE   branch_id = 'B-DH01'
              AND   cust_id IS NOT NULL       -- exclude walk-in NULL rows
        );

-- Version B: using JOIN
SELECT DISTINCT c.*
FROM    customer c
        JOIN sale s ON (c.cust_id = s.cust_id)
WHERE   s.branch_id = 'B-DH01';


-- ============================================================
--  Q11 – Scalar Subquery in SELECT Clause
--  Show each branch with the total number of employees.
-- ============================================================

SELECT  b.branch_id,
        b.branch_name,
        (
            SELECT  COUNT(*)
            FROM    employee e
            WHERE   e.branch_id = b.branch_id
        ) AS total_employees
FROM    branch b;

-- Alternative: implicit join + GROUP BY
SELECT  b.branch_id,
        b.branch_name,
        COUNT(e.emp_id) AS total_employees
FROM    branch   b
        LEFT JOIN employee e ON (b.branch_id = e.branch_id)  
GROUP BY b.branch_id, b.branch_name;


-- ============================================================
--  Q12 – Subquery in FROM Clause
--  Find branches whose total sales revenue exceeds
--  the average branch revenue.
-- ============================================================

-- FROM version
SELECT  branch_id,
        branch_name
FROM    (
            SELECT  branch_id,
                    SUM(total_amt) AS tot_amt
            FROM    sale
            GROUP BY branch_id
        ) AS tot_rev

        NATURAL JOIN

        (
            SELECT  AVG(t_amt) AS avg_amt
            FROM    (
                        SELECT  SUM(total_amt) AS t_amt
                        FROM    sale
                        GROUP BY branch_id
                    ) AS branch_totals      
        ) AS avg_rev

        NATURAL JOIN branch
WHERE   tot_amt > avg_amt;                  


-- WITH version 
WITH tot_rev AS (
    SELECT  branch_id,
            SUM(total_amt) AS tot_amt
    FROM    sale
    GROUP BY branch_id
),
avg_rev AS (
    SELECT  AVG(tot_amt) AS avg_amt
    FROM    tot_rev
)
SELECT  branch_id,
        branch_name
FROM    tot_rev
        NATURAL JOIN avg_rev
        NATURAL JOIN branch
WHERE   tot_amt > avg_amt;


-- ============================================================
--  Q13 – Correlated Subquery in WHERE Clause
--  Find customers whose loyalty points exceed the average
--  loyalty points of customers in the same membership tier.
-- ============================================================
SELECT  *
FROM    customer c
WHERE   loyalty_points > (
            SELECT  AVG(loyalty_points)
            FROM    customer m
            WHERE   m.membership_type = c.membership_type
        );

-- ============================================================
--  Q14 – GROUP BY and HAVING
--  Calculate total sales revenue for each category and
--  show only categories with revenue above 1000 BDT.
--
--  FIX A: original used sale.total_amt (whole-sale total) grouped
--         by cat_id — this double-counts revenue for multi-category
--         sales. Use sale_item.line_total instead.
--  FIX B: No HAVING clause was present despite the query title.
--         Added a meaningful HAVING filter below.
-- ============================================================
SELECT  c.cat_id,
        c.cat_name,
        SUM(si.line_total)  AS category_revenue,
        COUNT(DISTINCT si.sale_id) AS num_sales
FROM    product  p
        JOIN sale_item si USING (product_id)
        JOIN category  c USING (cat_id)
GROUP BY c.cat_id, c.cat_name
HAVING  SUM(si.line_total) > 1000          
ORDER BY category_revenue DESC;

-- ============================================================
--  Q15 – Multiple Column GROUP BY with ORDER BY
--  For each branch and order type display:
--  number of sales, total revenue, average revenue.
-- ============================================================
SELECT  branch_id,
        order_type,
        COUNT(sale_id)      AS num_sales,
        SUM(total_amt)      AS total_revenue,
        AVG(total_amt)      AS avg_revenue
FROM    sale
GROUP BY branch_id, order_type
ORDER BY branch_id, order_type;           


-- ============================================================
--  Q16 – WITH Clause (Single CTE)
--  Find customers whose total spending exceeds average
--  customer spending.
-- ============================================================
WITH tot_spnd AS (
    SELECT  cust_id,
            SUM(total_amt) AS tot_sum
    FROM    sale
    WHERE   cust_id IS NOT NULL
    GROUP BY cust_id
)
SELECT  c.*,
        ts.tot_sum
FROM    tot_spnd ts
        NATURAL JOIN customer c
WHERE   ts.tot_sum > (
            SELECT  AVG(tot_sum)
            FROM    tot_spnd
        );


-- ============================================================
--  Q17 – Multiple CTEs
--  Find the top-selling product (by sale count) in each branch.
-- ============================================================
WITH selling_cnt AS (
    SELECT  s.branch_id,
            si.product_id,
            COUNT(*) AS times_sold        
    FROM    sale      s
            JOIN sale_item si USING (sale_id)
    GROUP BY s.branch_id, si.product_id
),
max_selling AS (
    SELECT  branch_id,
            MAX(times_sold) AS top_sale
    FROM    selling_cnt
    GROUP BY branch_id
)
SELECT  sc.branch_id,
        sc.product_id,
        p.product_name,
        sc.times_sold AS top_sale
FROM    selling_cnt sc
        JOIN max_selling ms ON (sc.branch_id = ms.branch_id
                            AND sc.times_sold = ms.top_sale)
        JOIN product p      ON (sc.product_id = p.product_id)
ORDER BY sc.branch_id;


-- ============================================================
--  Q18 – String Manipulation Functions
--  Display employee name in uppercase, email username only
--  (part before @), and a formatted employee label.
-- ============================================================
SELECT  UPPER(emp_name)                         AS emp_name_upper,
        SPLIT_PART(email, '@', 1)               AS email_username, 
        LENGTH(emp_name)                        AS name_length,
        emp_id || ' – ' || position             AS formatted_emp_label
FROM    employee;


-- ============================================================
--  Q19 – Set Operations  (UNION / INTERSECT / EXCEPT)
-- ============================================================

-- UNION
-- Customer IDs who made an in-store purchase OR placed an online order.
SELECT  cust_id
FROM    sale
WHERE   order_type = 'IN_STORE'
  AND   cust_id IS NOT NULL
  
UNION

SELECT  cust_id
FROM    online_order;


-- INTERSECT
-- Customers who have BOTH made in-store purchases AND online orders.
SELECT  cust_id
FROM    sale
WHERE   order_type = 'IN_STORE'
  AND   cust_id IS NOT NULL            

INTERSECT

SELECT  cust_id
FROM    online_order;


-- EXCEPT  (MINUS in Oracle)
-- Customers who made in-store purchases but NEVER placed an online order.
SELECT  cust_id
FROM    sale
WHERE   order_type = 'IN_STORE'
  AND   cust_id IS NOT NULL             

EXCEPT

SELECT  cust_id
FROM    online_order;


-- ============================================================
--  Q20 – Aggregate Functions
--  For each branch calculate COUNT, SUM, AVG, MAX, MIN of
--  paid sales revenue.
-- ============================================================
SELECT  b.branch_id,
        b.branch_name,
        COUNT(s.sale_id)    AS total_sales,
        SUM(s.total_amt)    AS total_revenue,
        AVG(s.total_amt)    AS avg_sale_value,
        MAX(s.total_amt)    AS largest_sale,
        MIN(s.total_amt)    AS smallest_sale
FROM    branch b
        NATURAL JOIN sale s
WHERE   s.payment_status = 'PAID'
GROUP BY b.branch_id, b.branch_name
ORDER BY total_revenue DESC;


-- ============================================================
--  END OF QUERIES — SuperShop Bangladesh
-- ============================================================