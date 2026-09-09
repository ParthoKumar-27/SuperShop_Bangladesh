-- ============================================================
--  SuperShop Bangladesh — Convenience VIEWS for Supabase
--  Course : CSE-2201  Database Management System
--  University of Dhaka — Department of CSE
-- ============================================================


-- ============================================================
--  VIEW 1 — Daily branch revenue (paid sales only)
--  Useful for dashboards and the existing
--  templates/admin/sales.html report.
-- ============================================================
CREATE OR REPLACE VIEW v_branch_daily_revenue AS
SELECT  s.branch_id,
        b.branch_name,
        c.city_name,
        DATE_TRUNC('day', s.sale_date) AS sale_day,
        COUNT(s.sale_id)                AS num_sales,
        SUM(s.subtotal)                 AS gross_subtotal,
        SUM(s.discount_amt)             AS total_discount,
        SUM(s.tax_amt)                  AS total_tax,
        SUM(s.total_amt)                AS net_revenue
FROM    sale s
        JOIN branch b ON s.branch_id = b.branch_id
        JOIN city   c ON b.city_id   = c.city_id
WHERE   s.payment_status = 'PAID'
GROUP BY s.branch_id, b.branch_name, c.city_name,
         DATE_TRUNC('day', s.sale_date);


-- ============================================================
--  VIEW 2 — Branch-level rollup (current snapshot)
-- ============================================================
CREATE OR REPLACE VIEW v_branch_summary AS
SELECT  b.branch_id,
        b.branch_name,
        c.city_name,
        b.is_active,
        b.open_time,
        b.close_time,
        COALESCE(SUM(s.total_amt), 0)                                 AS lifetime_revenue,
        COUNT(s.sale_id)                                              AS lifetime_sales,
        COALESCE(AVG(s.total_amt), 0)                                 AS avg_sale_value,
        (SELECT COUNT(*) FROM employee  e WHERE e.branch_id = b.branch_id AND e.is_active = 'Y') AS active_employees,
        (SELECT COUNT(*) FROM online_order o WHERE o.branch_id = b.branch_id)                   AS total_online_orders
FROM    branch  b
        JOIN     city       c ON b.city_id   = c.city_id
        LEFT JOIN sale       s ON b.branch_id = s.branch_id
GROUP BY b.branch_id, b.branch_name, c.city_name,
         b.is_active, b.open_time, b.close_time;


-- ============================================================
--  VIEW 3 — Top-selling products (all branches, lifetime)
-- ============================================================
CREATE OR REPLACE VIEW v_top_selling_products AS
SELECT  p.product_id,
        p.product_name,
        c.cat_name,
        SUM(si.quantity)                AS total_qty_sold,
        SUM(si.line_total)              AS total_revenue,
        COUNT(DISTINCT si.sale_id)      AS times_ordered
FROM    sale_item si
        JOIN product  p ON si.product_id = p.product_id
        JOIN category c ON p.cat_id      = c.cat_id
GROUP BY p.product_id, p.product_name, c.cat_name
ORDER BY total_qty_sold DESC;


-- ============================================================
--  VIEW 4 — Low-stock inventory (branch level)
--  Mirrors the in-app "low stock" badge on
--  templates/employee/branch_manager/inventory.html.
-- ============================================================
CREATE OR REPLACE VIEW v_low_stock AS
SELECT  bi.inv_id,
        b.branch_id,
        b.branch_name,
        bi.product_id,
        p.product_name,
        bi.quantity,
        bi.reorder_level,
        (bi.reorder_level - bi.quantity)  AS units_to_reorder,
        bi.shelf_location,
        bi.last_restocked
FROM    branch_inventory bi
        JOIN branch  b ON bi.branch_id  = b.branch_id
        JOIN product p ON bi.product_id = p.product_id
WHERE   bi.quantity <= bi.reorder_level
  AND   p.is_active  = 'Y'
  AND   b.is_active  = 'Y'
ORDER BY units_to_reorder DESC;

