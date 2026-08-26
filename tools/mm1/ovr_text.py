#!/usr/bin/env python3
"""Extract the data block of each map overlay: event-handler table and text.

The data half of an .OVR is loaded at 0xC940 and holds, in order:
  - 50 bytes of per-map parameters (see tools/mm1/ovr_params.py)
  - the event tables: a count, then that many ids, masks and handler words
  - NUL-terminated text strings

One map, `demon`, has no event tables at all -- its text starts right after the
parameter block.

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

NPARAM = 50            # the parameter block; the event count sits right after it

# The dispatch routine 54 of the 55 overlays carry (see doc 8):
#   mov al,[3C3A] / mov bx,0 / cmp al,[bx+0C973h] / je .. / inc bl
#   cmp bl,[0C972h] / jb ..
# Match on the opcode skeleton: the two jump displacements vary between maps.
MOVBX0 = bytes.fromhex('bb0000')
CMPIDX = bytes.fromhex('3a87')
INCBL  = bytes.fromhex('fec3')
CMPCNT = bytes.fromhex('3a1e')

def has_events(code):
    p = struct.unpack('<H', code[1:3])[0] - CODE_BASE     # pointer the stub registers
    if p < 0 or p + 20 > len(code):
        return False
    return (code[p] == 0xA0 and code[p+3:p+6] == MOVBX0
            and code[p+6:p+8] == CMPIDX and code[p+10] == 0x74
            and code[p+12:p+14] == INCBL and code[p+14:p+16] == CMPCNT
            and code[p+18] == 0x72)

def handler_table(code, data):
    """(offset, handler words). Empty for a map with no per-square events."""
    if not has_events(code):
        return NPARAM, []
    n = data[NPARAM]                       # count, then n ids, n masks, n words
    off = NPARAM + 1 + 2*n
    return off, [struct.unpack('<H', data[off+2*k:off+2*k+2])[0]
                 for k in range(n) if off+2*k+2 <= len(data)]

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
