#!/usr/bin/env python3
"""List a Might & Magic 3 .CC archive.

The directory stores a 16-bit hash of each member's filename and no name, so
names are recovered by hashing the filename literals in the unpacked MM3.EXE
and matching (doc mm3/03). Members the search does not reach are listed by id.

  python tools/mm3/cc_list.py               # MM3.CC
  python tools/mm3/cc_list.py MM3.CUR       # the other archive
  python tools/mm3/cc_list.py --check       # the tiling test on both
"""
import os, sys, collections, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import mmlib3
from names import table as name_table


def entropy(b):
    if not b:
        return 0.0
    c = collections.Counter(b)
    return -sum(v / len(b) * math.log2(v / len(b)) for v in c.values())


if len(sys.argv) > 1 and sys.argv[1] == '--check':
    for f in ('MM3.CC', 'MM3.CUR'):
        ents = mmlib3.read_directory(f)
        over, unused = mmlib3.tiling(f)
        print(f'{f:<8s} {len(ents):3d} members, '
              f'{sum(m.size for m in ents)} bytes stored, '
              f'{over} overlapping, {unused} unused, '
              f'{len(ents) - len({m.id for m in ents})} duplicate ids')
    sys.exit()

fname = sys.argv[1] if len(sys.argv) > 1 else 'MM3.CC'
ents = mmlib3.read_directory(fname)
table = name_table({m.id for m in ents})
print(f'{fname}: {len(ents)} members, {len(table)} named')
print(f'{"#":>4}  {"id":>4}  {"name":<14s} {"offset":>8}  {"stored":>6}  {"actual":>6}')
for i, m in enumerate(ents):
    n = sorted(table.get(m.id, ()))
    label = n[0] if len(n) == 1 else ('|'.join(n) if n else '')
    print(f'{i:4d}  {m.id:04X}  {label:<14s} {m.offset:8d}  {m.size:6d}  '
          f'{len(mmlib3.read_member(m, fname)):6d}')
