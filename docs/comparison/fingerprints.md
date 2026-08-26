# Cross-title fingerprints

The point of documenting more than one Might & Magic is to see what New World
Computing kept, evolved, or threw away. These are the concrete, cheap-to-test
markers that came out of the Might & Magic 1 analysis. Each one is a question
that can be answered against a later title in minutes, long before that title
is fully documented.

M&M2 and M&M3 have each had a first pass ([mm2/01](../mm2/01-file-inventory.md),
[mm3/01](../mm3/01-file-inventory.md)); nothing below has been tested on any
later title. Every game column says what that game does, not a prediction.

| # | Marker | How to test | M&M1 | M&M2 | M&M3 |
|---:|---|---|---|---|---|
| 1 | RLE codec | look for escape `0x7B`, run length = `count + 1` | yes, used for every picture | **no** — a different, higher-entropy codec, not yet decoded | n/a — everything is inside `MM3.CC`, compressed by an unidentified scheme |
| 2 | Pixel order | decode a title screen row-major vs column-major | column-major, `col * height + row` | unknown until the codec is decoded | unknown |
| 3 | Event storage | are the per-map files code or data? | 8086 code overlays, one per map | **data** — `EVENTSI.DAT` / `EVENTSO.DAT` | unknown — no loose per-map files at all |
| 4 | Map size and wall encoding | 16×16, four 2-bit sides packed in one byte? | yes, 512 bytes per map | `MAP.DAT` is compressed; not a flat array | unknown |
| 5 | Second map plane | is there one, and does it hold walls or state? | yes — per-side lock latches plus four per-tile flags | unknown | unknown |
| 6 | Record shapes | item and monster record sizes, name field width | items 24 B (14-char name first), monsters 32 B (15-char name first) | items **20 B** (12-char name first); monsters compressed | unknown |
| 7 | Shipped build artefacts | is there a stray symbol map / link map? | yes — `MM.RSM`, 579 symbols | **no** | **no** |
| 8 | Overlay header | a magic word, then (dest, size) pairs and an entry point? | `0x00F2`, two load descriptors, entry 62 bytes below the code end | **none** — raw code, thirteen of fourteen start `55 8B EC` | n/a — no loose overlays |
| 9 | Map identity | how does one map name another? | a 16-bit key looked up in a table, scoped by map type | unknown | unknown |
| 10 | Wall art | one set per map, or several? | three sets per map out of 18, chosen by the same key scheme | terrain-named picture sets, one per environment | unknown |
| 11 | Video strategy | one art set converted at runtime, or per-adapter art? | CGA art converted to EGA/Tandy at runtime | **per-adapter art**: 31 pictures shipped `.4` and `.16`, plus five `.DRV` | unknown |
| 12 | Font | shipped as a file, or built at runtime? | built in memory at startup | shipped: `MM2.CH`, 128 glyphs of 8×8, ASCII-indexed | unknown |
| 13 | Relocations | how many does the executable carry? | **3** | **500** | n/a — `MM3.EXE` is packed |
| 14 | Packaging | loose files, or an archive? | 75 loose files | 94 loose files | **two hashed archives**, six files in all |
| 15 | Binary code reuse | any long byte run shared with the previous game's binaries? | — | **none with M&M1** | untestable: `MM3.EXE` is packed |

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

## Packaging is not the engine — how much of this is really a rebuild?

Most markers above describe how a game is *packaged*: how many files, whether
art ships per adapter, whether there is an archive. A studio can repackage
without rewriting a line of engine code, so on their own these markers cannot
tell a rebuild from a re-wrap. That distinction is worth testing directly, and
marker 15 does it.

`tools/code_overlap.py` indexes every 16-byte window of one binary and looks for
it in another, extending each hit as far as it matches. Runs made of padding are
discarded — long stretches of zeroes match between any two DOS binaries and mean
nothing. What survives is shared *content*: reused hand-written assembly, a
library routine, a whole function lifted across.

The control comes first, because a null result is only worth reading if the test
can find a positive one:

| pair | substantive shared windows | longest run |
|---|---:|---:|
| `MM.EXE` vs `GRAPHSET.EXE` — M&M1's own setup utility | **25** | **157 B** |
| `MM.EXE` vs M&M2's `MM2.EXE` | 0 | 0 |
| `MM.EXE` vs M&M2's `2PLAY.OVL` | 0 | 0 |
| `MM.EXE` vs M&M2's `2COMBAT.OVL` | 0 | 0 |
| `MM.EXE` vs M&M2's compressed `MONSTERS.DAT` — chance | 0 | 0 |

The test sees 157 contiguous bytes shared between M&M1 and a utility from the
same build, and **not one 16-byte window** shared between M&M1 and any M&M2
binary. So the 1 → 2 rebuild is not just repackaging: no binary code carried
over.

Two honest limits on that. It rules out *binary* reuse, not reuse of the C
source recompiled by a different toolchain — though the jump from 3 relocations
to 500 says the toolchain and memory model changed too. And it says nothing at
all about M&M3, because `MM3.EXE` is packed: comparing against it returns zero
for a reason that has nothing to do with the question.

**For M&M3 there is currently no engine evidence either way.** Everything
documented about it is the container. Whether the engine inside is M&M2's,
repackaged, is genuinely open, and stays open until either the member
compression or the executable is unpacked. An earlier version of this file
called M&M3 a third architecture on the strength of its file layout alone;
that was packaging talking.

## What *is* recycled: the content

While no code carries over from M&M1 to M&M2, plenty of content does. Comparing
the two item tables, both truncated to M&M2's narrower 12-character field:

* 39 names match exactly, and **87 of 234 — 37 %** have a close counterpart
  (`ACCURATE SWORD` → `ACCURATE SWD`, `ANTIDOTE BREW` → `ANTIDOTE ALE`,
  `BARDICHE +1` → `BARDICHE`).
* The **order largely survives**: M&M1 items 1–10 land at M&M2 indices
  4, 6, 15, 12, 14, 17, 21, 23, 22, 19, and items 60–64 at 93, 95, 94, 96, 97.
  That is an edited list, not an independently written one.
* Both tables end on the same joke — `(USELESS ITEM)` and `Useless Item`.

And the cast recurs across titles even where the engine does not. M&M1 ships
with `CRAG THE HACK`; M&M2's default party is six entirely different names; and
`CRAG HACK` is back in M&M3's `MM3.CUR`, alongside `MAXIMUS`, `KASTORE` and
`RESURECTRA`.

So the fair summary is: **the content is a continuous line, the binaries are
not.** New World Computing carried the world forward and rewrote the machinery
underneath it — at least once, at 1 → 2, provably.

## M&M3 answers the 2 → 3 question by refusing it

The boundary this project was set up to examine was 2 → 3. It turns out there
is no shared surface to compare across it. M&M3 ships **six files**: two
archives, a packed loader, a launcher stub, a config word and an installer.
There are no per-map files to classify, no overlays to check for a header, no
loose art to test a codec on. Most markers simply do not apply until the
archive's member compression is decoded.

What can be said is that the direction has never reversed. Each title moves
more of itself out of the executable and into content, and packages that
content more tightly:

| | M&M1 | M&M2 | M&M3 |
|---|---|---|---|
| files shipped | 75 | 94 | **6** |
| where per-map behaviour lives | compiled code | data files | inside an archive |
| how content is named | filename, or a 16-bit key in a table | filename | a 16-bit hash, no names stored |

The last row is the one worth flagging. M&M1 already refused to store a plain
map index, resolving destinations through a 16-bit key looked up in a table
(marker 9). M&M3 does the same thing to filenames: the archive directory stores
a 16-bit hash and no name at all. Different mechanism, same instinct, five years
apart — and it is the only habit that visibly survives two complete rebuilds.

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

That grouping is wrong at both of its first two joins. M&M1 and M&M2 do not
share an engine in any meaningful sense — every structural marker differs — and
M&M3 discards the loose-file layout entirely for two hashed archives. Three
consecutive titles, three architectures. Whether M&M3 and *World of Xeen*
belong together is now the open question, and `MM3.CC`'s member compression is
what has to be decoded to ask it.

## Prior art

ScummVM has an `mm` engine covering Might & Magic 1 and the Xeen titles. That
should be treated as a cross-check once a format here is independently derived,
not as a starting point — the value of this repository is the derivation and the
write-up, and the comparative angle in particular does not appear to be covered
elsewhere. Worth confirming properly before investing in a later title.
