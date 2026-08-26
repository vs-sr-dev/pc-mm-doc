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

## Two segments

Symbols (below) carry a type byte: `0x02` and `0x03`. The two form **distinct
address spaces**, not one. Type `0x02` runs from `0x0000` to `0xF482`, type
`0x03` from `0x50A6` to `0xC82E`; they overlap numerically, yet `itemlow`
(type `0x03`, `0x9972`) and `combat` (type `0x02`, `0x9799`) sit 473 apart while
their contents are 64 KB apart in the file. Two segments:

```
file 0x000200  image 0x00000   type-0x02 space (code)   last symbol brk_ at 0xF482
file 0x010200  image 0x10000   type-0x03 space (data)   content runs to 0xCFE0
file 0x01D1E0  image 0x1CFE0   end of image
```

**The data segment begins at file offset `0x10200`.** This was confirmed, not
assumed: the symbol `itemlow` (`0x9972`) lands exactly on the first record of
the item-name table (`SPEAR`, `SHORT SWORD`, `MACE`, …) and `itemhigh`
(`0xA962`) lands exactly on the first record of the second item table
(`10 FOOT POLE`, `GARLIC`, `WOLFSBANE`, …). Two independent exact hits on
record boundaries.

## Where the overlays land

Every `.OVR` header names two destinations, `0xF48F` for code and `0xC940` for
data, and both are confirmed by measurement (see [doc 3](03-map-overlays.md)).

**Overlay code, `0xF48F`, is placed.** It sits 13 bytes above `brk_` (`0xF482`),
the last type-`0x02` symbol — and `brk_` is a C runtime's program-break
variable, i.e. the top of the static image. The overlay code buffer is exactly
"just past the end of everything the linker placed", which is also why overlay
code can call the engine with plain `call rel16`.

**Overlay data, `0xC940`, is not placed.** `0xC940` cannot be an offset in
either known segment, because both already hold live content there: in the
type-`0x03` space it is the tail of the monster table (`AOKRIM`) with the hint
strings 47 bytes later, and in the type-`0x02` space it is code, with 51 named
routines between `0xC940` and `0xEC9B`. Loading a map there would destroy either
one.

So the overlay data area is a third address space, most likely a block allocated
at run time — the engine has a `getseg_` routine at `0x061A`. Resolving this
means reading `ovloader_` (`0x010D`). Until then, treat `0xC940` as an offset
whose segment is unknown.

An earlier version of this document claimed `0xC940` was `_Eol_ + 2`, the end of
the linked image. That does not hold: `_Eol_` is an absolute symbol (type
`0x09`), initialised data continues for another 1,186 bytes past it, and the
arithmetic was a coincidence.

## MM.RSM — the shipped symbol map

`MM.RSM` is not used by the game. It is the **linker's symbol map, accidentally
shipped with the retail files**, and it names 579 symbols with their addresses.
This is the single most useful artefact in the distribution.

Record format, after a 0x23-byte header:

```
<name> 0x00  <type>  <class>  <offset:word LE>
```

`type` is `0x02` for code and `0x03` for data (`class` is `0x28` for every
symbol). Run `python tools/mm1/dump_symbols.py` for the full list; a sample:

```
code 0000  ovbgn            code 0d5b  loadmaze         data 9972  itemlow
code 001c  main_            code 1504  uncomp           data a962  itemhigh
code 010d  ovloader_        code 1878  nextwall         data c1c2  mondata
code 0142  loadabort_       code 4582  random           data c5dc  endtipsc
code 0188  readmaze_        code 9799  combat           data c69a  _STKSIZ_
code 0222  readwall_        code 6f98  rest             data c804  _PSP_
code 0231  readmon_         code 7dbd  equip            abs  c93e  _Eol_
```

The names alone map out the whole program: `readmaze_`, `readwall_`, `readmon_`,
`readscr_`, `readrost_`/`writrost_` for I/O; `uncomp`, `getshape`, `nextwall`,
`plot`, `draw`, `buildega`, `to_ega`, `cga_movsw` for rendering; `town`,
`tavern`, `temple`, `training`, `blacks`, `inn` for town services; `combat`,
`figatt`, `shootatt`, `regenmon`, `chkmisl` for the battle system.

Runtime symbols such as `_STKSIZ_`, `_HEAPSIZ_`, `_mbot_`, `_mtop_`, `_PSP_`,
`ctp__`, `_ioflg_`, `errno_` identify a mid-1980s DOS C runtime, while names
like `cga_movsw`, `ega_movax` and `egamovsw` are hand-written assembly. The game
is a C and assembly mix, with the inner rendering loops in assembly.

The trailing underscore on `main_`, `ovloader_`, `readmaze_`, `Sound_`, `wait_`
marks the C-callable entry points; the un-suffixed names are internal assembly
labels.
