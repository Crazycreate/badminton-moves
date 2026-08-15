# 🏸 Badminton Moves Dataset

**English** | [简体中文](README.zh-CN.md)

A structured badminton movement & technique dataset with an interactive viewer. The layout follows the "JSON data layer + per-item animation + `index.html` browser" pattern of [exercises-dataset](https://github.com/hasaneyldrm/exercises-dataset).

One key difference from the fitness dataset: there is no license-free GIF library for badminton, so **every animation here is rendered in real time by self-drawn SVG engines, driven entirely by the data specs** — no media files, no copyright issues, fully offline.

## What's inside

**32 moves** across **6 categories**:

| Category | Prefix | Count | Animation |
|---|---|---|---|
| Footwork | `fw-` | 7 | Top-down court view: movement paths, step types, incoming shuttle |
| Strokes | `sk-` | 8 | **Trajectory view** — side-view full-court flight arcs (solid = model shot, dashed = variation, red = anti-pattern); net play adds a stick-figure tab, cross-court net uses top-down |
| Doubles | `db-` | 6 | **Two-player synchronized top-down animation** (solid = you, hollow = partner) with multi-shot rallies |
| Split step & balance | `st-` | 4 | Timing axis (split step), top-down (recovery / direction change), stance coverage |
| Power generation | `pw-` | 4 | **Side-view stick figure** — upper-arm / forearm / racket-face keyframes with pronation–supination arrows, active-segment highlighting and racket-tip trail, plus a kinetic-chain tab |
| Defense | `df-` | 3 | Top-down + incoming smash lines |

Every record contains: bilingual name, category, difficulty, summary, key points, common mistakes, drills, related-move links, an animation spec, and a reserved `video` field for future real-footage links.

## File structure

```
badminton-moves/
├── index.html            # Viewer: category filter + search + six animation engines
├── data/
│   ├── moves.json        # Source of truth (for programmatic use)
│   ├── moves.js          # Generated from moves.json, lets index.html run from file://
│   └── moves.schema.json # JSON Schema for the data layer
├── README.md             # This file
└── README.zh-CN.md       # Chinese version
```

## Usage

Just open `index.html` in a browser — data is loaded via `moves.js`, so it works from `file://` without a local server.

After editing the data, regenerate `moves.js`:

```bash
python3 -c "
import json
d=json.load(open('data/moves.json'))
open('data/moves.js','w').write('window.BADMINTON_MOVES = '+json.dumps(d,ensure_ascii=False,indent=1)+';')"
```

## Coordinate systems

**Top-down half court** (footwork / doubles / stance), in centimetres: `x` 0–610 left→right facing the net, `y` 0 = net, `y` 670 = baseline, `y < 0` = a compressed strip of the opponent's side used as shuttle origins. Short service line y=198, doubles long service line y=594, singles sidelines x=46 / x=564, centre line x=305.

**Side-view full court** (trajectory): `x` 0–1340 cm along the court length with the net at 670 (own baseline 30, opponent baseline 1310, service lines 472/868); heights are cm above ground. Arcs crossing the net should clear 155 cm (net height) at x=670 — the dataset's arcs are validated against this.

**Stick figure** (side view): joint angles in degrees, screen space — 0° = right (player's back side), 90° = down, 180° = left (net side), −90° = up. Keep consecutive keyframe angles numerically continuous (use values beyond ±180 instead of wrapping) so linear interpolation sweeps the correct arc.

## Adding a move

Append a record to `data/moves.json` (validate against `moves.schema.json`) and pick an animation type:

- `footwork` — `phases` (position + step kind + label + duration); optional `shuttle` (a single shot or an array for multi-shot rallies, each firing at its phase index); optional `phases2` adds a doubles partner (hollow marker, same length as `phases`, synchronized)
- `chain` — kinetic-chain `nodes` (title + caption; `hit: true` marks the contact link)
- `timing` — timeline `events` (0–1 instants + labels; `hit: true` = opponent's contact)
- `stance` — `player` position and `zones` coverage rectangles
- `figure` — side-view stick-figure keyframes: per-frame joint angles (upper arm / forearm / racket / torso / legs), `focus` highlights the active segment, `spin` shows a pronation (`in`) or supination (`out`) arrow, `hit` flashes at the racket tip at the end of the frame
- `trajectory` — full-court flight arcs, each defined by `from` / `apex` / `to` (`[x, height-cm]`, net at x=670); `kind` distinguishes model / variation / anti-pattern arcs

A record may also carry an optional `anim2` (any type) — the viewer shows a tab toggle (e.g. power moves pair a stick-figure view with a kinetic-chain view).

Regenerate `moves.js` and you're done — the viewer needs no code changes.

## License

[MIT](LICENSE). Move content and animation specs are original work; the repository layout is inspired by [exercises-dataset](https://github.com/hasaneyldrm/exercises-dataset).
