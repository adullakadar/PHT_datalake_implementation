-- PHT 06a: benchmarks - what Hive is good at (reports) and what it is bad at (live stock)
USE pht_dw;

-- B1. partition pruning: same question on the TEXT staging table (whole table read) and the ORC partitioned fact
EXPLAIN DEPENDENCY SELECT ROUND(SUM(amount), 0) FROM stg_sales_lines WHERE year = 2026 AND month = 9;
EXPLAIN DEPENDENCY SELECT ROUND(SUM(amount), 0) FROM fact_sales WHERE year = 2026 AND month = 9;
SELECT COUNT(*) AS lines, ROUND(SUM(amount), 0) AS revenue FROM stg_sales_lines WHERE year = 2026 AND month = 9;
SELECT COUNT(*) AS lines, ROUND(SUM(amount), 0) AS revenue FROM fact_sales WHERE year = 2026 AND month = 9;

-- B2. "how many of this item does DB1 have?" - a single-row lookup in Hive (compare: HBase get in 06b)
SELECT location_id, item_id, qty FROM fact_stock_snapshot
WHERE snapshot_date_key = 20261031 AND location_id = 'DB1' AND item_id = 'PHT-01133';

-- B3. recording ONE stock change in Hive: every INSERT is a full job and leaves a new small file
DROP TABLE IF EXISTS bench_stock_changes;
CREATE TABLE bench_stock_changes (rowkey STRING, qty INT) STORED AS ORC;
INSERT INTO TABLE bench_stock_changes VALUES ('DB1|PHT-01133', 25);
INSERT INTO TABLE bench_stock_changes VALUES ('DB1|PHT-01133', 24);
INSERT INTO TABLE bench_stock_changes VALUES ('DB1|PHT-01133', 20);

-- B4. changing a row in place is not allowed on a normal (non-ACID) Hive table -> an ERROR is expected here
UPDATE fact_stock_snapshot SET qty = 20 WHERE location_id = 'DB1' AND item_id = 'PHT-01133';
