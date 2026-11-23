#!/usr/bin/env python3
# Job 3 reducer - calculated = opening count + movements; compare with closing count
# output only the discrepancies: location, item, opening, movements, calculated, counted, difference
import sys
cur, b, m, e = None, 0, 0, 0
def out():
    calc = b + m
    if calc != e:
        loc, item = cur.split("|")
        print("%s\t%s\t%d\t%d\t%d\t%d\t%d" % (loc, item, b, m, calc, e, e - calc))
for line in sys.stdin:
    key, tag, q = line.rstrip("\n").split("\t")
    if key != cur:
        if cur is not None:
            out()
        cur, b, m, e = key, 0, 0, 0
    if tag == "B":
        b += int(q)
    elif tag == "E":
        e += int(q)
    else:
        m += int(q)
if cur is not None:
    out()
