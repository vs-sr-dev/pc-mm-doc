# 2. The executable, and getting inside it — Might & Magic III

`MM3.EXE` is 280,032 bytes and gives up nothing on inspection: entropy 6.78,
no readable strings, and 76 KB of the file is the word `andy` written
backwards over and over. The [file inventory](01-file-inventory.md) had to stop
there, and with it every question about M&M3's engine.

It is packed **twice**. Undoing both layers is mechanical once the stub is
read, and it hands over three things: the running program, its relocation
table, and a 114 KB overlay pool that was never compressed at all.

```sh
python tools/mm3/unpack_exe.py            # the numbers below
python tools/mm3/unpack_exe.py out        # write the images out
```

## Layer 1 — a loader that reopens its own file

The MZ header is honest about very little. It declares 324 pages against a
file of 547, one relocation, and an entry point at the very start of the image.
That entry is `jmp +0x99`, and what it lands on is a self-contained stub.

The stub does something a normal DOS program never does: it **opens its own
executable by name**. On DOS 3 or later it takes the full pathname DOS leaves
past the end of the environment block; failing that it falls back to a literal
`MM3.EXE` 77 bytes into the stub; and failing that it gives up with `Might and
Magic ]I[ encountered a disk error!`.

It then seeks to a fixed offset held in the two bytes before that filename —
`0x0699` — where a **second `MZ` header** sits:

| field | value | |
|---|---|---|
| pages / last page | 250 / 401 | 127,377 bytes of image |
| relocations | **0** | see below |
| header paragraphs | 32 | so the payload starts at `0x0899` |
| `cs:ip` | `1EA1:0012` | |
| `ss:sp` | `2805:0080` | |

The stub reads 37 bytes of that header, allocates from it, and streams the
rest of the file through a decompressor, refilling an 8 KB input window from
disk as it goes.

### The codec is LZW

Not inferred from the data — read off the routine at the stub's offset
`0x4ba`. Every parameter is there in the open:

* `mov word ptr [0x90], 9` — codes start at **9 bits**, and `cmp [0x90], 0xc`
  caps them at **12**.
* `mov bp, 0x102` — the first free code is `0x102`, so `0x100` and `0x101` are
  taken. `cmp ax, 0x100 / je` re-runs the initialiser: that is the **clear**
  code. `cmp ax, 0x101 / je` returns: **end of stream**.
* `cmp bp, [0x92]`, with `[0x92]` starting at `0x200` and doubling, widens the
  code as the table fills.
* The bit reader loads a 24-bit little-endian window at `bitpos >> 3` and
  shifts it **right** by `bitpos & 7` — codes are packed **low bits first**.
* The dictionary is three bytes per entry (prefix word, suffix byte) and
  strings are emitted by pushing suffixes and popping them back, which is the
  ordinary LZW walk.

Decoding from `0x0899` produces **127,680 bytes** and consumes 87,165 of the
file. The inner header declared 127,377; the difference is the packer rounding
the last page, and the stream terminates on its own `0x101` rather than
running out of input, so the boundary is not in doubt.

That leaves 76,202 bytes between the end of the stream and the end of the
declared image. They are the filler: `ydna` repeated 19,049 times — `andy`,
stored as a little-endian dword. Entropy 2.00, and no other content.

## Layer 2 — EXEPACK

The 127,680 bytes are still not a program. The inner header claimed **zero
relocations**, which no 127 KB large-model DOS program can be true of, and the
last bytes at `cs:0000` are `... 01 00 52 42` — `RB`, the **EXEPACK**
signature.

The 18-byte header in front of it reads:

| field | value |
|---|---|
| real `cs:ip` | `0000:0000` |
| real `ss:sp` | `2784:0080` |
| `exepack_size` | `0x0781` |
| `dest_len` | `0x278C` paragraphs = **161,984 bytes** |
| `skip_len` | 1 |

EXEPACK expands in place from the top down, reading a command byte and a count
backwards from the end of the packed data: `0xB0` repeats one byte, `0xB2`
copies a run, and the low bit ends the stream. Its relocation table follows
the unpacker, grouped into sixteen 64 KB pages.

Two things confirm the result rather than merely producing it. The unpacker's
read and write pointers **meet exactly** — 76,591 bytes of source consumed,
76,591 bytes of destination left untouched, which is what "expands in place"
means when it is done right. And the relocation table ends on offset `0x0781`,
**exactly `exepack_size`**, to the byte.

**The real program carries 794 relocations**, and its entry point at
`0000:0000` is an ordinary Borland C startup. The image says so itself:

```
Borland C++ - Copyright 1991 Borland Intl.
```

## The overlays were never packed

`MM3.EXE`'s declared image ends at `0x286C0`; the file runs to `0x445E0`. The
114,464 bytes past the end begin `FBOV` — Borland's overlay pool — and the
image contains `Runtime overlay error` to match. Entropy 6.87, against 7.80
for the LZW stream and 2.00 for the filler: this pool is **stored plain**.
It needs no unpacking and never did; it was simply behind a file whose front
end could not be read.

So the packing was only ever protecting the resident half of the program, and
one third of M&M3's code was sitting in the clear the whole time.

## What this opens

| | |
|---|---|
| program image | 161,984 bytes, Borland C++ 1991, 794 relocations |
| overlay pool | 114,464 bytes, plain |
| filename literals | 214, including seven sound drivers and twenty printf templates |
| the archive module | hand-written assembly: the directory cipher, the filename hash, and the member decompressor, all in the clear |

The last row is the one that matters. Every open question the inventory left
behind is answered by code inside this image — see
[the archive members](03-archive-members.md) — and the engine comparison the
[fingerprints](../comparison/fingerprints.md) could not run now runs.
