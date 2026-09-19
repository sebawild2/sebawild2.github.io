#!/usr/bin/env python3
"""Re-scale the coordinates of graph files drawn with the old graph editor.

The old editor stored coordinates in the unit square and stretched them to the canvas with
separate x and y scales; the pages now draw coordinates to scale (one unit = same length both
ways), so old files look squashed horizontally. Multiplying every x by the aspect ratio of the
old drawing area restores the look you laid out. Only the trailing coordinate lines are touched;
V, E, edges, weights and comments are copied verbatim.

Usage:
    fix-graph-aspect.py --viewport 2560 graphs/*.txt        # window width the graphs were drawn in
    fix-graph-aspect.py --aspect 3.1 graphs/maze.txt        # or give the aspect ratio directly
    fix-graph-aspect.py --viewport 1920 -o converted/ graphs/*.txt

Without -o, files are rewritten in place and the original kept as <name>.orig.
The old editor's drawing area, at a window width W px, was about
    width  = (W - 72) * 0.6 - 34 - 80      (1.5fr column, panel padding, 40px canvas margins)
    height = 520 - 80
and the aspect ratio is width / height (2560px window -> 3.13, 1920px -> 2.26, 1440px -> 1.61).
"""
import argparse, re, shutil, sys
from pathlib import Path

def old_aspect(viewport_width):
    width = (viewport_width - 72) * 0.6 - 34 - 80
    height = 520 - 80
    return width / height

def convert(text, aspect):
    lines = text.split('\n')
    # tokenise like the pages do: blank lines and '#' comments are not counted
    def toks(line):
        line = line.split('#', 1)[0].strip()
        return line.split() if line else None
    content = [(i, toks(l)) for i, l in enumerate(lines) if toks(l)]
    if not content:
        raise ValueError('empty file')
    # header: "V E" on one line, or V and E on two lines
    first = content[0][1]
    if len(first) >= 2:
        V, E, body = int(first[0]), int(first[1]), content[1:]
    else:
        V, E, body = int(first[0]), int(content[1][1][0]), content[2:]
    coord_rows = body[E:]
    if len(coord_rows) != V:
        raise ValueError(f'expected {V} coordinate lines after {E} edges, found {len(coord_rows)} — no coordinates to convert?')
    for idx, t in coord_rows:
        x, y = float(t[0]), float(t[1])
        rest = ' '.join(t[2:])
        new = f'{round(x * aspect, 4):g} {round(y, 4):g}' + (f' {rest}' if rest else '')
        # keep any trailing comment on that line
        comment = lines[idx].split('#', 1)[1] if '#' in lines[idx] else None
        lines[idx] = new + (f'  #{comment}' if comment is not None else '')
    return '\n'.join(lines)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--viewport', type=float, help='browser window width (px) the graphs were drawn in')
    g.add_argument('--aspect', type=float, help='aspect ratio (width/height) of the old drawing area')
    ap.add_argument('-o', '--outdir', type=Path, help='write converted files here instead of in place')
    ap.add_argument('files', nargs='+', type=Path)
    a = ap.parse_args()
    aspect = a.aspect if a.aspect else old_aspect(a.viewport)
    print(f'x *= {aspect:.4f}')
    if a.outdir: a.outdir.mkdir(parents=True, exist_ok=True)
    for f in a.files:
        try:
            out = convert(f.read_text(), aspect)
        except (ValueError, IndexError) as e:
            print(f'  skip {f}: {e}', file=sys.stderr); continue
        if a.outdir:
            (a.outdir / f.name).write_text(out)
        else:
            shutil.copy2(f, f.with_suffix(f.suffix + '.orig'))
            f.write_text(out)
        print(f'  ok   {f}')

if __name__ == '__main__':
    main()
