# 7. The overlay data block

Every `.OVR` carries a data half that is loaded to `0xC940` (doc 3). It has
three regions, in this order:

```
0xC940   per-map binary parameters   variable length, not decoded
         event-handler table         words pointing into this overlay's code
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

## Where the table starts

The parameter block before it is **variable in length** — between `0x3F` and
`0x77` bytes across the 55 maps — and no consistent delimiter separates it from
the table (`FF FF` precedes the table in 20 of 55 files, and nothing does in the
rest). So the parameter block is genuinely per-map data rather than a fixed
header, and it is not decoded.

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
