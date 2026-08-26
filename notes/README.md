# Generated dumps

Nothing in here is committed. These files are verbatim extractions from the
game — symbol names, map dialogue — so they are regenerated locally from your
own copy rather than redistributed. The documentation quotes only short
excerpts, as illustration.

```sh
export MM1_DATA="/path/to/Might and Magic 1"

python tools/mm1/dump_symbols.py > notes/mm1/symbols.txt    # 579 symbols
python tools/mm1/ovr_text.py     > notes/mm1/map-text.txt   # all 55 maps' text
python tools/mm1/disasm.py --ovr sorpigal 0xf48f 0x346 > notes/mm1/sorpigal.asm
```

`disasm.py` needs Capstone (`pip install capstone`); everything else is
stdlib-only.
