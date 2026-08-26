# 8. The event system

This is the bridge between a map's squares and its behaviour: how stepping on a
particular tile ends up running a particular routine in that map's overlay.

## The path in

Three steps, all now named:

```
stclr   11D3   al = the square's plane-1 byte
               shl al,1            ; test bit 7
               if set -> jmp special
special 0D2E   di = [specaddr]     ; the overlay's dispatcher, 0xF4A1
               call di
```

`specaddr` (`DS:0x0134`) is one of the two pointers the overlay's entry stub
registers; the other, `ovdatadr` (`DS:0x0132`), is its data base (doc 3). Bit 7
of the maze's second plane is the pre-filter that decides whether the question
is worth asking at all — see [doc 4](04-maze-format.md).

## The dispatcher

18 bytes into every overlay, at `0xF4A1`. In Sorpigal:

```
F4A1  a0 3a 3c        mov  al, [3C3A]        ; the party's packed position
F4A4  bb 00 00        mov  bx, 0
F4A7  3a 87 73 c9     cmp  al, [bx+0C973h]   ; the map's list of event squares
F4AB  74 0e           je   found
F4AD  fe c3           inc  bl
F4AF  3a 1e 72 c9     cmp  bl, [0C972h]      ; how many entries
F4B3  72 f2           jb   F4A7              ; linear search
F4B5  e8 91 4f        call 4449h             ; erase   -- no event here
F4B8  e9 42 51        jmp  45FDh             ; encountr
F4BB  found: ...
```

**54 of the 55 overlays carry this routine**, with the same addresses and the
same variable; only the two jump displacements vary. `demon` is the exception —
see below.

The not-found path is the other half of the pre-filter: `erase` clears bit 7 for
this square, so the engine never asks about it again, and control falls through
to `encountr` for a wandering-monster roll.

## `[3C3A]` is a packed coordinate

`draw` (`0x0F45`) builds it:

```
0F55  a0 39 3c        mov  al, [3C39]        ; the north/south coordinate
0F58  b9 04 00        mov  cx, 4
0F5B  d2 e0           shl  al, cl
0F5D  12 06 38 3c     adc  al, [3C38]        ; the east/west coordinate
0F61  a2 3a 3c        mov  [3C3A], al
```

so **`[3C3A] = (north/south << 4) | (east/west)`**, the same byte that indexes
the maze planes. Which variable is which comes from the edge transitions:
`yplus` and `ymin` write `[3C39]`, `xplus` and `xmin` write `[3C38]` (doc 4).

## The table in the overlay's data

Three parallel arrays, at fixed addresses, preceded by a count:

```
offset 50   byte      N, the number of events on this map   (0xC972)
offset 51   N bytes   event squares, each packed as above   (0xC973)
   + N      N bytes   direction mask, one per event
   + 2N     N words   handler addresses, one per event
```

Offset 50 is exactly where the 50-byte parameter block ends (doc 7), so the two
structures tile with nothing in between.

**821 events across the 54 maps that have them**: 17–29 for a town, 6–10 for
open countryside. Handler entries of `FFFF` occur and mark a slot with no
routine.

### The direction mask

One byte per event, holding four 2-bit fields in **exactly the same layout as a
maze tile** (doc 4): bits 0-1 west, 2-3 south, 4-5 east, 6-7 north. A field is
`11` if the event fires when the party faces that way.

In 808 of 821 mask bytes (98.4 %) every field is `00` or `11` — it is a mask,
not a value. `FF` is by far the commonest (438), meaning "any direction"; then
the four single-direction masks `C0` north, `30` east, `0C` south, `03` west —
the same four values the party-movement code in `qcast` tests.

Ten of the thirteen exceptions are in `pp4` and are not masks at all; see below.
Three remain: two in `areae2` and one in `areae4`.

## Cross-check against the maze

Take only the events with a single-direction mask and look at what the maze has
on that side of that square:

| maze indexing | open | wall | **door** | solid |
|---|---:|---:|---:|---:|
| `(N/S)*16 + (E/W)` (correct) | 13 % | 51 % | **30 %** | 6 % |
| transposed | 41 % | 43 % | 8 % | 8 % |

Under the correct indexing a directional event overwhelmingly faces a wall or a
door, and 30 % face a door specifically — shops, inns and temples are entered
through one. Under the transposed indexing 41 % of events face open space, which
is meaningless.

This is what established the index order of `MAZEDATA.DTA`, and it is also the
best evidence that maze side value `2` is a door.

Rendering Sorpigal with events marked shows it directly — the directional ones
sit hard against a `D`:

```
     +---+---+---+---+---+---+---+---+---+###+---+---+---+---+---+---+
Y=15 |   |   D   |   |     * D           |   |   |       |       |   |
     +---+   +---+   +---+---+---+---+---+   +---+   +   +   +---+   +
Y=14 |   D   |       |                   | *     D *     |   | * |   |
     +---+   +---+   +   +---+###+---+   +   +---+---+---+   +---+   +
```

(The events with an `FF` mask fire from any direction and are not tied to a
door, so not every `*` has one.)

## What a handler does

The handlers are compiled C, and with the load address and the symbol map both
resolved they read straight off. Sorpigal's second handler, at `0xF508`, is the
sign outside the shops:

```
F508  call 0F544h                            ; the shared preamble below
F50B  mov  al, [3C3D]                        ; which way the party faces
F50E  cmp  al, 30h                           ; east?
F512  mov  word [3BD4], 0CA28h               ; "EULARDS FINE FOODS"
F518  mov  byte [3BC4], 6                    ;   at column 6
F520  cmp  al, 3                             ; west?
F524  mov  word [3BD4], 0CA3Dh               ; "B AND B BLACKSMITHS"
F532  mov  word [3BD4], 0CA53h               ; otherwise "THE INN OF SORPIGAL"
F53D  call 40E1h                             ; ph2      -- print it
F540  call 4582h                             ; wait_    -- wait for a key
F543  ret

F544  mov  al, 2
F546  call 1AB3h                             ; noises   -- a beep
F549  mov  word [3BD4], 0CA0Ah               ; "A SIGN ABOVE THE DOOR READS:"
F54F  mov  byte [3BC3], 15h                  ;   row 21
F554  mov  byte [3BC4], 2                    ;   column 2
F559  call 40E1h                             ; ph2
F55C  ret
```

The idiom is the same everywhere: put a string pointer in `bdw` (`DS:0x3BD4`),
set the row and column in `DS:0x3BC3` / `DS:0x3BC4`, call `ph2` to print,
`wait_` for a keypress, `stanp` for the standard one-line message, `random` to
roll, `erase` to mark the square done. Those six account for most of the 2,181
calls the overlays make (doc 3).

`python tools/mm1/disasm.py --ovr <map> <address>` prints this, with engine
calls named and string pointers resolved to their text.

## The two maps that differ

**`demon` has no per-square events at all.** Its dispatcher does not search
anything:

```
F4A1  e8 bd 4e     call 4361h            ; clrall7
      b8 72 c9     mov  ax, 0C972h
      a3 d4 3b     mov  [3BD4], ax       ; the string pointer
      b0 11        mov  al, 11h
      a2 c3 3b     mov  [3BC3], al       ; row 17
```

It prints the string at `0xC972` — the address every other map uses for its
event count — and runs a fixed sequence. `demon`'s text simply starts where the
parameter block ends:

```
A STRANGE ALIEN BEING IN A SHIMMERING
SILVER JUMPSUIT PROCLAIMS, "THIS IS A
SOUL MAZE AND YOU ARE ITS PRISONER! ...
```

Reading its byte at offset 50 as a count yields 65, which is just the `A` of
that sentence. That accounts for the whole discrepancy between the 886 events a
naive sum reports and the 821 that exist.

**`pp4` was never finished, and says so.** It declares 20 events and carries the
standard dispatcher, so the engine really does search 20 ids — but only the
first ten handler words are addresses. Read the remaining ten as bytes:

```
4144 474E 5245 2021 5544 474E 4F45 204E 4E55 4544
 D A  N G  E R  ! ␠  D U  N G  E O  N ␠  U N  D E
```

and the text immediately after the table continues `R CONSTRUCTION.` The
message **"DANGER! DUNGEON UNDER CONSTRUCTION."** was written into the handler
array itself. The ten unusable masks and the ten unusable handlers are the same
artefact, which also disposes of ten of the thirteen odd mask bytes above.

`pp1` is unfinished in a matching way: none of its four edge triples resolves to
a map (doc 7).

```sh
python tools/mm1/dump_maze.py sorpigal    # walls with event squares marked
python tools/mm1/ovr_text.py sorpigal     # the handler table and the text
python tools/mm1/disasm.py --ovr sorpigal 0xf508   # one handler
```
