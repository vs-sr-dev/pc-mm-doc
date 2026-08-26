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
| [Executable layout and the shipped symbol map](docs/mm1/02-executable-and-symbols.md) | solid |
| [Per-map code overlays (`*.OVR`)](docs/mm1/03-map-overlays.md) | header and load addresses solved; engine call graph resolved |
| [Maze format (`MAZEDATA.DTA`)](docs/mm1/04-maze-format.md) | wall plane solved (column-major); second plane partly understood |
| [Graphics formats (RLE, `SCREEN*`, `MONPIX`, `WALLPIX`)](docs/mm1/05-graphics-formats.md) | solved except `WALLPIX` sprite geometry |
| [Data tables (items, monsters, hints)](docs/mm1/06-data-tables.md) | located and partly decoded |
| [The overlay data block](docs/mm1/07-overlay-data-block.md) | handler table and text solved; parameters not decoded |
| [The event system](docs/mm1/08-events.md) | solved: squares, facing masks and handlers |
| [Open questions](docs/mm1/open-questions.md) | — |

## Method

Every claim here was derived from the shipped files and validated against them,
not taken from secondary sources. Where a layout was inferred statistically the
document says so and gives the test and its result, so the reasoning can be
checked or overturned. Anything still uncertain is marked as such rather than
smoothed over — and where a later measurement has overturned an earlier
inference, the correction is in the history.

## Using the tools

The scripts under [`tools/`](tools/) are stdlib-only Python 3 (no third-party
packages). Game-specific code lives in a per-game subdirectory; anything shared
across titles sits at the top level. They expect the original game files, which
are **not** part of this repository — point them at your own installed copy:

```sh
export MM1_DATA="/path/to/Might and Magic 1"

python tools/mm1/extract_gfx.py out      # every picture in the game -> PNG
python tools/mm1/dump_maze.py sorpigal   # a map's wall plane as ASCII
python tools/mm1/dump_symbols.py         # the 579 symbols shipped in MM.RSM
python tools/mm1/ovr_calls.py            # engine calls made by the 55 map overlays
python tools/mm1/ovr_text.py sorpigal    # a map's event-handler table and text
```

`tools/mm1/mmlib.py` is the shared reader library if you want to work with the
data directly.

## Layout

```
docs/mm1/          Might & Magic 1
docs/comparison/   cross-title analysis
tools/png.py       shared, format-agnostic helpers
tools/mm1/         Might & Magic 1 readers and dump scripts
notes/mm1/         generated dumps
```

## Provenance

Analysed against the GOG.com release of *Might and Magic 1* (a legally purchased
copy), which ships the original DOS files unmodified alongside DOSBox.

## Legal

Might & Magic is a trademark of its respective rights holders. This repository
contains only original analysis, documentation, and tools. No game code, game
data, or extracted assets are included or redistributed. You need your own copy
of the game to use anything here.
