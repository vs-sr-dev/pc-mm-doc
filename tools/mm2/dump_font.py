#!/usr/bin/env python3
"""MM2.CH -- 128 glyphs of 8x8, one bit per pixel, indexed by ASCII code.

  python tools/mm2/dump_font.py           # printable range as ASCII art
  python tools/mm2/dump_font.py 65        # one glyph
  python tools/mm2/dump_font.py --png out/mm2font.png
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import mmlib2, png

font = mmlib2.read_font()

if len(sys.argv) > 2 and sys.argv[1] == '--png':
    out = sys.argv[2]
    os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
    cols = 16
    rows = (len(font) + cols - 1) // cols
    W, H = cols * 9 + 1, rows * 9 + 1
    canvas = [[(24, 24, 24)] * W for _ in range(H)]
    for g, glyph in enumerate(font):
        ox, oy = 1 + (g % cols) * 9, 1 + (g // cols) * 9
        for y, row in enumerate(glyph):
            for x, on in enumerate(row):
                canvas[oy + y][ox + x] = (255, 255, 255) if on else (48, 48, 48)
    png.write(out, W, H, canvas)
    print(f'{out}  {len(font)} glyphs, {W}x{H}')
    sys.exit()

which = [int(sys.argv[1])] if len(sys.argv) > 1 else range(32, 127)
for g in which:
    label = chr(g) if 32 <= g < 127 else ' '
    print(f'  {g:3d}  {label!r}')
    for row in font[g]:
        print('       ' + ''.join('#' if on else '.' for on in row))
