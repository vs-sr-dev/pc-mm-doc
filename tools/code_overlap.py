#!/usr/bin/env python3
"""Does one binary contain code copied from another?

Indexes every k-byte window of the first file, then walks the second looking
for those windows and extending each hit as far as it matches. Shared library
code, hand-written assembly reused between builds, or a whole routine lifted
from one program into another all show up as long runs; unrelated 8086 code
shares no 16-byte window at all, because 16 bytes is 128 bits.

A result is only worth reading next to a control. Run it against a binary you
know shares code with the first (a utility from the same build) to confirm the
test can see reuse, and against compressed data to confirm chance gives zero.

  python tools/code_overlap.py a.exe b.exe [window]
"""
import sys, collections


MIN_DISTINCT = 8   # a run with fewer distinct byte values is filler, not code


def runs(a, b, k=16):
    """Maximal matching runs of b that start on a shared k-byte window, as
    (length, distinct byte values). Long stretches of padding match between any
    two DOS binaries and mean nothing, so the caller filters on the second
    field -- see MIN_DISTINCT."""
    index = collections.defaultdict(list)
    for i in range(len(a) - k):
        index[a[i:i + k]].append(i)
    out, i = [], 0
    while i < len(b) - k:
        hits = index.get(b[i:i + k])
        if not hits:
            i += 1
            continue
        best = k
        for j in hits:
            n = k
            while i + n < len(b) and j + n < len(a) and a[j + n] == b[i + n]:
                n += 1
            best = max(best, n)
        out.append((best, len(set(b[i:i + best]))))
        i += best
    return out


def report(name_a, a, name_b, b, k=16):
    r = [n for n, d in runs(a, b, k) if d >= MIN_DISTINCT]
    print(f'{name_a} vs {name_b}: {len(r)} substantive shared {k}-byte windows, '
          f'longest run {max(r) if r else 0} bytes, '
          f'{sum(1 for x in r if x >= 2 * k)} runs >= {2 * k} B')
    return r


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    k = int(sys.argv[3]) if len(sys.argv) > 3 else 16
    report(sys.argv[1], open(sys.argv[1], 'rb').read(),
           sys.argv[2], open(sys.argv[2], 'rb').read(), k)
