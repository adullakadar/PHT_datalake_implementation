#!/usr/bin/env python3
# Job 2 - transfer matching (reduce-side join of the two separate Tally records of each transfer)
# input : clean/transfer_records (tab separated)
# output: from_loc|to_loc|item_id <TAB> direction <TAB> date <TAB> qty <TAB> pink_slip <TAB> voucher_no <TAB> recorded_by
import sys
for line in sys.stdin:
    f = line.rstrip("\n").split("\t")
    if len(f) < 13:
        continue
    recorded_by, voucher, date, item_id, frm, to, direction, qty, slip = f[0], f[1], f[2], f[5], f[6], f[7], f[8], f[9], f[12]
    if direction not in ("OUT", "IN") or not item_id:
        continue                     # WH_TO_SHJ1 is a single entry inside SHJ1's Tally: nothing to match
    print("%s|%s|%s\t%s\t%s\t%s\t%s\t%s\t%s" % (frm, to, item_id, direction, date, qty, slip, voucher, recorded_by))
