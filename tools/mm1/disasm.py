"""
disasm -- a 16-bit disassembler for MM.EXE and the .OVR overlays, with the
shipped symbol map (MM.RSM) resolved into every branch target.

The two address spaces are kept apart: code symbols (type 0x02) name branch and
call targets, data symbols (type 0x03) name absolute memory operands. Overlay
code is disassembled at its load address 0xF48F and can therefore call the
engine by name like any other code.

  python tools/mm1/disasm.py plot            # an engine routine, by symbol
  python tools/mm1/disasm.py 0x0f45 0x40     # an address and a byte count
  python tools/mm1/disasm.py --ovr sorpigal 0xf4a1
"""
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mmlib
from capstone import Cs, CS_ARCH_X86, CS_MODE_16

CODE_FILE_BASE = 0x200      # file offset of CS:0000 in MM.EXE
OVR_CODE_BASE  = 0xF48F     # where an overlay's code half is loaded
OVR_DATA_BASE  = 0xC940     # where an overlay's data half is loaded


def _symbols():
    code, data = {}, {}
    for name, typ, _cls, off in mmlib.read_symbols():
        if typ == 0x02:
            code.setdefault(off, name)
        elif typ == 0x03:
            data.setdefault(off, name)
    return code, data

CODE_SYMS, DATA_SYMS = _symbols()


def engine_image():
    """The whole MM.EXE image, addressed so that image[a] is code address a."""
    return open(mmlib.path('MM.EXE'), 'rb').read()[CODE_FILE_BASE:]


def overlay(name):
    """(code bytes, data bytes) of one .OVR, header stripped."""
    d = open(mmlib.path(name.upper() + '.OVR'), 'rb').read()
    csz = struct.unpack('<H', d[4:6])[0]
    dsz = struct.unpack('<I', d[8:12])[0]
    return d[14:14 + csz], d[14 + csz:14 + csz + dsz]


def sym(addr, kind='code'):
    table = CODE_SYMS if kind == 'code' else DATA_SYMS
    if addr in table:
        return table[addr]
    # nearest preceding symbol, if it is close enough to be the same routine
    prev = max((a for a in table if a <= addr), default=None)
    if prev is not None and addr - prev < 0x400:
        return '%s+%d' % (table[prev], addr - prev)
    return None


OVR_TEXT = {}          # overlay data offset -> the string stored there

def annotate(ins):
    """A trailing comment naming whatever the instruction refers to."""
    notes = []
    op = ins.op_str
    if ins.mnemonic in ('call', 'jmp') or ins.mnemonic.startswith('j'):
        try:
            t = int(op, 16) & 0xFFFF if op.startswith('0x') else None
        except ValueError:
            t = None
        if t is not None:
            s = sym(t)
            if s:
                notes.append(s)
    # a string pointer handed to the engine: mov word [bdw], <overlay text>
    import re
    for m in re.finditer(r', (0x[0-9a-f]+)$', op):
        a = int(m.group(1), 16)
        if a in OVR_TEXT:
            notes.append('%r' % OVR_TEXT[a])
    # absolute memory operands: word ptr [0x1234]
    for m in re.finditer(r'\[(0x[0-9a-f]+)\]', op):
        a = int(m.group(1), 16)
        s = DATA_SYMS.get(a)
        if s:
            notes.append('%s = %s' % (m.group(1), s))
        elif a in OVR_TEXT:
            notes.append('%s = %r' % (m.group(1), OVR_TEXT[a]))
        elif OVR_DATA_BASE <= a < OVR_DATA_BASE + 0x2000:
            notes.append('%s = overlay data +%d' % (m.group(1), a - OVR_DATA_BASE))
    return '  ; ' + ', '.join(notes) if notes else ''


def disasm(buf, base, start, length, out=sys.stdout, labels=True):
    md = Cs(CS_ARCH_X86, CS_MODE_16)
    off = start - base
    for ins in md.disasm(buf[off:off + length], start):
        if labels and ins.address in CODE_SYMS:
            print('%s:' % CODE_SYMS[ins.address], file=out)
        op = ins.op_str
        if op.startswith('0x') and (ins.mnemonic in ('call', 'jmp')
                                    or ins.mnemonic.startswith('j')):
            op = '0x%04x' % (int(op, 16) & 0xFFFF)
        print('%04X  %-16s %-6s %-28s%s' % (
            ins.address, ins.bytes.hex(), ins.mnemonic, op,
            annotate(ins)), file=out)


def main(argv):
    if argv and argv[0] == '--ovr':
        name = argv[1]
        code, data = overlay(name)
        for off in range(len(data)):
            if (off == 0 or data[off-1] == 0) and 32 <= data[off] < 127:
                end = data.find(0, off)
                if end > off + 3:
                    OVR_TEXT[OVR_DATA_BASE + off] =                         data[off:min(end, off+46)].decode('latin1')
        buf, base, default_len = code, OVR_CODE_BASE, len(code)
        argv = argv[2:]
    else:
        buf, base, default_len = engine_image(), 0, 0x80
    if not argv:
        print(__doc__); return
    a = argv[0]
    if a.lower() in (n.lower() for n in CODE_SYMS.values()):
        start = next(k for k, v in CODE_SYMS.items() if v.lower() == a.lower())
    else:
        start = int(a, 0)
    n = int(argv[1], 0) if len(argv) > 1 else default_len
    disasm(buf, base, start, n)


if __name__ == '__main__':
    main(sys.argv[1:])
