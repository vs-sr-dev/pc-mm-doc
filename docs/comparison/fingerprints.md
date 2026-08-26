# Cross-title fingerprints

The point of documenting more than one Might & Magic is to see what New World
Computing kept, evolved, or threw away. These are the concrete, cheap-to-test
markers that came out of the Might & Magic 1 analysis. Each one is a question
that can be answered against a later title in minutes, long before that title
is fully documented.

Nothing below has been tested on any game except M&M1. The right-hand column is
what M&M1 does, not a prediction.

| # | Marker | How to test | M&M1 |
|---:|---|---|---|
| 1 | RLE codec | look for escape `0x7B`, run length = `count + 1` | yes, used for every picture |
| 2 | Pixel order | decode a title screen row-major vs column-major | column-major, `col * height + row` |
| 3 | Event storage | are the per-map files code or data? | 8086 code overlays, one per map |
| 4 | Map size and wall encoding | 16×16, four 2-bit sides packed in one byte? | yes, 512 bytes per map incl. a second plane |
| 5 | Record shapes | item and monster record sizes, name field width | items 24 B, monsters 32 B, 15-char names |
| 6 | Shipped build artefacts | is there a stray symbol map / link map? | yes — `MM.RSM`, 579 symbols |
| 7 | Video strategy | one art set converted at runtime, or per-adapter art? | CGA art converted to EGA/Tandy at runtime |

## Why marker 3 is the interesting one

M&M1's per-map events are native code at fixed absolute addresses
(see [mm1/03](../mm1/03-map-overlays.md)). Resolving the call graph shows that
code does almost nothing but print text, clear lines, and roll `random` — it is
an event script that happens to be compiled rather than interpreted.

That buys speed and costs portability: every overlay is tied to one specific
link of `MM.EXE`, and any port to another CPU has to rebuild all 55. If New
World Computing ever moved to an interpreted or table-driven event format, the
release where that happens is the most informative single fact this project can
turn up.

## Scope note

The series splits naturally: M&M1 (1986/87) and M&M2 (1988); M&M3 (1991);
M&M4 and M&M5 (1992/93), which shipped combined as *World of Xeen* and so
clearly share an engine; and M&M6 (1998), a different 3D engine entirely. The
boundary worth looking at first is **2 → 3**.

## Prior art

ScummVM has an `mm` engine covering Might & Magic 1 and the Xeen titles. That
should be treated as a cross-check once a format here is independently derived,
not as a starting point — the value of this repository is the derivation and the
write-up, and the comparative angle in particular does not appear to be covered
elsewhere. Worth confirming properly before investing in a later title.
