#!/usr/bin/env python3
"""Bake animated SMIL SVGs for the README from data/moves.json.

The viewer animates with JS; GitHub READMEs can't run JS, but they do render
SMIL-animated SVGs inside <img>. This script re-samples the same animation
specs and emits self-contained looping SVGs into media/. The figure demo uses
the same volumetric body renderer as the viewer (tapered-capsule limbs,
jersey/shorts/shoes, headband, strung racket).
"""
import json, math, os

C = dict(bg="#EAF1EC", line="#FFFFFF", ink="#48544D", ink3="#71807A",
         accent="#1E7A5F", accent2="#14614A", cork="#A8482C", paper="#F6F8F6",
         skin="#D9A87F", shorts="#2A3530", shoe="#FAFAF8", grip="#1A231E", strings="#DCE3DE")
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


# ================= top-down court (footwork / doubles) =================
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
    out = []
    for s in shots:
        t0 = bounds[s["at"]]
        t1 = min(t0 + 450, bounds[s["at"] + 1])
        fx, fy = s["from"]; tx, ty = s["to"]
        times = [0, t0, t1, total]
        op = (f'<animate attributeName="opacity" values="0;1;.45;.45" keyTimes="{kt(times, total)}" '
              f'dur="{dur}s" repeatCount="indefinite" calcMode="discrete"/>')
        out.append(
            f'<line x1="{fx}" y1="{fy}" stroke="{C["cork"]}" stroke-width="6" stroke-dasharray="16 12" opacity="0">'
            f'{anim("x2", [fx, fx, tx, tx], times, total, dur)}{anim("y2", [fy, fy, ty, ty], times, total, dur)}{op}</line>'
            f'<circle r="13" fill="{C["cork"]}" opacity="0">'
            f'{anim("cx", [fx, fx, tx, tx], times, total, dur)}{anim("cy", [fy, fy, ty, ty], times, total, dur)}{op}</circle>')
    return "".join(out)


def marker_anim(phases, bounds, total):
    times = bounds + [total]
    xs = [phases[0]["pos"][0]] + [p["pos"][0] for p in phases] + [phases[-1]["pos"][0]]
    ys = [phases[0]["pos"][1]] + [p["pos"][1] for p in phases] + [phases[-1]["pos"][1]]
    return times, xs, ys


def gen_footwork(move, fname, partner=False):
    a = move["anim"]
    ph = a["phases"]
    bounds = [0]
    for p in ph: bounds.append(bounds[-1] + p["dur"])
    total = bounds[-1] + 900
    dur = total / 1000
    route = " ".join(f'{p["pos"][0]},{p["pos"][1]}' for p in ph)
    inner = [f'<polyline points="{route}" fill="none" stroke="{C["accent"]}" stroke-width="7" stroke-dasharray="18 14" opacity=".35"/>']
    shots = a.get("shuttle") or []
    if isinstance(shots, dict): shots = [shots]
    inner.append(shots_svg(shots, bounds, total, dur))
    if partner and a.get("phases2"):
        t2, xs2, ys2 = marker_anim(a["phases2"], bounds, total)
        inner.append(f'<circle r="17" fill="{C["bg"]}" stroke="{C["ink"]}" stroke-width="5">'
                     f'{anim("cx", xs2, t2, total, dur)}{anim("cy", ys2, t2, total, dur)}</circle>')
    t1, xs1, ys1 = marker_anim(ph, bounds, total)
    inner.append(f'<circle r="17" fill="{C["accent"]}">{anim("cx", xs1, t1, total, dur)}{anim("cy", ys1, t1, total, dur)}</circle>'
                 f'<circle r="7" fill="{C["paper"]}">{anim("cx", xs1, t1, total, dur)}{anim("cy", ys1, t1, total, dur)}</circle>')
    open(fname, "w").write(court_top("".join(inner)))


# ================= volumetric human figure =================
FIG = dict(torso=95, neck=13, headR=15, ua=62, fa=58, rk=64, th=78, sh=74, ft=26,
           oua=54, ofa=50, rootX=330, rootY=318, ground=486)
DEF = dict(otherUpper=115, otherFore=100, frontFoot=180, backFoot=0, rootX=0, rootY=0, face=0)
STAND = dict(torso=-88, upperArm=80, foreArm=150, racket=-175, face=0.25,
             frontThigh=103, frontShin=92, frontFoot=182, backThigh=78, backShin=88, backFoot=5)


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
    s = dict(rt=rt, sh=sh, hd=hd, el=el, wr=wr, tp=tp, oe=oe, ow=ow, fk=fk, fn=fn,
             ffp=ffp, bk=bk, bn=bn, bfp=bfp, face=g("face"), rka=P["racket"], ta=P["torso"])
    s["hc"] = ext(wr, P["racket"], FIG["rk"] + 18)
    s["grip"] = ext(wr, P["racket"], 16)
    s["rx"] = 5 + 16 * s["face"]
    rr = math.radians(s["rka"]); sx, sy = math.cos(rr), math.sin(rr); pxv, pyv = -sy, sx
    s["chords"] = []
    for o in (-9, 0, 9):
        cx0, cy0 = s["hc"][0] + sx * o, s["hc"][1] + sy * o
        half = s["rx"] * math.sqrt(max(0, 1 - o * o / 484))
        s["chords"].append(((cx0 + pxv * half, cy0 + pyv * half), (cx0 - pxv * half, cy0 - pyv * half)))
    tr = math.radians(s["ta"]); qx, qy = -math.sin(tr), math.cos(tr)
    hb = (s["hd"][0] + math.cos(tr) * 5, s["hd"][1] + math.sin(tr) * 5)
    s["band"] = ((hb[0] + qx * 13, hb[1] + qy * 13), (hb[0] - qx * 13, hb[1] - qy * 13))
    return s


def cap_pts(a, b, r1, r2):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L, dx / L
    return (f"{F(a[0]+nx*r1)},{F(a[1]+ny*r1)} {F(b[0]+nx*r2)},{F(b[1]+ny*r2)} "
            f"{F(b[0]-nx*r2)},{F(b[1]-ny*r2)} {F(a[0]-nx*r1)},{F(a[1]-ny*r1)}")


class BodyEmitter:
    """Emits volumetric body markup — static (1 sample) or SMIL-animated (many)."""
    def __init__(self, samples, times=None, total=None, dur=None):
        self.s, self.t, self.T, self.d = samples, times, total, dur
        self.animated = len(samples) > 1

    def _an(self, attr, vals):
        return anim(attr, vals, self.t, self.T, self.d) if self.animated else ""

    def _static(self, attr, vals):
        return f'{attr}="{F(vals[0])}"'

    def cap(self, ka, kb, r1, r2, fill, extra=""):
        pas = [s[ka] for s in self.s]; pbs = [s[kb] for s in self.s]
        pts = [cap_pts(a, b, r1, r2) for a, b in zip(pas, pbs)]
        if self.animated:
            poly = (f'<polygon fill="{fill}" {extra} points="{pts[0]}">'
                    f'<animate attributeName="points" values="{";".join(pts)}" keyTimes="{kt(self.t, self.T)}" '
                    f'dur="{self.d}s" repeatCount="indefinite" calcMode="linear"/></polygon>')
        else:
            poly = f'<polygon fill="{fill}" {extra} points="{pts[0]}"/>'
        return poly + self.circle(ka, r1, fill, extra) + self.circle(kb, r2, fill, extra)

    def circle(self, key, r, fill, extra=""):
        xs = [s[key][0] for s in self.s]; ys = [s[key][1] for s in self.s]
        return (f'<circle r="{r}" fill="{fill}" {extra} {self._static("cx", xs)} {self._static("cy", ys)}>'
                f'{self._an("cx", xs)}{self._an("cy", ys)}</circle>')

    def seg(self, get_a, get_b, stroke, w, cap="round"):
        ax = [get_a(s)[0] for s in self.s]; ay = [get_a(s)[1] for s in self.s]
        bx = [get_b(s)[0] for s in self.s]; by = [get_b(s)[1] for s in self.s]
        return (f'<line stroke="{stroke}" stroke-width="{w}" stroke-linecap="{cap}" '
                f'{self._static("x1", ax)} {self._static("y1", ay)} {self._static("x2", bx)} {self._static("y2", by)}>'
                f'{self._an("x1", ax)}{self._an("y1", ay)}{self._an("x2", bx)}{self._an("y2", by)}</line>')

    def body(self):
        shoeX = f'stroke="{C["ink3"]}" stroke-width="2.5"'
        parts = [
            f'<g opacity=".5">{self.cap("sh","oe",9,7.5,C["skin"])}{self.cap("oe","ow",7.5,6,C["skin"])}</g>',
            f'<g opacity=".62">{self.cap("rt","bk",13,10,C["shorts"])}{self.cap("bk","bn",9.5,7.5,C["skin"])}'
            f'{self.cap("bn","bfp",8,7,C["shoe"],shoeX)}</g>',
            self.cap("rt", "sh", 15, 17, C["accent"]),
            self.circle("rt", 15, C["shorts"]),
            self.cap("rt", "fk", 13, 10, C["shorts"]), self.cap("fk", "fn", 9.5, 7.5, C["skin"]),
            self.cap("fn", "ffp", 8, 7, C["shoe"], shoeX),
            self.cap("sh", "hd", 6.5, 5, C["skin"]), self.circle("hd", 15, C["skin"]),
            self.seg(lambda s: s["band"][0], lambda s: s["band"][1], C["accent"], 6),
            self.cap("sh", "el", 9.5, 8, C["skin"]), self.cap("el", "wr", 8, 6.5, C["skin"]),
            self.cap("wr", "grip", 5.5, 5, C["grip"]),
            self.seg(lambda s: s["grip"], lambda s: s["tp"], C["ink"], 4, cap="butt"),
        ]
        # racket head ellipse
        cxs = [s["hc"][0] for s in self.s]; cys = [s["hc"][1] for s in self.s]
        rxs = [s["rx"] for s in self.s]
        if self.animated:
            rot = ";".join(f'{F(s["rka"]+90)} {F(s["hc"][0])} {F(s["hc"][1])}' for s in self.s)
            parts.append(
                f'<ellipse ry="22" fill="{C["paper"]}" fill-opacity=".3" stroke="{C["accent2"]}" stroke-width="4.5">'
                f'{self._an("cx",cxs)}{self._an("cy",cys)}{self._an("rx",rxs)}'
                f'<animateTransform attributeName="transform" type="rotate" values="{rot}" '
                f'keyTimes="{kt(self.t,self.T)}" dur="{self.d}s" repeatCount="indefinite" calcMode="linear"/></ellipse>')
        else:
            s0 = self.s[0]
            parts.append(f'<ellipse cx="{F(cxs[0])}" cy="{F(cys[0])}" rx="{F(rxs[0])}" ry="22" '
                         f'fill="{C["paper"]}" fill-opacity=".3" stroke="{C["accent2"]}" stroke-width="4.5" '
                         f'transform="rotate({F(s0["rka"]+90)} {F(cxs[0])} {F(cys[0])})"/>')
        for k in range(3):
            parts.append(self.seg(lambda s, k=k: s["chords"][k][0], lambda s, k=k: s["chords"][k][1], C["strings"], 2, cap="butt"))
        parts.append(self.circle("wr", 6.5, C["skin"]))
        parts.append(self.circle("ow", 6, C["skin"], 'opacity=".5"'))
        return "".join(parts)


def over_svg(samps, Ps, times, total, dur):
    """gymvisual-style firing-region highlights driven by pose m* keys (0–1)."""
    R = "#C2453A"; out = []
    act = lambda key: [p.get(key, 0) for p in Ps]

    def ell(ka, kb, offd, ry, key):
        a = act(key)
        if max(a) < .05: return ""
        cxs, cys, rxs, angs = [], [], [], []
        for s in samps:
            p, q = s[ka], s[kb]
            dx, dy = q[0]-p[0], q[1]-p[1]; L = math.hypot(dx, dy) or 1
            n = (-dy/L, dx/L); n = n if n[0] >= 0 else (-n[0], -n[1])
            cxs.append((p[0]+q[0])/2 + n[0]*offd); cys.append((p[1]+q[1])/2 + n[1]*offd)
            rxs.append(L*.4); angs.append(math.degrees(math.atan2(dy, dx)))
        rot = ";".join(f"{F(an)} {F(cx)} {F(cy)}" for an, cx, cy in zip(angs, cxs, cys))
        ops = [round(.8*v, 2) for v in a]
        return (f'<ellipse ry="{ry}" fill="{R}" opacity="{ops[0]}">'
                + anim("cx", cxs, times, total, dur) + anim("cy", cys, times, total, dur)
                + anim("rx", rxs, times, total, dur) + anim("opacity", ops, times, total, dur)
                + f'<animateTransform attributeName="transform" type="rotate" values="{rot}" '
                  f'keyTimes="{kt(times,total)}" dur="{dur}s" repeatCount="indefinite" calcMode="linear"/></ellipse>')

    def dot(k, r, key):
        a = act(key)
        if max(a) < .05: return ""
        xs = [s[k][0] for s in samps]; ys = [s[k][1] for s in samps]
        ops = [round(.8*v, 2) for v in a]
        return (f'<circle r="{r}" fill="{R}" opacity="{ops[0]}">'
                + anim("cx", xs, times, total, dur) + anim("cy", ys, times, total, dur)
                + anim("opacity", ops, times, total, dur) + "</circle>")

    out += [ell("bk", "bn", 5, 7, "mCalf"), dot("rt", 13, "mGlutes"), ell("rt", "sh", 0, 12, "mCore"),
            dot("sh", 11, "mShoulder"), ell("sh", "el", 0, 8, "mUarm"),
            ell("el", "wr", 0, 7, "mForearm"), dot("wr", 9, "mHand")]
    return "".join(out)


def gen_figure(move, fname):
    fr = move["anim"]["frames"]
    S = 6
    times, samples, Ps, t_acc = [0.0], [joints(fr[0]["pose"])], [fr[0]["pose"]], 0.0
    for i, f in enumerate(fr):
        prev = fr[0]["pose"] if i == 0 else fr[i - 1]["pose"]
        for j in range(1, S + 1):
            times.append(t_acc + f["dur"] * j / S)
            P = pose_lerp(prev, f["pose"], ease(j / S))
            samples.append(joints(P)); Ps.append(P)
        t_acc += f["dur"]
    total = t_acc + 1100
    times.append(total); samples.append(samples[-1]); Ps.append(Ps[-1])
    g = FIG["ground"]
    dur = total / 1000
    em = BodyEmitter(samples, times, total, dur)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="30 40 590 470">'
           f'<rect x="30" y="40" width="590" height="470" fill="{C["bg"]}"/>'
           f'<line x1="40" y1="{g}" x2="610" y2="{g}" stroke="#DCE3DE" stroke-width="3"/>'
           f'<line x1="72" y1="{g}" x2="72" y2="{g-168}" stroke="{C["ink3"]}" stroke-width="4" opacity=".55"/>'
           f'{em.body()}{over_svg(samples, Ps, times, total, dur)}</svg>')
    open(fname, "w").write(svg)


# ================= anatomy (medical plate) =================
AN = dict(S=(200, 360), hum=150, fore=140, hand=38,
          plate="#F8F4EA", edge="#D9CFBA", bone="#EFE7D2", boneS="#C4B896",
          musPale=(216, 154, 148), musRed=(178, 62, 52), ink="#6A5F4B",
          handF="#E6D9BC", grip="#3A342C")
MUSCLE_TXT = dict(triceps="肱三头肌", biceps="肱二头肌", pronator="旋前圆肌",
                  supinator="旋后肌", flexors="前臂屈肌群")


def perp_to(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1.0
    n = (-dy / L, dx / L)
    return n if n[0] >= 0 else (-n[0], -n[1])


def offp(p, n, d):
    return (p[0] + n[0] * d, p[1] + n[1] * d)


def anat_geom(P, origin=None):
    S = tuple(origin) if origin else AN["S"]
    E = ext(S, P["upperArm"], AN["hum"]); W = ext(E, P["foreArm"], AN["fore"])
    H = ext(W, P.get("hand", P["foreArm"] + 12), AN["hand"])
    G = ext(W, P.get("hand", P["foreArm"] + 12), AN["hand"] + 34)
    nH = perp_to(S, E); nF = perp_to(E, W); pron = P.get("pron", 0)
    rP = offp(E, nF, 9); rD = offp(W, nF, 9 - 18 * pron)
    uP = offp(E, nF, -5); uD = offp(W, nF, -5)
    rad = lambda t: (rP[0] + (rD[0] - rP[0]) * t, rP[1] + (rD[1] - rP[1]) * t)
    mus = dict(
        triceps=(offp(S, nH, 16), offp(E, nH, 12)),
        biceps=(offp(S, nH, -14), offp((E[0]*.82+W[0]*.18, E[1]*.82+W[1]*.18), nF, -8)),
        pronator=(offp(E, nF, -10), rad(.42)),
        supinator=(offp(E, nH, 10), rad(.25)),
        flexors=(offp(E, nF, -11), offp(W, nF, -7)))
    return dict(S=S, E=E, W=W, H=H, G=G, rP=rP, rD=rD, uP=uP, uD=uD,
                nH=nH, nF=nF, mus=mus, pron=pron)


def gen_anatomy(move, fname):
    a = move["anim"]
    fr, show = a["frames"], a.get("show", ["triceps", "pronator", "flexors"])
    origin = a.get("origin")
    S_ = 6
    times, geos, acts = [0.0], [anat_geom(fr[0]["pose"], origin)], [fr[0]["pose"]]
    t_acc = 0.0
    for i, f in enumerate(fr):
        prev = fr[0]["pose"] if i == 0 else fr[i - 1]["pose"]
        for j in range(1, S_ + 1):
            P = pose_lerp(prev, f["pose"], ease(j / S_))
            times.append(t_acc + f["dur"] * j / S_)
            geos.append(anat_geom(P, origin)); acts.append(P)
        t_acc += f["dur"]
    total = t_acc + 1100
    times.append(total); geos.append(geos[-1]); acts.append(acts[-1])
    dur = total / 1000

    def cap_a(ka, kb, r1, r2, fill, extra=""):
        pas = [g[ka] for g in geos]; pbs = [g[kb] for g in geos]
        pts = [cap_pts(p, q, r1, r2) for p, q in zip(pas, pbs)]
        out = (f'<polygon fill="{fill}" {extra} points="{pts[0]}">'
               f'<animate attributeName="points" values="{";".join(pts)}" keyTimes="{kt(times,total)}" '
               f'dur="{dur}s" repeatCount="indefinite" calcMode="linear"/></polygon>')
        for plist, r in ((pas, r1), (pbs, r2)):
            out += (f'<circle r="{r}" fill="{fill}" {extra} cx="{F(plist[0][0])}" cy="{F(plist[0][1])}">'
                    + anim("cx", [p[0] for p in plist], times, total, dur)
                    + anim("cy", [p[1] for p in plist], times, total, dur) + "</circle>")
        return out

    def bone_a(ka, kb, shaft, end):
        x = f'stroke="{AN["boneS"]}" stroke-width="2"'
        return cap_a(ka, kb, shaft, shaft, AN["bone"], x) + "".join(
            f'<circle r="{end}" fill="{AN["bone"]}" {x} cx="{F(geos[0][k][0])}" cy="{F(geos[0][k][1])}">'
            + anim("cx", [g[k][0] for g in geos], times, total, dur)
            + anim("cy", [g[k][1] for g in geos], times, total, dur) + "</circle>"
            for k in (ka, kb))

    def muscle_a(key, ry0, ryx):
        os_ = [g["mus"][key][0] for g in geos]; is_ = [g["mus"][key][1] for g in geos]
        cxs = [(o[0]+i[0])/2 for o, i in zip(os_, is_)]
        cys = [(o[1]+i[1])/2 for o, i in zip(os_, is_)]
        rxs = [math.hypot(i[0]-o[0], i[1]-o[1])/2 for o, i in zip(os_, is_)]
        angs = [math.degrees(math.atan2(i[1]-o[1], i[0]-o[0])) for o, i in zip(os_, is_)]
        av = [p.get(key, 0) for p in acts]
        rys = [ry0 + ryx * v for v in av]
        cols = [f"rgb({round(AN['musPale'][0]+(AN['musRed'][0]-AN['musPale'][0])*v)},"
                f"{round(AN['musPale'][1]+(AN['musRed'][1]-AN['musPale'][1])*v)},"
                f"{round(AN['musPale'][2]+(AN['musRed'][2]-AN['musPale'][2])*v)})" for v in av]
        rot = ";".join(f"{F(an)} {F(cx)} {F(cy)}" for an, cx, cy in zip(angs, cxs, cys))
        return (f'<ellipse opacity=".88" fill="{cols[0]}">'
                + anim("cx", cxs, times, total, dur) + anim("cy", cys, times, total, dur)
                + anim("rx", rxs, times, total, dur) + anim("ry", rys, times, total, dur)
                + f'<animate attributeName="fill" values="{";".join(cols)}" keyTimes="{kt(times,total)}" dur="{dur}s" repeatCount="indefinite" calcMode="linear"/>'
                + f'<animateTransform attributeName="transform" type="rotate" values="{rot}" keyTimes="{kt(times,total)}" dur="{dur}s" repeatCount="indefinite" calcMode="linear"/></ellipse>')

    parts = [f'<rect x="6" y="6" width="628" height="458" fill="{AN["plate"]}" stroke="{AN["edge"]}" stroke-width="3"/>',
             bone_a("S", "E", 6, 11)]
    for k in ("triceps", "biceps"):
        if k in show: parts.append(muscle_a(k, 13 if k == "triceps" else 11, 7 if k == "triceps" else 6))
    parts += [bone_a("uP", "uD", 5, 8), bone_a("rP", "rD", 4.5, 7)]
    for k in ("pronator", "supinator", "flexors"):
        if k in show: parts.append(muscle_a(k, 8 if k != "supinator" else 7, 5))
    parts += [cap_a("W", "H", 9, 7, AN["handF"], f'stroke="{AN["boneS"]}" stroke-width="1.5"'),
              cap_a("H", "G", 4.5, 4, AN["grip"])]
    # labels (static text, animated leader lines)
    label_defs = [("humerus", "肱骨"), ("radius", "桡骨"), ("ulna", "尺骨")] + [(k, MUSCLE_TXT[k]) for k in show]
    for idx, (key, txt) in enumerate(label_defs):
        y = 64 + idx * 40
        if key == "humerus": anc = [((g["S"][0]+g["E"][0])/2, (g["S"][1]+g["E"][1])/2) for g in geos]
        elif key == "radius": anc = [(g["rP"][0]+(g["rD"][0]-g["rP"][0])*.6, g["rP"][1]+(g["rD"][1]-g["rP"][1])*.6) for g in geos]
        elif key == "ulna": anc = [((g["uP"][0]+g["uD"][0])/2, (g["uP"][1]+g["uD"][1])/2) for g in geos]
        else: anc = [((g["mus"][key][0][0]+g["mus"][key][1][0])/2, (g["mus"][key][0][1]+g["mus"][key][1][1])/2) for g in geos]
        pl = [f"{F(p[0])},{F(p[1])} 452,{y} 468,{y}" for p in anc]
        parts.append(f'<polyline fill="none" stroke="{AN["boneS"]}" stroke-width="1.5" points="{pl[0]}">'
                     f'<animate attributeName="points" values="{";".join(pl)}" keyTimes="{kt(times,total)}" dur="{dur}s" repeatCount="indefinite" calcMode="linear"/></polyline>'
                     f'<text x="474" y="{y+5}" font-size="16" fill="{AN["ink"]}">{txt}</text>')
    open(fname, "w").write(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 470">{"".join(parts)}</svg>')


# ================= trajectory =================
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
    stand = BodyEmitter([joints(STAND)])
    parts = [f'<rect x="0" y="130" width="1360" height="660" fill="{C["bg"]}"/>',
             f'<line x1="10" y1="{ground}" x2="1350" y2="{ground}" stroke="{C["line"]}" stroke-width="5"/>']
    for x in (30, 472, 868, 1310):
        parts.append(f'<line x1="{x}" y1="{ground}" x2="{x}" y2="{ground-16}" stroke="{C["line"]}" stroke-width="4"/>')
    parts += [f'<line x1="{net}" y1="{ground}" x2="{net}" y2="{ty(155)}" stroke="{C["ink3"]}" stroke-width="6"/>',
              f'<rect x="{net-9}" y="{ty(155)}" width="18" height="15" fill="{C["ink3"]}"/>',
              f'<g transform="translate({px},{ground}) scale(0.5) translate({-FIG["rootX"]},{-FIG["ground"]})">{stand.body()}</g>']
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
gen_anatomy(moves["pw-02"], "media/demo-anatomy.svg")
gen_footwork(moves["fw-02"], "media/demo-footwork.svg")
gen_footwork(moves["db-01"], "media/demo-doubles.svg", partner=True)
gen_trajectory(moves["sk-04"], "media/demo-trajectory.svg")
for f in sorted(os.listdir("media")):
    print(f, os.path.getsize(os.path.join("media", f)) // 1024, "KB")
