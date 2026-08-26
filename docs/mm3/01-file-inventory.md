# 1. File inventory and the `.CC` archive — Might & Magic III

Might & Magic 3 ships **six** game files, plus its own installer. Might & Magic
1 shipped 75 and Might & Magic 2 shipped 94; this one puts the entire game
inside two containers.

| File | Size | Role |
|---|---:|---|
| `MM3.CC` | 3,430,389 | **The game.** 558 members: all the code, data and art. |
| `MM3.CUR` | 207,551 | A second archive, same format, 240 members. Current game state. |
| `MM3.EXE` | 280,032 | Loader. Packed — see below. |
| `MM3.$$$` | 28,600 | Unexamined. |
| `Mm3.com` | 776 | A launcher stub. |
| `MM3.CFG` | 4 | Four bytes: `00 01 20 02`. |
| `Install.exe` | 21,650 | The game's own installer, not part of the game. |

## The `.CC` container — solved

```
word         number of members, N
N x 8 bytes  the directory, obfuscated
             per entry:  word  16-bit hash of the member's filename
                         3 bytes   offset of the member, from the start of file
                         word      size of the member
                         byte      always 0
rest         the members, back to back
```

### Deobfuscating the directory

Each directory byte is **rotated left by two and then had a running key
subtracted**, the key starting at `0x54` and advancing by `0x99` per byte:

```
plain[i] = (rotl(cipher[i], 2) - key) & 0xFF ,   key = (0x54 + 0x99 * i) & 0xFF
```

None of that was assumed. It was solved in three steps, each one measured:

**The key is linear, and its stride is `0xC8` every eight bytes.** The last byte
of each entry is constant in the plaintext, so whatever the operation is, the
transformed ciphertext at those positions differs by exactly one key step per
entry. Rotating left by two and taking differences between consecutive entries
gives `0xC8` for **557 of 557** consecutive pairs. Byte 4 — the high byte of a
3-byte offset, which changes slowly — gives `0xC8` for 505 pairs and `0xC9` for
the other 52, exactly the pattern a slowly increasing plaintext produces.

**The operation is subtraction, not XOR.** A constant plaintext under XOR with a
linearly increasing key does not produce a constant difference in the
ciphertext; under subtraction it does exactly that. The perfectly constant
`0xC8` above is therefore evidence for the arithmetic, not just the stride.

`0xC8 = 8 × step` leaves eight candidates for the per-byte step. A search over
those, both rotation directions, all eight rotation amounts, both addition and
subtraction, and all 256 starting keys — 65,536 transforms — was scored on
whether the resulting members **tile the archive**: every byte accounted for,
nothing overlapping.

**Exactly one combination scores perfectly**, and it does so on both archives at
once:

| | `MM3.CC` | `MM3.CUR` |
|---|---:|---:|
| members | 558 | 240 |
| bytes stored | 3,425,923 | 205,629 |
| overlapping members | **0** | **0** |
| bytes covered by no member | **0** | **0** |
| duplicate ids | **0** | **0** |
| distinct values of the last entry byte | **1** (`0x00`) | **1** (`0x00`) |

Two independent archives, 798 members between them, tiling their containers to
the byte with no slack and no collisions. There is no second reading.

```sh
python tools/mm3/cc_list.py --check       # the table above
python tools/mm3/cc_list.py               # every member of MM3.CC
python tools/mm3/cc_list.py MM3.CUR
```

### The member ids

The first field of an entry is a 16-bit value, unique across each archive and
**not** sorted — neither ascending nor grouped. It behaves like a hash of the
member's original filename, which is how the game asks for a file by name
without storing any names.

**The hash is not solved**, and cannot be from these files alone: it needs
filename plaintext to test against, and there is none. `MM3.EXE` is packed
(entropy 6.78, no readable strings, and a long `ydnaydnayd…` fill pattern), so
the usual source of filename literals is closed off, and the 174 filename-shaped
byte sequences found inside archive members are coincidences in compressed data
— none of them hashes onto a real id under any rotate-and-add variant tried.

Unpacking `MM3.EXE` is the route in.

## What the members hold

The two archives are used quite differently, and the entropy says so cleanly:

| | members ≥ 256 bytes | high entropy (> 7 bits/byte) |
|---|---:|---:|
| `MM3.CC` | 523 | **523** |
| `MM3.CUR` | 186 | **0** |

Every substantial member of `MM3.CC` is compressed; **not one** member of
`MM3.CUR` is. That fits what they are for — `MM3.CC` is the shipped content,
`MM3.CUR` is the live game state the program writes back.

The small members of `MM3.CC` that are not compressed are startup messages, and
they read straight out:

```
id FDAA   132 bytes  "Might and Magic ]I[ requires %lu bytes free to run properly..."
id 9B08   237 bytes  " There are only %lu bytes free on your hard drive. ..."
```

`MM3.CUR` is plain throughout, and its members are readable as data — character
records (`Sir Canegm`), tables, `"…ault Characters"`.

**The member compression is not solved.** One structural clue is recorded here
for whoever picks it up: **556 of 558 members of `MM3.CC` begin with two
identical bytes** (`1F 1F …`, `FA FA …`, `56 56 …`), against 84 of 240 in the
uncompressed `MM3.CUR`, which is about what chance gives. Whatever the format
is, it opens with a doubled byte.

## Against the earlier games

Three titles, three completely different shapes:

* M&M1 — 75 loose files, one code overlay per map, art converted at runtime.
* M&M2 — 94 loose files, code overlays per subsystem, events as data, art
  shipped per adapter.
* M&M3 — **six** files, two of which are hashed, compressed archives holding
  everything.

The direction is consistent even though nothing is reused: each game moves more
of itself out of the executable and into content, and packages that content more
tightly. See [fingerprints](../comparison/fingerprints.md).
