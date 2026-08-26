# pc-m&m-doc

File-format and data-layout documentation for **Might & Magic: Secret of the
Inner Sanctum**, PC / MS-DOS version (New World Computing, 1986–1987).

This is a **documentation project**. It describes how the shipped data files
are structured and how the executable is laid out. It is not a port, not a
re-implementation, and contains no game assets.

## What is documented so far

| Topic | Status |
|---|---|
| [File inventory](docs/01-file-inventory.md) | complete |
| [Executable layout and the shipped symbol map](docs/02-executable-and-symbols.md) | solid |
| [Per-map code overlays (`*.OVR`)](docs/03-map-overlays.md) | container solved, code not yet analysed |
| [Maze format (`MAZEDATA.DTA`)](docs/04-maze-format.md) | wall plane solved; second plane partly understood |
| [Graphics formats (RLE, `SCREEN*`, `MONPIX`, `WALLPIX`)](docs/05-graphics-formats.md) | solved except `WALLPIX` sprite geometry |
| [Data tables (items, monsters, hints)](docs/06-data-tables.md) | located and partly decoded |
| [Open questions](docs/open-questions.md) | — |

## Method

Every claim here was derived from the shipped files and validated against them,
not taken from secondary sources. Where a layout was inferred statistically the
document says so and gives the test and its result, so the reasoning can be
checked or overturned. Anything still uncertain is marked as such rather than
smoothed over.

## Using the tools

The scripts under [`tools/`](tools/) are stdlib-only Python 3 (no third-party
packages). They expect the original game files in `gamedata/`, which is **not**
part of this repository — point them at your own installed copy:

```sh
export MM1_DATA="/path/to/Might and Magic 1"

python tools/extract_gfx.py out      # every picture in the game -> PNG
python tools/dump_maze.py sorpigal   # a map's wall plane as ASCII
python tools/dump_symbols.py         # the 579 symbols shipped in MM.RSM
```

`tools/mmlib.py` is the shared reader library if you want to work with the data
directly.

## Provenance

Analysed against the GOG.com release of *Might and Magic 1* (a legally purchased
copy), which ships the original DOS files unmodified alongside DOSBox.

## Legal

Might & Magic is a trademark of its respective rights holders. This repository
contains only original analysis, documentation, and tools. No game code, game
data, or extracted assets are included or redistributed. You need your own copy
of the game to use anything here.
