# 8. The event system

This is the bridge between a map's squares and its behaviour: how stepping on a
particular tile ends up running a particular routine in that map's overlay.

## The dispatcher

Every overlay's entry stub registers a pointer at `[0134h]` (doc 3). It points
at the overlay's own dispatch routine, 18 bytes in, at `0xF4A1`. In Sorpigal:

```
F4A1  a0 3a 3c        mov  al, [3C3A]        ; the party's packed position
F4A4  bb 00 00        mov  bx, 0
F4A7  3a 87 73 c9     cmp  al, [bx+0C973h]   ; the map's list of event squares
F4AB  74 0e           je   found
F4AD  fe c3           inc  bl
F4AF  3a 1e 72 c9     cmp  bl, [0C972h]      ; how many entries
F4B3  72 f2           jb   F4A7              ; linear search
F4B5  e8 91 4f        call 4449h             ; stanp2  -- nothing here
F4B8  e9 42 51        jmp  45FDh             ; resgrph
F4BB  found: ...
```

**54 of the 55 overlays carry this routine byte-for-byte**, with the same
addresses and the same variable. `demon` is the exception and uses a different
shape.

## `[3C3A]` is a packed coordinate

`plot` (`0x0F45`) builds it:

```
0F55  a0 39 3c        mov  al, [3C39]        ; X
0F58  b9 04 00        mov  cx, 4
0F5B  d2 e0           shl  al, cl
0F5D  12 06 38 3c     adc  al, [3C38]        ; Y
0F61  a2 3a 3c        mov  [3C3A], al
```

so **`[3C3A] = (X << 4) | Y`**. Which variable is which comes from the movement
routines: `yplus` (`0x5022`) and `ymin` (`0x5076`) both write `[3C38]`, and
`xplus` (`0x504C`) writes `[3C39]`.

## The table in the overlay's data

Three parallel arrays, at fixed addresses, preceded by a count:

```
0xC972   byte      N, the number of events on this map
0xC973   N bytes   event squares, each (X << 4) | Y
0xC973+N N bytes   direction mask, one per event
0xC973+2N N words  handler addresses, one per event
```

816 events across the 55 maps: 17–29 for a town, 6–10 for open countryside.
Handler entries of `FFFF` occur and mark a slot with no routine.

### The direction mask

One byte per event, holding four 2-bit fields in **exactly the same layout as a
maze tile** (doc 4): bits 0-1 `-Y`, 2-3 `-X`, 4-5 `+Y`, 6-7 `+X`. A field is
`11` if the event fires when the party faces that way.

In 808 of 821 mask bytes (98.4 %) every field is `00` or `11` — it is a mask,
not a value. `FF` is by far the commonest (438), meaning "any direction"; then
the four single-direction masks `C0`, `03`, `0C`, `30`.

## Cross-check against the maze

Take only the events with a single-direction mask and look at what the maze has
on that side of that square:

| maze indexing | open | wall | **door** | solid |
|---|---:|---:|---:|---:|
| `x*16 + y` (correct) | 14 % | 50 % | **30 %** | 6 % |
| `y*16 + x` | 41 % | 42 % | 8 % | 9 % |

Under the correct indexing a directional event overwhelmingly faces a wall or a
door, and 30 % face a door specifically — shops, inns and temples are entered
through one. Under the transposed indexing 41 % of events face open space, which
is meaningless.

This is what established that `MAZEDATA.DTA` is column-major, and it is also the
best evidence that maze side value `2` is a door.

Rendering Sorpigal with events marked shows the result directly — every `*` sits
against a `D`:

```
 0  |   |   # * |   # * |   # * |       | *     |   |   |   |   |   |
    +---+---+---+---+---+---+---+---+---+###+---+---+---+---+---+---+
    0   1   2   3   4   5   6   7   8   9   10  11  12  13  14  15
```

```sh
python tools/mm1/dump_maze.py sorpigal    # walls with event squares marked
python tools/mm1/ovr_text.py sorpigal     # the handler table and the text
```

## Loose ends

* `demon` uses a different dispatcher and is not covered by the layout above.
* `pp4` declares 20 events but only 10 of its handler words are valid code
  addresses; the rest is text. Either its count means something else or the
  arrays are laid out differently.
* What the handler does once selected — and how the 13 mask bytes with `01` or
  `10` fields behave — is not traced.
