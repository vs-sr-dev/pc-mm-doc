#!/usr/bin/env python3
"""The per-map parameter block: bytes 0..49 of an overlay's data area.

The engine reads these through an indexed accessor at 0x0D5B (read) and 0x0D66
(write), always with a literal index. Scanning the engine for those call sites
gives, for every one of the 50 bytes, the routines that consume it -- which
names the fields functionally even where their encoding is still unknown.

  python tools/mm1/ovr_params.py            # index -> consumers, from MM.EXE
  python tools/mm1/ovr_params.py sorpigal   # one map's parameter bytes, annotated
"""
import os, sys, struct, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import mmlib
from ovr_text import blocks

READ, WRITE, NPARAM = 0x0D5B, 0x0D66, 50

def consumers():
    d = open(mmlib.path('MM.EXE'), 'rb').read()
    code = d[0x200:0x200+0x10000]
    syms = sorted((o, n) for n, t, c, o in mmlib.read_symbols() if t == 0x02)
    def owner(off):
        prev = None
        for o, n in syms:
            if o > off: break
            prev = (o, n)
        return prev[1] if prev else '?'
    out = collections.defaultdict(set)
    for i in range(len(code) - 3):
        if code[i] != 0xE8:
            continue
        tgt = (i + 3 + struct.unpack('<h', code[i+1:i+3])[0]) & 0xFFFF
        if tgt not in (READ, WRITE):
            continue
        for back in range(3, 12):
            j = i - back
            if j >= 0 and code[j] == 0xBB:
                out[struct.unpack('<H', code[j+1:j+3])[0]].add(
                    owner(i) + ('' if tgt == READ else ' (w)'))
                break
    return out

def main():
    con = consumers()
    if len(sys.argv) > 1:
        name = sys.argv[1]
        data = blocks(name)[1]
        print(f"{name}  (map {mmlib.MAPS.index(name)})  parameter block, "
              f"loads at {0xC940:04X}h\n")
        for i in range(NPARAM):
            who = ', '.join(sorted(con.get(i, []))) or '-- no literal-index read --'
            print(f"  [{i:2d}] {data[i]:02X}   {who}")
        print(f"  [{NPARAM}] {data[NPARAM]:02X}   event count (see doc 8)")
        return
    print(f"{'idx':>4}  consumers in MM.EXE")
    for i in range(NPARAM):
        print(f"  {i:2d}  {', '.join(sorted(con.get(i, []))) or '--'}")

if __name__ == '__main__':
    main()
