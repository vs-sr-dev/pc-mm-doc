# 3. Per-map code overlays (`*.OVR`)

There are 55 `.OVR` files, one per map, named after the entries in the map table
(doc 1). They are **not** data files: they contain **8086 machine code**. Each
map's events, encounters and dialogue are a compiled overlay that the game loads
into a fixed buffer when you enter the map.

`SORPIGAL.OVR` begins, after its header:

```
b8 a1 f4        mov  ax, 0F4A1h     ; -> its own dispatch table
a3 34 01        mov  [0134h], ax
b8 40 c9        mov  ax, 0C940h     ; -> its own data block
a3 32 01        mov  [0132h], ax
c6 06 a6 0d 00  mov  byte [0DA6h], 0
c3              ret
```

The entry routine registers two pointers with the engine and returns. Everything
after that is the map's event code.

## Header

Every one of the 55 files starts with the same 14-byte header. It is two
matched (destination, size) load descriptors:

| Offset | Size | `SORPIGAL.OVR` | Meaning |
|---:|---:|---|---|
| `+0` | word | `0x00F2` | constant across all 55 files; **unknown** |
| `+2` | word | `0xF48F` | **code destination** |
| `+4` | word | `0x0346` | **code size** |
| `+6` | word | `0xC940` | **data destination** |
| `+8` | dword | `0x000004E0` | **data size** |
| `+12` | word | `0xF797` | always `0xF451 + code size`; **unknown** |

The file body is `code` followed by `data`, and

```
14 + code_size + data_size == file size
```

holds **exactly for all 55 files** (Sorpigal: 14 + 838 + 1248 = 2100).

### Verifying the two destinations

**Code, `0xF48F`.** Overlay code calls the engine with ordinary `call rel16`, so
if the load address is right, every target must land on a real function. Taking
all 2,181 `E8` bytes across the 55 overlays and solving for the base that
maximises exact hits against the 345 code symbols in `MM.RSM`:

| candidate base | calls resolving to an exact symbol |
|---|---:|
| **`0xF48F`** | **1,750 of 2,181 — 80.2 %** |
| next best | 749 — 34.3 % |
| chance | ~11.5 — 0.5 % |

Independently: the overlay's own first instruction loads `0xF4A1`. Under
`0xF48F` that resolves to file offset `0x20`, a clean `mov al,[3C3A]`
instruction boundary; under any neighbouring base it lands mid-instruction.

**Data, `0xC940`.** Overlay code is full of `mov word [3BD4h], imm`
instructions that hand a string pointer to the engine. All **197** such
immediates across all 55 files fall inside `[+6, +6 + (+8))` — 100 %.

What is established is the offset, not the segment: `0xC940` collides with live
content in both known segments, so overlay data must go to a third, probably
run-time-allocated block. See [doc 2](02-executable-and-symbols.md).

Fields `+0` and `+12` are still unexplained. `+12` tracks code size with a
constant offset (`+12 − code size = 0xF451` in every file), 62 bytes below the
code destination, but nothing observed depends on it.

## What map code actually does

Because the load address is known, every engine call can be named. Ranked over
all 55 overlays:

| calls | maps using it | routine |
|---:|---:|---|
| 377 | 54/55 | `setgraph` |
| 371 | 55/55 | `random` |
| 327 | 55/55 | `clr13to19` |
| 155 | 44/55 | `ph2one` |
| 152 | 53/55 | `stanp2` |
| 121 | 33/55 | `outline` |
| 57 | 36/55 | `getdisk2` |
| 42 | 28/55 | `ph2` |
| 41 | 13/55 | `move21` |
| 30 | 21/55 | `clrp2` |
| 27 | 17/55 | `ph1` |
| 14 | 7/55 | `noises` |

Almost every call is a text/screen primitive or a dice roll. Map code prints a
message, clears lines 13–19, rolls `random`, branches. These overlays are event
scripts — they are simply compiled to native code instead of interpreted.

```sh
python tools/mm1/ovr_calls.py            # the table above
python tools/mm1/ovr_calls.py sorpigal   # one map's calls in address order
```

## Consequences of the design

The overlays are **absolutely addressed and non-relocatable**. `0xF48F` and
`0xC940` are baked into all 55 files, the engine entry points are reached by
fixed relative offsets, and `0xC940` is literally "wherever the linker happened
to stop". Relinking `MM.EXE` — adding one global, growing one table — moves
`_Eol_` and invalidates every `.OVR` file at once. The game and its 55 overlays
had to be built together, as one unit, every time.

## Not yet done

The overlay code has not been disassembled beyond its call targets. That is
where all per-map behaviour lives: which square triggers what, the text of every
message, treasure and monster placement, and map-to-map transitions. See
[open questions](open-questions.md).
