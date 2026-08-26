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
**it is not the same engine.** Per-map events moved from compiled code into
data files, the overlays are now subsystems rather than maps, the executable
went from 3 relocations to 500, art ships per adapter instead of being
converted at runtime, and the run-length codec is gone. The rebuild New World
Computing was expected somewhere around book three happened at book two.

Decoding M&M2's compression is the gate to everything else in it.

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
```

`tools/mm1/mmlib.py` and `tools/mm2/mmlib2.py` are the reader libraries if you
want to work with the data directly.

## Layout

```
docs/mm1/          Might & Magic 1
docs/mm2/          Might & Magic 2
docs/comparison/   cross-title analysis
tools/png.py       shared, format-agnostic helpers
tools/mm1/         Might & Magic 1 readers, dump scripts and disassembler
tools/mm2/         Might & Magic 2 readers
gamedata/mm1/      your own copy of each game (gitignored, never committed)
gamedata/mm2/
notes/mm1/         generated dumps
```

## Provenance

Analysed against the GOG.com releases of *Might and Magic 1* and *Might and
Magic 2* (legally purchased copies), which ship the original DOS files
unmodified alongside DOSBox.

## Legal

Might & Magic is a trademark of its respective rights holders. This repository
contains only original analysis, documentation, and tools. No game code, game
data, or extracted assets are included or redistributed. You need your own copy
of the game to use anything here.
