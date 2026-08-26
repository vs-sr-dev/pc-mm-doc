# 7. The overlay data block

Every `.OVR` carries a data half that is loaded to `0xC940` (doc 3) — an offset
in the ordinary data segment, `0x110` bytes above the end of the linked data
(doc 2). It has three regions, in this order:

```
0xC940   per-map parameters          exactly 50 bytes
0xC972   event count, then the event tables      (doc 8)
         text                        NUL-terminated strings
```

Across the 55 maps this accounts for 37,858 bytes of data against 43,236 bytes
of code, holding **821 event handlers** and **649 text strings**.

## The event-handler table

The count sits at offset 50, right after the parameter block, and the handler
words follow the id and mask arrays (doc 8). Every word falls inside
`[0xF48F, 0xF48F + code size)` — this overlay's own code. Sorpigal's has 24
entries:

```
F4E0 F508 F55D F570 F583 F5A8 F5BB F5CE
F5E1 F6A2 F6BD F6C5 F6CD F6D5 F6DD F6E5
F6ED F6F5 F715 F71D F725 F72D F74C F769
```

The entries are ascending, and a word landing in that range by chance has
probability `code size / 65536`, about 1.3 %, so a run of 24 cannot be
accidental.

Handler counts track how much is going on in a map, which is a good sanity
check on the interpretation:

| map type | handlers |
|---|---|
| towns (`sorpigal`, `dusk`, `algary`, …) | 17–29 |
| caves and dungeons | 14–34 |
| outdoor areas (`areaa1`, `areab2`, …) | 6–10 |

Towns are dense with shops, inns and temples; open countryside has a handful of
transitions and set pieces.

## The parameter block

The first 50 bytes are a fixed header. The engine never touches them directly:
it goes through an indexed accessor — `getod` (`0x0D5B`) reads a byte,
`putod` (`0x0D66`) writes one — with the overlay's data base in `ovdatadr`
(`DS:0x0132`). There are **80 such call sites in the engine and every one uses a
literal index**, all in the range 0–49. That bounds the block exactly, and it
also names each byte by whoever reads it.

| index | consumers | reading |
|---|---|---|
| 0 | `bash`, `blacks`, `food`, `qcast`, `tavern`, `temple`, `unlock`, … | **map identifier** — all 55 maps hold a different value |
| 1 | `loadtype`, written by `alldead` | **map type**: 1 town/cave, 2 outdoor, 3 dungeon |
| 2–7 | `loadtype` | rest of the map-type setup |
| 8–10 | `yplus` | edge transition, leaving **north** |
| 11–13 | `xplus` | edge transition, leaving **east** |
| 14–16 | `ymin` | edge transition, leaving **south** |
| 17–19 | `xmin` | edge transition, leaving **west** |
| 20–28, 33–34, 47 | `encounter` (23–24 also `goretr`) | wandering-monster setup |
| 29 | `mforward` | 70–200, usually 100 |
| 30–32 | — | never read with a literal index |
| 35–43 | `ddal` (38 also `goz34`, `zerospls`) | spell handling |
| 44 | `rest` | 8–40 |
| 45, 48, 49 | `bash`, `trap`, `unlock` | lock, trap and bash difficulty |
| 46 | `ddal`, `draw` | |

Index 1 is exact: all 14 towns and caves hold 1, all 20 outdoor maps hold 2,
all 21 named dungeons hold 3.

### The four edge transitions — solved

Each is three bytes, and each has a routine that parks the entry coordinate at
the opposite edge before reading them:

| routine | sets | meaning |
|---|---|---|
| `yplus` `0x4FF8` | `Y := 0` | walked off the **north** edge (+Y), arrive at the south edge |
| `xplus` `0x5022` | `X := 0` | walked off the **east** edge (+X), arrive at the west edge |
| `ymin` `0x504C` | `Y := 15` | walked off the **south** edge (−Y), arrive at the north edge |
| `xmin` `0x5076` | `X := 15` | walked off the **west** edge (−X), arrive at the east edge |

All four load the triple into `al`, `bl` and `bp` and jump to the shared tail
`loadnext` (`0x509D`), which prints ` PLEASE WAIT ` and calls `loadmaze`
(`0x0D35`). The lookup itself is the helper at `0x0D71`:

```
0D71  mov ah, bl                  ; ah = second byte, al = first
0D73  shl bp, 1                   ; bp = map type * 2
0D75  mov bx, [bp + 0x173]        ; where to start searching, per map type
0D79  cmp ax, [bx + 0x17b]        ; the per-map key table
0D7D  je  found
0D7F  add bx, 2
0D82  jmp 0D79
found: shr bx, 1                  ; bx is now the destination map number
```

So the two "unknown" bytes are not coordinates and not an index. They are a
**16-bit key**, `(second << 8) | first`, looked up in a 55-entry key table at
`DS:0x017B`. The third byte, the map type, picks where the linear search starts,
from three offsets at `DS:0x0173`:

| map type | search starts at | which is |
|---:|---:|---|
| 1 | map 0 | `sorpigal`, the first town |
| 2 | map 14 | `areaa1`, the first outdoor map |
| 3 | map 34 | `doom`, the first dungeon |

Keys are unique *within* a type group — 14, 20 and 21 distinct values for 14, 20
and 21 maps — and repeat freely across groups, which is exactly the freedom the
type-scoped search buys.

### Verifying it

Decode all 220 edges and ask whether they agree with each other. If map A's
north edge leads to B, B's south edge should lead back to A:

```
62 reciprocal, 150 self (map edge), 4 one-way, 4 unresolved, of 220
```

The 150 self-links are the sealed maps — every town, cave and dungeon names
itself on all four edges — plus the outer border of the outdoor grid. The four
one-way links are all `pp2` → `dragad`, a deliberate exit. The four unresolved
are `pp1`, whose triples match no key; `pp1` is unfinished in other ways too
(doc 8).

Nothing else disagrees, and the outdoor maps assemble into the 5 × 4 grid their
names promise, with `areaa1` in the north-west corner:

```
  areaa1   N=areaa1   E=areab1   S=areaa2   W=areaa1
  areaa2   N=areaa1   E=areab2   S=areaa3   W=areaa2
  areab1   N=areab1   E=areac1   S=areab2   W=areaa1
  ...
  areae4   N=areae3   E=areae4   S=areae4   W=aread4
```

An earlier version of this document reported that `areaa1` named its north and
south neighbours identically, "which no 5×4 grid does". It names *itself* to the
north, because there is no map north of it.

## Text

Plain NUL-terminated ASCII, uppercase, with `0x0D` as an explicit line break.
The strings are written for a **40-column display**: where a message is longer
than one line and has no explicit break, it relies on the engine wrapping hard
at column 40. Stored, one of Sorpigal's blacksmith lines runs together as

```
"DISTINGUISHED TRAVELERS, YOU'VE COME TOTHE RIGHT PLACE. …
```

and laid out at 40 columns it breaks exactly on the word boundary:

```
A MAN WEARING A LEATHER APRON SPEAKS:
"DISTINGUISHED TRAVELERS, YOU'VE COME TO
THE RIGHT PLACE.CAN I HELP YOU (Y/N)?"
```

24 of the stored segments exceed 40 characters and depend on this. (The missing
space in `PLACE.CAN` is in the original data.)

## Reading it

```sh
python tools/mm1/ovr_params.py            # index -> consumers
python tools/mm1/ovr_params.py sorpigal   # one map's 50 bytes, annotated
python tools/mm1/map_links.py             # every map's four neighbours
python tools/mm1/map_links.py --check     # the reciprocity test above
python tools/mm1/ovr_text.py sorpigal     # handler table + text
```

The extracted text is game content, so it is not committed here — the tool
reads your own copy. See [`notes/README.md`](../../notes/README.md).
