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

Symbols (below) fall into two ranges that do not overlap: code offsets run from
`0x0000` to about `0xEC9B`, data offsets from about `0x50A6` to `0xC93E`. Since
the image is 118,752 bytes — a little under two 64 KB segments — the layout is:

```
file 0x000200  image 0x00000   code segment, DS-independent   (offsets 0x0000..0xFFFF)
file 0x010200  image 0x10000   data segment                   (offsets 0x0000..~0xC93E)
file 0x01D1E0  image 0x1CFE0   end of image; BSS follows
```

**The data segment begins at file offset `0x10200`.** This was confirmed, not
assumed: the symbol `itemlow` (`0x9972`) lands exactly on the first record of
the item-name table (`SPEAR`, `SHORT SWORD`, `MACE`, …) and `itemhigh`
(`0xA962`) lands exactly on the first record of the second item table
(`10 FOOT POLE`, `GARLIC`, `WOLFSBANE`, …). Two independent exact hits on
record boundaries.

Above the static data the game keeps two overlay buffers, both in the code
segment's address space:

```
0xC93E   _Eol_          last symbol; end of initialised data
0xC940   overlay data   loaded here
0xF48F   overlay code   loaded here
```

`0xC940` is `_Eol_ + 2`: the overlay data area starts immediately after the end
of the linked image. Both addresses are the destination fields of every `.OVR`
header and both are confirmed by measurement — see [doc 3](03-map-overlays.md).

## MM.RSM — the shipped symbol map

`MM.RSM` is not used by the game. It is the **linker's symbol map, accidentally
shipped with the retail files**, and it names 579 symbols with their addresses.
This is the single most useful artefact in the distribution.

Record format, after a 0x23-byte header:

```
<name> 0x00  <type>  <class>  <offset:word LE>
```

`type` is `0x02` for code and `0x03` for data (`class` is `0x28` for every
symbol). Run `python tools/dump_symbols.py` for the full list; a sample:

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
