#!/usr/bin/env python3
"""The 256 records of ITEMS.DAT: a 12-byte name and 8 stat bytes each.

  python tools/mm2/dump_items.py          # all 256
  python tools/mm2/dump_items.py sling    # only names matching a substring
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import mmlib2

want = sys.argv[1].lower() if len(sys.argv) > 1 else None
for i, (name, stats) in enumerate(mmlib2.read_items()):
    if want and want not in name.lower():
        continue
    print(f'{i:3d}  {name:<12s}  {stats.hex(" ")}')
