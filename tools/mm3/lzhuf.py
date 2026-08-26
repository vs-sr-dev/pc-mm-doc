"""The codec Might & Magic III uses for the members of its `.CC` archives.

It is LZHUF -- LZSS over a 4096-byte ring buffer, with the literal/length
symbol carried by an adaptive (dynamically rebuilt) Huffman tree and the match
position by a fixed prefix code. The parameters were read out of the
decompressor in the unpacked `MM3.EXE`, not guessed: see docs/mm3/03.

M&M3's one departure from the published algorithm is that the value the ring
buffer is primed with is stored in the member header instead of being fixed at
`' '`, which is why almost every stored member begins with a doubled byte.
"""

N, F, THRESHOLD = 4096, 60, 2
N_CHAR = 256 - THRESHOLD + F      # 314 -- the `mov cx, 0x13a` in the binary
T = N_CHAR * 2 - 1                # 627
R = T - 1                         # 626
MAX_FREQ = 0x8000

# Position prefix code: 64 symbols giving the top six bits of a match offset.
_P_LEN = [3] + [4] * 3 + [5] * 8 + [6] * 12 + [7] * 24 + [8] * 16
_P_CODE = [0x00, 0x20, 0x30, 0x40, 0x50, 0x58, 0x60, 0x68,
           0x70, 0x78, 0x80, 0x88, 0x90, 0x94, 0x98, 0x9C,
           0xA0, 0xA4, 0xA8, 0xAC, 0xB0, 0xB4, 0xB8, 0xBC,
           0xC0, 0xC2, 0xC4, 0xC6, 0xC8, 0xCA, 0xCC, 0xCE,
           0xD0, 0xD2, 0xD4, 0xD6, 0xD8, 0xDA, 0xDC, 0xDE,
           0xE0, 0xE2, 0xE4, 0xE6, 0xE8, 0xEA, 0xEC, 0xEE,
           0xF0, 0xF1, 0xF2, 0xF3, 0xF4, 0xF5, 0xF6, 0xF7,
           0xF8, 0xF9, 0xFA, 0xFB, 0xFC, 0xFD, 0xFE, 0xFF]
_D_CODE, _D_LEN = [0] * 256, [0] * 256
for _j, (_c, _l) in enumerate(zip(_P_CODE, _P_LEN)):
    for _i in range(_c, _c + (1 << (8 - _l))):
        _D_CODE[_i], _D_LEN[_i] = _j, _l


class _Bits:
    """MSB-first bit reader. The game reads big-endian words and shifts them
    left through carry against a sentinel bit; over a byte stream that is the
    same thing as taking bits from the top of each byte in turn."""

    def __init__(self, data):
        self.data, self.pos = data, 0

    def bit(self):
        i = self.pos >> 3
        v = (self.data[i] >> (7 - (self.pos & 7))) & 1 if i < len(self.data) else 0
        self.pos += 1
        return v

    def bits(self, n):
        v = 0
        for _ in range(n):
            v = (v << 1) | self.bit()
        return v


def decompress(body, out_size, fill, want_bits=False):
    """`body` is a member with its four-byte header removed, `out_size` the
    size that header declares, `fill` the byte it primes the ring buffer with.

    With want_bits, also return how many bits were consumed -- a genuine
    member ends within a byte of its own end, which is how a caller can tell a
    compressed member from a stored one without knowing its name.
    """
    freq = [0] * (T + 1)
    prnt = [0] * (T + N_CHAR)
    son = [0] * T
    for i in range(N_CHAR):
        freq[i], son[i], prnt[i + T] = 1, i + T, i
    i, j = 0, N_CHAR
    while j <= R:
        freq[j], son[j] = freq[i] + freq[i + 1], i
        prnt[i] = prnt[i + 1] = j
        i, j = i + 2, j + 1
    freq[T], prnt[R] = 0xFFFF, 0

    def reconstruct():
        """Halve every leaf's count and rebuild the tree -- what the game does
        when the root count reaches MAX_FREQ."""
        j = 0
        for i in range(T):
            if son[i] >= T:
                freq[j], son[j] = (freq[i] + 1) >> 1, son[i]
                j += 1
        i, j = 0, N_CHAR
        while j < T:
            f = freq[j] = freq[i] + freq[i + 1]
            k = j - 1
            while f < freq[k]:
                k -= 1
            k += 1
            for m in range(j, k, -1):
                freq[m], son[m] = freq[m - 1], son[m - 1]
            freq[k], son[k] = f, i
            i, j = i + 2, j + 1
        for i in range(T):
            k = son[i]
            prnt[k] = i
            if k < T:
                prnt[k + 1] = i

    def update(c):
        if freq[R] == MAX_FREQ:
            reconstruct()
        c = prnt[c + T]
        while True:
            freq[c] += 1
            k = freq[c]
            l = c + 1
            if k > freq[l]:
                while k > freq[l + 1]:
                    l += 1
                freq[c], freq[l] = freq[l], k
                i = son[c]
                prnt[i] = l
                if i < T:
                    prnt[i + 1] = l
                j = son[l]
                son[l], prnt[j] = i, c
                if j < T:
                    prnt[j + 1] = c
                son[c], c = j, l
            c = prnt[c]
            if c == 0:
                break

    bits = _Bits(body)
    text = bytearray([fill]) * N
    r = N - F                      # the game's `mov cx, 0xfc4`
    out = bytearray()
    while len(out) < out_size:
        c = son[R]
        while c < T:
            c = son[c + bits.bit()]
        c -= T
        update(c)
        if c < 256:
            out.append(c)
            text[r] = c
            r = (r + 1) & (N - 1)
        else:
            i = bits.bits(8)
            pos = _D_CODE[i] << 6
            for _ in range(_D_LEN[i] - 2):
                i = ((i << 1) | bits.bit()) & 0xFFFF
            pos |= i & 0x3F
            src = (r - pos - 1) & (N - 1)
            for k in range(c - 255 + THRESHOLD):
                b = text[(src + k) & (N - 1)]
                out.append(b)
                text[r] = b
                r = (r + 1) & (N - 1)
    return (bytes(out[:out_size]), bits.pos) if want_bits else bytes(out[:out_size])
