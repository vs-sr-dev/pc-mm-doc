# 4. Maze format — `MAZEDATA.DTA`

28,160 bytes = **55 maps × 512 bytes**, indexed by the map table in doc 1.
Each 512-byte block is two 256-byte planes:

```
+0x000  wall plane        16x16 tiles, one byte each
+0x100  attribute plane   16x16 tiles, one byte each
```

Both planes are stored **column-major** — `index = x*16 + y`, the same
convention the graphics use (doc 5) — and both use the same per-tile encoding:
**four 2-bit fields, one per side of the tile.**

## Byte layout

| Bits | Axis | Compass |
|---|---|---|
| 0–1 | −Y | **West** |
| 2–3 | −X | **South** |
| 4–5 | +Y | **East** |
| 6–7 | +X | **North** |

| Value | Meaning |
|---|---|
| 0 | open |
| 1 | wall |
| 2 | door |
| 3 | special / solid fill |

Value 2 is a door: events with a single-direction mask face one 30 % of the time
(doc 8), which is what shop and inn entrances look like.

### How this was determined

A wall between two tiles is stored twice, once from each side, so the correct
field assignment is the one under which neighbours agree. Testing all 24
permutations of the four fields against both row-major and column-major
orderings, across all 55 maps:

| assignment | agreement |
|---|---|
| **+X = bits 6-7, −X = bits 2-3, +Y = bits 4-5, −Y = bits 0-1** | **98.35 %** |
| next best | 75.23 % |

The gap is decisive.

Reciprocity alone cannot tell row-major from column-major, because transposing a
map preserves it — both scored 98.35 %. The tie was broken separately, by the
event tables in the overlays: see doc 8. Session 1 documented this as row-major,
which was wrong, and every map it rendered came out transposed.

### The compass

North is **+X** and east is **+Y**. This comes from the teleport spell in
`qcast`, which prompts `DIRECTION (N,E,S,W)`, stores the typed letter at
`[2D51h]`, and then dispatches on it at `0x94D0`:

```
cmp al,'N'  ->  [3C39] += n     ; X   -> north is +X
cmp al,'E'  ->  [3C38] += n     ; Y   -> east  is +Y
cmp al,'S'  ->  [3C39] -= n     ; X
    else        [3C38] -= n     ; Y   -> west  is -Y
```

(`[3C39]` is X and `[3C38]` is Y — doc 8.) Three independent things agree with
it: the party-movement guards elsewhere in `qcast` test the masks `C0`, `30`,
`0C`, `03` for X+1, Y+1, X−1, Y−1, which are exactly the four side fields above;
the event direction masks use the same encoding (doc 8); and the four
edge-transition routines set the entry coordinate to the opposite edge in each
case (doc 7).

So `tools/mm1/dump_maze.py` prints X up the page and Y across it, which puts
north at the top.

The residual 1.65 % is not noise. Broken down by the pair of values involved:

```
1 <-> 3 : 362      2 <-> 1 :  53      everything else : 21
```

Nearly all disagreements are a plain wall on one side facing a `3` on the other,
or a wall facing a `2`. These look like deliberate one-sided constructions
(illusory walls, one-way passages, doors seen from one face), not parse errors.

## Which plane is which

Plane 0 is the **physical** wall plane. Counting how many of the 64 outward-
facing border edges are open per map:

| map group | plane 0 | plane 1 |
|---|---:|---:|
| all 5 towns, 9 caves, all named dungeons | **0** | 0 |
| outdoor areas `areaA1`–`areaE4` | 0–2 | 3–48 |
| `demon` | 28 | 29 |
| `astral` | **64** | 9 |

Plane 0 seals every town and dungeon perfectly, which is what a physical wall
plane must do, and leaves `astral` open on all 64 border edges — the Astral
Plane wraps around. Plane 1 does neither: it leaves outdoor borders wide open.

Plane 1 is nonetheless tile-aligned with plane 0 (40.4 % of its bytes are
identical, versus ~10 % at any shifted alignment) and is itself directional
(88–91 % neighbour agreement). So it is a second per-side 2-bit value, not a
per-tile attribute.

Its purpose is **not settled**. The working hypothesis is that plane 0 is what
blocks movement and plane 1 is what is drawn, which would account for the two
interesting off-diagonal cases in the joint histogram:

| plane 0 | plane 1 | count | reading |
|---:|---:|---:|---|
| 1 | 0 | 1,852 | blocks but is not drawn — invisible wall |
| 0 | 1 | 544 | drawn but does not block — illusory wall |
| 3 | 0 | 4,116 | solid fill outside the playable area |

It also fits the outdoor border result: you see across the edge of an outdoor
map but cannot walk off it, and the overlay code handles the transition. This
is consistent with everything measured but has not been confirmed against the
rendering code.

One combination was tested and **ruled out**: treating the two planes as a
combined 4-bit wall type drops neighbour agreement to 86.63 %, well below
plane 0's own 98.35 %. The planes are independent.

## Reading it

```sh
python tools/mm1/dump_maze.py sorpigal      # physical walls
python tools/mm1/dump_maze.py areaa1 1      # attribute plane
```
