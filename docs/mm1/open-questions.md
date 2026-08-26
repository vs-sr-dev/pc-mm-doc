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

## 1b. What indexes the event-handler table

Each overlay's data block holds a table of pointers into its own code — 816
handlers across the 55 maps (doc 7). The engine receives a pointer to it at
overlay entry. What selects an entry is not traced: the natural guess is a
per-square event id, which would tie the table to the maze data, but that is a
guess. Answering this is probably the single highest-value next step, because it
connects map squares to map behaviour.

## 1c. The per-map parameter block

The variable-length block that precedes the handler table (0x3F to 0x77 bytes)
is not decoded. It plausibly holds the map's monster set, encounter rates,
starting position and light level, but nothing is established.

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

## 6. The `mondata` and second-base anomaly

`mondata` points 134 records into the monster table rather than at its start,
and a handful of late data symbols (`tp1`…`tp5`, `rum`, `spd1c1`) do not land on
plausible boundaries under the otherwise well-confirmed data base `0x10200`.
Something about the data segment's structure is still not understood. See
doc 6.

## 7. `ROSTER.DTA`

Recognised as the character roster and left alone — it is save data and the game
rewrites it. Character record layout is not documented yet.

## 8. Which compiler and linker

The runtime symbols (`_STKSIZ_`, `_HEAPSIZ_`, `_mbot_`, `_mtop_`, `ctp__`,
`_ioflg_`, `_PSP_`) identify a mid-1980s DOS C runtime and the `.RSM` extension
belongs to its linker, but the exact toolchain has not been pinned down. Knowing
it would explain the overlay mechanism and the two-segment layout directly
rather than by inference.
