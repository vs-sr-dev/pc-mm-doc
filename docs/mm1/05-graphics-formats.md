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
four repeats — the break-even point for a three-byte escape.

`tools/mm1/mmlib.py` implements both directions and the encoder round-trips.

## The decoder, and what it says about pixel order

The engine's decoder is `nextwall` (`0x1504`), entered through the nine-byte
stub `uncomp` (`0x14FB`) which points the source at `compbuf_` and resets the
read cursor. Stripped of bookkeeping it is:

```
bp = 0                          ; running destination offset
[eocol] = width * height        ; set by the caller
loop:
    fetch one literal, or an escape triple giving a count
    store the byte at es:[bp + di]
    bp += [widthh_]             ; <- next row, not next byte
    if bp >= [eocol]: bp = 0; di += 1     ; end of column, move one byte right
```

Consecutive bytes of the decompressed stream walk **down a column**, while the
destination is an ordinary row-major bitmap of `widthh_` bytes per row. So the
stored order is column-major:

```
byte index = column * height + row
```

which is what autocorrelation had already suggested — the strongest repeat
distance in a decoded `SCREEN` file is 200 (the height), not 80 (the row
width). Four pixels per byte, most significant pair leftmost. Palette is CGA
palette 1, high intensity: black, cyan, magenta, white.

The same two variables drive every picture in the game, so the callers name the
geometry outright: `treaspix` sets `widthh_ = 26`, `eocol = 2496`; `monstpix`
and `titlescr` set `80` and `16000`.

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

### `MONPIX.DTA`

2,496 bytes = 26 byte-columns × 96 rows = **104 × 96 pixels**, the geometry
`treaspix` sets. All 76 decode cleanly: monsters, plus a few scene portraits
(treasure chests, a castle, a throne room).

76 portraits serve 195 monster entries, so pictures are shared.

### `WALLPIX.DTA` — twelve sprites per set

Each 11,200-byte set is **twelve sprites of different sizes**, decoded one after
another out of a single RLE stream. `getshape` (`0x128C`) does it:

```
di = destination base                    ; in the off-screen video segment
call uncomp                              ; shape 0: reset the source cursor
bp = 11                                  ; and eleven more
bx = 2
loop:
    di       = [0x0D02]                  ; running destination offset
    widthh_  = [bx + 0x0CD2]             ; width in bytes
    eocol    = widthh_ * [bx + 0x0CEA]   ; times height
    [0x0D02] += eocol
    call nextwall                        ; decode one shape, advance the cursor
    bx += 2; dec bp; jnz loop
```

Two parallel twelve-entry word tables at `DS:0x0CD2` (widths, in bytes) and
`DS:0x0CEA` (heights) give the geometry, and the source cursor carries across
calls, so the sprites are simply concatenated in the stream:

| # | width | height | bytes | offset in the set |
|---:|---:|---:|---:|---:|
| 0 | 8 B = 32 px | 128 | 1024 | 0 |
| 1 | 10 B = 40 px | 96 | 960 | 1024 |
| 2 | 6 B = 24 px | 64 | 384 | 1984 |
| 3 | 4 B = 16 px | 32 | 128 | 2368 |
| 4 | 8 B = 32 px | 128 | 1024 | 2496 |
| 5 | 10 B = 40 px | 96 | 960 | 3520 |
| 6 | 6 B = 24 px | 64 | 384 | 4480 |
| 7 | 4 B = 16 px | 32 | 128 | 4864 |
| 8 | 44 B = 176 px | 96 | 4224 | 4992 |
| 9 | 24 B = 96 px | 64 | 1536 | 9216 |
| 10 | 12 B = 48 px | 32 | 384 | 10752 |
| 11 | 4 B = 16 px | 16 | 64 | 11136 |

`8 · 128 + 10 · 96 + … + 4 · 16 = 11,200` — the set size exactly, with nothing
left over.

The size ladder repeats: 0–3 and 4–7 have identical dimensions (128, 96, 64 and
32 rows), then 8–10 step down again (176 × 96, 96 × 64, 48 × 32), then a 16 × 16
patch. Rendered, that reads directly: **0–3 and 4–7 are side walls at four
depths, slanting opposite ways** — the left and right sides of the corridor —
and **8–10 are the wall you face, at three depths**, flat frontal panels of
brickwork, doorways and torches.

The slant is what separates the two groups, not the texture. Comparing sprite 0
against a horizontally mirrored sprite 4 gives 93 % equal pixels in set 0 but
only 73 % in set 1 and 36 % in set 5, so the two sides share a mirrored outline
and carry independent detail rather than being one bitmap flipped.

This is also the second, independent fix on the data segment base (doc 2):
searching the whole file for a base at which those 24 words total 11,200 with
plausible values returns exactly one, `0x109B0`, and the sprites render.

### Which set a map uses

A map loads **three** wall sets, not one. `loadtype` (`0x4639`) reads parameter
bytes 2-7 of the overlay as three 16-bit keys -- the same (low, high) encoding
the map destinations use (doc 7) -- and hands each to `getshape` along with the
map type from parameter 1:

```
key  = (getod(3) << 8) | getod(2);  list = getod(1);  setn = 1;  getshape()
key  = (getod(5) << 8) | getod(4);  list = getod(1);  setn = 2;  getshape()
key  = (getod(7) << 8) | getod(6);  list = getod(1);  setn = 3;  getshape()
```

`getshape` resolves the pair: the map type picks one of three key lists
(pointers at `DS:0x043B`, starting numbers at `DS:0x0441`) and the key's
position in that list, added to the starting number, is the set.

All 165 references -- 55 maps x 3 -- resolve, all of them inside 0..17, and all
18 sets are used. The grouping falls out cleanly:

| sets | used by |
|---|---|
| 0-2 | the five towns |
| 3-5 | the nine caves |
| 6-13 | the outdoor grid |
| 14-17 | the named dungeons |

An index past the end of the 18 sets is clamped to set 0 and raises a flag, and
`getshape` then ANDs the whole 11,200-byte set with `0xAA`. That forces the low
bit of every 2-bit pixel off, collapsing the four colours to two -- the same
artwork drawn in a darker two-colour variant. `doom` is the only map that uses
it.

```sh
python tools/mm1/extract_gfx.py out       # every picture in the game -> PNG
python tools/mm1/wallsets.py              # each map's three wall sets
python tools/mm1/wallsets.py --usage      # which maps use each set
```
