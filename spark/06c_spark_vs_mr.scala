// PHT 06c - MapReduce Job 1 (monthly qty & revenue per branch per item) done again in Spark, same input, same output
// run:  $SPARK_HOME/bin/spark-shell --master local[*] --driver-memory 1g --conf spark.sql.shuffle.partitions=4 -i /home/bigdata/PHT/spark/06c_spark_vs_mr.scala
import org.apache.spark.sql.functions._

val PHT = "/user/bigdata/pht"

val sales = spark.read.option("sep", "\t").csv(PHT + "/clean/sales_lines")
  .select(col("_c0").as("branch"), col("_c6").as("item_id"), substring(col("_c2"), 1, 7).as("ym"),
          col("_c7").cast("int").as("qty"), col("_c12").cast("double").as("amount"))

println("---- run 1 (cold)")
spark.time {
  sales.groupBy("branch", "item_id", "ym").agg(sum("qty").as("qty"), round(sum("amount"), 2).as("amount"))
    .write.mode("overwrite").option("sep", "\t").csv(PHT + "/bench/spark_sales_monthly")
}
println("---- run 2 (warm)")
spark.time {
  sales.groupBy("branch", "item_id", "ym").agg(sum("qty").as("qty"), round(sum("amount"), 2).as("amount"))
    .write.mode("overwrite").option("sep", "\t").csv(PHT + "/bench/spark_sales_monthly")
}

val sparkRows = spark.read.option("sep", "\t").csv(PHT + "/bench/spark_sales_monthly").count()
val mrRows    = spark.read.option("sep", "\t").csv(PHT + "/curated/mr_sales_monthly").count()
println("rows - Spark: " + sparkRows + "   MapReduce Job 1: " + mrRows)
