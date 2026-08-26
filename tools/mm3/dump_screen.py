#!/usr/bin/env python3
"""Write a Might & Magic 3 full-screen picture out as a PNG.

Every `.raw` member decompresses to exactly 64,000 bytes, which is one
320x200 mode 13h screen. The palette is not in the archive as a plain table,
so these come out as grey levels indexed by the pixel value -- shape only, not
colour. See docs/mm3/03.

  python tools/mm3/dump_screen.py front.raw out/front.png
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import mmlib3, png

W, H = 320, 200
if len(sys.argv) < 3:
    print(__doc__)
    sys.exit(1)
name, dest = sys.argv[1], sys.argv[2]
wanted = mmlib3.hash_name(name)
for m in mmlib3.read_directory('MM3.CC'):
    if m.id == wanted:
        data = mmlib3.read_member(m)
        if len(data) != W * H:
            sys.exit(f'{name} is {len(data)} bytes, not a {W}x{H} screen')
        os.makedirs(os.path.dirname(dest) or '.', exist_ok=True)
        png.write(dest, W, H,
                  [[(p, p, p) for p in data[y * W:(y + 1) * W]] for y in range(H)])
        print(f'{name} -> {dest}')
        break
else:
    sys.exit(f'no member hashes to {name} ({wanted:04X})')
