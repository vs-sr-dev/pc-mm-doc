# 3. Per-map code overlays (`*.OVR`)

There are 55 `.OVR` files, one per map, named after the entries in the map table
(doc 1). They are **not** data files: they contain **8086 machine code**. Each
map's events, encounters and dialogue are a compiled overlay that the game loads
into a fixed buffer when you enter the map.

## Header

Every one of the 55 files starts with the same 14-byte header, and `ovloader_`
(`0x001C`) validates every field of it:

| Offset | Size | `SORPIGAL.OVR` | Meaning |
|---:|---:|---|---|
| `+0` | word | `0x00F2` | **magic number** — mismatch aborts with error 30 |
| `+2` | word | `0xF48F` | **code destination**, must be ≥ `0xF48F` |
| `+4` | word | `0x0346` | **code size** |
| `+6` | word | `0xC940` | **data destination**, must be ≥ `0xC940` |
| `+8` | dword | `0x000004E0` | **data size** |
| `+12` | word | `0xF797` | **entry point** — the loader jumps here when done |

The file body is `code` followed by `data`, and

```
14 + code_size + data_size == file size
```

holds **exactly for all 55 files** (Sorpigal: 14 + 838 + 1248 = 2100).

## The loader

`ovloader_` takes the map name, appends the `.ovr` at `DS:0x0002`, and reads the
file in two pieces — the code with `_csread_`, into the *code* segment, and the
data with an ordinary `read_`, into the data segment:

```
[0xC830] = name                    ; kept for the error message
open(strcat(strcpy(buf, name), ".ovr"))          ; fail -> loadabort_(10)
read(fd, header, 14)                             ; short -> loadabort_(20)
header[+0] != 0x00F2                             ->        loadabort_(30)
header[+6] + data size > _mbot_                  ->        loadabort_(40)
header[+2] < 0xF48F  or  header[+6] < 0xC940     ->        loadabort_(60)
_csread_(fd, header[+2], header[+4])             ; short -> loadabort_(50)
read_   (fd, header[+6], data size)              ; short -> loadabort_(50)
close(fd)
return header[+12]        ; and the caller does  jmp ax
```

`loadabort_` (`0x010D`) formats `"Error %d loading overlay: %s"` from that code
and the saved name, prints it, and exits with status 100. The `%d` values are
the six above.

The memory check is against `_mbot_`, the C runtime's bottom-of-heap variable —
so the overlay data area is heap, in the ordinary data segment, and `0xC940` is
simply where it starts (doc 2).

## The entry point

Header `+12` is always exactly 62 bytes below the end of the loaded code, and
those 62 bytes are the compiler's overlay prologue, appended after the map's own
code. In Sorpigal:

```
F797  pop  [0CE1Eh]              ; stash the return address
F79B  pop  cx
F79C  mov  [0CE1Ah], sp          ; save sp, bp, si, di in the overlay's data tail
F7A0  mov  [0CE1Ch], bp
F7A4  mov  [0CE16h], si
F7A8  mov  [0CE18h], di
F7AC  cld
F7AD  mov  di, 0CE20h            ; zero-fill the overlay's BSS...
F7B0  mov  cx, 0CE20h            ; ...which is empty in all 55 files
F7B3  sub  cx, di
F7B5  shr  cx, 1
F7B7  je   F7BD
F7B9  sub  ax, ax
F7BB  rep  stosw
F7BD  call 0F48Fh                ; the map's own entry, at the start of the code
F7C0  mov  bp, [0CE1Ch]          ; restore and return
      ...
F7D1  jmp  [0CE1Eh]
```

`0xCE20` is `0xC940 + 0x4E0`, the end of this overlay's data block; the save
slots are the six bytes below it. All 55 files have `di == cx`, so no overlay
carries uninitialised data and the fill never runs.

Only then does the map's own entry stub run:

```
F48F  b8 a1 f4        mov  ax, 0F4A1h     ; -> its own dispatch routine
F492  a3 34 01        mov  [0134h], ax    ; specaddr
F495  b8 40 c9        mov  ax, 0C940h     ; -> its own data block
F498  a3 32 01        mov  [0132h], ax    ; ovdatadr
F49B  c6 06 a6 0d 00  mov  byte [0DA6h], 0
F4A0  c3              ret
```

Two pointers registered with the engine, and that is all. `specaddr` is what
`special` (`0x0D2E`) calls when a square has an event; `ovdatadr` is what
`getod` and `putod` index. See [doc 8](08-events.md).

### Verifying the two destinations

**Code, `0xF48F`.** Overlay code calls the engine with ordinary `call rel16`, so
if the load address is right, every target must land on a real function. Taking
all 2,181 `E8` bytes across the 55 overlays and solving for the base that
maximises exact hits against the 344 distinct code addresses in `MM.RSM`:

| candidate base | calls resolving to an exact symbol |
|---|---:|
| **`0xF48F`** | **1,750 of 2,181 — 80.2 %** |
| next best | 749 — 34.3 % |
| chance | ~11.5 — 0.5 % |

Two further things agree: the loader refuses any header naming a code
destination below `0xF48F`, and `MM.RSM`'s own header carries `0xF48F` at
offset +10 as the top of the code segment.

**Data, `0xC940`.** Overlay code is full of `mov word [3BD4h], imm` instructions
that hand a string pointer to the engine. All **197** such immediates across all
55 files fall inside `[+6, +6 + (+8))` — 100 %. The loader likewise refuses any
data destination below `0xC940`.

## What map code actually does

Because the load address is known, every engine call can be named. Ranked over
all 55 overlays:

| calls | maps using it | routine | what it is |
|---:|---:|---|---|
| 377 | 54/55 | `stanp` | print the standard message line |
| 371 | 55/55 | `wait_` | wait for a keypress |
| 327 | 55/55 | `clrbtm2` | clear the text area |
| 155 | 44/55 | `ph2` | print at the set row and column |
| 152 | 53/55 | `erase` | clear this square's event flag |
| 121 | 33/55 | `random` | roll |
| 57 | 36/55 | `noises` | play a sound |
| 42 | 28/55 | `pnames` | list the party |
| 41 | 13/55 | `setgraph` | switch to the graphics view |
| 30 | 21/55 | `clrall7` | clear the whole text window |
| 27 | 17/55 | `ph2one` | print one line |
| 14 | 7/55 | `dosound` | play a longer effect |

Almost every call is a text or screen primitive or a dice roll. Map code prints
a message, clears the text area, rolls `random`, branches. These overlays are
event scripts — they are simply compiled to native code instead of interpreted.
A worked example of one handler is in [doc 8](08-events.md).

```sh
python tools/mm1/ovr_calls.py               # the table above
python tools/mm1/ovr_calls.py sorpigal      # one map's calls in address order
python tools/mm1/disasm.py --ovr sorpigal 0xf508    # one handler, annotated
```

## Consequences of the design

The overlays are **absolutely addressed and non-relocatable**. `0xF48F` and
`0xC940` are baked into all 55 files, the engine entry points are reached by
fixed relative offsets, and `0xC940` is literally "wherever the linker happened
to stop, plus a bit". Relinking `MM.EXE` — adding one global, growing one table
— moves the end of the data segment and invalidates every `.OVR` file at once.
The game and its 55 overlays had to be built together, as one unit, every time.
