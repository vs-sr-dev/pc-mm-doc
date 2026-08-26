# Open questions

What is left on Might & Magic 1, roughly in order of how much each would
unlock. Everything here is genuinely unresolved; where a route in is known, it
is named.

## 1. The stat fields

Every record table is located, bounded and counted exactly (doc 6), and none of
the stat fields is decoded:

* **items** — 10 bytes per record, 255 records
* **monsters** — 17 bytes per record, 195 records
* **characters** — 127 bytes per record in `ROSTER.DTA`, 18 slots

This is now the largest single gap, and it is the one the files alone cannot
close: it wants correlation against in-game values, or against the combat code
(`combat`, `figatt`, `shootatt`, `chkmisl`), which is disassemblable but long.

## 2. The overlay handlers, at scale

The idiom is solved and one handler is worked through in doc 8, and
`tools/mm1/disasm.py` will print any of them with engine calls named and string
pointers resolved. What has not been done is the 821-handler sweep: what every
statue, shop, trap and teleporter in the game actually does.

That is a cataloguing job now, not a research one.

## 3. How the twelve wall sprites are placed on screen

`draw` (`0x0F45`) walks the squares in front of the party and, for each one,
picks a sprite and a position out of a dense group of byte tables between
`DS:0x03DB` and `DS:0x0433`, then calls `pdyreal` (`0x0DA7`). The sprite
geometry is solved (doc 5) and the wall lookups are readable, but the tables
themselves — which sprite, at which x and y, for which view cell — are not
decoded.

Route in: `draw` is 654 bytes and already disassembles cleanly; the tables are
adjacent and small.

## 4. Smaller loose ends

* **Parameter indices 30, 31 and 32** are never read with a literal index
  anywhere in the engine. (doc 7)
* **Three mask bytes** out of 821 have `01` or `10` in a 2-bit field rather than
  `00` or `11`: two in `areae2`, one in `areae4`. The other ten such bytes were
  `pp4` and are explained. (doc 8)
* **`pp1`'s four edge triples** match no key in the destination table, so its
  edges resolve to nothing. `pp1` looks unfinished in the same way `pp4` is.
  (doc 7)
* **The 16-bit keys.** The scheme is solved and verified — the same (low, high)
  key format identifies both a destination map and a wall set — but whether the
  two bytes mean anything individually, or are just arbitrary ids, is unknown.
* **The toolchain.** The runtime symbols (`_STKSIZ_`, `_HEAPSIZ_`, `_mbot_`,
  `_mtop_`, `ctp__`, `_ioflg_`, `_PSP_`) identify a mid-1980s DOS C runtime,
  `.RSM` belongs to its linker, and the overlay mechanism is now fully
  described (doc 3) — a 14-byte header with magic `0x00F2`, a 62-byte
  compiler-generated prologue, `_csread_` to load code into the code segment.
  That is a distinctive enough signature to identify the product, but it has
  not been identified. `MM.EXE` carries no version or copyright string.

## Settled

For the record, because several of these were wrong at first and the
corrections are the useful part.

### This session

| | |
|---|---|
| `MM.RSM` alignment | the trailing word is where a symbol **ends**; reading it as the address shifted all 579 symbols by one record |
| Data segment base | `0x109B0`, not the `0x10200` first inferred — which was out by exactly 82 item records, so the item table appeared to fit both |
| Overlay data segment | no third address space: `0xC940` is in the ordinary data segment, `0x110` above the linked data and two bytes above `_Eol_` |
| `WALLPIX` geometry | twelve sprites per set, from the tables `getshape` reads; four depths of left wall, four of right, three frontal, one patch |
| Wall-set selection | three sets per map, chosen by 16-bit key; an out-of-range index is clamped and the art recoloured by `AND 0xAA` |
| Maze plane 1 | not scenery — four per-side lock latches plus four per-tile flags (event, dark, no-magic, no-rest) |
| Edge transitions | the two "unknown" bytes are a 16-bit key into a per-map table; the outdoor grid resolves to its 5 × 4 shape |
| `.OVR` header `+0` and `+12` | a magic number the loader checks, and the entry point it jumps to |
| Item / monster tables | 255 items in two named runs of 85 and 170; 195 monsters, name first |
| `ROSTER.DTA` | 18 records of 127 bytes plus an 18-byte occupancy tail, aliased onto the maze buffer |
| `pp4` | unfinished: the string `DANGER! DUNGEON UNDER CONSTRUCTION.` is written into its handler array |

### Earlier

| | |
|---|---|
| Overlay load address | `0xF48F`, not the `0xF451` first inferred from header arithmetic |
| `MAZEDATA` indexing | `(north/south) * 16 + (east/west)`; session 1 rendered every map transposed |
| Compass | north and east raise the two coordinates; the engine calls them Y and X respectively |
| Maze side value 2 | a door |
| What indexes the event handlers | the packed position |
| Parameter block | exactly 50 bytes, every byte attributed to its consumers |
| `demon` | has no per-square events at all |
| `_Eol_ + 2` | retracted in session 2, reinstated in session 3: `_Eol_` is `0xC93E` and the overlay data really does start two bytes later |
