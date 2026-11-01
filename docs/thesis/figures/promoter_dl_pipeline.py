"""Generate the promoter deep-learning pipeline schematic as a static SVG."""
import math
import sys

NAVY, TEAL, PURPLE, ORANGE = "#1F3B5C", "#2A8C82", "#7A6AA6", "#D9822B"
INK, GRAY, LINE = "#22303C", "#5F6B78", "#C5CED8"
L_NAVY, L_TEAL, L_PURPLE, L_ORANGE, L_GRAY = "#E6ECF3", "#E2F1EF", "#ECE9F4", "#FBEEDF", "#F1F3F6"
NUC = {"A": NAVY, "C": TEAL, "G": PURPLE, "T": ORANGE}
SANS = "Helvetica Neue, Helvetica, Arial, sans-serif"
MONO = "Consolas, Menlo, DejaVu Sans Mono, monospace"

out = []


def add(s):
    out.append(s)


def text(x, y, s, size=12, color=INK, weight="normal", anchor="middle", family=SANS, style="normal", extra=""):
    add(f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" fill="{color}" '
        f'font-weight="{weight}" font-style="{style}" text-anchor="{anchor}" {extra}>{s}</text>')


def rect(x, y, w, h, fill="none", stroke=LINE, sw=1, rx=0, extra=""):
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>')


def line(x1, y1, x2, y2, color=NAVY, sw=1.4, arrow=False, dash=None, marker="arrow"):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    m = f' marker-end="url(#{marker})"' if arrow else ""
    add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{sw}"{d}{m}/>')


def path(d, color=NAVY, sw=1.4, fill="none", arrow=False, dash=None, marker="arrow", extra=""):
    da = f' stroke-dasharray="{dash}"' if dash else ""
    m = f' marker-end="url(#{marker})"' if arrow else ""
    add(f'<path d="{d}" fill="{fill}" stroke="{color}" stroke-width="{sw}"{da}{m} {extra}/>')


def chip(cx, y, w, h, lines, fill, stroke, color=INK, size=11.5, bold_first=True, dash=None):
    da = f'stroke-dasharray="{dash}"' if dash else ""
    rect(cx - w / 2, y, w, h, fill=fill, stroke=stroke, sw=1, rx=5, extra=da)
    n = len(lines)
    for i, s in enumerate(lines):
        yy = y + h / 2 + (i - (n - 1) / 2) * (size + 3) + size * 0.36
        text(cx, yy, s, size=size if i == 0 else size - 1, color=color if i == 0 else GRAY,
             weight="bold" if (i == 0 and bold_first) else "normal")


def lock(x, y, color=ORANGE, s=1.0):
    # Simple flat padlock icon with its top-left corner at (x, y).
    path(f"M{x + 3 * s},{y + 6 * s} v{-2.5 * s} a{3 * s},{3 * s} 0 0 1 {6 * s},0 v{2.5 * s}", color=color, sw=1.4)
    rect(x + 1 * s, y + 6 * s, 10 * s, 8 * s, fill=color, stroke=color, sw=1, rx=1.5)


W, H = 1600, 900
add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
add("<title>Deep learning pipeline for DNA promoter classification</title>")
add("<defs>"
    f'<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
    f'<path d="M0,0 L10,5 L0,10 z" fill="{NAVY}"/></marker>'
    f'<marker id="arrow_t" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
    f'<path d="M0,0 L10,5 L0,10 z" fill="{TEAL}"/></marker>'
    f'<marker id="arrow_o" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
    f'<path d="M0,0 L10,5 L0,10 z" fill="{ORANGE}"/></marker>'
    f'<marker id="arrow_g" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
    f'<path d="M0,0 L10,5 L0,10 z" fill="{GRAY}"/></marker>'
    "</defs>")
rect(0, 0, W, H, fill="#FFFFFF", stroke="none", sw=0)

# Panel geometry: (x, width).
PY, PB = 110, 710
P = {"A": (15, 220), "B": (269, 220), "C": (523, 220), "D": (777, 300), "E": (1111, 220), "F": (1365, 220)}
TITLES = {"A": "DNA Sequence Dataset", "B": "Sequence Preprocessing", "C": "DNA Sequence Encoding",
          "D": "Deep Learning Architecture", "E": "Training &amp; Validation", "F": "Prediction &amp; Evaluation"}

# Phase brackets.
for x0, x1, label in [(15, 743, "DATASET PREPARATION"), (777, 1331, "MODEL DEVELOPMENT"), (1365, 1585, "FINAL EVALUATION")]:
    path(f"M{x0},70 V60 H{x1} V70", color=GRAY, sw=1)
    text((x0 + x1) / 2, 48, label, size=12.5, color=GRAY, weight="bold", extra='letter-spacing="1.5"')

for k, (x, w) in P.items():
    main = k == "D"
    rect(x, PY, w, PB - PY, fill="#F7F9FC" if main else "#FFFFFF", stroke=NAVY if main else LINE, sw=1.6 if main else 1, rx=8)
    text(x + 2, 100, k, size=21, color=NAVY, weight="bold", anchor="start")
    text(x + w / 2, PY + 30, TITLES[k], size=15, color=NAVY, weight="bold")
    line(x + 14, PY + 46, x + w - 14, PY + 46, color=LINE, sw=1)

# Stage arrows at mid-height.
keys = list(P)
for a, b in zip(keys, keys[1:]):
    xa = P[a][0] + P[a][1]
    xb = P[b][0]
    line(xa + 4, 410, xb - 5, 410, color=NAVY, sw=1.8, arrow=True)

# ---------------- A: dataset ----------------
x, w = P["A"]
cx = x + w / 2
x0, x1, cy, amp, per = cx - 72, cx + 72, 192, 15, 48
s1, s2 = [], []
n = 160
for i in range(n + 1):
    xx = x0 + (x1 - x0) * i / n
    ph = 2 * math.pi * (xx - x0) / per
    s1.append(f"{xx:.1f},{cy + amp * math.sin(ph):.1f}")
    s2.append(f"{xx:.1f},{cy + amp * math.sin(ph + math.pi):.1f}")
xx = x0 + 3
while xx < x1:
    ph = 2 * math.pi * (xx - x0) / per
    if abs(math.sin(ph)) > 0.35:
        line(xx, cy + amp * math.sin(ph), xx, cy - amp * math.sin(ph), color=LINE, sw=1.6)
    xx += 6
add(f'<polyline points="{" ".join(s1)}" fill="none" stroke="{NAVY}" stroke-width="2"/>')
add(f'<polyline points="{" ".join(s2)}" fill="none" stroke="{TEAL}" stroke-width="2"/>')

groups = [("Promoter (1)", TEAL, L_TEAL, ["TTGACAATTAATCATC", "GCTATAATGTGTGGAA", "TTTACACTTTATGCTT"]),
          ("Non-promoter (0)", PURPLE, L_PURPLE, ["GCCGTAGCAGTCAAGC", "ACGGTCTGAACCTGGA", "CTGAGGCATTCGAGTC"])]
gy = 236
for label, col, light, seqs in groups:
    rect(x + 18, gy, w - 36, 142, fill="#FFFFFF", stroke=col, sw=1.2, rx=6)
    rect(x + 18, gy, w - 36, 28, fill=light, stroke="none", sw=0, rx=6)
    line(x + 18, gy + 28, x + w - 18, gy + 28, color=col, sw=1)
    text(cx, gy + 19, label, size=13, color=col, weight="bold")
    for i, s in enumerate(seqs):
        text(cx, gy + 54 + i * 26, s, size=13, color=INK, family=MONO, extra='letter-spacing="0.6"')
    text(cx, gy + 128, "&#8942;", size=13, color=GRAY)
    gy += 160
text(cx, 586, "Labeled sequences", size=12.5, color=INK, weight="bold")
text(cx, 606, '(<tspan font-style="italic">x</tspan>, <tspan font-style="italic">y</tspan>),  '
     '<tspan font-style="italic">y</tspan> &#8712; {0, 1}', size=12.5, color=GRAY)

# ---------------- B: preprocessing ----------------
x, w = P["B"]
cx = x + w / 2
steps = [("Quality control", "Valid A/C/G/T bases only"),
         ("Window extraction", "Standardized length"),
         ("Redundancy check", "Duplicates and overlaps"),
         ("Partitioning", "Fixed train / test split")]
sy = 174
for i, (t1, t2) in enumerate(steps):
    rect(x + 15, sy, w - 30, 54, fill="#FFFFFF", stroke=LINE, sw=1, rx=6)
    add(f'<circle cx="{x + 34}" cy="{sy + 27}" r="11" fill="{NAVY}"/>')
    text(x + 34, sy + 31.5, str(i + 1), size=12, color="#FFFFFF", weight="bold")
    text(x + 54, sy + 23, t1, size=12.5, color=INK, weight="bold", anchor="start")
    text(x + 54, sy + 40, t2, size=11, color=GRAY, anchor="start")
    if i < 3:
        line(cx, sy + 56, cx, sy + 70, color=GRAY, sw=1.2, arrow=True, marker="arrow_g")
    sy += 72
bx, bw, by = x + 15, w - 30, 486
text(cx, by - 12, "Fixed benchmark train/test split", size=11.5, color=INK, weight="bold")
segs = [(0.78, NAVY, "Training set"), (0.22, ORANGE, "Independent test set")]
xx = bx
for frac, col, _ in segs:
    ww = bw * frac
    rect(xx, by, ww, 22, fill=col, stroke="#FFFFFF", sw=1.5)
    xx += ww
for i, (_, col, lab) in enumerate(segs):
    yy = by + 46 + i * 22
    rect(bx + 4, yy - 10, 12, 12, fill=col, stroke="none", sw=0, rx=2)
    text(bx + 24, yy, lab, size=11.5, color=INK, anchor="start")
line(x + 15, 625, x + w - 15, 625, color=LINE, sw=1, dash="3 3")
text(cx, 648, "Performed before any", size=11, color=GRAY, style="italic")
text(cx, 663, "model fitting", size=11, color=GRAY, style="italic")

# ---------------- C: encoding ----------------
x, w = P["C"]
cx = x + w / 2
onehot = {"A": "1, 0, 0, 0", "C": "0, 1, 0, 0", "G": "0, 0, 1, 0", "T": "0, 0, 0, 1"}
for i, nuc in enumerate("ACGT"):
    yy = 200 + i * 26
    text(cx - 58, yy, nuc, size=14, color=NUC[nuc], weight="bold", family=MONO)
    text(cx - 38, yy, "&#8594;", size=14, color=GRAY)
    text(cx - 22, yy, f"[{onehot[nuc]}]", size=13.5, color=INK, family=MONO, anchor="start")
line(cx, 296, cx, 322, color=NAVY, sw=1.6, arrow=True)
seq = "ACGTTAGC"
cell = 20
mx = cx - (len(seq) * cell) / 2 + 8
my = 356
for j, nuc in enumerate(seq):
    text(mx + j * cell + cell / 2, my - 8, nuc, size=13, color=NUC[nuc], weight="bold", family=MONO)
for i, row in enumerate("ACGT"):
    text(mx - 12, my + i * cell + 14, row, size=11.5, color=GRAY, family=MONO)
    for j, nuc in enumerate(seq):
        hot = nuc == row
        rect(mx + j * cell, my + i * cell, cell, cell, fill=NUC[row] if hot else L_GRAY, stroke="#FFFFFF", sw=1.5)
        text(mx + j * cell + cell / 2, my + i * cell + 14, "1" if hot else "0", size=10.5,
             color="#FFFFFF" if hot else "#9AA5B1", family=MONO)
text(cx, 470, "Numerical Sequence", size=13, color=NAVY, weight="bold")
text(cx, 487, "Representation", size=13, color=NAVY, weight="bold")
text(cx, 511, '4 &#215; <tspan font-style="italic">L</tspan> one-hot matrix', size=11.5, color=GRAY)
text(cx, 528, '(<tspan font-style="italic">L</tspan> = sequence length)', size=11, color=GRAY)

# ---------------- D: architecture ----------------
x, w = P["D"]
cx = x + w / 2
# Encoded input.
cs = 10
ix = cx - 50
iseq = "ACGTTAGCAT"
for i, row in enumerate("ACGT"):
    for j, nuc in enumerate(iseq):
        rect(ix + j * cs, 180 + i * cs, cs, cs, fill=NUC[row] if nuc == row else L_GRAY, stroke="#FFFFFF", sw=1)
text(cx, 240, "Encoded sequence input", size=12.5, color=INK, weight="bold")
line(cx, 250, cx, 274, color=NAVY, sw=1.6, arrow=True)


def stack(x0, y0, sw_, sh, k, off):
    for i in range(k - 1, -1, -1):
        xx, yy = x0 + i * off, y0 + i * off
        rect(xx, yy, sw_, sh, fill=L_PURPLE if i else "#FFFFFF", stroke=PURPLE, sw=1, rx=2)
    # Faint grid on the front map.
    for t in range(1, 4):
        line(x0 + sw_ * t / 4, y0, x0 + sw_ * t / 4, y0 + sh, color=L_PURPLE, sw=1)
        line(x0, y0 + sh * t / 4, x0 + sw_, y0 + sh * t / 4, color=L_PURPLE, sw=1)
    rect(x0, y0, sw_, sh, fill="none", stroke=PURPLE, sw=1, rx=2)


stack(cx - 88, 284, 64, 52, 4, -6)
line(cx - 10, 318, cx + 14, 318, color=NAVY, sw=1.4, arrow=True)
stack(cx + 36, 298, 40, 34, 3, -6)
text(cx + 100, 322, "&#8943;", size=16, color=GRAY)
text(cx, 370, "Feature extraction layers", size=12.5, color=INK, weight="bold")
text(cx, 386, "Stacked feature maps", size=11, color=GRAY)
line(cx, 396, cx, 420, color=NAVY, sw=1.6, arrow=True)
ops = [0.30, 0.75, 0.45, 0.90, 0.20, 0.60, 0.85, 0.35, 0.55, 0.70]
vx = cx - (len(ops) * 17 - 3) / 2
for i, o in enumerate(ops):
    add(f'<rect x="{vx + i * 17:.1f}" y="430" width="14" height="14" rx="2" fill="{PURPLE}" fill-opacity="{o}" stroke="{PURPLE}" stroke-width="1"/>')
text(cx, 466, "Learned feature representation", size=12.5, color=INK, weight="bold")
line(cx, 476, cx, 500, color=NAVY, sw=1.6, arrow=True)
l1 = [cx + d for d in (-52, -26, 0, 26, 52)]
l2 = [cx + d for d in (-26, 0, 26)]
for a in l1:
    for b in l2:
        line(a, 518, b, 552, color=LINE, sw=0.9)
for b in l2:
    line(b, 552, cx, 586, color=LINE, sw=0.9)
for a in l1:
    add(f'<circle cx="{a}" cy="518" r="7" fill="#FFFFFF" stroke="{NAVY}" stroke-width="1.3"/>')
for b in l2:
    add(f'<circle cx="{b}" cy="552" r="7" fill="#FFFFFF" stroke="{NAVY}" stroke-width="1.3"/>')
add(f'<circle cx="{cx}" cy="586" r="8" fill="{L_ORANGE}" stroke="{ORANGE}" stroke-width="1.6"/>')
text(cx, 616, "Classification head", size=12.5, color=INK, weight="bold")
text(cx, 632, "Single output unit", size=11, color=GRAY)
text(cx, 682, "Generic, modular classifier", size=11, color=GRAY, style="italic")

# ---------------- E: training & validation ----------------
x, w = P["E"]
cx = x + w / 2 + 6
chip(cx, 170, 176, 26, ["Training folds"], L_NAVY, NAVY)
line(cx, 197, cx, 211, color=NAVY, sw=1.4, arrow=True)
chip(cx, 212, 176, 26, ['Forward pass  &#375; = <tspan font-style="italic">f</tspan><tspan font-size="8" dy="2">&#952;</tspan><tspan dy="-2">(</tspan><tspan font-style="italic">x</tspan>)'],
     "#FFFFFF", LINE, bold_first=False)
line(cx, 239, cx, 253, color=NAVY, sw=1.4, arrow=True)
chip(cx, 254, 176, 38, ["Binary classification loss", '<tspan font-style="italic">L</tspan>(<tspan font-style="italic">y</tspan>, &#375;)'],
     "#FFFFFF", LINE)
line(cx, 293, cx, 307, color=NAVY, sw=1.4, arrow=True)
chip(cx, 308, 176, 38, ["Gradient-based optimization", "&#952; &#8592; &#952; &#8722; &#951;&#8711;<tspan font-size=\"8\" dy=\"2\">&#952;</tspan><tspan dy=\"-2\" font-style=\"italic\">L</tspan>"],
     "#FFFFFF", LINE)
lx = cx - 88
path(f"M{lx},327 H{x + 12} V225 H{lx - 2}", color=NAVY, sw=1.2, arrow=True)
text(x + 9, 280, "iterate", size=10, color=GRAY, extra=f'transform="rotate(-90 {x + 9} 280)"')
# Five-fold stratified CV inside the training partition.
text(cx, 372, "5-fold stratified CV", size=12, color=INK, weight="bold")
text(cx, 387, "within the training set", size=11, color=GRAY)
gx0, gw, gh, gap = cx - 77.5, 28, 10, 3
for r in range(5):
    for c in range(5):
        rect(gx0 + c * (gw + gap), 396 + r * (gh + gap), gw, gh, fill=TEAL if r == c else L_NAVY,
             stroke="none", sw=0, rx=1.5)
rect(cx - 88, 469, 10, 10, fill=TEAL, stroke="none", sw=0, rx=1.5)
text(cx - 74, 478, "Validation fold", size=10.5, color=INK, anchor="start")
rect(cx + 8, 469, 10, 10, fill=L_NAVY, stroke=NAVY, sw=0.6, rx=1.5)
text(cx + 22, 478, "Training folds", size=10.5, color=INK, anchor="start")
# Loss curves within one fold (schematic, no values).
ox, oy, pw, ph = x + 42, 570, 130, 66
k = ph / 112
line(ox, oy, ox, oy - ph, color=INK, sw=1.1)
line(ox, oy, ox + pw, oy, color=INK, sw=1.1)
text(ox + pw / 2, oy + 13, "Epoch", size=10.5, color=GRAY)
text(ox - 9, oy - ph / 2, "Loss", size=10.5, color=GRAY, extra=f'transform="rotate(-90 {ox - 9} {oy - ph / 2})"')


def tr_y(t):
    return oy - k * (12 + 86 * math.exp(-3.2 * t))


def va_y(t):
    return oy - k * (30 + 70 * math.exp(-3.6 * t) + 136 * max(0.0, t - 0.5) ** 2)


ts = [i / 40 for i in range(41)]
px = [ox + 6 + t * (pw - 12) for t in ts]
tbest = max(ts, key=va_y)
px_best = ox + 6 + tbest * (pw - 12)
line(px_best, oy, px_best, oy - ph + 8, color=ORANGE, sw=1.1, dash="3 3")
add(f'<polyline points="{" ".join(f"{a:.1f},{tr_y(t):.1f}" for a, t in zip(px, ts))}" fill="none" stroke="{NAVY}" stroke-width="1.8"/>')
add(f'<polyline points="{" ".join(f"{a:.1f},{va_y(t):.1f}" for a, t in zip(px, ts))}" fill="none" stroke="{TEAL}" stroke-width="1.8" stroke-dasharray="5 3"/>')
add(f'<circle cx="{px_best:.1f}" cy="{va_y(tbest):.1f}" r="3.2" fill="{ORANGE}"/>')
text(px_best, oy - ph + 2, "Best epoch", size=10, color=ORANGE, weight="bold")
text(ox + pw + 3, va_y(1) + 4, "val", size=10, color=TEAL, weight="bold", anchor="start")
text(ox + pw + 3, tr_y(1) + 4, "train", size=10, color=NAVY, weight="bold", anchor="start")
chip(cx, 594, 184, 36, ["Selection on CV folds", "then refit on full training set"], L_TEAL, TEAL)
rect(cx - 92, 640, 184, 46, fill=L_ORANGE, stroke=ORANGE, sw=1, rx=5, extra='stroke-dasharray="4 3"')
lock(cx - 82, 655)
text(cx + 8, 659, "Test set not used for", size=11, color=INK, weight="bold")
text(cx + 8, 675, "training or selection", size=11, color=INK, weight="bold")

# ---------------- F: prediction & evaluation ----------------
x, w = P["F"]
cx = x + w / 2
chip(cx - 48, 170, 90, 26, ["Final model"], L_NAVY, NAVY, size=11)
chip(cx + 48, 170, 90, 26, ["Test set"], L_ORANGE, ORANGE, size=11)
line(cx - 48, 197, cx - 8, 215, color=NAVY, sw=1.3, arrow=True)
line(cx + 48, 197, cx + 8, 215, color=ORANGE, sw=1.3, arrow=True, marker="arrow_o")
chip(cx, 216, 150, 28, ["P(promoter) &#8712; [0, 1]"], "#FFFFFF", NAVY)
line(cx - 10, 245, cx - 44, 273, color=NAVY, sw=1.3, arrow=True)
line(cx + 10, 245, cx + 44, 273, color=NAVY, sw=1.3, arrow=True)
text(cx - 44, 258, "&#8805; 0.5", size=11, color=GRAY, anchor="end")
text(cx + 44, 258, "&lt; 0.5", size=11, color=GRAY, anchor="start")
chip(cx - 48, 275, 90, 26, ["Promoter"], L_TEAL, TEAL, color=TEAL, size=11)
chip(cx + 48, 275, 90, 26, ["Non-promoter"], L_PURPLE, PURPLE, color=PURPLE, size=11)
text(cx, 320, "Fixed decision threshold", size=10.5, color=GRAY)
line(x + 14, 336, x + w - 14, 336, color=LINE, sw=1)
# Confusion matrix.
c0x, c0y, cc = x + 30, 366, 34
text(c0x + cc, c0y - 8, "Predicted", size=10.5, color=GRAY)
text(c0x - 9, c0y + cc, "Actual", size=10.5, color=GRAY, extra=f'transform="rotate(-90 {c0x - 9} {c0y + cc})"')
for (r, c), lab in {(0, 0): "TP", (0, 1): "FN", (1, 0): "FP", (1, 1): "TN"}.items():
    good = r == c
    rect(c0x + c * cc, c0y + r * cc, cc, cc, fill=L_TEAL if good else L_GRAY, stroke="#FFFFFF", sw=2)
    text(c0x + c * cc + cc / 2, c0y + r * cc + 21, lab, size=11, color=TEAL if good else GRAY, weight="bold")
text(c0x + cc, c0y + 2 * cc + 32, "Confusion matrix", size=10.5, color=GRAY)
# ROC curve.
rx0, ry0, rs = x + 128, c0y + 2 * cc, 68
path(f"M{rx0},{ry0} Q{rx0 + 4},{ry0 - rs + 6} {rx0 + rs},{ry0 - rs} L{rx0 + rs},{ry0} Z", color="none", sw=0,
     fill=NAVY, extra='fill-opacity="0.10"')
line(rx0, ry0, rx0 + rs, ry0 - rs, color=GRAY, sw=1, dash="3 3")
path(f"M{rx0},{ry0} Q{rx0 + 4},{ry0 - rs + 6} {rx0 + rs},{ry0 - rs}", color=NAVY, sw=1.8)
line(rx0, ry0, rx0, ry0 - rs, color=INK, sw=1.1)
line(rx0, ry0, rx0 + rs, ry0, color=INK, sw=1.1)
text(rx0 + rs / 2, ry0 + 13, "FPR", size=10, color=GRAY)
text(rx0 - 7, ry0 - rs / 2, "TPR", size=10, color=GRAY, extra=f'transform="rotate(-90 {rx0 - 7} {ry0 - rs / 2})"')
text(rx0 + rs / 2, c0y + 2 * cc + 32, "ROC curve", size=10.5, color=GRAY)
line(x + 14, 482, x + w - 14, 482, color=LINE, sw=1)
text(cx, 504, "Test-set performance metrics", size=12, color=INK, weight="bold")
metrics = ["Accuracy", "Precision", "Recall", "F1-score", "MCC", "ROC-AUC"]
for i, m in enumerate(metrics):
    col, row = i % 2, i // 2
    chip(cx - 48 + col * 96, 516 + row * 34, 88, 26, [m], "#FFFFFF", NAVY, size=11, bold_first=False)
text(cx, 638, "Computed once, on held-out", size=11, color=GRAY, style="italic")
text(cx, 653, "data after model selection", size=11, color=GRAY, style="italic")

# ---------------- Data-split routing below panels ----------------
bxs = P["B"][0]
ex = P["E"][0]
fx = P["F"][0]
routes = [  # (start x, y level, end x, colour, marker, dash, label, label x)
    (bxs + 182, 758, ex + 110, NAVY, "arrow", None, "Training set (CV folds and final refit)", 760),
    (bxs + 38, 802, fx + 158, ORANGE, "arrow_o", "6 4", "Independent test set: isolated until final evaluation", 960),
]
for sx, yl, exx, col, mk, dash, lab, lx_ in routes:
    path(f"M{sx},{PB} V{yl} H{exx} V{PB + 2}", color=col, sw=1.6, arrow=True, marker=mk, dash=dash)
    tw = len(lab) * 5.6 + 16
    rect(lx_ - tw / 2, yl - 9, tw, 18, fill="#FFFFFF", stroke="none", sw=0)
    text(lx_, yl + 4, lab, size=11.5, color=col, weight="bold")
lock(960 - (len(routes[1][6]) * 5.6 + 16) / 2 - 8, 794)

# Legend.
lgx = 610
line(lgx, 866, lgx + 34, 866, color=NAVY, sw=1.8, arrow=True)
text(lgx + 42, 870, "Information flow", size=11.5, color=GRAY, anchor="start")
line(lgx + 170, 866, lgx + 204, 866, color=ORANGE, sw=1.6, dash="6 4", arrow=True, marker="arrow_o")
text(lgx + 212, 870, "Held-out test data path (no optimization or selection)", size=11.5, color=GRAY, anchor="start")

add("</svg>")
with open(sys.argv[1], "w", encoding="utf-8") as fh:
    fh.write("\n".join(out))
