# 4. Maze format — `MAZEDATA.DTA`

28,160 bytes = **55 maps × 512 bytes**, indexed by the map table in doc 1.
Each 512-byte block is two 256-byte planes:

```
+0x000  wall plane        16x16 tiles, one byte each
+0x100  attribute plane   16x16 tiles, one byte each
```

`loadmaze` (`0x0D35`) seeks to `map index × 512` and `readmaze_` (`0x0142`)
reads all 512 bytes into `base1` (`DS:0x3CFA`), which puts the second plane at
`base2` (`DS:0x3DFA`). That is how the renderer addresses them.

Both planes use the same per-tile encoding: **four 2-bit fields, one per side.**

## Indexing

The engine keeps the party position as two bytes and packs them once, in
`draw` (`0x0F45`):

```
0F55  mov al, [3C39]      ; the north/south coordinate
0F58  mov cx, 4
0F5B  shl al, cl
0F5D  adc al, [3C38]      ; the east/west coordinate
0F61  mov [3C3A], al
```

and then indexes the plane with that byte directly, `[bp + base1]`. So

```
tile index = (north/south) * 16 + (east/west)
```

The engine's own names for the two axes come from the four edge-transition
routines, each of which parks one coordinate at an extreme before handing over:
`yplus` and `ymin` write `[3C39]`, `xplus` and `xmin` write `[3C38]`. So the
game calls the **north/south axis Y** and the **east/west axis X**, and the tile
index is `Y * 16 + X`. Earlier versions of this document had those two letters
the other way round, from the mis-aligned symbol table (doc 2); the layout and
every rendering are unaffected, only the axis names change.

## Byte layout

| Bits | Axis | Compass |
|---|---|---|
| 0–1 | −X | **West** |
| 2–3 | −Y | **South** |
| 4–5 | +X | **East** |
| 6–7 | +Y | **North** |

| Value | Meaning |
|---|---|
| 0 | open |
| 1 | wall |
| 2 | door |
| 3 | special / solid fill |

### How this was determined

A wall between two tiles is stored twice, once from each side, so the correct
field assignment is the one under which neighbours agree. Testing all 24
permutations of the four fields against both index orders, across all 55 maps:

| assignment | agreement |
|---|---|
| **N = bits 6-7, S = bits 2-3, E = bits 4-5, W = bits 0-1** | **98.35 %** |
| next best | 75.23 % |

Reciprocity alone cannot tell the two index orders apart, because transposing a
map preserves it — both scored 98.35 %. The tie was broken by the event tables
in the overlays: see doc 8.

### The compass

North is **+Y** and east is **+X**. This comes from the teleport spell in
`qcast`, which prompts `DIRECTION (N,E,S,W)`, stores the typed letter, and
dispatches on it at `0x94D0`:

```
cmp al,'N'  ->  [3C39] += n     ; north raises the Y coordinate
cmp al,'E'  ->  [3C38] += n     ; east  raises the X coordinate
cmp al,'S'  ->  [3C39] -= n
    else        [3C38] -= n
```

Three independent things agree: the party-movement guards elsewhere in `qcast`
test the masks `C0`, `30`, `0C`, `03` for Y+1, X+1, Y−1, X−1, which are exactly
the four side fields above; the event direction masks use the same encoding
(doc 8); and the four edge transitions set the entry coordinate to the opposite
edge in each case, which the resolved map graph then confirms (doc 7).

`tools/mm1/dump_maze.py` prints Y up the page and X across it, which puts north
at the top.

The residual 1.65 % is not noise. Broken down by the pair of values involved:

```
1 <-> 3 : 362      2 <-> 1 :  53      everything else : 21
```

Nearly all disagreements are a plain wall on one side facing a `3` on the other,
or a wall facing a `2`. These look like deliberate one-sided constructions
(illusory walls, one-way passages, doors seen from one face), not parse errors.

## Plane 0 — the walls

Plane 0 is the **physical** wall plane, and the only one `draw` consults for
geometry. Counting how many of the 64 outward-facing border edges are open per
map:

| map group | plane 0 | plane 1 |
|---|---:|---:|
| all 5 towns, 9 caves, all named dungeons | **0** | 0 |
| outdoor areas `areaA1`–`areaE4` | 0–2 | 3–48 |
| `demon` | 28 | 29 |
| `astral` | **64** | 9 |

Plane 0 seals every town and dungeon perfectly, which is what a physical wall
plane must do, and leaves `astral` open on all 64 border edges — the Astral
Plane wraps around.

## Plane 1 — square state, not scenery

Plane 1 is **not** a second set of walls. Every routine that touches it says
what it is, and they split the byte in two.

The **low bit of each 2-bit field** (mask `0x55`) is a per-side latch:

```
unlock  4A6C   al = [3C10] & 0x55 & facing ;  nothing set -> nothing to unlock
search  4BE4   al = [3C10] & 0x55 & facing ;  nothing set -> nothing to search
               ...and on success, both do:
               al = facing & 0x55
               xor al, base2[pos]
               mov base2[pos], al           ; the latch is cleared
```

(`[3C10]` is just the current square's plane-1 byte, refreshed by `draw`.)
`inwait` uses the same test to decide which action the square even offers, and
`qcast` uses it to decide whether the party may move that way. So a set low bit
means **"this side is still locked / still unsearched"**, and succeeding at the
lock or the search clears it for the rest of the visit.

The **high bit of each field** (mask `0xAA`) is not directional at all — each of
the four is a separate per-tile flag, tested on its own with no facing mask:

| bit | mask | tested by | meaning |
|---:|---|---|---|
| 1 | `0x02` | `qcast`, `donespel` | no spellcasting on this square |
| 3 | `0x08` | `rest` (`0x6EE5`) | too dangerous to rest — prints exactly that |
| 5 | `0x20` | `draw` (`0x0F45`) | dark: with no light left, the view is not drawn |
| 7 | `0x80` | `stclr` (`0x11D3`), cleared by `erase` (`0x4449`) | this square has an event |

Bit 7 is the one that can be checked against something independent, and it
holds:

```
bit 7 set on   812 of the   817 squares that have an event handler   99.4 %
bit 7 set on 2,278 of the 13,263 squares that do not                 17.2 %
```

It is the renderer's cheap pre-filter: set means "ask this map's overlay about
this square". `erase` clears it when the overlay turns out to have nothing for
that square, so the question is asked once — which is why the extra 17 % exists
and why the dispatcher's not-found path calls `erase` (doc 8).

The per-map counts read the way the flags predict. `dusk` has 22 no-magic
squares and `doom` 33; `cave5` has 29 dark ones while towns have few or none;
`astral` marks 255 of its 256 squares as no-resting.

An earlier version of this document offered "plane 0 blocks, plane 1 is drawn"
as a working hypothesis. It is withdrawn: nothing draws from plane 1.

## Reading it

```sh
python tools/mm1/dump_maze.py sorpigal      # walls, with event squares marked
python tools/mm1/dump_maze.py areaa1 1      # the attribute plane
```
