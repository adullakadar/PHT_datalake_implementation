#!/usr/bin/env python3
# Job 3 - stock reconciliation: counted stock (godown summary) vs stock calculated from recorded movements
# reads 4 clean datasets at once; RECON_FROM / RECON_TO are snapshot dates passed with -cmdenv
# output: location|item_id <TAB> B|M|E <TAB> qty     (B = opening count, M = movement, E = closing count)
import sys, os
FROM = os.environ.get("RECON_FROM", "2026-08-31")
TO = os.environ.get("RECON_TO", "2026-10-31")
def inside(day):
    return FROM < day <= TO
def out(loc, item, tag, q):
    print("%s|%s\t%s\t%d" % (loc, item, tag, q))
for line in sys.stdin:
    f = line.rstrip("\n").split("\t")
    n = len(f)
    if n == 5:                                              # stock_snapshots: date, location, item, qty, value
        if f[2] and f[0] == FROM:
            out(f[1], f[2], "B", int(f[3]))
        elif f[2] and f[0] == TO:
            out(f[1], f[2], "E", int(f[3]))
    elif n >= 14 and f[8] in ("OUT", "IN", "WH_TO_SHJ1"):  # transfer_records
        if f[5] and inside(f[2]):
            q = int(f[9])
            if f[8] == "OUT":
                out(f[6], f[5], "M", -q)
            elif f[8] == "IN":
                out(f[7], f[5], "M", q)
            else:
                out("WH1", f[5], "M", -q); out("SHJ1", f[5], "M", q)
    elif n >= 17 and f[0].startswith("PUR/"):              # purchase_lines: booked into the warehouse on entry date
        if f[9] and inside(f[1]):
            out("WH1", f[9], "M", int(f[10]))
    elif n >= 17:                                          # sales_lines: stock leaves the branch (actual qty)
        if f[6] and inside(f[2]):
            out(f[0], f[6], "M", -int(f[7]))
