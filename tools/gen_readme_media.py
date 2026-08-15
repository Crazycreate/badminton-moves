#!/usr/bin/env python3
"""Bake animated SMIL SVGs for the README from data/moves.json.

The viewer animates with JS; GitHub READMEs can't run JS, but they do render
SMIL-animated SVGs inside <img>. This script re-samples the same animation
specs and emits self-contained looping SVGs into media/.
"""
import json, math, os

C = dict(bg="#EAF1EC", line="#FFFFFF", ink="#48544D", ink3="#71807A",
         accent="#1E7A5F", accent2="#14614A", cork="#A8482C", paper="#F6F8F6")
F = lambda v: f"{v:.1f}".rstrip("0").rstrip(".")


def kt(times, total):
    out = [max(0.0, min(1.0, t / total)) for t in times]
    out[0], out[-1] = 0.0, 1.0
    return ";".join(f"{t:.4f}" for t in out)


def anim(attr, vals, times, total, dur):
    return (f'<animate attributeName="{attr}" values="{";".join(F(v) for v in vals)}" '
            f'keyTimes="{kt(times, total)}" dur="{dur}s" repeatCount="indefinite" calcMode="linear"/>')


def ease(t):
    return 2 * t * t if t < .5 else 1 - (-2 * t + 2) ** 2 / 2


# ---------- top-down court ----------
def court_top(inner):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-18 -132 646 828">'
            f'<rect x="-18" y="-132" width="646" height="828" fill="{C["bg"]}"/>'
            f'<rect x="0" y="-120" width="610" height="120" fill="{C["ink"]}" opacity=".05"/>'
            f'<rect x="0" y="0" width="610" height="670" fill="none" stroke="{C["line"]}" stroke-width="3"/>'
            f'<line x1="46" y1="0" x2="46" y2="670" stroke="{C["line"]}" stroke-width="3"/>'
            f'<line x1="564" y1="0" x2="564" y2="670" stroke="{C["line"]}" stroke-width="3"/>'
            f'<line x1="0" y1="198" x2="610" y2="198" stroke="{C["line"]}" stroke-width="3"/>'
            f'<line x1="0" y1="594" x2="610" y2="594" stroke="{C["line"]}" stroke-width="3"/>'
            f'<line x1="305" y1="198" x2="305" y2="670" stroke="{C["line"]}" stroke-width="3"/>'
            f'<line x1="-14" y1="0" x2="624" y2="0" stroke="{C["ink3"]}" stroke-width="5" opacity=".8"/>'
            f'{inner}</svg>')


def shots_svg(shots, bounds, total, dur):
    """Animated shuttle lines + dots, gated to their phase slice."""
    out = []
    for s in shots:
        t0 = bounds[s["at"]]
        t1 = min(t0 + 450, bounds[s["at"] + 1])
        fx, fy = s["from"]; tx, ty = s["to"]
        times = [0, t0, t1, total]
        op = f'<animate attributeName="opacity" values="0;1;.45;.45" keyTimes="{kt(times, total)}" dur="{dur}s" repeatCount="indefinite" calcMode="discrete"/>'
        out.append(
            f'<line x1="{fx}" y1="{fy}" stroke="{C["cork"]}" stroke-width="6" stroke-dasharray="16 12" opacity="0">'
            f'{anim("x2", [fx, fx, tx, tx], times, total, dur)}{anim("y2", [fy, fy, ty, ty], times, total, dur)}{op}</line>'
            f'<circle r="13" fill="{C["cork"]}" opacity="0">'
            f'{anim("cx", [fx, fx, tx, tx], times, total, dur)}{anim("cy", [fy, fy, ty, ty], times, total, dur)}{op}</circle>')
    return "".join(out)


def marker_anim(phases, bounds, total, dur):
    # value at bounds[k] (end of phase k-1) = phases[k-1].pos; phase 0 holds its own pos
    times = bounds + [total]
    xs = [phases[0]["pos"][0]] + [p["pos"][0] for p in phases] + [phases[-1]["pos"][0]]
    ys = [phases[0]["pos"][1]] + [p["pos"][1] for p in phases] + [phases[-1]["pos"][1]]
    return times, xs, ys


def gen_footwork(move, fname, partner=False):
    a = move["anim"]
    ph = a["phases"]
    durs = [p["dur"] for p in ph]
    bounds = [0]
    for d in durs: bounds.append(bounds[-1] + d)
    pause = 900
    total = bounds[-1] + pause
    dur = total / 1000
    route = " ".join(f'{p["pos"][0]},{p["pos"][1]}' for p in ph)
    inner = [f'<polyline points="{route}" fill="none" stroke="{C["accent"]}" stroke-width="7" stroke-dasharray="18 14" opacity=".35"/>']
    shots = a.get("shuttle") or []
    if isinstance(shots, dict): shots = [shots]
    inner.append(shots_svg(shots, bounds, total, dur))
    if partner and a.get("phases2"):
        t2, xs2, ys2 = marker_anim(a["phases2"], bounds, total, dur)
        inner.append(f'<circle r="17" fill="{C["bg"]}" stroke="{C["ink"]}" stroke-width="5">'
                     f'{anim("cx", xs2, t2, total, dur)}{anim("cy", ys2, t2, total, dur)}</circle>')
    t1, xs1, ys1 = marker_anim(ph, bounds, total, dur)
    inner.append(f'<circle r="17" fill="{C["accent"]}">{anim("cx", xs1, t1, total, dur)}{anim("cy", ys1, t1, total, dur)}</circle>'
                 f'<circle r="7" fill="{C["paper"]}">{anim("cx", xs1, t1, total, dur)}{anim("cy", ys1, t1, total, dur)}</circle>')
    open(fname, "w").write(court_top("".join(inner)))


# ---------- figure ----------
FIG = dict(torso=95, neck=13, headR=15, ua=62, fa=58, rk=64, th=78, sh=74, ft=26,
           oua=54, ofa=50, rootX=330, rootY=318, ground=486)
DEF = dict(otherUpper=115, otherFore=100, frontFoot=180, backFoot=0, rootX=0, rootY=0, face=0)


def ext(p, a, l):
    r = math.radians(a); return (p[0] + math.cos(r) * l, p[1] + math.sin(r) * l)


def pose_lerp(A, B, t):
    keys = set(A) | set(B)
    return {k: (A.get(k, B.get(k)) * (1 - t) + B.get(k, A.get(k)) * t) for k in keys}


def joints(P):
    g = lambda k: P.get(k, DEF.get(k, 0))
    rt = (FIG["rootX"] + g("rootX"), FIG["rootY"] + g("rootY"))
    sh = ext(rt, P["torso"], FIG["torso"]); hd = ext(sh, P["torso"], FIG["neck"] + FIG["headR"])
    el = ext(sh, P["upperArm"], FIG["ua"]); wr = ext(el, P["foreArm"], FIG["fa"]); tp = ext(wr, P["racket"], FIG["rk"])
    oe = ext(sh, g("otherUpper"), FIG["oua"]); ow = ext(oe, g("otherFore"), FIG["ofa"])
    fk = ext(rt, P["frontThigh"], FIG["th"]); fn = ext(fk, P["frontShin"], FIG["sh"]); ffp = ext(fn, g("frontFoot"), FIG["ft"])
    bk = ext(rt, P["backThigh"], FIG["th"]); bn = ext(bk, P["backShin"], FIG["sh"]); bfp = ext(bn, g("backFoot"), FIG["ft"])
    hc = ext(wr, P["racket"], FIG["rk"] + 18)
    return dict(rt=rt, sh=sh, hd=hd, el=el, wr=wr, tp=tp, oe=oe, ow=ow, fk=fk, fn=fn,
                ffp=ffp, bk=bk, bn=bn, bfp=bfp, hc=hc, face=g("face"), rka=P["racket"])


def gen_figure(move, fname):
    fr = move["anim"]["frames"]
    S = 6
    times, samples = [], []
    t_acc = 0.0
    for i, f in enumerate(fr):
        prev = fr[0]["pose"] if i == 0 else fr[i - 1]["pose"]
        for j in range(1, S + 1):
            P = pose_lerp(prev, f["pose"], ease(j / S))
            t_acc_j = t_acc + f["dur"] * j / S
            times.append(t_acc_j); samples.append(joints(P))
        t_acc += f["dur"]
    pause = 1100
    total = t_acc + pause
    dur = total / 1000
    times = [0.0] + times + [total]
    samples = [samples[0]] + samples + [samples[-1]]
    # wait: first sample should be frame0 pose at rest
    samples[0] = joints(fr[0]["pose"])

    def line(a, b, w, color, dash=False, op=1):
        va = [s[a] for s in samples]; vb = [s[b] for s in samples]
        dashattr = ' stroke-dasharray="10 8"' if dash else ''
        return (f'<line stroke="{color}" stroke-width="{w}" stroke-linecap="round" opacity="{op}"{dashattr}>'
                + anim("x1", [p[0] for p in va], times, total, dur)
                + anim("y1", [p[1] for p in va], times, total, dur)
                + anim("x2", [p[0] for p in vb], times, total, dur)
                + anim("y2", [p[1] for p in vb], times, total, dur) + "</line>")

    g = FIG["ground"]
    parts = [f'<rect x="30" y="40" width="590" height="470" fill="{C["bg"]}"/>',
             f'<line x1="40" y1="{g}" x2="610" y2="{g}" stroke="#DCE3DE" stroke-width="3"/>',
             f'<line x1="72" y1="{g}" x2="72" y2="{g-168}" stroke="{C["ink3"]}" stroke-width="4" opacity=".55"/>',
             line("sh", "oe", 8, C["ink"], op=.45), line("oe", "ow", 8, C["ink"], op=.45),
             line("rt", "bk", 11, C["ink"]), line("bk", "bn", 11, C["ink"]), line("bn", "bfp", 9, C["ink"]),
             line("rt", "fk", 11, C["ink"]), line("fk", "fn", 11, C["ink"]), line("fn", "ffp", 9, C["ink"]),
             line("rt", "sh", 13, C["ink"])]
    hd = [s["hd"] for s in samples]
    parts.append(f'<circle r="{FIG["headR"]}" fill="none" stroke="{C["ink"]}" stroke-width="9">'
                 + anim("cx", [p[0] for p in hd], times, total, dur)
                 + anim("cy", [p[1] for p in hd], times, total, dur) + "</circle>")
    parts += [line("sh", "el", 11, C["accent"]), line("el", "wr", 11, C["accent"]),
              line("wr", "tp", 5, C["accent2"])]
    hc = [s["hc"] for s in samples]
    rot = ";".join(f'{F(s["rka"] + 90)} {F(s["hc"][0])} {F(s["hc"][1])}' for s in samples)
    parts.append(f'<ellipse ry="22" fill="none" stroke="{C["accent2"]}" stroke-width="5">'
                 + anim("cx", [p[0] for p in hc], times, total, dur)
                 + anim("cy", [p[1] for p in hc], times, total, dur)
                 + anim("rx", [5 + 16 * s["face"] for s in samples], times, total, dur)
                 + f'<animateTransform attributeName="transform" type="rotate" values="{rot}" '
                   f'keyTimes="{kt(times, total)}" dur="{dur}s" repeatCount="indefinite" calcMode="linear"/></ellipse>')
    open(fname, "w").write(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="30 40 590 470">{"".join(parts)}</svg>')


# ---------- trajectory ----------
def gen_trajectory(move, fname):
    arcs = move["anim"]["arcs"]
    ground, sy, net = 730, 0.85, 670
    ty = lambda h: ground - h * sy
    KIND = dict(main=(C["accent"], ""), alt=(C["accent2"], "12 12"), bad=(C["cork"], "12 12"))

    def pts(arc):
        P0 = (arc["from"][0], ty(arc["from"][1])); P2 = (arc["to"][0], ty(arc["to"][1]))
        A = (arc["apex"][0], ty(arc["apex"][1]))
        Cx = ((4 * A[0] - P0[0] - P2[0]) / 2, (4 * A[1] - P0[1] - P2[1]) / 2)
        return [((1-t)**2*P0[0] + 2*(1-t)*t*Cx[0] + t*t*P2[0],
                 (1-t)**2*P0[1] + 2*(1-t)*t*Cx[1] + t*t*P2[1]) for t in (k/48 for k in range(49))]

    slices, t_acc = [], 0.0
    for arc in arcs:
        d = arc.get("dur", 1300)
        slices.append((t_acc, t_acc + d)); t_acc += d + 350
    total = t_acc + 1250
    dur = total / 1000
    px = arcs[0]["from"][0]
    parts = [f'<rect x="0" y="130" width="1360" height="660" fill="{C["bg"]}"/>',
             f'<line x1="10" y1="{ground}" x2="1350" y2="{ground}" stroke="{C["line"]}" stroke-width="5"/>']
    for x in (30, 472, 868, 1310):
        parts.append(f'<line x1="{x}" y1="{ground}" x2="{x}" y2="{ground-16}" stroke="{C["line"]}" stroke-width="4"/>')
    parts += [f'<line x1="{net}" y1="{ground}" x2="{net}" y2="{ty(155)}" stroke="{C["ink3"]}" stroke-width="6"/>',
              f'<rect x="{net-9}" y="{ty(155)}" width="18" height="15" fill="{C["ink3"]}"/>',
              f'<line x1="{px}" y1="{ground}" x2="{px}" y2="{ground-118}" stroke="{C["ink"]}" stroke-width="9" stroke-linecap="round"/>',
              f'<circle cx="{px}" cy="{ground-138}" r="17" fill="none" stroke="{C["ink"]}" stroke-width="8"/>']
    for arc, (s0, s1) in zip(arcs, slices):
        col, dash = KIND[arc.get("kind", "main")]
        path = "M " + " L ".join(f"{F(x)} {F(y)}" for x, y in pts(arc))
        pid = f'p{int(s0)}'
        dashattr = f' stroke-dasharray="{dash}"' if dash else ''
        parts.append(f'<path id="{pid}" d="{path}" fill="none" stroke="{col}" stroke-width="7" opacity=".55"{dashattr}/>')
        times = [0, s0, s1, total]
        parts.append(
            f'<circle r="12" fill="{col}" opacity="0">'
            f'<animate attributeName="opacity" values="0;1;.5;.5" keyTimes="{kt(times, total)}" dur="{dur}s" repeatCount="indefinite" calcMode="discrete"/>'
            f'<animateMotion dur="{dur}s" repeatCount="indefinite" calcMode="linear" '
            f'keyPoints="0;0;1;1" keyTimes="{kt(times, total)}"><mpath href="#{pid}"/></animateMotion></circle>')
    open(fname, "w").write(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 130 1360 660">{"".join(parts)}</svg>')


os.makedirs("media", exist_ok=True)
moves = {m["id"]: m for m in json.load(open("data/moves.json"))}
gen_figure(moves["pw-01"], "media/demo-figure.svg")
gen_footwork(moves["fw-02"], "media/demo-footwork.svg")
gen_footwork(moves["db-01"], "media/demo-doubles.svg", partner=True)
gen_trajectory(moves["sk-04"], "media/demo-trajectory.svg")
for f in sorted(os.listdir("media")):
    print(f, os.path.getsize(os.path.join("media", f)) // 1024, "KB")
