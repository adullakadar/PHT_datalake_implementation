-- PHT 05c - OLAP reports (run: beeline ... -f 05c_olap_queries.hql --outputformat=table)
USE pht_dw;

-- Q1. ROLLUP - revenue by branch and year, with branch subtotals and grand total
SELECT location_id, year, COUNT(DISTINCT voucher_no) AS invoices, ROUND(SUM(amount), 0) AS revenue_aed
FROM pht_dw.fact_sales
GROUP BY location_id, year WITH ROLLUP
ORDER BY location_id, year;

-- Q2. CUBE - revenue by product group x branch (2025), every combination of subtotals
SELECT stock_group, location_id, ROUND(SUM(amount), 0) AS revenue_aed
FROM (SELECT i.stock_group, s.location_id, s.amount
      FROM pht_dw.fact_sales s JOIN pht_dw.dim_item i ON s.item_id = i.item_id
      WHERE s.year = 2025) t
GROUP BY stock_group, location_id WITH CUBE
ORDER BY stock_group, location_id;

-- Q3. GROUPING SETS - monthly revenue per branch and yearly revenue per customer emirate
SELECT location_id, year, month, emirate, ROUND(SUM(amount), 0) AS revenue_aed
FROM (SELECT s.location_id, s.year, s.month, c.emirate, s.amount
      FROM pht_dw.fact_sales s JOIN pht_dw.dim_customer c ON s.customer_id = c.customer_id
      WHERE s.year >= 2025) t
GROUP BY location_id, year, month, emirate
GROUPING SETS ((location_id, year, month), (year, emirate))
ORDER BY year, location_id, month, emirate;

-- Q4. Ajman case - where 2025 revenue comes from (customer emirate)
SELECT customer_emirate, revenue_aed, ROUND(100 * revenue_aed / SUM(revenue_aed) OVER (), 1) AS pct_of_revenue
FROM (SELECT CASE WHEN c.emirate = '' THEN '(walk-in)' ELSE c.emirate END AS customer_emirate,
             ROUND(SUM(s.amount), 0) AS revenue_aed
      FROM pht_dw.fact_sales s JOIN pht_dw.dim_customer c ON s.customer_id = c.customer_id
      WHERE s.year = 2025
      GROUP BY CASE WHEN c.emirate = '' THEN '(walk-in)' ELSE c.emirate END) g
ORDER BY revenue_aed DESC;

-- Q5. Quotations - how many quotes become invoices, per branch per year
SELECT location_id, year, COUNT(DISTINCT quote_no) AS quotes,
       COUNT(DISTINCT CASE WHEN converted = 'Y' THEN quote_no END) AS converted,
       ROUND(100 * COUNT(DISTINCT CASE WHEN converted = 'Y' THEN quote_no END) / COUNT(DISTINCT quote_no), 1) AS conversion_pct
FROM pht_dw.fact_quote
GROUP BY location_id, year
ORDER BY location_id, year;

-- Q6. Transfer problems found by MapReduce, per route
SELECT from_loc, to_loc,
       SUM(CASE WHEN status = 'MATCHED' THEN 1 ELSE 0 END) AS matched,
       SUM(CASE WHEN status = 'QTY_MISMATCH' THEN 1 ELSE 0 END) AS qty_mismatch,
       SUM(CASE WHEN status = 'RECEIPT_MISSING' THEN 1 ELSE 0 END) AS receipt_missing,
       SUM(CASE WHEN status = 'IN_TRANSIT' THEN 1 ELSE 0 END) AS in_transit,
       ROUND(AVG(entry_lag_days), 1) AS avg_days_until_receipt_typed
FROM pht_dw.fact_transfer
WHERE status <> 'RECEIPT_WITHOUT_DISPATCH'
GROUP BY from_loc, to_loc
ORDER BY from_loc, to_loc;

-- Q7. Transfer problems per year (drill down by time)
SELECT year, COUNT(*) AS transfer_lines,
       SUM(CASE WHEN status = 'QTY_MISMATCH' THEN 1 ELSE 0 END) AS qty_mismatch,
       SUM(CASE WHEN status = 'RECEIPT_MISSING' THEN 1 ELSE 0 END) AS receipt_missing
FROM pht_dw.fact_transfer
GROUP BY year ORDER BY year;

-- Q8. Slow and dead stock - items in stock on 31-Oct-2026 with no sale in the last 12 months
SELECT i.stock_group, COUNT(DISTINCT ss.item_id) AS dead_items, ROUND(SUM(ss.value), 0) AS stock_value_aed
FROM pht_dw.fact_stock_snapshot ss
JOIN pht_dw.dim_item i ON ss.item_id = i.item_id
LEFT JOIN (SELECT DISTINCT item_id FROM pht_dw.fact_sales WHERE (year = 2025 AND month >= 11) OR year = 2026) recent
       ON ss.item_id = recent.item_id
WHERE ss.snapshot_date_key = 20261031 AND recent.item_id IS NULL
GROUP BY i.stock_group
ORDER BY stock_value_aed DESC;

-- Q9. Supplier delivery performance (order date -> goods received)
SELECT sp.supplier_name, sp.country, COUNT(DISTINCT p.voucher_no) AS deliveries,
       ROUND(AVG(p.lead_days), 1) AS avg_lead_days, MAX(p.lead_days) AS worst_lead_days,
       ROUND(AVG(p.entry_lag_days), 1) AS avg_days_until_bill_typed_in
FROM pht_dw.fact_purchase p JOIN pht_dw.dim_supplier sp ON p.supplier_id = sp.supplier_id
WHERE p.year = 2026
GROUP BY sp.supplier_name, sp.country
ORDER BY avg_lead_days DESC;

-- Q10. Top 10 items by revenue in 2026 (note the recurring SPECIAL items - candidates for the regular catalogue)
SELECT i.item_name, i.stock_group, SUM(s.actual_qty) AS units, ROUND(SUM(s.amount), 0) AS revenue_aed
FROM pht_dw.fact_sales s JOIN pht_dw.dim_item i ON s.item_id = i.item_id
WHERE s.year = 2026
GROUP BY i.item_name, i.stock_group
ORDER BY revenue_aed DESC
LIMIT 10;

-- Q11. Stock records that don't add up (MapReduce reconciliation, Sep-Oct 2026)
SELECT location, COUNT(*) AS items_with_gap, SUM(ABS(difference)) AS total_units_off
FROM pht_dw.mr_stock_reconciliation
GROUP BY location ORDER BY items_with_gap DESC;
