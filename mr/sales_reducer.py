#!/usr/bin/env python3
# Job 1 reducer - sums qty and amount per key (input arrives sorted by key)
import sys
cur, qty, amt = None, 0, 0.0
def out():
    b, item, ym = cur.split("|")
    print("%s\t%s\t%s\t%d\t%.2f" % (b, item, ym, qty, amt))
for line in sys.stdin:
    key, q, a = line.rstrip("\n").split("\t")
    if key != cur:
        if cur is not None:
            out()
        cur, qty, amt = key, 0, 0.0
    qty += int(q); amt += float(a)
if cur is not None:
    out()
