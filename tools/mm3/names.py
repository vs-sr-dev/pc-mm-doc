"""Put the names back on the members of Might & Magic III's archives.

The directory stores a 16-bit hash of each filename and no name. The hash is
one-way, but it does not need inverting: the program that computes it also
contains the strings it is computed over. Harvesting every filename-shaped
literal out of the unpacked `MM3.EXE`, expanding its printf templates over
their numeric range, and hashing the lot recovers most of the archive.

This is a search, so it has a false-positive rate, and the rate is measured
rather than assumed -- see docs/mm3/03.
"""
import re, collections

import mmlib3

LITERAL = re.compile(rb'[A-Za-z0-9_\-%.]{1,12}\.[A-Za-z0-9%]{1,3}\x00')
TEMPLATE_RANGE = 256


def literals(*blobs):
    """Every filename-shaped, NUL-terminated string in the given images."""
    out = set()
    for b in blobs:
        for m in LITERAL.finditer(b):
            out.add(m.group()[:-1].decode())
    return out


def candidates(lits):
    """Literal names, plus each numeric printf template expanded over its
    range. `%s` templates are deliberately left alone: expanding them over
    arbitrary words generates far more names than the archive has members and
    turns every id ambiguous."""
    out = {n for n in lits if '%' not in n}
    for t in lits:
        if '%' not in t or '%s' in t:
            continue
        for n in range(TEMPLATE_RANGE):
            f = (t.replace('%02u', f'{n:02d}').replace('%02d', f'{n:02d}')
                  .replace('%d', str(n)).replace('%u', str(n)))
            if '%' not in f:
                out.add(f)
    return out


def match(cands, hash_name, ids):
    """{id: {name, ...}} for every candidate whose hash is a member id."""
    out = collections.defaultdict(set)
    for n in cands:
        h = hash_name(n)
        if h in ids:
            out[h].add(n)
    return dict(out)


def table(ids):
    """{id: {name, ...}} for the given member ids, searched against the
    filename literals in this installation's own MM3.EXE."""
    exe = mmlib3.unpack_exe()
    return match(candidates(literals(exe['image'], exe['overlays'])),
                 mmlib3.hash_name, ids)
