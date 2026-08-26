#!/usr/bin/env python3
"""Extract the data block of each map overlay: event-handler table and text.

The data half of an .OVR is loaded at 0xC940 and holds, in order:
  - a block of per-map binary parameters (variable length, not decoded)
  - a table of words pointing into the overlay's own code: the event handlers
  - NUL-terminated text strings

Text is written for a 40-column display: 0x0D is an explicit line break, and
longer runs rely on the engine wrapping hard at column 40. Pass --wrap to see
the text laid out as the game shows it rather than as it is stored.

  python tools/mm1/ovr_text.py             # every map, text as stored
  python tools/mm1/ovr_text.py sorpigal    # one map, with handler table
  python tools/mm1/ovr_text.py --wrap      # wrapped to 40 columns
  python tools/mm1/ovr_text.py --summary   # one line per map
"""
import os, sys, struct
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import mmlib

CODE_BASE, DATA_BASE = 0xF48F, 0xC940
MIN_LEN, COLS = 4, 40
CR = chr(13)

def blocks(name):
    d = open(mmlib.path(name.upper() + '.OVR'), 'rb').read()
    cs = struct.unpack('<H', d[4:6])[0]
    dsz = struct.unpack('<I', d[8:12])[0]
    return d[14:14+cs], d[14+cs:14+cs+dsz]

def handler_table(code, data):
    """Longest run of words that point into this overlay's own code."""
    hi = CODE_BASE + len(code)
    best_n = best_off = 0
    i = 0
    while i + 2 <= len(data):
        j, n = i, 0
        while j + 2 <= len(data) and CODE_BASE <= struct.unpack('<H', data[j:j+2])[0] < hi:
            j += 2; n += 1
        if n > best_n:
            best_n, best_off = n, i
        i = j + 2 if n else i + 1
    return best_off, [struct.unpack('<H', data[best_off+2*k:best_off+2*k+2])[0]
                      for k in range(best_n)]

def strings(data):
    """NUL-terminated runs of printable text, with their load addresses."""
    out, start = [], None
    for i, c in enumerate(data + b'\x00'):
        if 0x20 <= c < 0x7F or c == 0x0D:
            if start is None:
                start = i
            continue
        if start is not None and i - start >= MIN_LEN and c == 0x00:
            out.append((DATA_BASE + start, data[start:i].decode('ascii')))
        start = None
    return out

def lay_out(text):
    """Render as the engine does: explicit 0x0D breaks, hard wrap at column 40."""
    lines = []
    for para in text.split(CR):
        if not para:
            lines.append('')
        while para:
            lines.append(para[:COLS]); para = para[COLS:]
    return lines

def show(name, table=False, wrap=False):
    code, data = blocks(name)
    off, tbl = handler_table(code, data)
    print(f"=== {name}  (map {mmlib.MAPS.index(name)})  "
          f"code {len(code)}B  data {len(data)}B ===")
    if table:
        print(f"  event handlers: {len(tbl)} entries at {DATA_BASE+off:04X}h")
        for k in range(0, len(tbl), 8):
            print("    " + " ".join(f"{v:04X}" for v in tbl[k:k+8]))
        print()
    for addr, s in strings(data):
        body = lay_out(s) if wrap else s.split(CR)
        print(f"  {addr:04X}  " + ("\n" + " " * 8).join(body))
    print()

def main():
    args = list(sys.argv[1:])
    wrap = '--wrap' in args
    args = [a for a in args if a != '--wrap']
    if args and args[0] == '--summary':
        print(f"{'map':10s} {'code':>5s} {'data':>5s} {'handlers':>9s} {'strings':>8s}")
        for n in mmlib.MAPS:
            c, d = blocks(n)
            print(f"{n:10s} {len(c):5d} {len(d):5d} "
                  f"{len(handler_table(c, d)[1]):9d} {len(strings(d)):8d}")
        return
    for n in (args or mmlib.MAPS):
        show(n, table=bool(args), wrap=wrap)

if __name__ == '__main__':
    main()
