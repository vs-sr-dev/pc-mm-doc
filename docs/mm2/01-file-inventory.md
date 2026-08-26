# 1. File inventory — Might & Magic II

94 game files: one executable, fourteen code overlays, six display drivers, ten
`.DAT` tables, a font, and 31 pictures shipped twice over. (The GOG directory
also holds DOSBox, the manual and installer leftovers; those are not counted.)

This is a **first pass**. It records what is measured; several formats are
identified but not decoded, and those are marked.

| File | Size | Role |
|---|---:|---|
| `MM2.EXE` | 77,824 | The game. DOS MZ executable, **500 relocations**. |
| `*.OVL` | 2,784–17,184 | Fourteen code overlays, named by **function**. |
| `CGA.DRV` | 3,187 | Display driver, 4-colour CGA. |
| `EGA.DRV` | 5,601 | Display driver, 16-colour EGA. |
| `HGA.DRV` | 3,283 | Display driver, Hercules. |
| `MCGA.DRV` | 3,110 | Display driver, MCGA. |
| `TGA.DRV` | 3,180 | Display driver, Tandy. |
| `TIMER.DRV` | 759 | Timer driver. |
| `MM2.CH` | 1,024 | **The font.** 128 glyphs, 8×8, 1 bit per pixel, ASCII-indexed. |
| `ITEMS.DAT` | 5,120 | **256 items**, 20 bytes each: 12-byte name, 8 stat bytes. Plain text. |
| `MONSTERS.DAT` | 5,702 | Monster table. Compressed — see below. |
| `SPELLS.DAT` | 192 | Spell table. 96 words, if the stride is 2. |
| `STR.DAT` | 4,700 | Strings, presumably. Compressed. |
| `ATTRIB.DAT` | 1,768 | Compressed. |
| `MAP.DAT` | 18,748 | The maps. Compressed. |
| `EVENTSI.DAT` | 49,609 | **Indoor events.** Compressed. |
| `EVENTSO.DAT` | 25,797 | **Outdoor events.** Compressed. |
| `DEFAULT.DAT` | 780 | The shipped starting party: **6 records of 130 bytes**. |
| `ROSTER.DAT` | 8,292 | Character roster, same 130-byte record. Save data. |
| `*.16` / `*.4` | 496–168,257 | 31 pictures, each shipped as 16-colour **and** 4-colour. |

## The overlays are named by function, not by map

```
1MENU1   1MENU2   1RETINN  2BRAIN   2CAST1   2CAST2   2CAVES
2CMDS    2COMBAT  2MISC    2MISC2   2PLAY    2SMITH   2TEMPLE
```

Might & Magic 1 shipped 55 overlays, one per map, each holding that map's
events as compiled code. Might & Magic 2 ships fourteen, and they are the
*subsystems* — combat, the smithy, the temple, spellcasting, the menus. The
per-map behaviour has moved out of code entirely and into `EVENTSI.DAT` and
`EVENTSO.DAT`. See [fingerprints](../comparison/fingerprints.md).

They also carry **no header**. Thirteen of the fourteen begin `55 8B EC` —
`push bp` / `mov bp, sp`, the entry of a C function — so they are raw code
images entered at offset 0. Might & Magic 1's overlays had a validated 14-byte
header with a magic word, two load descriptors and an entry point. `1MENU1.OVL`
is the exception and begins `2B C7 00 00 74 C6`; it has not been looked at.

## The executable

```
e_cs:e_ip     077D:0488
e_ss:e_sp     1822:0800
e_cparhdr     0x0080   -- a 2,048-byte header
relocations   500
```

500 relocations against Might & Magic 1's **three**. That single number is the
architectural difference: M&M1 was two hand-rolled segments that computed their
own addresses and could not be relinked without invalidating all 55 overlays;
M&M2 is an ordinary relocatable multi-segment program built by a normal
toolchain.

There is no `.RSM` — no stray symbol map this time. That is a real loss: almost
everything in the M&M1 documentation was reached through its 579 shipped
symbols.

## Graphics ship per adapter

31 names, each present as `NAME.4` and `NAME.16`, and all 31 pairs are complete:

```
BOOK CASTLE CASTLEB CASTLEF CASTLET CAVE CAVEB CAVEF CAVET DESERT DISK
ENDGAME GLOBE MASTER MONSTERS NWCP OCEAN OUTB OUTDOOR1 OUTDOOR2 OUTDOOR3
OUTF SKY SWAMP THROW TOWN TOWNB TOWNF TOWNT TUNDRA XFER
```

M&M1 shipped one set of CGA art and converted it to EGA and Tandy at runtime.
M&M2 ships the artwork twice and picks a `.DRV` to draw it with. The `B`, `F`
and `T` suffixes look like background / foreground / top layers of the same
scene, and `OUTDOOR1..3`, `DESERT`, `SWAMP`, `TUNDRA`, `OCEAN`, `SKY` are the
outdoor terrain sets.

## What is compressed, and what is not

Entropy, in bits per byte, over the whole file:

| file | bits/byte | |
|---|---:|---|
| `ROSTER.DAT` | 1.71 | plain |
| `DEFAULT.DAT` | 2.55 | plain |
| `MM2.CH` | 4.36 | plain |
| `ITEMS.DAT` | 5.40 | plain |
| `ATTRIB.DAT` | 7.41 | compressed |
| `MAP.DAT` | 7.50 | compressed |
| `MONSTERS.DAT` | 7.56 | compressed |
| `EVENTSI.DAT`, `EVENTSO.DAT` | 7.72 | compressed |
| `STR.DAT` | 7.80 | compressed |

Everything above 7.4 bits per byte is genuinely compressed, not merely
obfuscated: a single-byte XOR would leave the histogram shape, and therefore the
entropy, unchanged. It is also **not** M&M1's codec — that one leaves long
literal runs and an obvious `0x7B` escape, and neither is present.

Two corroborating facts. `MAP.DAT` is 18,748 bytes, whose only divisors between
16 and 2,047 are 43, 86, 109, 172, 218 and 436 — no plausible fixed map size, so
it is not a flat array the way M&M1's `MAZEDATA.DTA` was. And the picture files
open with a size-like word which is *not* a plain decompressed length: across
the 31 pairs the `.16`/`.4` ratio runs from 1.00 to 2.00, where a straight
2-bits-to-4-bits widening of the same image would give exactly 2 every time.

**Decoding the compression is the gate to everything else in M&M2.** The route
in is the drivers and `2PLAY.OVL`, which are code and can be disassembled with
the same tooling used on M&M1.

## What is already readable

**`ITEMS.DAT`** — 5,120 / 20 = 256 exactly, and the names are plain ASCII:

```
  0  BLANK         00 00 f0 00 00 00 00 00
  1  Small Club    00 00 00 00 02 00 01 00
  2  Small Knife   00 10 00 00 03 00 05 00
  4  Dagger        00 10 00 00 04 00 08 00
 93  Sling         00 18 00 00 05 00 0f 00
100  Quiet Sling   00 18 bf bd 05 00 dc 05
255  Useless Item  00 00 f0 00 00 00 01 00
```

M&M1's item table was 255 records of 24 bytes with a 14-character name; M&M2's
is 256 of 20 with a 12-character name. Both are name-first, both fill the last
slot with a joke — `(USELESS ITEM)` there, `Useless Item` here. The stat bytes
are not decoded.

**`MM2.CH`** — 1,024 / 8 = 128 glyphs of 8×8, one bit per pixel, most
significant bit leftmost, indexed straight by ASCII code: glyph 65 is `A`,
glyph 48 is `0`. M&M1 had no font file; it built one in memory at startup.

**`DEFAULT.DAT`** — 780 / 130 = 6 records exactly, name first, starting with
`Sir Felgar`. `ROSTER.DAT` uses the same 130-byte record, with names found at
offsets 0, 130, 260, 390, 520, 650 and then 3120 — so the shipped roster has the
six-character default party in the first slots and empty ones after. Its 8,292
bytes are 63 records of 130 plus 102 left over, which the record size alone does
not explain.

```sh
export MM2_DATA="/path/to/Might and Magic 2"

python tools/mm2/dump_items.py            # the 256 items
python tools/mm2/dump_items.py sling      # or just the ones you want
python tools/mm2/dump_font.py             # the font as ASCII art
python tools/mm2/dump_font.py --png out/mm2font.png
```
