#!/usr/bin/env python3
"""Unpack MM3.EXE and report what the two layers of packing say.

  python tools/mm3/unpack_exe.py            # the facts
  python tools/mm3/unpack_exe.py out        # also write the images to out/
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import mmlib3

e = mmlib3.unpack_exe()
size = os.path.getsize(mmlib3.path('MM3.EXE'))
print(f'MM3.EXE                    {size} bytes')
print(f'  stub reopens             {e["reopens"]!r} and seeks to {e["payload_at"]:#x}')
print(f'  LZW stream               {e["lzw_bytes"]} bytes -> {len(e["packed"])} '
      f'(inner MZ declares {e["packed_declared"]}, {e["inner_nreloc"]} relocations)')
print(f'  EXEPACK image            {len(e["image"])} bytes, '
      f'cs:ip {e["cs"]:04X}:{e["ip"]:04X}, ss:sp {e["ss"]:04X}:{e["sp"]:04X}')
print(f'  real relocations         {len(e["relocs"])}')
print(f'  overlay pool             {len(e["overlays"])} bytes at {e["overlays_at"]:#x}, stored plain')
print(f'  built with               '
      f'{"Borland C++ 1991" if b"Borland C++ - Copyright 1991" in e["image"] else "unknown"}')

if len(sys.argv) > 1:
    os.makedirs(sys.argv[1], exist_ok=True)
    for name, blob in (('mm3-image.bin', e['image']),
                       ('mm3-overlays.bin', e['overlays'])):
        open(os.path.join(sys.argv[1], name), 'wb').write(blob)
        print('wrote', os.path.join(sys.argv[1], name))
