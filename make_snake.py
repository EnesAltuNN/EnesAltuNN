"""Generate the profile snake SVG (light + dark).

The grid spells ENES ALTUN in a 5x7 bitmap font; the snake crosses it
left to right, eating the letters from the E to the final N.
"""
import datetime
import os
import random
import sys

TEXT = "ENES ALTUN"
FONT = {
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "N": ["#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
}
GLYPH_W, ROWS = 5, 7
KERN, SPACE = 1, 3           # columns between letters / for a word break

CELL, GAP, PAD = 12, 2, 10
PITCH = CELL + GAP
SEG = 5                      # snake length in cells
DUR = 20.0                   # seconds per loop
OFF = 4                      # cells travelled off-grid before wrapping

LIGHT = dict(empty="#ebedf0", levels=["#9be9a8", "#40c463", "#30a14e", "#216e39"],
             snake="#6f42c1")
DARK = dict(empty="#161b22", levels=["#0e4429", "#006d32", "#26a641", "#39d353"],
            snake="#a371f7")


def letters():
    """Lay TEXT out on the grid. Returns (total columns, {(col, row)} that are lit)."""
    lit, c = set(), 0
    for ch in TEXT:
        if ch == " ":
            c += SPACE
            continue
        for r, line in enumerate(FONT[ch]):
            for dc, px in enumerate(line):
                if px == "#":
                    lit.add((c + dc, r))
        c += GLYPH_W + KERN
    return c - KERN, lit


COLS, LIT = letters()


def path():
    """Serpentine over every cell, then off-grid right and back on from the left.

    Returns (cells, loop length, stops): cells is [(col, row, t_units)] in eating
    order, stops is [(t_units, col, row)] the snake's keyframe corners.
    """
    cells, stops, t = [], [], 0
    for c in range(COLS):
        rows = list(range(ROWS) if c % 2 == 0 else range(ROWS - 1, -1, -1))
        stops.append((t, c, rows[0]))
        for i, r in enumerate(rows):
            cells.append((c, r, t + i))
        t += ROWS - 1
        stops.append((t, c, rows[-1]))
        t += 1                                   # step sideways into next column
    t -= 1                                       # no sideways step after the last
    last_row = stops[-1][2]
    stops.append((t + OFF, COLS - 1 + OFF, last_row))   # glide off the right edge
    stops.append((t + OFF + 1, -OFF, 0))                # jump back, off-screen
    stops.append((t + OFF + 1 + OFF, 0, 0))             # glide back in
    return cells, stops[-1][0], stops


def svg(theme, seed):
    rnd = random.Random(seed)
    cells, total, stops = path()
    unit = DUR / total
    w = PAD * 2 + COLS * PITCH - GAP
    h = PAD * 2 + ROWS * PITCH - GAP

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
           f'viewBox="0 0 {w} {h}">', "<style>",
           f'.d{{animation:eat {DUR}s linear infinite}}',
           f'.s{{animation:mv {DUR}s linear infinite}}',
           "@keyframes eat{0%{fill:var(--c)}2%{fill:var(--e)}"
           "18%{fill:var(--e)}30%,100%{fill:var(--c)}}",
           "@keyframes mv{" + "".join(
               f"{t / total * 100:.4f}%{{transform:translate({c * PITCH}px,{r * PITCH}px)}}"
               for t, c, r in stops) + "}",
           "</style>",
           f'<g transform="translate({PAD},{PAD})" style="--e:{theme["empty"]}">']

    for c, r, t in cells:
        # lit cells get a random green so the name still has contribution-graph texture
        color = (rnd.choices(theme["levels"], weights=(8, 30, 32, 30))[0]
                 if (c, r) in LIT else theme["empty"])
        delay = -(DUR - t * unit)
        out.append(f'<rect class="d" x="{c * PITCH}" y="{r * PITCH}" width="{CELL}" '
                   f'height="{CELL}" rx="3" fill="{color}" '
                   f'style="--c:{color};animation-delay:{delay:.3f}s"/>')

    for i in range(SEG):
        delay = 0 if i == 0 else -(DUR - i * unit)
        out.append(f'<rect class="s" width="{CELL}" height="{CELL}" rx="4" '
                   f'fill="{theme["snake"]}" opacity="{1 - i * 0.14:.2f}" '
                   f'style="animation-delay:{delay:.3f}s"/>')

    out += ["</g>", "</svg>"]
    return "\n".join(out)


def check():
    cols, lit = letters()
    expected = sum(line.count("#") for ch in TEXT if ch != " " for line in FONT[ch])
    assert len(lit) == expected, "every glyph pixel landed on its own cell"
    assert max(c for c, _ in lit) == cols - 1, "the last letter ends at the last column"
    assert min(c for c, _ in lit) == 0, "the first letter starts at column 0"
    assert all(0 <= r < ROWS for _, r in lit), "glyphs fit the grid height"

    cells, total, stops = path()
    seen = {(c, r) for c, r, _ in cells}
    assert len(cells) == COLS * ROWS == len(seen), "every cell eaten exactly once"
    times = [t for _, _, t in cells]
    assert times == sorted(times), "cells are eaten left to right, E before N"
    assert times[0] == 0 and times[-1] < total, "eat times fit inside one loop"
    assert [s[0] for s in stops] == sorted(s[0] for s in stops), "keyframes ascend"
    assert stops[-1][1:] == (0, 0), "loop ends back at the start cell"
    assert stops[-2][1] < 0, "the wrap jump happens off-screen"


if __name__ == "__main__":
    check()
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(out, exist_ok=True)
    seed = datetime.date.today().isoformat()      # new shading every day
    for name, theme in (("snake-light.svg", LIGHT), ("snake-dark.svg", DARK)):
        dest = os.path.join(out, name)
        open(dest, "wb").write(svg(theme, seed + name).encode())
        print(dest, f"{COLS}x{ROWS}", seed)
