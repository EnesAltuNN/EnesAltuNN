"""Generate a decorative contribution-grid snake SVG (light + dark).

Static artwork: the grid is seeded noise, not real contribution data, so it
always looks full regardless of how much was committed that week.
"""
import random

COLS, ROWS = 53, 7
CELL, GAP, PAD = 12, 2, 10
PITCH = CELL + GAP
SEG = 5                      # snake length in cells
DUR = 20.0                   # seconds per loop
OFF = 4                      # cells the snake travels off-grid before wrapping

LIGHT = dict(empty="#ebedf0", levels=["#9be9a8", "#40c463", "#30a14e", "#216e39"],
             snake="#6f42c1", bg="none")
DARK = dict(empty="#161b22", levels=["#0e4429", "#006d32", "#26a641", "#39d353"],
            snake="#a371f7", bg="none")


def path():
    """Serpentine over every cell, then off-grid right and back on from the left.

    Returns (cells, stops): cells is [(col, row, t_units)] in eating order,
    stops is [(t_units, col, row)] keyframe corners for the snake.
    """
    cells, stops, t = [], [], 0
    for c in range(COLS):
        rows = range(ROWS) if c % 2 == 0 else range(ROWS - 1, -1, -1)
        rows = list(rows)
        stops.append((t, c, rows[0]))
        for i, r in enumerate(rows):
            cells.append((c, r, t + i))
        t += ROWS - 1
        stops.append((t, c, rows[-1]))
        t += 1                                  # step sideways into next column
    t -= 1                                      # no sideways step after last column
    last_row = stops[-1][2]
    stops.append((t + OFF, COLS - 1 + OFF, last_row))      # glide off the right edge
    stops.append((t + OFF + 1, -OFF, 0))                   # jump back, off-screen
    stops.append((t + OFF + 1 + OFF, 0, 0))                # glide back in
    return cells, stops[-1][0], cells, stops


def svg(theme, seed=7):
    rnd = random.Random(seed)
    cells, total, _, stops = path()
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
        color = rnd.choices(theme["levels"], weights=(25, 30, 25, 20))[0]
        delay = -(DUR - t * unit)
        out.append(f'<rect class="d" x="{c * PITCH}" y="{r * PITCH}" width="{CELL}" '
                   f'height="{CELL}" rx="3" fill="{color}" '
                   f'style="--c:{color};animation-delay:{delay:.3f}s"/>')

    for i in range(SEG):
        delay = 0 if i == 0 else -(DUR - i * unit)
        op = 1 - i * 0.14
        out.append(f'<rect class="s" width="{CELL}" height="{CELL}" rx="4" '
                   f'fill="{theme["snake"]}" opacity="{op:.2f}" '
                   f'style="animation-delay:{delay:.3f}s"/>')

    out += ["</g>", "</svg>"]
    return "\n".join(out)


def check():
    cells, total, _, stops = path()
    seen = {(c, r) for c, r, _ in cells}
    assert len(cells) == COLS * ROWS == len(seen), "every cell eaten exactly once"
    times = [t for _, _, t in cells]
    assert times == sorted(times), "cells are eaten in order"
    assert times[0] == 0 and times[-1] < total, "eat times fit inside one loop"
    assert [s[0] for s in stops] == sorted(s[0] for s in stops), "keyframes ascend"
    assert stops[-1][1:] == (0, 0), "loop ends back at the start cell"
    assert stops[-2][1] < 0, "the wrap jump happens off-screen"


if __name__ == "__main__":
    check()
    for name, theme in (("snake-light.svg", LIGHT), ("snake-dark.svg", DARK)):
        open(name, "w", encoding="utf-8", newline="\n").write(svg(theme))
        print(name, "ok")
