# Open questions

What is left on Might & Magic 1, roughly in order of how much each would
unlock. Everything here is genuinely unresolved; where a route in is known, it
is named.

## 1. `WALLPIX.DTA` sprite geometry

The container and the codec are solved; the internal layout of each
11,200-byte set is not. Each set is a concatenation of sprites of differing
heights, with the *same* layout in all 18 sets — structural boundaries fall at
identical offsets (1776, 1871, 3597, …) and the local repeat distance shifts
along the file (~126, then ~96, then ~95, with a clean 32 near the end where a
brick pattern does render correctly).

Route in: the drawing code — `getshape` `0x14FB`, `nextwall` `0x1878`, `draw`
`0x11D3`, `plot` `0x0F45` — and the `baseline` / `bufbasel` data tables.

**This is the largest thing still fully unknown.**

## 2. The overlay code itself

The overlays' engine calls are all resolved (doc 3) and their event tables are
decoded (doc 8), but the code inside each handler has not been disassembled.
That is where the actual per-map behaviour lives: what a statue does, what a
shop sells, what a trap costs.

Route in: the load address `0xF48F` is established, so a disassembler can be
pointed at the code with correct symbol resolution.

## 3. Which segment the overlay data lands in

The `.OVR` header's data destination, `0xC940`, is solid as an offset — all 197
string pointers in overlay code fall inside `[0xC940, 0xC940 + data size)`. But
it cannot be an offset in either known segment: both hold live content there
(the monster table's tail in one, 51 named routines in the other). A third,
probably run-time-allocated block is the likely answer.

Route in: `getseg_` (`0x061A`) and `ovloader_` (`0x010D`).

Related, and probably the same puzzle: `mondata` points 134 records into the
monster table rather than at its start, and a few late type-`0x03` symbols
(`tp1`…`tp5`, `rum`, `spd1c1`) do not land on plausible boundaries under the
otherwise well-confirmed base `0x10200`. See doc 6.

## 4. What the second maze plane means

Plane 1 of `MAZEDATA.DTA` is per-side and tile-aligned, but its role is a
hypothesis (drawn-versus-blocking) rather than a finding. Doc 4 sets out what is
measured and what the candidate readings predict.

Route in: the renderer.

## 5. The destination fields in the edge transitions

Each of the four edge triples is (unknown, unknown, map type). The first byte
ranges 0–27, the second 0–15, and neither is an index into the 55-map table —
`areaa1` gives its north and south neighbours the same value, which no 5×4 grid
does.

Route in: the shared tail at `0x509D` and `loadnext` (`0x50E3`).

## 6. Record field meanings

Item records (10 stat bytes) and monster records (16) are located and tile
exactly, but the individual fields are not decoded. Mostly a matter of
correlating with in-game values.

## 7. Smaller loose ends

* **`pp4`** declares 20 events and carries the standard dispatcher, so the
  engine really does search 20 ids — but only 10 of its handler words are valid
  addresses, the rest is text. (doc 8)
* **Parameter indices 30, 31 and 32** are never read with a literal index
  anywhere in the engine. (doc 7)
* **13 mask bytes** out of 821 have `01` or `10` in a 2-bit field rather than
  `00` or `11`. (doc 8)
* **`ROSTER.DTA`** is recognised as the character roster and otherwise
  untouched; it is save data and the game rewrites it.
* **The toolchain.** The runtime symbols (`_STKSIZ_`, `_HEAPSIZ_`, `_mbot_`,
  `_mtop_`, `ctp__`, `_ioflg_`, `_PSP_`) identify a mid-1980s DOS C runtime and
  `.RSM` belongs to its linker, but the exact product is not pinned down.
  Knowing it would explain the overlay mechanism and the segment layout
  directly rather than by inference.

## Settled since session 1

For the record, because several of these were wrong at first and the
corrections are the useful part:

| | |
|---|---|
| Overlay load address | `0xF48F`, not the `0xF451` first inferred from header arithmetic |
| `MAZEDATA` indexing | column-major `x*16+y`; session 1 rendered every map transposed |
| Compass | north = +X, east = +Y |
| Maze side value 2 | a door |
| What indexes the event handlers | the packed position `(X << 4) | Y` |
| Parameter block | exactly 50 bytes, every byte attributed to its consumers |
| `demon` | has no per-square events at all |
| `_Eol_ + 2` | coincidence; retracted |
