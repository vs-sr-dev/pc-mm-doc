# Cross-title fingerprints

The point of documenting more than one Might & Magic is to see what New World
Computing kept, evolved, or threw away. These are the concrete, cheap-to-test
markers that came out of the Might & Magic 1 analysis. Each one is a question
that can be answered against a later title in minutes, long before that title
is fully documented.

M&M2 has had a first pass ([mm2/01](../mm2/01-file-inventory.md)); nothing
below has been tested on any later title. Both game columns say what that game
does, not a prediction.

| # | Marker | How to test | M&M1 | M&M2 |
|---:|---|---|---|---|
| 1 | RLE codec | look for escape `0x7B`, run length = `count + 1` | yes, used for every picture | **no** — a different, higher-entropy codec, not yet decoded |
| 2 | Pixel order | decode a title screen row-major vs column-major | column-major, `col * height + row` | unknown until the codec is decoded |
| 3 | Event storage | are the per-map files code or data? | 8086 code overlays, one per map | **data** — `EVENTSI.DAT` / `EVENTSO.DAT` |
| 4 | Map size and wall encoding | 16×16, four 2-bit sides packed in one byte? | yes, 512 bytes per map | `MAP.DAT` is compressed; not a flat array |
| 5 | Second map plane | is there one, and does it hold walls or state? | yes — per-side lock latches plus four per-tile flags | unknown |
| 6 | Record shapes | item and monster record sizes, name field width | items 24 B (14-char name first), monsters 32 B (15-char name first) | items **20 B** (12-char name first); monsters compressed |
| 7 | Shipped build artefacts | is there a stray symbol map / link map? | yes — `MM.RSM`, 579 symbols | **no** |
| 8 | Overlay header | a magic word, then (dest, size) pairs and an entry point? | `0x00F2`, two load descriptors, entry 62 bytes below the code end | **none** — raw code, thirteen of fourteen start `55 8B EC` |
| 9 | Map identity | how does one map name another? | a 16-bit key looked up in a table, scoped by map type | unknown |
| 10 | Wall art | one set per map, or several? | three sets per map out of 18, chosen by the same key scheme | terrain-named picture sets, one per environment |
| 11 | Video strategy | one art set converted at runtime, or per-adapter art? | CGA art converted to EGA/Tandy at runtime | **per-adapter art**: 31 pictures shipped `.4` and `.16`, plus five `.DRV` |
| 12 | Font | shipped as a file, or built at runtime? | built in memory at startup | shipped: `MM2.CH`, 128 glyphs of 8×8, ASCII-indexed |
| 13 | Relocations | how many does the executable carry? | **3** | **500** |

## Marker 3 flipped immediately

This was the marker set up as "the most informative single fact this project
can turn up": whether New World Computing ever moved per-map events out of
compiled code. **They did it in the very next game.**

M&M1's per-map events are native code at fixed absolute addresses
(see [mm1/03](../mm1/03-map-overlays.md)). Resolving the call graph shows that
code does almost nothing but print text, clear lines, wait for a key and roll
`random` — an event script that happens to be compiled rather than interpreted.
It buys speed and costs portability: every overlay is tied to one specific link
of `MM.EXE`, and any port has to rebuild all 55.

M&M2 keeps overlays but repurposes them completely. There are fourteen, and
they are named for *subsystems* — `2COMBAT`, `2SMITH`, `2TEMPLE`, `2CAST1`,
`2PLAY` — not for maps. The per-map behaviour has become two data files,
`EVENTSI.DAT` for indoors and `EVENTSO.DAT` for outdoors.

Markers 7, 8, 11, 12 and 13 all moved the same way, and they say the same
thing. M&M1 was a program that computed its own addresses, hand-placed its
overlays past the end of its own image, converted its art at runtime and drew
with a font it built in memory. M&M2 is an ordinary relocatable DOS program —
500 relocations against three — that loads headerless code modules, reads its
content out of data files, ships art per adapter and draws it through a driver.

The rebuild happened between book one and book two, not later. Whatever
continuity survives the jump is therefore *content*, not architecture — and
some does: both item tables are name-first and both end on a joke item.

## Marker 9 is worth its own note

M&M1 never stores a map *number* in data that ships with a map. A destination —
and a wall-set choice — is a 16-bit key, resolved by a linear scan of a table
compiled into `MM.EXE`, with the search window chosen by a type byte. It is
indirection for its own sake: the same information as an index, one table
lookup slower, and it means the map files carry no knowledge of the map order.

Whether a later title keeps that, or just stores an index, says a lot about how
the data was being authored.

## Scope note

The series was expected to split as M&M1 (1986/87) with M&M2 (1988); M&M3
(1991); M&M4 and M&M5 (1992/93), which shipped combined as *World of Xeen* and
so clearly share an engine; and M&M6 (1998), a different 3D engine entirely.
The boundary picked out in advance as the one to look at first was **2 → 3**.

That grouping is wrong at its first join. M&M1 and M&M2 do not share an engine
in any meaningful sense — every structural marker differs. Whether M&M2 and
M&M3 belong together is now the open question, and it is the next thing worth
testing.

## Prior art

ScummVM has an `mm` engine covering Might & Magic 1 and the Xeen titles. That
should be treated as a cross-check once a format here is independently derived,
not as a starting point — the value of this repository is the derivation and the
write-up, and the comparative angle in particular does not appear to be covered
elsewhere. Worth confirming properly before investing in a later title.
