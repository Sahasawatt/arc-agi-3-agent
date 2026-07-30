# ls20 level 7: first look (2026-07-30)

Replay `results/prefix1822.txt` (the level-6-clearing run's actions) with `probe6.py`;
grid dump in `results/l7-grid.txt`. Everything below is one frame plus one action — a
sighting, not a model.

- The play area SHRINKS: the colour-5 border eats in diagonally from both sides (rows
  27-36 narrow to a point at ~(17-24, 35-36)). A triangle-ish arena, top-left anchored.
- **No plates at all** — `gate.plates` reads zero framed regions, so no panel, no
  marked doors, nothing `locked`/`matched` can ever fire on. Whatever the lock is, it
  is not the level 2-6 mechanism.
- A large colour-12 GLYPH is drawn in the HUD zone, bottom-left (rows 55-59: a boot/L
  shape) — the piece's own colour, six cells counted in `hud` as `12: 6`. Possibly the
  level's ask drawn as a picture rather than a plate.
- `hud` also carries `8: 12` (a colour-8 counter, 12 cells) alongside the familiar
  budget pair; after one action the budget moved 84 -> 80 (4 units/action again) and a
  `3: 4` appeared.
- Two refills: rings at (10-12, 6-8) and (30-32, 21-23).
- One small colour-1 object at (39-40, 19), 1-2 cells, beside the wall — carry-marker
  sized. Whether anything patrols needs the oscillation probe (piece parts: 10-cell
  piece at (19,15), 12-over-9 as before).
- Wall blocks (colour 4) split the arena into corridors again: block at x24-28 y10-19,
  x14-18 y20-24 region, x30-33..., plus the diagonal border.

Probe (1) is done — `results/l7-osc.txt`, 18 safe oscillation actions: **nothing
patrols**. No object but the piece moves; the colour-1 fragment's x39/x39-40 flicker is
a read artifact on a static marker. The clock is the familiar pair (budget falls 4 a
move, grey grows 4), so a life is 21 moves at full 84.

Next probes: (2) walk the corridors and watch `hud`'s colour-8 counter and the big
colour-12 HUD glyph for changes — one of them is presumably the goal condition; (3)
touch the colour-1 marker's cell and the two refills; (4) map what the shrinking
diagonal border means for `walkable` (the piece starts three steps from a wall of 5s,
which every earlier level treated as decoration and this one uses as terrain).
