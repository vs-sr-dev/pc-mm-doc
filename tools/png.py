"""Minimal PNG writer (stdlib only)."""
import zlib, struct

def write(path, w, h, rows_rgb):
    raw = b''.join(b'\x00' + bytes(v for px in row for v in px) for row in rows_rgb)
    def chunk(t, d):
        c = t + d
        return struct.pack('>I', len(d)) + c + struct.pack('>I', zlib.crc32(c))
    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n'
                + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
                + chunk(b'IDAT', zlib.compress(raw, 9))
                + chunk(b'IEND', b''))

def sheet(path, imgs, per_row, gap=4, bg=(32, 32, 32)):
    ih, iw = len(imgs[0]), len(imgs[0][0])
    nrows = (len(imgs) + per_row - 1) // per_row
    W, H = per_row*(iw+gap)+gap, nrows*(ih+gap)+gap
    canvas = [[bg]*W for _ in range(H)]
    for k, im in enumerate(imgs):
        ox, oy = gap + (k % per_row)*(iw+gap), gap + (k // per_row)*(ih+gap)
        for y, r in enumerate(im):
            canvas[oy+y][ox:ox+iw] = r
    write(path, W, H, canvas)
