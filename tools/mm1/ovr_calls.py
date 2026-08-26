#!/usr/bin/env python3
"""Resolve the engine calls made by the 55 map overlays.

Overlay code is loaded at 0xF48F (the word at header offset +2) and calls the
engine with ordinary `call rel16`, so every target can be matched against the
symbol table in MM.RSM.

  python tools/mm1/ovr_calls.py            # ranked call graph over all 55 maps
  python tools/mm1/ovr_calls.py sorpigal   # one map, in address order
"""
import os, sys, struct, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]   # this game's lib, then shared tools/
import mmlib

CODE_BASE = 0xF48F

def calls(name):
    d = open(mmlib.path(name.upper() + '.OVR'), 'rb').read()
    code = d[14:14 + struct.unpack('<H', d[4:6])[0]]
    for i in range(len(code) - 2):
        if code[i] == 0xE8:
            rel = struct.unpack('<h', code[i+1:i+3])[0]
            yield CODE_BASE + i, (CODE_BASE + i + 3 + rel) & 0xFFFF

def main():
    syms = {off: n for n, t, c, off in mmlib.read_symbols() if t == 0x02}
    if len(sys.argv) > 1:
        for at, tgt in calls(sys.argv[1]):
            if tgt in syms:
                print(f"  {at:04X}  call {tgt:04X}  {syms[tgt]}")
        return
    cnt, reach = collections.Counter(), collections.Counter()
    for name in mmlib.MAPS:
        seen = set()
        for _, tgt in calls(name):
            if tgt in syms:
                cnt[syms[tgt]] += 1; seen.add(syms[tgt])
        for s in seen:
            reach[s] += 1
    print(f"{'calls':>6} {'maps':>6}  routine")
    for k, v in cnt.most_common():
        print(f"{v:6d} {reach[k]:5d}/55  {k}")

main()
