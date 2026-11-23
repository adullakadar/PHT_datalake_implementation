-- PHT Notebook 05b: star schema in the CURATED zone (ORC, facts partitioned by year/month)
USE pht_dw;
SET hive.exec.dynamic.partition=true;
SET hive.exec.dynamic.partition.mode=nonstrict;
SET hive.exec.max.dynamic.partitions=2000;
SET hive.exec.max.dynamic.partitions.pernode=2000;
SET hive.optimize.sort.dynamic.partition=true;

-- ---------------- dimensions
DROP TABLE IF EXISTS dim_location;
CREATE TABLE dim_location (location_id STRING, location_name STRING, emirate STRING, location_type STRING, opened STRING) STORED AS ORC;
INSERT INTO TABLE dim_location VALUES
  ('SHJ1', 'Sharjah 1 (main)', 'Sharjah', 'Branch', '2019-07-01'),
  ('WH1', 'Main Warehouse', 'Sharjah', 'Warehouse', '2019-07-01'),
  ('DB1', 'Dubai 1', 'Dubai', 'Branch', '2021-04-01'),
  ('SHJ2', 'Sharjah 2', 'Sharjah', 'Branch', '2023-02-01'),
  ('AJM1', 'Ajman (proposed)', 'Ajman', 'Branch', '');

DROP TABLE IF EXISTS dim_item;
CREATE TABLE dim_item (item_id STRING, item_name STRING, stock_group STRING, uom STRING, std_cost DOUBLE, is_special STRING) STORED AS ORC;
INSERT OVERWRITE TABLE dim_item SELECT * FROM stg_items;

DROP TABLE IF EXISTS dim_customer;
CREATE TABLE dim_customer (customer_id STRING, ledger_name STRING, trn STRING, emirate STRING, address STRING) STORED AS ORC;
INSERT OVERWRITE TABLE dim_customer SELECT * FROM stg_customers;

DROP TABLE IF EXISTS dim_supplier;
CREATE TABLE dim_supplier (supplier_id STRING, supplier_name STRING, trn STRING, country STRING, location STRING) STORED AS ORC;
INSERT OVERWRITE TABLE dim_supplier SELECT * FROM stg_suppliers;

DROP TABLE IF EXISTS dim_date;
CREATE TABLE dim_date (date_key INT, full_date DATE, year INT, quarter INT, month INT, month_name STRING, day_name STRING) STORED AS ORC;
INSERT OVERWRITE TABLE dim_date
SELECT CAST(date_format(d, 'yyyyMMdd') AS INT), d, year(d), quarter(d), month(d), date_format(d, 'MMM'), date_format(d, 'EEEE')
FROM (SELECT sale_date AS d FROM stg_sales_lines
      UNION SELECT quote_date FROM stg_quote_lines
      UNION SELECT received_date FROM stg_purchase_lines
      UNION SELECT snapshot_date FROM stg_stock_snapshots) x
WHERE d IS NOT NULL;

-- ---------------- facts
DROP TABLE IF EXISTS fact_sales;
CREATE TABLE fact_sales (voucher_no STRING, date_key INT, location_id STRING, customer_id STRING, item_id STRING,
  actual_qty INT, billed_qty INT, rate DOUBLE, disc_pct DOUBLE, amount DOUBLE, vat_amount DOUBLE, quote_no STRING,
  delivered STRING, payment_terms STRING)
PARTITIONED BY (year INT, month INT) STORED AS ORC;
INSERT OVERWRITE TABLE fact_sales PARTITION (year, month)
SELECT voucher_no, CAST(date_format(sale_date, 'yyyyMMdd') AS INT), branch, customer_id, item_id, actual_qty, billed_qty, rate,
       disc_pct, amount, vat_amount, quote_no, delivered, payment_terms, year, month
FROM stg_sales_lines;

DROP TABLE IF EXISTS fact_quote;
CREATE TABLE fact_quote (quote_no STRING, date_key INT, location_id STRING, customer_id STRING, item_id STRING, qty INT,
  amount DOUBLE, converted STRING)
PARTITIONED BY (year INT, month INT) STORED AS ORC;
INSERT OVERWRITE TABLE fact_quote PARTITION (year, month)
SELECT quote_no, CAST(date_format(quote_date, 'yyyyMMdd') AS INT), branch, customer_id, item_id, qty, amount, converted, year, month
FROM stg_quote_lines;

DROP TABLE IF EXISTS fact_purchase;
CREATE TABLE fact_purchase (voucher_no STRING, received_date_key INT, supplier_id STRING, item_id STRING, po_no STRING,
  received_qty INT, billed_qty INT, amount DOUBLE, lead_days INT, entry_lag_days INT)
PARTITIONED BY (year INT, month INT) STORED AS ORC;
INSERT OVERWRITE TABLE fact_purchase PARTITION (year, month)
SELECT voucher_no, CAST(date_format(received_date, 'yyyyMMdd') AS INT), supplier_id, item_id, po_no, received_qty, billed_qty,
       amount, lead_days, entry_lag_days, year, month
FROM stg_purchase_lines;

DROP TABLE IF EXISTS fact_transfer;
CREATE TABLE fact_transfer (from_loc STRING, to_loc STRING, item_id STRING, status STRING, sent_date_key INT,
  received_entry_date_key INT, qty_sent INT, qty_received INT, entry_lag_days INT, match_method STRING)
PARTITIONED BY (year INT) STORED AS ORC;
INSERT OVERWRITE TABLE fact_transfer PARTITION (year)
SELECT from_loc, to_loc, item_id, status,
       CAST(regexp_replace(out_date, '-', '') AS INT), CAST(regexp_replace(in_date, '-', '') AS INT),
       CAST(qty_sent AS INT), CAST(qty_received AS INT), CAST(entry_lag_days AS INT), match_method,
       CAST(substr(CASE WHEN out_date <> '' THEN out_date ELSE in_date END, 1, 4) AS INT)
FROM mr_transfer_matching;

DROP TABLE IF EXISTS fact_stock_snapshot;
CREATE TABLE fact_stock_snapshot (snapshot_date_key INT, location_id STRING, item_id STRING, qty INT, value DOUBLE) STORED AS ORC;
INSERT OVERWRITE TABLE fact_stock_snapshot
SELECT CAST(date_format(snapshot_date, 'yyyyMMdd') AS INT), location, item_id, qty, value FROM stg_stock_snapshots;

SHOW PARTITIONS fact_sales;
