# Open questions

Ordered by how much they would unlock.

## 1. The overlay code (`*.OVR`)

The overlays' engine calls are all resolved (doc 3), but the code between them
has not been disassembled. This is where all per-map behaviour lives: which
square triggers which event, every piece of map text, treasure and encounter
placement, and the transitions between maps. It is by far the biggest remaining
piece.

The way in is now open: the load address `0xF48F` is established, so a
disassembler can be pointed at the code with correct symbol resolution. The
entry stub, identical in all 55 files, registers a dispatch table at code offset
`+0x12` (`0xF4A1`) and the data base `0xC940`.

Two header fields remain unexplained: `+0` (always `0x00F2`) and `+12` (always
`0xF451 + code size`, i.e. 62 bytes below the code destination). Nothing
observed so far depends on either.

## 1b. The per-map parameter block

Bounded at exactly 50 bytes and every byte attributed to the routines that read
it (doc 7), with index 0 identified as the map id and index 1 as the map type.
What remains is the encoding of individual fields — in particular the first two
bytes of each of the four edge-transition triples, which name the destination
map somehow but not by its index in the 55-map table. Disassembling the shared
tail at `0x509D` and `loadnext` (`0x50E3`) should settle it.

Indices 30, 31 and 32 are never read with a literal index anywhere in the
engine, which is worth explaining on its own.

## 1c. Two maps that do not fit the event layout

`demon` uses a different dispatcher shape, and `pp4` declares 20 events but has
only 10 valid handler words. Both need looking at individually. See doc 8.

## 2. `WALLPIX.DTA` sprite geometry

The container and the codec are solved; the internal layout of each 11,200-byte
set is not. Each set is several sprites of differing heights, with the same
layout in all 18 sets (see doc 5). The sprite table is almost certainly derived
from the drawing code — `getshape` `0x14FB`, `nextwall` `0x1878`, `draw`
`0x11D3`, `plot` `0x0F45` — and the `baseline` / `bufbasel` data tables.

## 3. What the second maze plane means

Plane 1 of `MAZEDATA.DTA` is per-side and tile-aligned, but its role is a
hypothesis (drawn-vs-blocking) rather than a finding. Confirming it means
reading the renderer. See doc 4 for what is measured and what the two candidate
readings predict.

## 4. Compass orientation

The maze bit layout is fixed as (+X, −X, +Y, −Y). Which of those is north is
not determined by the file. The `LOCATION:` / `FACING:` display code, or a
cross-check against a known in-game position, would settle it.

## 5. Record field meanings

Item records (10 stat bytes) and monster records (16 stat bytes) are located and
tiled exactly, but the individual fields are not decoded. Doing so is mostly a
matter of correlating with in-game values.

## 6. Which segment the overlay data lands in

The `.OVR` header's data destination, `0xC940`, is solid as an offset — all 197
string pointers in overlay code fall inside `[0xC940, 0xC940 + data size)`. But
it cannot be an offset in either known segment: both hold live content there
(the monster table's tail in one, 51 named routines in the other). A third,
probably run-time-allocated block is the likely answer, and `getseg_` (`0x061A`)
plus `ovloader_` (`0x010D`) are where to look. See doc 2.

Related and probably the same puzzle: `mondata` points 134 records into the
monster table rather than at its start, and a few late type-`0x03` symbols
(`tp1`…`tp5`, `rum`, `spd1c1`) do not land on plausible boundaries under the
otherwise well-confirmed base `0x10200`. See doc 6.

## 7. `ROSTER.DTA`

Recognised as the character roster and left alone — it is save data and the game
rewrites it. Character record layout is not documented yet.

## 8. Which compiler and linker

The runtime symbols (`_STKSIZ_`, `_HEAPSIZ_`, `_mbot_`, `_mtop_`, `ctp__`,
`_ioflg_`, `_PSP_`) identify a mid-1980s DOS C runtime and the `.RSM` extension
belongs to its linker, but the exact toolchain has not been pinned down. Knowing
it would explain the overlay mechanism and the two-segment layout directly
rather than by inference.
