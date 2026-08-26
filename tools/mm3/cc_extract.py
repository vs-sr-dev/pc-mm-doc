#!/usr/bin/env python3
"""Extract the members of a Might & Magic 3 archive, decompressing as needed.

Members whose filename the name search recovers are written under that name;
the rest are written as their 16-bit id.

  python tools/mm3/cc_extract.py out             # MM3.CC -> out/
  python tools/mm3/cc_extract.py out MM3.CUR
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import mmlib3
from names import table as name_table

out = sys.argv[1] if len(sys.argv) > 1 else 'out'
fname = sys.argv[2] if len(sys.argv) > 2 else 'MM3.CC'
os.makedirs(out, exist_ok=True)
ents = mmlib3.read_directory(fname)
table = name_table({m.id for m in ents})
named = 0
for m in ents:
    n = sorted(table.get(m.id, ()))
    label = n[0] if len(n) == 1 else f'{m.id:04X}.bin'
    named += len(n) == 1
    open(os.path.join(out, label), 'wb').write(mmlib3.read_member(m, fname))
print(f'{fname}: wrote {len(ents)} members to {out}/ ({named} under a single recovered name)')
