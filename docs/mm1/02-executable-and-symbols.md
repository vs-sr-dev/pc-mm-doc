# 2. Executable layout, and the symbol map the game shipped with

## MZ header

`MM.EXE` is a plain DOS MZ executable with an unusually bare header:

| Field | Value | Note |
|---|---|---|
| `e_cblp` / `e_cp` | `0x01E0` / `0x00E9` | image = 232·512 + 480 = **118,752 bytes** |
| `e_crlc` | `3` | only three relocations |
| `e_cparhdr` | `0x0020` | 512-byte header, so image starts at file `0x200` |
| `e_ss:e_sp` | `0x1E42:0x4000` | |
| `e_cs:e_ip` | `0x0000:0xEFA0` | entry inside the first segment |
| relocations | `0x03A7`, `0x03C6`, `0xEFA1` | all with segment `0x0000` |

Three relocations for a 116 KB program means almost nothing is a far pointer.
Two of them fall inside `clearkey`/`crit_err` and one at the entry point — the
far pointers an interrupt handler needs, and nothing else. This is a two-segment
program that computes what it needs at runtime.

## MM.RSM — the shipped symbol map

`MM.RSM` is not used by the game. It is the **linker's symbol map, accidentally
shipped with the retail files**, and it names 579 symbols with their addresses.
This is the single most useful artefact in the distribution — and reading it
correctly is what everything else in this repository rests on.

### The record format, and the trap in it

After a 35-byte header the file is a flat run of records:

```
<name> 0x00  <type>  <class>  <word>
```

`type` is `0x02` for code and `0x03` for data; `class` is `0x28` throughout.
The trap is the trailing word. It reads like the symbol's own address, and it
is not: **it is where the symbol ends.** A symbol therefore starts at the end of
the previous symbol *of the same type*, and the first symbol of each type starts
at `0x0000`.

That also hands over every symbol's size for free, which is how several tables
below are counted exactly.

Read naively, every symbol in the file is off by one record, and the whole
program is mis-named in a way that stays plausible — an earlier version of this
document, and of docs 3 and 5–8, did exactly that. Four independent checks fix
the alignment, each one a routine whose behaviour is unmistakable:

| address | naive name | correct name | what the code there actually does |
|---|---|---|---|
| `0x010D` | `ovloader_` | **`loadabort_`** | formats `"Error %d loading overlay: %s"` and exits with code 100 |
| `0x0D35` | `special` | **`loadmaze`** | sets the `MAZEDATA.DTA` seek offset, calls `readmaze_`, then `ovloader_` |
| `0x0D5B` | `loadmaze` | **`getod`** | reads one byte from the overlay data block at `[ovdatadr] + bx` |
| `0x6EE5` | `getviewo` | **`rest`** | prints `*** TOO DANGEROUS TO REST HERE!` |

More fall out of the same correction and all agree. `soundflag_` lands on two
zero bytes instead of on code. `blk24`, `blk16` and `blk12` land on runs of
exactly 24, 16 and 12 blanks. `knight`, `pal`, `arc`, `clrc`, `sor` and `rob`
land on `"1) KNIGHT"` … `"6) ROBBER"`, one per class, in order. And the sizes
come out right where they are checkable:

| symbol | size | reading |
|---|---:|---|
| `font` / `narrowfont` | 1040 / 520 | 130 characters at 8 bytes, then the same 130 at 4 |
| `compbuf_` | 16,000 | one full CGA frame of decompression input |
| `bufbasel` | 402 | 200 screen-row offsets, one per scanline |
| `scrfile_` | 192 | a filename buffer, and it contains `screen0` |
| `itemlow` / `itemhigh` | 2040 / 4080 | 85 and 170 records of 24 bytes |
| `mondata` | 6240 | 195 records of 32 bytes |
| `endroster` | 18 | one occupancy byte per roster slot (doc 6) |

Under the naive reading none of those are whole numbers of anything.

`tools/mm1/mmlib.py` does the pairing; `python tools/mm1/dump_symbols.py`
prints the corrected list.

### What the names show

```
code 0000  main_            code 0f45  draw             data 0134  specaddr
code 001c  ovloader_        code 128c  getshape         data 0d04  widthh_
code 010d  loadabort_       code 14fb  uncomp           data 3cfa  base1
code 0142  readmaze_        code 1504  nextwall         data 917a  itemlow
code 0d35  loadmaze         code 4436  stanp            data a962  mondata
code 0d5b  getod            code 4582  wait_            data c1c2  tp1
code 0d66  putod            code 509d  loadnext         data c698  _STKSIZ_
```

`readmaze_`, `readrost_`/`writrost_`, `readpix_` for I/O; `uncomp`,
`getshape`, `nextwall`, `draw`, `buildega`, `to_ega`, `cga_movsw` for
rendering; `town`, `tavern`, `temple`, `training`, `blacks`, `inn` for town
services; `combat`, `figatt`, `shootatt`, `regenmon`, `chkmisl` for the battle
system.

Runtime symbols such as `_STKSIZ_`, `_HEAPSIZ_`, `_mbot_`, `_mtop_`, `_PSP_`,
`ctp__`, `_ioflg_`, `errno_` identify a mid-1980s DOS C runtime, while names
like `cga_movsw`, `ega_movax` and `egamovsw` are hand-written assembly. The game
is a C and assembly mix, with the inner rendering loops in assembly.

The trailing underscore on `main_`, `ovloader_`, `readmaze_`, `Sound_`, `wait_`
marks the C-callable entry points; the un-suffixed names are internal assembly
labels.

### The header

Two of the header's words are load-time constants that the overlays depend on:

| offset | value | meaning |
|---|---|---|
| `+10` | `0xF48F` | top of the code segment — and the overlay code destination |
| `+12` | `0xC830` | size of the data segment |
| `+18` | `0x0243` | 579, the symbol count |

## Two segments

Type `0x02` and type `0x03` form **distinct address spaces**, not one. Type
`0x02` runs from `0x0000` to `0xF482`, type `0x03` from `0x0000` to `0xC82E`;
they overlap numerically, yet their contents are 64 KB apart in the file.

```
file 0x000200  image 0x00000   code segment, ends with brk_ at 0xF482
file 0x0109B0  image 0x107B0   data segment, 0xC830 bytes
file 0x01D1E0  image 0x1CFE0   end of image = end of the data segment
```

**The data segment begins at file offset `0x109B0`.** Two independent
derivations agree:

* The header says the segment is `0xC830` bytes, and it ends exactly at the end
  of the load image, so it starts `0xC830` below it: `0x1D1E0 − 0xC830`.
* Searching every possible base for one where the twelve wall sprites named by
  the tables at `DS:0x0CD2` and `DS:0x0CEA` total exactly the 11,200 bytes a
  `WALLPIX.DTA` set decompresses to gives **exactly one hit** across the whole
  file, at `0x109B0` (doc 5). The sprites render correctly at that base.

Content confirms it. `itemlow` lands on `CLUB`, the first item; `mondata` on
`FLESH EATER`, the first monster; `tp1` on the first hint string; and the
16 KB of nothing between `bufbasel` and `itemlow` is exactly the run of
zero bytes the image has there, because those symbols are runtime buffers.

An earlier version of this document put the base at `0x10200`. That is `0x7B0`
too low — and `0x7B0` happens to be a whole number of 24-byte item records,
which is why the item table appeared to line up under both.

## Where the overlays land

Every `.OVR` header names two destinations, `0xF48F` for code and `0xC940` for
data, and both are confirmed by measurement (see [doc 3](03-map-overlays.md)).

**Overlay code, `0xF48F`.** It sits 13 bytes above the end of `brk_`
(`0xF3F6`–`0xF482`), the last code symbol — and `brk_` is a C runtime's
program-break variable, i.e. the top of the static image. The value is also written into the `MM.RSM` header at
`+10`, so the toolchain computed it and the overlays were built against it. The
overlay code buffer is exactly "just past the end of everything the linker
placed", which is also why overlay code can call the engine with plain
`call rel16`.

**Overlay data, `0xC940`.** It is an offset in the data segment, `0x110` bytes
above the end of the linked data (`0xC830`). Two things establish that directly:

* The engine reaches overlay data only through `getod` (`0x0D5B`) and `putod`
  (`0x0D66`), and both do `si = [ovdatadr]; byte at [si + bx]` — a plain
  DS-relative access, with `ovdatadr` (`DS:0x0132`) holding the `0xC940` the
  overlay's entry stub wrote there.
* `loadabort_` formats its error message from the word at `DS:0xC830`, the
  first word above the linked data, so that region is live addressable memory
  in the same segment and not a separate allocation.

An earlier version of this document reported that `0xC940` collided with the
monster table in one segment and with 51 named routines in the other, and
concluded a third address space was needed. Both collisions were artefacts of
the wrong data base and the wrong symbol alignment. Withdrawn.

Two pieces of arithmetic point at the same gap, and both are exact:

```
_Eol_  = 0xC93E        an absolute symbol -- "end of load"
0xC940 = _Eol_ + 2
0xC940 = 0xC830 + 0x110      the header's data size, plus the word at header +14
```

`0xC830` is what the file holds; the remaining `0x10E` bytes are uninitialised
data the runtime clears, so `_Eol_` is where the program really stops and the
overlay data area begins two bytes later. Session 1 noticed `_Eol_ + 2` and
session 2 retracted it as a coincidence, on the grounds that initialised data
continued past `_Eol_`. Under the corrected base it does not — `DS:0xC93E` is
already past the end of the image — so the retraction goes and the observation
stands.
