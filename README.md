# pc-m&m-doc

File-format and data-layout documentation for the **Might & Magic** series on
PC / MS-DOS, starting with *Secret of the Inner Sanctum* (New World Computing,
1986–1987).

This is a **documentation project**. It describes how the shipped data files are
structured and how the executables are laid out. It is not a port, not a
re-implementation, and contains no game assets.

The long-term aim is to cover the DOS titles one at a time and then compare
them, to see what New World Computing reused, evolved, or rebuilt between
releases. See [cross-title fingerprints](docs/comparison/fingerprints.md) for
the markers being tracked.

## Might & Magic 1 — Secret of the Inner Sanctum

| Topic | Status |
|---|---|
| [File inventory](docs/mm1/01-file-inventory.md) | complete |
| [Executable layout and the shipped symbol map](docs/mm1/02-executable-and-symbols.md) | solved: record alignment, segment bases, where the overlays land |
| [Per-map code overlays (`*.OVR`)](docs/mm1/03-map-overlays.md) | solved: header, loader, entry point, call graph |
| [Maze format (`MAZEDATA.DTA`)](docs/mm1/04-maze-format.md) | solved: both planes |
| [Graphics formats (RLE, `SCREEN*`, `MONPIX`, `WALLPIX`)](docs/mm1/05-graphics-formats.md) | solved, including `WALLPIX` sprite geometry and set selection |
| [Data tables (items, monsters, hints, roster)](docs/mm1/06-data-tables.md) | tables placed and counted; stat fields not decoded |
| [The overlay data block](docs/mm1/07-overlay-data-block.md) | solved: parameters, and where every map edge leads |
| [The event system](docs/mm1/08-events.md) | solved: squares, facing masks, dispatch and handler idiom |
| [Open questions](docs/mm1/open-questions.md) | what is left, and what was corrected along the way |

## Might & Magic 2 — Gates to Another World

| Topic | Status |
|---|---|
| [File inventory](docs/mm2/01-file-inventory.md) | first pass: what ships, what is readable, what is compressed |

The short version, against the [fingerprints](docs/comparison/fingerprints.md):
**it is not the same engine, and that is measured rather than inferred from the
file layout.** No M&M2 binary shares a single 16-byte window with `MM.EXE`,
while the same test finds 157 contiguous shared bytes between `MM.EXE` and
M&M1's own setup utility. On top of that, per-map events moved from compiled
code into data files, the overlays became subsystems rather than maps, the
executable went from 3 relocations to 500, and art ships per adapter. The
rebuild expected somewhere around book three happened at book two.

The *content*, meanwhile, is continuous: 37 % of M&M1's items have a
counterpart in M&M2's list, in largely the same order.

Decoding M&M2's compression is the gate to everything else in it.

## Might & Magic 3 — Isles of Terra

| Topic | Status |
|---|---|
| [File inventory and the `.CC` archive](docs/mm3/01-file-inventory.md) | container solved: directory cipher, tiling proof |
| [The executable, and getting inside it](docs/mm3/02-executable.md) | solved: both layers of packing, relocations, the overlay pool |
| [Inside the archives](docs/mm3/03-archive-members.md) | solved: member codec, filename hash, most member names |

M&M3 ships **six files**. The whole game is two `.CC` archives whose directory
is obfuscated and whose members are compressed, addressed by a 16-bit hash of a
filename that the archive never stores.

All of that is now open, and the way in was the executable. `MM3.EXE` is packed
twice — a loader that reopens its own file and LZW-decompresses the program out
of its own tail, wrapped around a Microsoft EXEPACK image — and the 114 KB of
Borland overlays past the end were never compressed at all. Inside is a Borland
C++ 1991 program carrying 794 relocations, and inside *that* is the archive
module: the directory cipher, the filename hash and the member decompressor, in
plain assembly.

The members are **LZHUF** — LZSS plus an adaptive Huffman tree — with one
change from the published algorithm: the value the ring buffer is primed with
is stored per member instead of being fixed at `' '`. All 556 compressed
members decode to their declared size and consume their input to the byte, and
all twelve `.raw` members land on exactly 64,000 bytes, which is a 320×200 VGA
screen.

**And the engine question is answered.** With the executable open, the
binary-overlap test that showed M&M1 and M&M2 share no code now runs on M&M3:
it shares no code with either. The eighteen byte runs it does share with
`MM2.EXE` are seventeen string tables — the class list, the stat list, the
condition list, the copyright banner — and one table of powers of two. Three
consecutive titles, three independently built engines, with the game's
vocabulary carried across each rewrite intact. See the
[fingerprints](docs/comparison/fingerprints.md).

## Method

Every claim here was derived from the shipped files and validated against them,
not taken from secondary sources. Where a layout was inferred statistically the
document says so and gives the test and its result, so the reasoning can be
checked or overturned. Anything still uncertain is marked as such rather than
smoothed over — and where a later measurement has overturned an earlier
inference, the correction is in the history.

The largest such correction is in [doc 2](docs/mm1/02-executable-and-symbols.md):
`MM.RSM`'s trailing word per record is where a symbol *ends*, not where it
starts, so reading it the obvious way mis-names all 579 symbols by one record —
plausibly enough that several earlier findings were built on top of it.

## Using the tools

The scripts under [`tools/`](tools/) are stdlib-only Python 3, except
`disasm.py` which needs [Capstone](https://www.capstone-engine.org/).
Game-specific code lives in a per-game subdirectory; anything shared across
titles sits at the top level. They expect the original game files, which are
**not** part of this repository — point them at your own installed copy:

```sh
export MM1_DATA="/path/to/Might and Magic 1"

python tools/mm1/extract_gfx.py out       # every picture in the game -> PNG
python tools/mm1/dump_maze.py sorpigal    # a map's wall plane as ASCII
python tools/mm1/dump_symbols.py          # the 579 symbols shipped in MM.RSM
python tools/mm1/ovr_calls.py             # engine calls made by the 55 overlays
python tools/mm1/ovr_text.py sorpigal     # a map's event-handler table and text
python tools/mm1/ovr_params.py sorpigal   # a map's 50 parameter bytes, annotated
python tools/mm1/map_links.py             # where each map's four edges lead
python tools/mm1/wallsets.py              # which wall graphics each map loads
python tools/mm1/disasm.py draw           # an engine routine, by symbol name
python tools/mm1/disasm.py --ovr sorpigal 0xf508    # one event handler
```

```sh
export MM2_DATA="/path/to/Might and Magic 2"

python tools/mm2/dump_items.py            # M&M2's 256 items
python tools/mm2/dump_font.py             # M&M2's 8x8 font

export MM3_DATA="/path/to/Might and Magic 3"

python tools/mm3/cc_list.py               # the 558 members of MM3.CC, named
python tools/mm3/cc_list.py --check       # the tiling test that proves the key
python tools/mm3/cc_extract.py out        # extract and decompress every member
python tools/mm3/unpack_exe.py out        # undo both layers of packing on MM3.EXE
python tools/mm3/dump_screen.py front.raw out/front.png
```

`tools/mm1/mmlib.py`, `tools/mm2/mmlib2.py` and `tools/mm3/mmlib3.py` are the
reader libraries if you want to work with the data directly; `tools/mm3/lzhuf.py`
and `tools/mm3/exeunpack.py` are M&M3's codec and its executable unpacker,
usable on their own.

## Layout

```
docs/mm1/          Might & Magic 1
docs/mm2/          Might & Magic 2
docs/mm3/          Might & Magic 3
docs/comparison/   cross-title analysis
tools/png.py       shared, format-agnostic helpers
tools/code_overlap.py  cross-title binary comparison
tools/mm1/         Might & Magic 1 readers, dump scripts and disassembler
tools/mm2/         Might & Magic 2 readers
tools/mm3/         Might & Magic 3 readers, codec and EXE unpacker
gamedata/mm1/      your own copy of each game (gitignored, never committed)
gamedata/mm2/
gamedata/mm3/
notes/mm1/         generated dumps
```

## Provenance

Analysed against the GOG.com releases of *Might and Magic 1*, *2* and *3*
(legally purchased copies), which ship the original DOS files unmodified
alongside DOSBox.

## Legal

Might & Magic is a trademark of its respective rights holders. This repository
contains only original analysis, documentation, and tools. No game code, game
data, or extracted assets are included or redistributed. You need your own copy
of the game to use anything here.
