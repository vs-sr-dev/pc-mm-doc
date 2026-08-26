# 3. Inside the archives — Might & Magic III

The [file inventory](01-file-inventory.md) solved the `.CC` container and left
two things open: the members are compressed by an unidentified scheme, and the
directory names them by a 16-bit hash that cannot be inverted. Both were
closed by reading the code, once [`MM3.EXE` was unpacked](02-executable.md).

The archive is one hand-written assembly module in the program image. It holds
the directory cipher, the filename hash and the decompressor, one after the
other, with its own data laid out behind them.

## The directory cipher, from the source

The inventory solved the obfuscation statistically — a search over 65,536
transforms scored on whether the members tile the container. The module
settles it in eight instructions:

```
    mov  ah, 0xAC          ; the running key
loop:
    mov  al, es:[di]
    rol  al, 1
    rol  al, 1             ; rotate left two
    add  al, ah
    stosb
    add  ah, 0x67          ; advance the key
    loop loop
```

`+0xAC` with a `+0x67` step is `-0x54` with a `-0x99` step: the same transform
the search found, written the other way round. Nothing needs correcting — but
`mmlib3` now states it in the game's own terms.

## The filename hash

Sixteen instructions, and no table:

```python
h = 0
for ch in name:
    c = ch & 0x7F
    if c >= 0x60: c -= 0x20              # fold to upper case
    h = ((h >> 8) | (h << 8)) & 0xFFFF   # swap the halves
    h = ((h << 1) | (h >> 15)) & 0xFFFF  # rotate left one
    h = (h + c) & 0xFFFF
```

The first names to test it on were already in hand: the program names its
seven sound drivers as literals. **All seven hash onto real member ids of
`MM3.CC`** — `roland.drv`, `blaster.drv`, `adlib.drv`, `covox.drv`,
`tandy.drv`, `ibm.drv`, `demo.drv`. Seven arbitrary 16-bit values all landing
inside a 558-element set happens about three times in 10^15.

### Putting the names back

The hash is one-way, but it does not need inverting. The program that computes
it also contains the strings it is computed over. Harvesting every
filename-shaped literal out of the unpacked image and its overlay pool gives
**214** names, of which 20 are printf templates — `maze%02u.dat`,
`text%02u.maz`, `eface%02u.out`, `cr%d.vga`. Expanding each numeric template
over 0-255 gives 3,009 candidate names to hash.

| | named | of |
|---|---:|---:|
| `MM3.CC` | 329 | 558 |
| `MM3.CUR` | **240** | **240** |

That is a search, so it has a false-positive rate, and the rate is measured
rather than waved at. Re-running the same 3,009 stems with an extension that
cannot exist — the stem kept, `.dat` replaced by `.qxz` and friends — lands on
**38.5 ids on average over 20 trials, at most 44**. So of the 584 ids matched
across the two archives, on the order of forty are chance and the rest are
real.

The coherence says the same thing more plainly than the baseline does.
`MM3.CUR`'s members come out as `maze01` to `maze106` in `.dat`, `.bin` and
`.evt`, plus `maze.chr`, `maze.pty` and `maze.nam` — a run with essentially no
gaps that accounts for all 240 members. Chance does not produce that.

`%s` templates were deliberately left unexpanded. Substituting arbitrary words
into `%s.vga` reaches 532 of 558 members, but at the cost of 527 ids carrying
more than one candidate name — a higher score and a worse answer.

## The member codec

Every member of `MM3.CC` past a couple of startup messages begins with a
doubled byte. That is the header:

```
byte   value the ring buffer is primed with
byte   the same value again
word   uncompressed size, BIG-endian -- the only big-endian field in M&M3
rest   the compressed stream
```

The codec is **LZHUF**: LZSS over a ring buffer, with the literal/length
symbol carried by an adaptive Huffman tree that is rebuilt as it runs, and the
match position by a fixed prefix code. Every constant was read out of the
decompressor rather than guessed:

| in the code | | meaning |
|---|---|---|
| `mov cx, 0x13a` | 314 | `N_CHAR` = 256 - THRESHOLD + F, so THRESHOLD 2 and F 60 |
| `mov cx, 0xfc4` | 4036 | `N - F`, the part of a 4096-byte ring buffer that is primed |
| `cmp [freq + 0x4e4], 0x8000` | `MAX_FREQ` | halve every count and rebuild the tree |
| `cmp bx, 0x4e6` | `T * 2` | walk the Huffman tree until the node is a leaf |
| `xchg ah, al` after each load | | bits arrive **most significant first**, a big-endian word at a time |

The one departure from the published algorithm is the header. LZHUF primes its
ring buffer with `' '`; M&M3 stores the prime value per member and fills with
that. It is a real gain — priming with the byte a file mostly consists of makes
the first matches pay — and it is why almost every member starts with a doubled
byte. `0x20` is still one of the commonest values, in 76 members; `0x1F` leads
with 86.

### Whether it decodes

| test | result |
|---|---|
| members of `MM3.CC` decoding to the size their header declares | **556 of 556** |
| trailing bits of input left over | 0 to 7 — every member ends **on its own last byte** |
| members overrunning their input | 0 |

Consuming the input exactly, 556 times over, is not something a wrong decoder
does once. And the content agrees:

```
spldesc.bin  "Provides a magical light for the darker areas."
quest.bin    "Take the precious sea shells to the nymph Athea, and become
              enchanted by her siren's song."
jester.bin   "What is a monster's favorite holiday?  April Ghoul's Day."
corak.bin    "In the days when Fountain Head was created Morphose was summoned
              to be its protector, but the Rat Overlord captured him..."
```

The strongest check is the one that needed no text at all. **All twelve `.raw`
members decompress to exactly 64,000 bytes** — 320 x 200, one mode 13h screen.
Twelve files, whose extension came out of a hash search, landing on the exact
byte count of a VGA screen. Rendered by pixel value they are pictures:
adjacent pixels match 58 % of the time in `front.raw`, against 3.5 % for the
same bytes shuffled.

```sh
python tools/mm3/dump_screen.py front.raw out/front.png
```

### How the game knows what is compressed

It goes by name. The reader folds the **first four characters** of the
requested filename to upper case and compares them against a literal `MAZE` in
the module; a match reads the member verbatim, anything else decompresses it.

That is exactly the shape of the two archives. Every one of `MM3.CUR`'s 240
members is a `maze*` file and every one is stored plain; not one member of
`MM3.CC` is genuinely named `maze*`. The three that the name search claimed
were — `maze208.dat`, `maze96.evt`, `maze178.evt` — are compressed, so they are
false positives, caught by the rule rather than by inspection.

The tools cannot use the rule, because the archive holds no names. They decide
by measurement instead: a member is compressed when it carries a plausible
header **and** decoding consumes its bytes exactly. That separates the archives
completely — 556 of 558 in `MM3.CC`, and none of the 65 members of `MM3.CUR`
that merely look like they have a header.

## What is in there

`MM3.CC` is the shipped game and `MM3.CUR` is the living world, and the split
is clean:

| `MM3.CC` - 329 of 558 named | | `MM3.CUR` - 240 of 240 named | |
|---|---:|---|---:|
| `.vga` pictures | 83 | `maze*.dat` | 105 |
| `.maz` map text | 69 | `maze*.bin` | 66 |
| `.icn` icons | 38 | `maze*.evt` | 66 |
| `.out` `.fac` `.brd` `.til` art | 54 | `maze.chr` roster | 1 |
| `.dat` tables | 26 | `maze.pty` party | 1 |
| `.m` / `.s` music | 23 | `maze.nam` | 1 |
| `.raw` full screens | 12 | | |
| `.drv` sound drivers | 8 | | |
| `.bin` text | 7 | | |
| `.spl` spells | 4 | | |
| unnamed | 229 | | |

`MM3.CUR`'s numbering runs `maze01` to `maze106`, and the three kinds do not
cover it evenly: every map has a `.dat`, but only the first 64 also have a
`.bin` and an `.evt`. Whatever that split is — indoor against outdoor is the
obvious guess — it is the next thing to look at, and it is now readable.

### One more check the names pass by themselves

Twenty-two of the recovered names begin `Mon` and end `.dat`, and their
decompressed sizes are all exact multiples of **90**:

| | files | bytes each |
|---|---:|---|
| `MonAC` `MonAcid` `MonAttP` `MonCold` `MonDmgN/S/T` `MonElec` `MonEner` `MonFire` `MonHitB` `MonMagi` `MonNumA` `MonPhys` `MonRang` `MonSpd` `MonSpec` `MonTrea` | 18 | 90 |
| `MonHP`, `MonGems` | 2 | 180 |
| `MonExp`, `MonGold` | 2 | 360 |

Twenty-two independently hashed filenames landing on 1x, 2x and 4x the same
count is not a coincidence a false-positive rate can supply. So there are **90
monsters**, and M&M3 does not store a monster *record* at all: every attribute
is its own file, a flat array indexed by monster number. M&M1 packed a monster
into 32 bytes and M&M2 into a compressed table; M&M3 turned the table on its
side.

```sh
python tools/mm3/cc_list.py               # every member, with names
python tools/mm3/cc_extract.py out        # extract MM3.CC
python tools/mm3/cc_extract.py out MM3.CUR
```

## Still open

* **The palette.** The `.raw` screens are 8-bit indexed and no member is a
  768-byte table of 6-bit values; nor is one in the program image. Colour is
  somewhere else.
* **Two members of `MM3.CC` have no name and are stored plain** — the
  `requires %lu bytes free` and `There are only %lu bytes free` startup
  messages. Under the `MAZE` rule the archive reader would try to decompress
  them, so something else reads them; `Install.exe`, which is not part of the
  game and has not been looked at, is the obvious candidate.
* **`MM3.$$$`**, 28,600 bytes, is still unexamined. It is not an archive and
  not LZHUF; its bytes cluster around `0x9E` and `0xC0`-`0xCA` at entropy 5.89.
