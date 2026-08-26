# 7. The overlay data block

Every `.OVR` carries a data half that is loaded to `0xC940` (doc 3). It has
three regions, in this order:

```
0xC940   per-map parameters          exactly 50 bytes
0xC972   event count, then the event tables      (doc 8)
         text                        NUL-terminated strings
```

Across the 55 maps this accounts for 37,858 bytes of data against 43,236 bytes
of code, holding **816 event handlers** and **649 text strings**.

## The event-handler table

A run of words, every one of which falls inside `[0xF48F, 0xF48F + code size)` —
this overlay's own code. Sorpigal's has 24 entries:

```
F4E0 F508 F55D F570 F583 F5A8 F5BB F5CE
F5E1 F6A2 F6BD F6C5 F6CD F6D5 F6DD F6E5
F6ED F6F5 F715 F71D F725 F72D F74C F769
```

The entries are ascending and the run is unmistakable — a word landing in that
range by chance has probability `code size / 65536`, about 1.3 %, so a run of
24 cannot be accidental. The tool finds the table by taking the longest such
run.

Handler counts track how much is going on in a map, which is a good sanity
check on the interpretation:

| map type | handlers |
|---|---|
| towns (`sorpigal`, `dusk`, `algary`, …) | 17–29 |
| caves and dungeons | 14–34 |
| outdoor areas (`areaa1`, `areab2`, …) | 6–10 |

Towns are dense with shops, inns and temples; open countryside has a handful of
transitions and set pieces.

**What indexes this table is not yet known.** The engine is handed a pointer at
overlay entry (`mov [0134h], ax`), and the natural guess is that a per-square
event id selects a handler, but that has not been traced. See
[open questions](open-questions.md).

## The parameter block

The first 50 bytes are a fixed header. The engine never touches them directly:
it goes through an indexed accessor — `0x0D5B` reads a byte, `0x0D66` writes one
— with the overlay's data base in `[0132h]`. There are **80 such call sites in
the engine and every one uses a literal index**, all in the range 0–49. That
bounds the block exactly, and it also names each byte by whoever reads it.

| index | consumers | reading |
|---|---|---|
| 0 | `getinfo`, `temple`, `training`, `food`, `unlock`, `use`, … | **map identifier** — all 55 maps hold a different value |
| 1 | `encountr`, written by `saveros` | **map type**: 1 town/cave, 2 outdoor, 3 dungeon |
| 2–7 | `encountr` | encounter setup, three pairs |
| 8–10 | `loadcom` | edge transition, party leaving via **+X** |
| 11–13 | `yplus` | edge transition, leaving via **+Y** |
| 14–16 | `xplus` | edge transition, leaving via **−X** |
| 17–19 | `ymin` | edge transition, leaving via **−Y** |
| 20–28, 33–34, 47 | `right8` | not identified |
| 29 | `inwait` | 70–200, usually 100 |
| 30–32 | — | never read with a literal index |
| 35–43 | `qcast` | spell handling |
| 44 | `getviewo` | 8–40 |
| 45, 48, 49 | `unlock`, `search`, `searchit` | lock and search difficulty |
| 46 | `plot`, `qcast` | |

### The four edge transitions

Each is three bytes and each has a routine that sets the entry coordinate before
reading them:

| routine | sets | meaning |
|---|---|---|
| `loadcom` `0x4FF8` | `X := 0` | walked off the +X edge, arrive at the west edge |
| `yplus` `0x5022` | `Y := 0` | walked off the +Y edge, arrive at the bottom |
| `xplus` `0x504C` | `X := 15` | walked off the −X edge, arrive at the east edge |
| `ymin` `0x5076` | `Y := 15` | walked off the −Y edge, arrive at the top |

All four then jump to a shared tail at `0x509D`.

Two things corroborate the reading. In every town, cave and dungeon the four
triples are **identical** — those maps are sealed, so any edge leads to the one
place you came from — while the outdoor maps have four different triples. And
the third byte of each triple takes exactly the same 1–3 values as index 1, the
map type.

What the first two bytes encode is **not** established. The first ranges 0–27,
the second 0–15, and neither behaves like a plain index into the 55-map table:
`areaa1` names its east and south neighbours identically, which no 5×4 grid
does. Decoding them means disassembling the shared tail at `0x509D` and
`loadnext` (`0x50E3`).

```sh
python tools/mm1/ovr_params.py            # index -> consumers
python tools/mm1/ovr_params.py sorpigal   # one map's 50 bytes, annotated
```

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

The text confirms what the call graph in doc 3 implies: map code is a script
that prints prompts and branches on the answer. Nearly every string ends in
`(Y/N)?` or offers a numbered choice.

## Reading it

```sh
python tools/mm1/ovr_text.py sorpigal        # handler table + text
python tools/mm1/ovr_text.py --wrap dusk     # text as the game lays it out
python tools/mm1/ovr_text.py --summary       # sizes and counts for all 55
```

The extracted text is game content, so it is not committed here — the tool
reads your own copy. See [`notes/README.md`](../../notes/README.md).
