#!/usr/bin/env python3
"""Print the 579 symbols from MM.RSM, with each one's size and file offset.

The trailing word in a record is where the symbol ends, not where it starts --
see doc 2 -- so the sizes below come straight out of the map.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]   # this game's lib, then shared tools/
import mmlib

TYPE = {0x02: 'code', 0x03: 'data', 0x09: 'abs ', 0x00: '----'}
for name, t, off, end in mmlib.symbol_extents():
    if t == 0x03:
        loc = f'file 0x{mmlib.DATA_SEG_FILE_BASE + off:06x}'
    elif t == 0x02:
        loc = f'file 0x{mmlib.CODE_SEG_FILE_BASE + off:06x}'
    else:
        loc = ''
    print(f'{TYPE.get(t, hex(t)):5s} {off:04x}..{end:04x} {end-off:6d}  {loc:16s} {name}')
