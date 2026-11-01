"""Draw the 12 dependency clusters of dataset_dependency_manifest_v3 as a
hand-drawn whiteboard illustration (matplotlib xkcd mode).

Usage: python dependency_clusters.py OUT_BASENAME  ->  OUT_BASENAME.svg/.pdf/.png
Counts are records with a cross-dataset neighbour (F-114, log R-033).
"""
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, FancyBboxPatch

BOARD, INK = "#FBFBF7", "#2B2B33"
MARKERS = {
    "mammal": "#E4572E", "arabidopsis": "#3FA34D", "enteric": "#2E86DE",
    "bacillus": "#9B5DE5", "single": "#F2A541",
}
NOTE = {
    "mammal": "#FFD6CC", "arabidopsis": "#D4F1D0", "enteric": "#D3E7FB",
    "bacillus": "#E9DCFB", "single": "#FFF1B8",
}

plt.xkcd(scale=1.2, length=120, randomness=3)
plt.rcParams["font.family"] = ["Comic Neue", "Comic Sans MS", "DejaVu Sans"]
plt.rcParams["svg.fonttype"] = "none"

fig, ax = plt.subplots(figsize=(16, 10.5))
fig.patch.set_facecolor(BOARD)
ax.set_facecolor(BOARD)
ax.set_xlim(0, 16)
ax.set_ylim(0, 10.5)
ax.axis("off")

# Whiteboard frame.
ax.add_patch(FancyBboxPatch((0.15, 0.15), 15.7, 10.2, boxstyle="round,pad=0.02,rounding_size=0.3",
                            fill=False, lw=4, ec="#9AA3AD"))


def sticky(x, y, label, kind, w=2.0, h=0.62, size=12.5):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.05,rounding_size=0.08",
                                fc=NOTE[kind], ec=INK, lw=1.6, zorder=4))
    ax.text(x, y, label, ha="center", va="center", fontsize=size, color=INK, zorder=5, weight="bold")


def bubble(x, y, w, h, kind, title, angle=0):
    ax.add_patch(Ellipse((x, y), w, h, angle=angle, fill=False, ec=MARKERS[kind], lw=4, zorder=2))
    ax.text(x, y + h / 2 + 0.18, title, ha="center", va="bottom", fontsize=15, color=MARKERS[kind], weight="bold")


def link(p, q, n, kind, label_off=(0, 0.18), new=False):
    lw = 1.5 + 4.5 * min(n, 3630) / 3630 + (1.5 if n >= 50 else 0)
    ax.plot([p[0], q[0]], [p[1], q[1]], color=MARKERS[kind], lw=lw, zorder=3, solid_capstyle="round",
            ls="--" if new else "-")
    mx, my = (p[0] + q[0]) / 2 + label_off[0], (p[1] + q[1]) / 2 + label_off[1]
    ax.text(mx, my, f"{n:,}", ha="center", va="center", fontsize=12, color=INK, zorder=6,
            bbox=dict(boxstyle="round,pad=0.15", fc=BOARD, ec="none"))


def star(x, y, text):
    ax.text(x, y, "★ " + text, fontsize=13, color="#D7263D", weight="bold", ha="center", zorder=7)


# Title.
ax.text(8, 9.85, "Who shares DNA with whom?", ha="center", fontsize=28, color=INK, weight="bold")
ax.text(8, 9.35, "18 eligible datasets  →  12 dependency clusters  (manifest v3)",
        ha="center", fontsize=16, color="#555")

# Mammal cluster.
bubble(3.0, 7.0, 5.4, 3.0, "mammal", "cnnprom-mammal")
H, Mn, Mt = (1.55, 7.6), (4.45, 7.6), (3.0, 6.1)
link(H, Mn, 3630, "mammal")
link(Mn, Mt, 1366, "mammal", label_off=(0.35, 0.05))
link(H, Mt, 63, "mammal", label_off=(-0.35, 0.05))
sticky(*H, "Human non-TATA", "mammal")
sticky(*Mn, "Mouse non-TATA", "mammal")
sticky(*Mt, "Mouse TATA", "mammal")

# Arabidopsis cluster.
bubble(7.4, 7.0, 3.0, 2.6, "arabidopsis", "cnnprom-arabidopsis")
A1, A2 = (7.4, 7.65), (7.4, 6.3)
link(A1, A2, 149, "arabidopsis", label_off=(0.45, 0))
sticky(*A1, "Arabidopsis non-TATA", "arabidopsis", w=2.5, size=11.5)
sticky(*A2, "Arabidopsis TATA", "arabidopsis", w=2.5, size=11.5)

# Enteric cluster (Klebsiella new in v3).
bubble(12.3, 7.0, 5.6, 3.0, "enteric", "enteric-cross-source")
S, E, K = (10.9, 7.55), (13.7, 7.55), (12.3, 6.1)
link(S, E, 294, "enteric")
link(K, S, 214, "enteric", label_off=(-0.35, 0), new=True)
link(K, E, 173, "enteric", label_off=(0.35, 0), new=True)
sticky(*S, "S. Typhimurium", "enteric")
sticky(*E, "E. coli (CNNProm)", "enteric")
sticky(*K, "K. pneumoniae", "enteric")
star(12.3, 5.25, "new in v3")

# Bacillus cluster (new in v3).
bubble(3.0, 3.1, 5.6, 2.2, "bacillus", "bacillus-cross-source")
Ba, Bs = (1.55, 3.1), (4.45, 3.1)
link(Ba, Bs, 72, "bacillus", new=True)
sticky(*Ba, "B. amyloliquefaciens", "bacillus", w=2.1, size=11)
sticky(*Bs, "B. subtilis (CNNProm)", "bacillus", w=2.1, size=11)
star(3.0, 1.75, "new in v3: was 2 clusters")

# Singletons: 8 clusters of one dataset each (CDBProm).
ax.text(11.0, 4.6, "8 islands: one dataset, one cluster", ha="center", fontsize=15,
        color="#C47F00", weight="bold")
singles = ["Anabaena", "Synechocystis", "Chlamydophila", "Corynebacterium",
           "Helicobacter", "Mycobacterium", "Pseudomonas", "Streptomyces"]
pos = {}
for i, name in enumerate(singles):
    x, y = 7.6 + (i % 4) * 2.3, 3.75 - (i // 4) * 1.35
    pos[name] = (x, y)
    ax.add_patch(Ellipse((x, y), 2.15, 1.0, fill=False, ec=MARKERS["single"], lw=2.5, zorder=2))
    sticky(x, y, name, "single", w=1.85, h=0.5, size=11.5)
# Weak link left unmerged.
p, q = pos["Anabaena"], pos["Synechocystis"]
ax.plot([p[0] + 0.95, q[0] - 0.95], [p[1], q[1]], color="#999", lw=1.5, ls=":", zorder=3)
ax.text((p[0] + q[0]) / 2, p[1] + 0.28, "6", ha="center", fontsize=11, color="#777")

# Legend / teacher's notes.
ax.text(0.55, 1.05, "How to read it:", fontsize=13.5, color=INK, weight="bold")
ax.text(0.55, 0.42, "line = records with a look-alike in the other dataset "
        "(≥80% identity, ≥80% coverage, either strand)   •   thicker = more\n"
        "dashed = link found by alignment, new in v3   •   dotted = ≤6 records, not merged",
        fontsize=11.5, color="#444")

fmt_base = sys.argv[1]
for ext in ("svg", "pdf", "png"):
    fig.savefig(f"{fmt_base}.{ext}", facecolor=BOARD, dpi=150 if ext == "png" else None, bbox_inches="tight")
