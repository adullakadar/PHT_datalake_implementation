# PHT Data Lake — ISIT312 Big Data Management (UOW Dubai, Autumn 2026)

Group project: a data lake for Piplodwala Hardware Trading LLC (PHT), a UAE marine rigging and hardware supplier whose three branches each run a separate TallyPrime install.
The lake sits beside Tally and takes over the history, live stock and reporting:

- HDFS raw / clean / curated zones
- Spark ETL (raw → clean) and Spark Structured Streaming for live stock
- HBase table `pht_stock` for per-location stock lookups
- MapReduce (Hadoop Streaming, Python) for transfer matching and stock reconciliation
- Hive star schema (ORC, partitioned) for OLAP reports
- Benchmarks showing why each tool fits its job and not the others

All transaction data is **simulated**, based on PHT's description and TallyPrime's real export formats.

## Start here

1. Put this repo at **`/home/bigdata/PHT`** on the VM.
2. Follow **[RUN_ORDER.txt](RUN_ORDER.txt)** steps 0–6 (about an hour end to end).

## Layout

| Folder              | Contents                                                          |
| ------------------- | ----------------------------------------------------------------- |
| `PHT_Dataset_v6/` | Simulated Tally exports, Ajman stream day, answer keys            |
| `spark/`          | ETL, streaming start/check/stop, Spark-vs-MapReduce benchmark     |
| `mr/`             | Mappers/reducers for the 3 MapReduce jobs                         |
| `hql/`            | Staging tables, star schema, OLAP queries Q1–Q11, Hive benchmark |
| `hbase/`          | Table creation, lookups, HBase benchmark                          |
| `sh/`             | `feed_stream.sh` stream replay                                  |
| `notebooks/`      | Zeppelin notebooks as .txt (paste paragraph by paragraph)         |
| `results/`        | Outputs copied from HDFS + Zeppelin export                        |
| `tools/`          | `generate_data.py` to rebuild the dataset                       |
