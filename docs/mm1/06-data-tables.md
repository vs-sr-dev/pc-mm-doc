# 6. Data tables inside `MM.EXE`

All of these live in the data segment, which starts at file offset `0x10200`
(doc 2). Offsets below are given both ways.

## Items — `itemlow` and `itemhigh`

Two tables of fixed 24-byte records:

```
+0   14 bytes   name, space-padded
+14  10 bytes   stats
```

| symbol | data offset | file offset | records |
|---|---|---|---:|
| `itemlow` | `0x9972` | `0x19B72` | 170 |
| `itemhigh` | `0xA962` | `0x1AB62` | 82 |

252 items in total, and the two tables tile exactly: `itemlow` runs for
`170 × 24 = 0xFF0` bytes and ends precisely at `itemhigh`, which runs for
`82 × 24 = 0x7B0` bytes and ends precisely where the monster names begin.

```
  0 SPEAR           07 00 00 00 00 00 00 0f 06 00
  1 SHORT SWORD     06 00 00 00 00 00 00 14 06 00
  2 MACE            02 00 00 00 00 00 00 28 06 00
...
166 DRAGON SHIELD   0a 58 0a ff 5c 14 1f 40 00 07
167 ROPE & HOOKS    00 01 00 ff 3a 1e 00 0a 00 00
168 TORCH           00 01 00 ff 04 01 00 02 00 00
169 LANTERN         00 01 00 ff 04 0a 00 14 00 00
--- itemhigh ---
  0 10 FOOT POLE    00 01 00 00 00 00 00 0a 00 00
  1 GARLIC          00 01 00 00 00 00 00 05 00 00
...
 81 (USELESS ITEM)  00 01 00 00 00 00 00 00 00 00
```

The ten stat bytes are not yet decoded. Byte `+21` looks like a price or weight
(`0x0F` spear, `0x14` short sword, `0x28` mace) and byte `+22` is small and
class-like, but that is an observation, not a finding.

## Monsters — `mondata`

Fixed 32-byte records holding a 15-character name field at record offset `+16`:

```
+0   16 bytes   stats
+16  15 bytes   name, space-padded
+31   1 byte    padding
```

Names run at file `0x1B312 + 32k` for **k = 0…194 — 195 monsters**, ending just
before the hint strings at `0x1CB6F`.

```
  0 FLESH EATER     20 06 00 02 02 06 01 07 32 00 ...
  ...
134 STORM GIANT     00 3c 08 06 06 10 70 17 00 80 87 11 00 00 30 40
135 12 HEADED HYDRA 01 64 09 1e 02 0e 10 27 c6 00 a7 00 13 28 26 17
136 INVISIBLE THING 00 46 0a 0a 0c 10 e0 2e 7f 00 83 00 0e 19 a2 2c
  ...
194 OKRIM           01 32 08 0c 03 0f dc 05 ff 00 01 09 00 00 f0 41
```

Two caveats, both unresolved:

* The symbol `mondata` (`0xC1C2`, file `0x1C3C2`) is **not** the first record —
  it sits at record 134, `STORM GIANT`. Whether the table is split like the item
  tables, or `mondata` is a base for one particular lookup, needs the code.
* The first record's stat half occupies the same 16 bytes as the tail of the
  last `itemhigh` record. The name-based tiling above is exact, so the record
  boundary is right; where the *stats* for monster 0 come from is not.

195 monsters share only 76 portraits in `MONPIX.DTA`, so pictures are reused.

## Hints

A block of plain NUL-terminated strings at file `0x1CB6F` onwards — the hints
given by fortune tellers and signs:

```
SEE MAN IN CAVE BELOW (1,2)        THE MAGIC TOTAL IS 34
CHECK WALLS NEAR (12,3)            ALL PORTALS ARE CONNECTED
STATUE AT (2,4) IS YOUR FIRST JOB  SORPIGAL HAS 8 STATUES
SEEK QUESTS BEHIND MOONS           THE BROTHERS LIVE BY DOCKS
DUE NORTH IS THE CAVE OF SQUARE MAGICTHE ICE PRINCESS HAS THE KEY
TELGORAN IS IN S.E. MAZE           VARN IS NOT WHAT IT APPEARS TO BE
DRAGADUNE HOLDS MANY GEMS          THE INNER SANCTUM IS A MYTH
```

## Other tables located but not decoded

| symbol | data offset | file offset | note |
|---|---|---|---|
| `tp1`…`tp5` | `0xC255`–`0xC416` | `0x1C455`–… | five blocks, ~125 bytes each |
| `rum` / `endtipsc` | `0xC5DC` | `0x1C7DC` | two names, same address |
| `spd1c1`, `spd2c1` | `0xC63A`, `0xC698` | | 94 bytes apart |
| `baseline`, `bufbasel` | `0x50A6`, `0x5238` | | wall-rendering tables (doc 5) |
| `compbuf_`, `pix_` | `0x90B8`, `0x90BA` | | decompression scratch buffers |
| `scrfile_` | `0x917A` | | screen-filename buffer |

With base `0x10200` these last few land inside the monster-name region rather
than at plausible table starts. Either they are runtime buffers whose file image
is irrelevant, or a second base applies to part of the data segment. Unresolved.

## Filenames and the map table

```
data 0x07B7   "Error %d loading overlay: %s$"
data 0x07D6   "mazedata.dta"
data 0x07E3   "roster.dta"       (also 0x07EE)
data 0x07F9   "wallpix.dta"
data 0x0805   "monpix.dta"
data 0x085C   "gacard.dta"
data 0x0A07   the 55 map names, NUL-terminated, back to back
```
