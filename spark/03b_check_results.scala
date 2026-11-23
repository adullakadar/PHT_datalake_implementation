// PHT 03b - check the live results. Inside the SAME spark-shell type:
//   :load /home/bigdata/PHT/spark/03b_check_results.scala
// (run it several times while the feeder is running)

// ---- 9. Streaming query status
spark.streams.active.foreach { q =>
  val p = q.lastProgress
  val rows = if (p == null) 0L else p.numInputRows
  val batch = if (p == null) -1L else p.batchId
  println(f"${q.name}%-16s batch=$batch%-4d rows in last batch=$rows%-5d status=${q.status.message}")
}

// ---- 10. LOW-STOCK ALERTS right now (re-run during the feed: alerts appear, then clear when a warehouse transfer arrives)
val alerts = spark.read.option("header", "true").option("inferSchema", "true")
  .csv(PHT + "/curated/stream/low_stock_alerts")
  .orderBy($"location_id", $"qty_now")
println("alerts: " + alerts.count())
alerts.show(50, false)
// ---- 11. Alerts per location
alerts.groupBy("location_id").count().orderBy("location_id").show(50, false)
// ---- 12. Transfers in transit (run this WHILE the feeder is running to catch items on the road)
spark.sql("""
  SELECT reference, product_id, to_location, qty_sent, qty_received,
         date_format(sent_ts, 'HH:mm') AS sent_at,
         CASE WHEN qty_received = 0 THEN 'IN TRANSIT' ELSE 'RECEIVED' END AS state
  FROM transfers_live
  WHERE qty_sent > 0
  ORDER BY state, sent_ts""").show(50, false)

// ---- 13. Sales per branch per 30-minute window (use the line/bar chart button)
spark.sql("""
  SELECT date_format(window.start, 'HH:mm') AS time_slot, location_id, revenue_aed, invoices
  FROM sales_by_window
  ORDER BY window.start, location_id""").show(50, false)
