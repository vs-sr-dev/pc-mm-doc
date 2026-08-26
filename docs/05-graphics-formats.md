# 5. Graphics formats

All artwork is CGA 320×200, four colours, and every picture file uses the same
run-length encoding.

## The RLE

```
0x7B <count> <value>   ->  (count + 1) copies of <value>
<any other byte>       ->  one literal byte
```

A literal `0x7B` is escaped as `0x7B 0x00 0x7B`.

The `+1` is not a guess. Decoding the ten `SCREEN` files with a plain
`count` gives 15,318–15,575 bytes, all different; with `count + 1` all ten give
**exactly 16,000 bytes**. The smallest count observed in normal use is 3, i.e.
four repeats — the break-even point for a three-byte escape. The engine-side
symbol is `uncomp` at code offset `0x1504`.

`tools/mmlib.py` implements both directions and the encoder round-trips.

## Pixel layout

16,000 bytes is 320×200 at 2 bits per pixel: four pixels per byte, most
significant pair leftmost. But the bytes are **stored column-major**:

```
byte index = column * height + row
```

This was found by autocorrelation — the strongest repeat distance in a decoded
`SCREEN` file is 200 (the height), not 80 (the row width). Decoding row-major,
with or without the usual CGA even/odd bank interleave, produces noise; decoding
column-major produces the title screen.

Palette is CGA palette 1, high intensity: black, cyan, magenta, white.

## `SCREEN0` … `SCREEN9`

```
word   length of the RLE stream that follows
bytes  RLE stream -> 16,000 bytes = one 320x200 frame
```

Ten full-screen images: title, credits and interstitials.

## `WALLPIX.DTA` and `MONPIX.DTA`

Both are the same container:

```
word        size of the offset table in bytes  (= 4 * image count)
dword[n]    offset of image n, relative to the end of the table
...
per image:  word length, then that many RLE bytes
```

| file | images | decompressed size each |
|---|---:|---:|
| `WALLPIX.DTA` | 18 | 11,200 bytes |
| `MONPIX.DTA` | 76 | 2,496 bytes |

Every image in each file decompresses to exactly the same size, which is a good
check on the container and the codec both.

### `MONPIX.DTA` — solved

2,496 bytes = 26 byte-columns × 96 rows = **104 × 96 pixels**. All 76 decode
cleanly: monsters, plus a few scene portraits (treasure chests, a castle, a
throne room). `python tools/extract_gfx.py` writes them out.

76 portraits serve roughly 195 monster entries, so pictures are shared.

### `WALLPIX.DTA` — container solved, geometry not

The 18 sets are wall-texture sets, one per environment. Each set is a
**concatenation of several sprites of differing heights**, not one image, so a
single width/height does not decode it. Evidence:

* Structural boundaries fall at the *same* offsets in all 18 sets
  (1776, 1871, 3597, …), so every set shares one sprite layout.
* Local repeat distance changes along the file: ~126 early on, then ~96, then
  ~95, with a clean 32 near the end — where a brick pattern does render
  correctly at height 32.

Deriving the sprite table almost certainly requires reading the drawing code
(`getshape` `0x14FB`, `nextwall` `0x1878`, `draw` `0x11D3`, `plot` `0x0F45`, and
the `baseline`/`bufbasel` data tables). The sets are dumped as raw `.bin` for
now.
