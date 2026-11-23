-- PHT Notebook 05a: external tables over the CLEAN zone and the MapReduce outputs (no data is copied)
CREATE DATABASE IF NOT EXISTS pht_dw;
USE pht_dw;

DROP TABLE IF EXISTS stg_items;
CREATE EXTERNAL TABLE stg_items (item_id STRING, item_name STRING, stock_group STRING, uom STRING, std_cost DOUBLE, is_special STRING)
ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' STORED AS TEXTFILE LOCATION '/user/bigdata/pht/clean/items';

DROP TABLE IF EXISTS stg_customers;
CREATE EXTERNAL TABLE stg_customers (customer_id STRING, ledger_name STRING, trn STRING, emirate STRING, address STRING)
ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' STORED AS TEXTFILE LOCATION '/user/bigdata/pht/clean/customers';

DROP TABLE IF EXISTS stg_suppliers;
CREATE EXTERNAL TABLE stg_suppliers (supplier_id STRING, supplier_name STRING, trn STRING, country STRING, location STRING)
ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' STORED AS TEXTFILE LOCATION '/user/bigdata/pht/clean/suppliers';

DROP TABLE IF EXISTS stg_sales_lines;
CREATE EXTERNAL TABLE stg_sales_lines (branch STRING, voucher_no STRING, sale_date DATE, year INT, month INT, customer_id STRING,
  item_id STRING, actual_qty INT, billed_qty INT, uom STRING, rate DOUBLE, disc_pct DOUBLE, amount DOUBLE, vat_amount DOUBLE,
  quote_no STRING, delivered STRING, payment_terms STRING)
ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' STORED AS TEXTFILE LOCATION '/user/bigdata/pht/clean/sales_lines';

DROP TABLE IF EXISTS stg_quote_lines;
CREATE EXTERNAL TABLE stg_quote_lines (branch STRING, quote_no STRING, quote_date DATE, year INT, month INT, customer_id STRING,
  item_id STRING, qty INT, rate DOUBLE, disc_pct DOUBLE, amount DOUBLE, converted STRING)
ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' STORED AS TEXTFILE LOCATION '/user/bigdata/pht/clean/quote_lines';

DROP TABLE IF EXISTS stg_purchase_lines;
CREATE EXTERNAL TABLE stg_purchase_lines (voucher_no STRING, entry_date DATE, received_date DATE, year INT, month INT,
  supplier_id STRING, supplier_invoice_no STRING, po_no STRING, po_date DATE, item_id STRING, received_qty INT, billed_qty INT,
  rate DOUBLE, amount DOUBLE, vat_amount DOUBLE, lead_days INT, entry_lag_days INT)
ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' STORED AS TEXTFILE LOCATION '/user/bigdata/pht/clean/purchase_lines';

DROP TABLE IF EXISTS stg_stock_snapshots;
CREATE EXTERNAL TABLE stg_stock_snapshots (snapshot_date DATE, location STRING, item_id STRING, qty INT, value DOUBLE)
ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' STORED AS TEXTFILE LOCATION '/user/bigdata/pht/clean/stock_snapshots';

DROP TABLE IF EXISTS mr_transfer_matching;
CREATE EXTERNAL TABLE mr_transfer_matching (from_loc STRING, to_loc STRING, item_id STRING, status STRING, out_date STRING,
  in_date STRING, qty_sent STRING, qty_received STRING, entry_lag_days STRING, out_voucher STRING, in_voucher STRING, match_method STRING)
ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' STORED AS TEXTFILE LOCATION '/user/bigdata/pht/curated/mr_transfer_matching';

DROP TABLE IF EXISTS mr_stock_reconciliation;
CREATE EXTERNAL TABLE mr_stock_reconciliation (location STRING, item_id STRING, opening_qty INT, movements INT, calculated_qty INT,
  counted_qty INT, difference INT)
ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' STORED AS TEXTFILE LOCATION '/user/bigdata/pht/curated/mr_stock_reconciliation';

DROP TABLE IF EXISTS mr_sales_monthly;
CREATE EXTERNAL TABLE mr_sales_monthly (branch STRING, item_id STRING, year_month STRING, qty INT, amount DOUBLE)
ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' STORED AS TEXTFILE LOCATION '/user/bigdata/pht/curated/mr_sales_monthly';

SHOW TABLES;
