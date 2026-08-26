#!/usr/bin/env python3
"""Print the 579 symbols from MM.RSM, with the MM.EXE file offset for each."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import mmlib

TYPE = {0x02: 'code', 0x03: 'data', 0x09: 'abs ', 0x00: '----'}
for name, t, cls, off in mmlib.read_symbols():
    if t == 0x03:
        loc = f'file 0x{mmlib.DATA_SEG_FILE_BASE + off:06x}'
    elif t == 0x02:
        loc = f'file 0x{0x200 + off:06x}'
    else:
        loc = ''
    print(f'{TYPE.get(t, hex(t)):5s} {off:04x}  {loc:16s} {name}')
