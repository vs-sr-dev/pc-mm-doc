# 3. Per-map code overlays (`*.OVR`)

There are 55 `.OVR` files, one per map, named after the entries in the map table
(doc 1). They are **not** data files: they contain **8086 machine code**. Each
map's events, encounters and dialogue are a compiled overlay that the game loads
over a fixed buffer when you enter the map.

`SORPIGAL.OVR` begins, after its header:

```
b8 a1 f4        mov  ax, 0F4A1h
a3 34 01        mov  [0134h], ax
b8 40 c9        mov  ax, 0C940h
a3 32 01        mov  [0132h], ax
c6 06 a6 0d 00  mov  byte [0DA6h], 0
c3              ret
```

The entry routine registers two pointers with the engine — one into its own code
at `0xF4A1`, one to the overlay data area at `0xC940` — and returns. Everything
after that is the map's event code, reached through the table at `0xF4A1`.

## Header

Every one of the 55 files starts with the same 14-byte header:

| Offset | Size | `SORPIGAL.OVR` | Meaning |
|---:|---:|---|---|
| `+0` | word | `0x00F2` | constant across all 55 files |
| `+2` | word | `0xF48F` | constant; also appears in the `MM.RSM` header |
| `+4` | word | `0x0346` | **code size** |
| `+6` | word | `0xC940` | **destination of the data block** (`_Eol_ + 2`) |
| `+8` | dword | `0x000004E0` | **data size** |
| `+12` | word | `0xF797` | **source of the data block** = `0xF451 + code size` |

The file body is `code` followed by `data`, and

```
14 + code_size + data_size == file size
```

holds **exactly for all 55 files** (Sorpigal: 14 + 838 + 1248 = 2100). Fields
`+6`, `+8` and `+12` are destination, length and source of a block copy: the
loader reads the whole file to `0xF443`, then moves the data half down to
`0xC940`, leaving the code in place at `0xF451`.

`+12 = 0xF451 + code_size` is what fixes the load address: the code lands at
`0xF451`, so the 14-byte header lands at `0xF443`.

Cross-check: the overlay's code is full of `mov word [3BD4h], imm` instructions
whose immediates (`0xCA28`, `0xCA3D`, `0xCB53`, `0xCDCB`, …) all fall inside
`0xC940 … 0xC940 + 0x4E0`. They are pointers to the map's text strings in the
copied data block, which is what confirms the destination field.

The matching engine-side symbols in `MM.RSM` are `ovbgn` (`0x0000`),
`ovloader_` (`0x010D`) and `loadabort_` (`0x0142`), and the error string at data
offset `0x07B7` reads `Error %d loading overlay: %s$`.

## Not yet done

The overlay code itself has not been disassembled. That is the largest remaining
body of work and the place where all per-map behaviour lives: which square
triggers what, the text of every message, treasure and monster placement, and
the map-to-map transitions. See [open questions](open-questions.md).
