#!/usr/bin/env python3
# Job 1 - monthly units & revenue per branch per item (the WordCount pattern with a business key)
# input : clean/sales_lines (tab separated)
# output: branch|item_id|yyyy-mm <TAB> qty <TAB> amount
import sys
for line in sys.stdin:
    f = line.rstrip("\n").split("\t")
    if len(f) < 13 or not f[6]:
        continue
    branch, sale_date, item_id, qty, amount = f[0], f[2], f[6], f[7], f[12]
    print("%s|%s|%s\t%s\t%s" % (branch, item_id, sale_date[:7], qty, amount))
