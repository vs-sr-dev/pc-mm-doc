# Cross-title fingerprints

The point of documenting more than one Might & Magic is to see what New World
Computing kept, evolved, or threw away. These are the concrete, cheap-to-test
markers that came out of the Might & Magic 1 analysis. Each one is a question
that can be answered against a later title in minutes, long before that title
is fully documented.

M&M2 has had a first pass ([mm2/01](../mm2/01-file-inventory.md)); M&M3 is
open as far as its archives ([mm3/01](../mm3/01-file-inventory.md),
[mm3/02](../mm3/02-executable.md), [mm3/03](../mm3/03-archive-members.md)).
Nothing below has been tested on M&M4 or later. Every game column says what
that game does, not a prediction.

| # | Marker | How to test | M&M1 | M&M2 | M&M3 |
|---:|---|---|---|---|---|
| 1 | Compression | what codec, and where is it applied? | RLE per picture, escape `0x7B`, run = `count + 1` | **no** — a different, higher-entropy codec, not yet decoded | **LZHUF** (LZSS + adaptive Huffman) applied per *archive member*, not per format |
| 2 | Pixel order | decode a full screen row-major vs column-major | column-major, `col * height + row` | unknown until the codec is decoded | **row-major** — the twelve `.raw` screens render as pictures one way and as vertical smear the other |
| 3 | Event storage | are the per-map files code or data? | 8086 code overlays, one per map | **data** — `EVENTSI.DAT` / `EVENTSO.DAT` | **data** — one `maze<nn>.evt` per map, in `MM3.CUR` |
| 4 | Map size and wall encoding | 16×16, four 2-bit sides packed in one byte? | yes, 512 bytes per map | `MAP.DAT` is compressed; not a flat array | flat `maze<nn>.dat`, 832 bytes for a town map; not yet decoded |
| 5 | Second map plane | is there one, and does it hold walls or state? | yes — per-side lock latches plus four per-tile flags | unknown | unknown |
| 6 | Record shapes | item and monster record sizes, name field width | items 24 B (14-char name first), monsters 32 B (15-char name first) | items **20 B** (12-char name first); monsters compressed | **no records at all** — 22 parallel `Mon*.dat` arrays over 90 monsters, one attribute per file |
| 7 | Shipped build artefacts | is there a stray symbol map / link map? | yes — `MM.RSM`, 579 symbols | **no** | **no** |
| 8 | Overlay mechanism | hand-rolled, or the compiler's? | hand-rolled: magic word `0x00F2`, two load descriptors, entry 62 B below the code end | headerless raw code, thirteen of fourteen start `55 8B EC` | **the compiler's** — Borland VROOM, an `FBOV` pool of 114 KB inside the EXE |
| 9 | Map identity | how does one map name another? | a 16-bit key looked up in a table, scoped by map type | unknown | by **number**, in a filename — `maze<nn>.dat` — which is then hashed |
| 10 | Wall art | one set per map, or several? | three sets per map out of 18, chosen by the same key scheme | terrain-named picture sets, one per environment | six tile sets: `castle`, `cave`, `dung`, `out`, `scifi`, `town` |
| 11 | Video strategy | one art set converted at runtime, or per-adapter art? | CGA art converted to EGA/Tandy at runtime | **per-adapter art**: 31 pictures shipped `.4` and `.16`, plus five `.DRV` | **one art set, VGA only**. The per-device drivers are for *sound* — seven of them |
| 12 | Font | shipped as a file, or built at runtime? | built in memory at startup | shipped: `MM2.CH`, 128 glyphs of 8×8, ASCII-indexed | unknown |
| 13 | Relocations | how many does the executable carry? | **3** | **500** | **794** |
| 14 | Packaging | loose files, or an archive? | 75 loose files | 94 loose files | **two hashed archives**, six files in all |
| 15 | Binary code reuse | any long byte run shared with a previous game's binaries? | — | **none with M&M1** | **none with M&M1 or M&M2** |

## Marker 3 flipped immediately

This was the marker set up as "the most informative single fact this project
can turn up": whether New World Computing ever moved per-map events out of
compiled code. **They did it in the very next game**, and never went back.

M&M1's per-map events are native code at fixed absolute addresses
(see [mm1/03](../mm1/03-map-overlays.md)). Resolving the call graph shows that
code does almost nothing but print text, clear lines, wait for a key and roll
`random` — an event script that happens to be compiled rather than interpreted.
It buys speed and costs portability: every overlay is tied to one specific link
of `MM.EXE`, and any port has to rebuild all 55.

M&M2 keeps overlays but repurposes them completely. There are fourteen, and
they are named for *subsystems* — `2COMBAT`, `2SMITH`, `2TEMPLE`, `2CAST1`,
`2PLAY` — not for maps. The per-map behaviour has become two data files,
`EVENTSI.DAT` for indoors and `EVENTSO.DAT` for outdoors. M&M3 goes one step
further and gives every map its own event file again — `maze01.evt` through
`maze64.evt` — but as data, not code.

Markers 7, 8, 11, 12 and 13 all moved the same way. M&M1 was a program that
computed its own addresses, hand-placed its overlays past the end of its own
image, converted its art at runtime and drew with a font it built in memory.
M&M2 is an ordinary relocatable DOS program — 500 relocations against three —
that loads headerless code modules, reads its content out of data files, ships
art per adapter and draws it through a driver. M&M3 stops hand-rolling
overlays at all and takes Borland's.

The rebuild happened between book one and book two, not later. Whatever
continuity survives the jump is therefore *content*, not architecture — and
some does: both item tables are name-first and both end on a joke item.

## Packaging is not the engine — and now all three have been tested

Most markers above describe how a game is *packaged*: how many files, whether
art ships per adapter, whether there is an archive. A studio can repackage
without rewriting a line of engine code, so on their own these markers cannot
tell a rebuild from a re-wrap. Marker 15 tests the distinction directly.

`tools/code_overlap.py` indexes every 16-byte window of one binary and looks
for it in another, extending each hit as far as it matches. Runs made of
padding are discarded — long stretches of zeroes match between any two DOS
binaries and mean nothing. What survives is shared *content*: reused
hand-written assembly, a library routine, a whole function lifted across.

The control comes first, because a null result is only worth reading if the
test can find a positive one:

| pair | substantive shared windows | longest run |
|---|---:|---:|
| `MM.EXE` vs `GRAPHSET.EXE` — M&M1's own setup utility | **25** | **157 B** |
| M&M3's program image vs M&M3's own overlay pool | **149** | **52 B** |
| `MM.EXE` vs M&M2's `MM2.EXE` | 0 | 0 |
| `MM.EXE` vs M&M2's `2PLAY.OVL` / `2COMBAT.OVL` | 0 | 0 |
| M&M3's image vs `MM.EXE` | 0 | 0 |
| M&M3's overlay pool vs `MM2.EXE` / `MM.EXE` | 0 | 0 |
| M&M3's image vs M&M2's `2PLAY.OVL` / `2COMBAT.OVL` / `2CAST1.OVL` | 0 | 0 |
| M&M3's image vs M&M2's compressed `MONSTERS.DAT` — chance | 0 | 0 |
| **M&M3's image vs `MM2.EXE`** | **18** | **46 B** |

The test sees 157 contiguous bytes shared between M&M1 and a utility from the
same build, and 149 windows between M&M3's resident image and its own
overlays, so it can find reuse when reuse is there. Against that, every
cross-title pair is zero — except the last row, and the last row is the
interesting one, because **all eighteen hits are data, not code**:

```
"Good\0Neutral\0Evil"
"Cartographer\0Crusader\0Di..."   "...Linguist\0Merchant\0Mountaineer\0Navigator\0Path..."
"Paralyzed\0Unconscious"          "Stone\0Eradicated"
"Might\0Intellect\0Personality"   "Speed\0Accuracy\0Luck"
"New World Computing, Inc."  x4   "All Rights Reserved"
80 00 40 00 20 00 10 00 08 00 04 00 02 00 01 00   (a bit-mask table, twice)
```

Seventeen string tables and one table of powers of two. **Not one shared
instruction byte** between M&M3 and either predecessor.

The codec did not carry over either. M&M3's LZHUF header — doubled prime byte,
big-endian size — appears on none of M&M2's compressed files, so book two's
codec is still unidentified and is not this one.

So none of the three shipped binaries carries code from the one before it.
M&M1 → M&M2 was a rewrite, and so was M&M2 → M&M3. Three consecutive titles,
three independently built engines.

Two honest limits, unchanged. This rules out *binary* reuse, not reuse of C
source recompiled by a different toolchain — and the toolchains did change:
M&M3 says `Borland C++ - Copyright 1991 Borland Intl.` in plain text, and its
relocation count went 3 → 500 → 794 across the series. And it is a statement
about the shipped `.EXE` files, not about design: the class list, the stat
list and the condition list came across verbatim, which is a strong hint that
somebody had the previous game's source in front of them even if none of its
object code survived.

## What *is* recycled: the content

While no code carries over between any two of the three, plenty of content
does. Comparing M&M1's and M&M2's item tables, both truncated to M&M2's
narrower 12-character field:

* 39 names match exactly, and **87 of 234 — 37 %** have a close counterpart
  (`ACCURATE SWORD` → `ACCURATE SWD`, `ANTIDOTE BREW` → `ANTIDOTE ALE`,
  `BARDICHE +1` → `BARDICHE`).
* The **order largely survives**: M&M1 items 1–10 land at M&M2 indices
  4, 6, 15, 12, 14, 17, 21, 23, 22, 19, and items 60–64 at 93, 95, 94, 96, 97.
  That is an edited list, not an independently written one.
* Both tables end on the same joke — `(USELESS ITEM)` and `Useless Item`.

M&M2 → M&M3 shows the same thing from the other direction: the strings that
survive the rewrite are exactly the game's *vocabulary* — what a character can
be, what can be wrong with one, what numbers describe one.

And the cast recurs across titles even where the engine does not. M&M1 ships
with `CRAG THE HACK`; M&M2's default party is six entirely different names; and
`CRAG HACK` is back in M&M3's `MM3.CUR`, alongside `MAXIMUS`, `KASTORE` and
`RESURECTRA`.

So the fair summary is: **the content is a continuous line, the binaries are
not.** New World Computing carried the world forward and rewrote the machinery
underneath it — twice, provably.

## The 2 → 3 question, answered

The boundary this project was set up to examine was 2 → 3. For a while it
looked unanswerable: M&M3 ships six files, `MM3.EXE` was packed, and there was
no shared surface to compare across. That was a limit of the analysis, not of
the evidence, and it is gone — `MM3.EXE` [comes apart in two
layers](../mm3/02-executable.md), and the answer is a clean negative.

What can still be said about direction is that it has never reversed. Each
title moves more of itself out of the executable and into content, and
packages that content more tightly:

| | M&M1 | M&M2 | M&M3 |
|---|---|---|---|
| files shipped | 75 | 94 | **6** |
| where per-map behaviour lives | compiled code | data files | data files, inside an archive |
| how content is named | filename, or a 16-bit key in a table | filename | a 16-bit hash of a filename, no names stored |
| who writes the overlay manager | New World | New World | Borland |

The last two rows are the ones worth flagging. M&M3 hashes its filenames but
its *maps* are just numbered — `maze01.dat` — so the indirection M&M1 built by
hand (marker 9) has moved down a layer into the file system, and the map
numbering itself has become plain. And by book three the studio has stopped
writing its own loader machinery: the overlay manager is the compiler's, and
the only hand-written assembly left in the resident image is the archive
module.

## Marker 9 is worth its own note

M&M1 never stores a map *number* in data that ships with a map. A destination —
and a wall-set choice — is a 16-bit key, resolved by a linear scan of a table
compiled into `MM.EXE`, with the search window chosen by a type byte. It is
indirection for its own sake: the same information as an index, one table
lookup slower, and it means the map files carry no knowledge of the map order.

M&M3 does the opposite, twice over. Maps are numbered 1 to 106 and the number
is in the filename; the *filename* is then hashed to 16 bits so the archive
need not store it. The habit of refusing a plain index survived, but it moved
from the map data to the container.

## Scope note

The series was expected to split as M&M1 (1986/87) with M&M2 (1988); M&M3
(1991); M&M4 and M&M5 (1992/93), which shipped combined as *World of Xeen* and
so clearly share an engine; and M&M6 (1998), a different 3D engine entirely.
The boundary picked out in advance as the one to look at first was **2 → 3**.

That grouping is wrong at both of its first two joins, and now measurably so at
both. M&M1 and M&M2 share no code; neither do M&M2 and M&M3. Three consecutive
titles, three engines. Whether M&M3 and *World of Xeen* belong together is now
the open question — and it is a cheap one to ask, because the `.CC` container,
the filename hash and the LZHUF codec are all in hand to test against M&M4.

## Prior art

ScummVM has an `mm` engine covering Might & Magic 1 and the Xeen titles. That
should be treated as a cross-check once a format here is independently derived,
not as a starting point — the value of this repository is the derivation and the
write-up, and the comparative angle in particular does not appear to be covered
elsewhere. Worth confirming properly before investing in a later title.
