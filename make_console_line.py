"""Turn a script into one line you can paste into Blender's Python console.

Usage:  python make_console_line.py scripts/02_seam_weight_match.py
Prints: exec("...")  -- paste into the console and press Enter.

Use this when Blender can't read a file from disk. If it can, this is simpler:
    exec(open(r"C:\\path\\to\\blender-tools\\scripts\\02_seam_weight_match.py").read())
"""
import sys

src = open(sys.argv[1], encoding="utf-8").read()
compile(src, sys.argv[1], "exec")  # fail early on syntax errors
print("exec(" + repr(src) + ")")
