# 6. Data tables inside `MM.EXE`

All of these live in the data segment, which starts at file offset `0x109B0`
(doc 2). Offsets below are given both ways. Sizes are exact, because the symbol
map records where each symbol ends as well as where it starts.

## Items — `itemlow` and `itemhigh`

One table of fixed 24-byte records, with a named split partway through:

```
+0   14 bytes   name, space-padded
+14  10 bytes   stats
```

| symbol | data offset | file offset | size | records |
|---|---|---|---:|---:|
| `itemlow` | `0x917A` | `0x19B2A` | 2,040 | **85** |
| `itemhigh` | `0x9972` | `0x1A322` | 4,080 | **170** |

255 items in total, and the two runs tile exactly: `itemlow` is 85 × 24 bytes
and ends precisely at `itemhigh`, which is 170 × 24 and ends precisely at
`mondata`. Nothing is left over anywhere.

```
  0 CLUB           00 00 00 00 00 00 00 01 03 00
  1 DAGGER         04 00 00 00 00 00 00 05 04 00
  2 HAND AXE       06 00 00 00 00 00 00 0a 05 00
  3 SPEAR          07 00 00 00 00 00 00 0f 06 00
  4 SHORT SWORD    06 00 00 00 00 00 00 14 06 00
...
 84 OBSIDIAN BOW   00 ff 00 ff 50 03 07 d0 03 00   <- last of itemlow
--- itemhigh ---
  0 STAFF          01 00 00 00 00 00 00 1e 08 00
  1 GLAIVE         07 00 00 00 00 00 00 50 0a 00
  2 BARDICHE       07 00 00 00 00 00 00 50 0a 00
...
167 THUNDRANIUM    00 01 00 18 0f fa 27 10 00 00
168 KEY CARD       00 01 00 00 00 00 00 00 00 00
169 (USELESS ITEM) 00 01 00 00 00 00 00 00 00 00
```

The boundary is a real one in the content, not just a symbol: `itemlow` runs
from `CLUB` through the one-handed weapons and every bow, ending at
`OBSIDIAN BOW`; `itemhigh` opens with the two-handed weapons (`STAFF`,
`GLAIVE`, `BARDICHE`, `HALBERD`, …) and carries on through armour, accessories
and quest items to `(USELESS ITEM)`.

The ten stat bytes are **not decoded**. Bytes `+21` and `+22` climb
monotonically through each weapon run and look like a price or a weight; that is
an observation, not a finding.

## Monsters — `mondata`

Fixed 32-byte records, name first:

```
+0   15 bytes   name, space-padded
+15  17 bytes   stats
```

| symbol | data offset | file offset | size | records |
|---|---|---|---:|---:|
| `mondata` | `0xA962` | `0x1B312` | 6,240 | **195** |

6,240 / 32 = 195 exactly, and the table ends precisely where the hints begin.
The name field is 15 bytes because the longest name, `12 HEADED HYDRA`, uses
all 15; byte `+15` varies across records (48 different values), so it is a stat
and not a terminator.

```
  0 FLESH EATER     00 02 02 06 01 07 32 00 00 00 00 82 00 00 10 04
  3 GNOME           32 03 05 06 01 0c 7d 00 02 14 01 00 84 00 06 08
134 STORM GIANT     01 64 09 1e 02 0e 10 27 c6 00 a7 00 13 28 26 17
194 OKRIM           01 50 0b 06 04 12 20 4e 27 00 8b 00 13 5f 2a 34
```

The 17 stat bytes are **not decoded**. 195 monsters share only 76 portraits in
`MONPIX.DTA`, so pictures are reused.

Two problems reported by an earlier version of this document — that `mondata`
sat at record 134 rather than at the start, and that monster 0's stats overlapped
the last item record — were both artefacts of the wrong segment base and the
mis-aligned symbol map (doc 2). Neither survives.

## Hints and rumours

Six blocks of plain NUL-terminated strings, back to back, all named:

| symbol | data offset | size | first string |
|---|---|---:|---|
| `tp1` | `0xC1C2` | 147 | `SEE MAN IN CAVE BELOW (1,2)` |
| `tp2` | `0xC255` | 125 | `SEEK QUESTS BEHIND MOONS` |
| `tp3` | `0xC2D2` | 126 | `ATTACKS SHOULD BE CONCENTRATED` |
| `tp4` | `0xC350` | 110 | `TELGORAN IS IN S.E. MAZE` |
| `tp5` | `0xC3BE` | 88 | `AGAR LIVES BEHIND THE INN` |
| `rum` | `0xC416` | 454 | `ALL PORTALS ARE CONNECTED` |

`tp1`–`tp5` are the five tip sets a fortune teller draws from; `rum` is the
tavern rumour pool, and `endtipsc` marks the end of the whole run.

## The character roster — `ROSTER.DTA`

2,304 bytes: **18 records of 127 bytes**, then an 18-byte tail. That is not a
guess — `roster` starts at `DS:0x3CFA` and `endroster` at `DS:0x45E8`, exactly
`18 × 127 = 2,286` bytes apart, and the tail runs from there to `DS:0x45FA`.

The shipped file holds the six pre-generated characters and one occupancy byte
per slot:

```
   0 CRAG THE HACK    01 02 02 01 01 08 08 11 11 08 08 0f 0f 0d 0d 0f
   1 SIR GALAND       01 01 01 03 02 0a 0a 10 10 0d 0d 10 10 0a 0a 0d
   2 ZENON III        01 03 03 05 03 0d 0d 11 11 05 05 0f 0f 0f 0f 0d
   3 SWIFTY SARG      01 02 02 04 06 09 09 0d 0d 06 06 0d 0d 0e 0e 0e
   4 SERENA           02 01 01 01 04 0a 0a 0c 0c 0f 0f 0d 0d 0c 0c 0a
   5 WIZZ BANE        01 01 01 02 05 10 10 08 08 0a 0a 0d 0d 11 11 0a
   6..17  empty
   tail  01 01 01 01 01 01 00 00 00 00 00 00 00 00 00 00 00 00
```

The record fields are not decoded. This is save data and the game rewrites it,
through `readrost_` and `writrost_`.

The roster buffer is **the same memory as the maze**: `base1` and `base2`, the
two 256-byte maze planes, sit at `DS:0x3CFA` and `DS:0x3DFA`, i.e. on top of the
first 512 bytes of the roster buffer. The two are never live at once — you are
either walking a map or managing characters.

## Other tables, now placed

| symbol | data offset | size | what it is |
|---|---|---:|---|
| `font` / `narrowfont` | `0x48FC` / `0x4D0C` | 1040 / 520 | 130 characters at 8 bytes, then the same 130 at 4 |
| `clrset` | `0x4F14` | 1 | the current map's colour set, from the table at `DS:0x013C` |
| `bufbasel` | `0x50A6` | 402 | 200 screen-row offsets, one per scanline |
| `compbuf_` | `0x5238` | 16,000 | the RLE input buffer; `uncomp` reads from here |
| `scrfile_` | `0x90BA` | 192 | the screen filename buffer — it contains `screen0` |
| `widthh_` / `eocol` | `0x0D04` / `0x0D09` | 2 / 2 | decoder geometry (doc 5) |

Those are runtime buffers, which is why the file image holds 16 KB of zeroes
between `bufbasel` and `itemlow`. That gap is itself a check on the base.

## Filenames and the map table

```
data 0x0007   "Error %d loading overlay: %s$"
data 0x0026   "mazedata.dta"
data 0x0033   "roster.dta"      (also 0x003E)
data 0x0049   "wallpix.dta"
data 0x0055   "monpix.dta"
data 0x00AC   "gacard.dta"
data 0x0257   the 55 map names, NUL-terminated, back to back
```
