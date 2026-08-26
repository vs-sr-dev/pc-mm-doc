# 1. File inventory

The DOS game is small and self-contained: one executable, one setup utility,
five `.DTA` data files, ten title/interstitial screens, a linker symbol map,
and 55 per-map overlays. 93 files in the GOG directory, of which the following
are the actual game; the rest is GOG packaging (DOSBox, icons, uninstaller).

| File | Size | Role |
|---|---:|---|
| `MM.EXE` | 119,264 | The game. DOS MZ executable. |
| `GRAPHSET.EXE` | 2,512 | Graphics-adapter setup; writes `GACARD.DTA`. |
| `MM.RSM` | 6,656 | Linker symbol map — 579 named symbols. See [doc 2](02-executable-and-symbols.md). |
| `MAZEDATA.DTA` | 28,160 | 55 maps × 512 bytes. See [doc 4](04-maze-format.md). |
| `WALLPIX.DTA` | 123,059 | 18 wall-graphic sets. See [doc 5](05-graphics-formats.md). |
| `MONPIX.DTA` | 81,872 | 76 monster/scene portraits. |
| `ROSTER.DTA` | 2,304 | Character roster (save data; mutated by the game). |
| `GACARD.DTA` | 1 | Selected graphics adapter. Ships as `0x03`. |
| `SCREEN0`…`SCREEN9` | 4,582–9,802 | Ten full-screen CGA images. |
| `*.OVR` | 544–2,246 | 55 per-map code overlays. See [doc 3](03-map-overlays.md). |

## The 55 maps

`MM.EXE` carries a table of 55 NUL-terminated names at data-segment offset
`0x0A07` (file offset `0x10C07`). Each name has exactly one matching `.OVR`
file, and the table order is the map index used by `MAZEDATA.DTA`.

| # | name | # | name | # | name |
|---:|---|---:|---|---:|---|
| 0 | sorpigal | 19 | areab2 | 38 | qvl2 |
| 1 | portsmit | 20 | areab3 | 39 | rwl1 |
| 2 | algary | 21 | areab4 | 40 | rwl2 |
| 3 | dusk | 22 | areac1 | 41 | enf1 |
| 4 | erliquin | 23 | areac2 | 42 | enf2 |
| 5 | cave1 | 24 | areac3 | 43 | whitew |
| 6 | cave2 | 25 | areac4 | 44 | dragad |
| 7 | cave3 | 26 | aread1 | 45 | udrag1 |
| 8 | cave4 | 27 | aread2 | 46 | udrag2 |
| 9 | cave5 | 28 | aread3 | 47 | udrag3 |
| 10 | cave6 | 29 | aread4 | 48 | demon |
| 11 | cave7 | 30 | areae1 | 49 | alamar |
| 12 | cave8 | 31 | areae2 | 50 | pp1 |
| 13 | cave9 | 32 | areae3 | 51 | pp2 |
| 14 | areaa1 | 33 | areae4 | 52 | pp3 |
| 15 | areaa2 | 34 | doom | 53 | pp4 |
| 16 | areaa3 | 35 | blackrn | 54 | astral |
| 17 | areaa4 | 36 | blackrs |  |  |
| 18 | areab1 | 37 | qvl1 |  |  |

The five towns come first, then the nine caves, then the 5×4 outdoor grid
(`areaA1`–`areaE4`), then the named dungeons, and finally the Astral Plane.

`28,160 / 55 = 512` exactly, which is the first evidence that `MAZEDATA.DTA` is
indexed by this same list.
