#!/usr/bin/env python3
# Job 2 reducer - all OUT and IN records of one route+item arrive together.
# pairs OUT with IN in 4 passes: same slip + same qty, same qty within 7 days, same slip, within 7 days
# status: MATCHED | QTY_MISMATCH | RECEIPT_MISSING | IN_TRANSIT (sent in the last 7 days) | RECEIPT_WITHOUT_DISPATCH
import sys, os
from datetime import datetime
DATA_END = datetime.strptime(os.environ.get("DATA_END", "2026-10-31"), "%Y-%m-%d")
WINDOW = 7

def d(s):
    return datetime.strptime(s, "%Y-%m-%d")

def emit(key, status, o, i, method):
    frm, to, item = key.split("|")
    out_date, out_q, out_v = (o[1], o[2], o[4]) if o else ("", "", "")
    in_date, in_q, in_v = (i[1], i[2], i[4]) if i else ("", "", "")
    lag = str((d(in_date) - d(out_date)).days) if (o and i) else ""
    print("\t".join([frm, to, item, status, out_date, in_date, str(out_q), str(in_q), lag, out_v, in_v, method]))

def match(key, recs):
    outs = sorted([r for r in recs if r[0] == "OUT"], key=lambda r: r[1])
    ins = sorted([r for r in recs if r[0] == "IN"], key=lambda r: r[1])
    used_in, done, pairs = set(), set(), []
    def in_window(o, r):
        return 0 <= (d(r[1]) - d(o[1])).days <= WINDOW
    # four passes, strictest first: slip+qty, date+qty, slip only, date only
    rules = [("SLIP", lambda o, r: o[3] and r[3] == o[3] and r[2] == o[2]),
             ("DATE", lambda o, r: in_window(o, r) and r[2] == o[2]),
             ("SLIP", lambda o, r: o[3] and r[3] == o[3]),
             ("DATE", lambda o, r: in_window(o, r))]
    for method, ok in rules:
        for j, o in enumerate(outs):
            if j in done:
                continue
            cands = [k for k, r in enumerate(ins) if k not in used_in and ok(o, r)]
            if cands:
                k = min(cands, key=lambda k: ins[k][1])
                used_in.add(k); done.add(j); pairs.append((o, ins[k], method))
    for j, o in enumerate(outs):
        if j not in done:
            pairs.append((o, None, ""))
    for o, i, method in pairs:
        if i is None:
            emit(key, "IN_TRANSIT" if (DATA_END - d(o[1])).days <= WINDOW else "RECEIPT_MISSING", o, None, "")
        else:
            emit(key, "MATCHED" if o[2] == i[2] else "QTY_MISMATCH", o, i, method)
    for k, r in enumerate(ins):
        if k not in used_in:
            emit(key, "RECEIPT_WITHOUT_DISPATCH", None, r, "")

cur, recs = None, []
for line in sys.stdin:
    p = line.rstrip("\n").split("\t")
    key, rec = p[0], (p[1], p[2], int(p[3]), p[4], p[5], p[6])   # direction, date, qty, slip, voucher, recorded_by
    if key != cur:
        if cur is not None:
            match(cur, recs)
        cur, recs = key, []
    recs.append(rec)
if cur is not None:
    match(cur, recs)
