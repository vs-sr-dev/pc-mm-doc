"""Undo the two layers of packing on `MM3.EXE`.

The shipped file is a stub that reopens itself by name, LZW-decompresses the
real program out of its own tail, and jumps to it. That program is in turn a
Microsoft EXEPACK image. Both layers were read out of the stub's own code;
see docs/mm3/02.

Returns three things: the running program image, its relocation table, and the
Borland overlay pool, which is stored uncompressed past the end of the stub's
declared image and so needs no unpacking at all.
"""
import struct

LZW_CLEAR, LZW_END, LZW_FIRST, LZW_MAX_WIDTH = 0x100, 0x101, 0x102, 12


def _lzw(buf):
    """9-to-12-bit LZW, codes packed low bits first, as the stub reads them."""
    pos, out = 0, bytearray()
    width, thresh, nxt = 9, 1 << 9, LZW_FIRST
    pre, suf = [0] * 4096, [0] * 4096
    prev, first = None, 0

    def get(w):
        nonlocal pos
        v = int.from_bytes(buf[pos >> 3:(pos >> 3) + 3].ljust(3, b'\0'), 'little')
        v = (v >> (pos & 7)) & ((1 << w) - 1)
        pos += w
        return v

    while True:
        code = get(width)
        if code == LZW_END:
            break
        if code == LZW_CLEAR:
            width, thresh, nxt, prev = 9, 1 << 9, LZW_FIRST, None
            code = get(width)
            out.append(code)
            prev = first = code
            continue
        stack, c = [], code
        if c >= nxt:
            stack.append(first)
            c = prev
        while c > 0xFF:
            stack.append(suf[c])
            c = pre[c]
        first = c
        out.append(c)
        while stack:
            out.append(stack.pop())
        if prev is not None:
            pre[nxt], suf[nxt] = prev, first
            nxt += 1
            if nxt >= thresh and width < LZW_MAX_WIDTH:
                width, thresh = width + 1, thresh << 1
        prev = code
    return bytes(out), (pos + 7) // 8


def _exepack(image, header_off):
    """Expand an EXEPACK image and read back its relocation table."""
    (ip, cs, _, ep_size, sp, ss,
     dest_len, skip_len) = struct.unpack('<8H', image[header_off:header_off + 16])
    if image[header_off + 16:header_off + 18] != b'RB':
        raise ValueError('no EXEPACK signature')
    src = image[:header_off - (skip_len - 1) * 16]
    out = bytearray(dest_len * 16)
    out[:len(src)] = src            # EXEPACK expands in place, top down
    i = len(src) - 1
    while src[i] == 0xFF:
        i -= 1
    d = len(out) - 1
    while True:
        cmd = src[i]
        i -= 1
        count = src[i - 1] | (src[i] << 8)
        i -= 2
        if cmd & 0xFE == 0xB0:
            b = src[i]
            i -= 1
            for _ in range(count):
                out[d] = b
                d -= 1
        elif cmd & 0xFE == 0xB2:
            for _ in range(count):
                out[d] = src[i]
                d -= 1
                i -= 1
        else:
            raise ValueError(f'bad EXEPACK command {cmd:#04x}')
        if cmd & 1:
            break
    # The relocation table sits inside the stub, grouped into sixteen 64K pages.
    p = header_off + 0x12D
    relocs = []
    for page in range(16):
        n = struct.unpack('<H', image[p:p + 2])[0]
        p += 2
        for _ in range(n):
            relocs.append((page * 0x1000,
                           struct.unpack('<H', image[p:p + 2])[0]))
            p += 2
    if p - header_off != ep_size:
        raise ValueError('relocation table does not end on exepack_size')
    return bytes(out), relocs, dict(cs=cs, ip=ip, ss=ss, sp=sp)


def unpack(exe):
    """`exe` is the bytes of MM3.EXE. Returns a dict."""
    stub_data = exe[0x200:]
    payload_at = struct.unpack('<H', stub_data[0x4B:0x4D])[0]
    name = stub_data[0x4D:stub_data.index(b'\0', 0x4D)].decode()
    mz = struct.unpack('<2s13H', exe[payload_at:payload_at + 28])
    lastpg, pages, nreloc, hdrpar = mz[1], mz[2], mz[3], mz[4]
    if mz[0] != b'MZ':
        raise ValueError('packed payload is not an MZ image')
    packed, used = _lzw(exe[payload_at + hdrpar * 16:])
    declared = (pages - 1) * 512 + (lastpg or 512) - hdrpar * 16
    ep_at = len(packed) - (len(packed) % 16 or 16)
    ep_at = packed.rfind(b'RB', 0, None)
    # the EXEPACK header is the 18 bytes ending at the "RB" signature
    ep_at -= 16
    image, relocs, regs = _exepack(packed, ep_at)
    overlays_at = (struct.unpack('<H', exe[4:6])[0] - 1) * 512 + \
                  (struct.unpack('<H', exe[2:4])[0] or 512)
    return dict(reopens=name, payload_at=payload_at, lzw_bytes=used,
                packed=packed, packed_declared=declared,
                image=image, relocs=relocs, overlays=exe[overlays_at:],
                overlays_at=overlays_at, inner_nreloc=nreloc, **regs)
