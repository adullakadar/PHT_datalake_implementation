// PHT 03c - stop the streaming queries. Inside the same spark-shell:  :load /home/bigdata/PHT/spark/03c_stop_streaming.scala

// ---- 16. Stop the streaming queries
spark.streams.active.foreach(_.stop())
println("active queries: " + spark.streams.active.length)
