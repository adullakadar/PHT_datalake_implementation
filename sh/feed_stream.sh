#!/bin/bash
PHT=/user/bigdata/pht
for f in $($HADOOP_HOME/bin/hadoop fs -ls $PHT/raw/stream/staging | grep -o 'events_[0-9]*\.csv' | sort); do
  # mv inside HDFS is atomic, so Spark never sees a half-written file
  $HADOOP_HOME/bin/hadoop fs -mv $PHT/raw/stream/staging/$f $PHT/raw/stream/events_landing/$f
  echo "$(date +%H:%M:%S)  POS file arrived: $f"
  sleep 2
done
echo "$(date +%H:%M:%S)  ALL FILES DELIVERED"
