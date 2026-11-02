"""Draw the data of all four studies: the 12 dependency clusters of the 18
eligible CNNProm and CDBProm datasets as Venn diagrams, the 8 excluded GraphPro
datasets, and the overlap of two external training resources (iPro-MP, GUE)
with the eligible test sets.

Usage: python dependency_clusters_studies.py OUT_BASENAME  ->  OUT_BASENAME.svg/.pdf/.png
Sources: F-114 and R-033 (clusters), dataset eligibility manifest (GraphPro),
F-108 and F-109 (external resources).
"""
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle

INK, MUTED, RULE, BG = "#1F2933", "#616E7C", "#D9E2EC", "#FFFFFF"
STUDY = {"CNNProm": "#E8833A", "CDBProm": "#2A9D8F", "GraphPro": "#8C7AB8", "external": "#5B6B7F"}
CLUSTER = {
    "mammal": "#C0392B", "arabidopsis": "#3E8E41", "enteric": "#2563A6",
    "bacillus": "#7B4FA0", "single": "#9AA5B1",
}

plt.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "none"})
fig, ax = plt.subplots(figsize=(16, 14.6))
fig.patch.set_facecolor(BG)
ax.set_xlim(0, 16)
ax.set_ylim(-5.0, 9.6)
ax.set_aspect("equal")
ax.axis("off")


def icon(x, y, kind, s=0.09, color=INK):
    """Flat organism icon: eukaryotic cell with nucleus, or rod-shaped bacterium."""
    if kind == "euk":
        ax.add_patch(Circle((x, y), s, fc=color, ec="none", zorder=8))
        ax.add_patch(Circle((x + s * 0.2, y + s * 0.1), s * 0.42, fc=BG, ec="none", zorder=9))
    else:
        ax.add_patch(FancyBboxPatch((x - s * 1.2, y - s * 0.5), s * 2.4, s, zorder=8, fc=color, ec="none",
                                    boxstyle=f"round,pad=0,rounding_size={s * 0.5}"))
        ax.plot([x + s * 1.2, x + s * 1.7], [y, y + s * 0.3], color=color, lw=1.6, zorder=8)


def section(x0, y0, w, h, key, title, subtitle):
    ax.add_patch(FancyBboxPatch((x0, y0), w, h, boxstyle="round,pad=0,rounding_size=0.12",
                                fc="#F8FAFC", ec=RULE, lw=1.2, zorder=1))
    ax.add_patch(Rectangle((x0, y0 + h - 0.08), w, 0.08, fc=CLUSTER[key], ec="none", zorder=2))
    ax.text(x0 + 0.22, y0 + h - 0.38, title, fontsize=13, weight="bold", color=INK, va="center")
    ax.text(x0 + 0.22, y0 + h - 0.72, subtitle, fontsize=9.5, color=MUTED, va="center")


def disc(x, y, r, study, label=None, kind=None, lx=0, ly=0):
    c = STUDY[study]
    ax.add_patch(Circle((x, y), r, fc=c, alpha=0.22, ec="none", zorder=3))
    ax.add_patch(Circle((x, y), r, fill=False, ec=c, lw=2, zorder=4))
    if label:
        icon(lx, ly, kind, color=c)
        ax.text(lx + 0.24, ly, label, fontsize=10, weight="bold", color=INK, va="center", zorder=10)


def count(x, y, n, new=False):
    ax.text(x, y, f"{n:,}", fontsize=12.5, weight="bold", color=INK, ha="center", va="center", zorder=10)
    if new:
        ax.text(x, y - 0.3, "new in v3", fontsize=8.5, color="#B42318", ha="center", va="center",
                weight="bold", zorder=10)


# Header.
ax.text(0.4, 9.15, "Promoter datasets by study", fontsize=22, weight="bold", color=INK)
ax.text(0.4, 8.72, "18 eligible datasets in 12 clusters  ·  8 excluded  ·  2 external resources",
        fontsize=12, color=MUTED)
lx = 10.5
for i, (study, txt) in enumerate([("CNNProm", "CNNProm study"), ("CDBProm", "CDBProm study"), ("GraphPro", "GraphPro study (excluded)")]):
    yy = 9.3 - i * 0.36
    ax.add_patch(Circle((lx, yy), 0.13, fc=STUDY[study], alpha=0.35, ec=STUDY[study], lw=1.8))
    ax.text(lx + 0.25, yy, txt, fontsize=11, color=INK, va="center")
icon(13.9, 9.2, "euk", s=0.11, color=MUTED)
ax.text(14.15, 9.2, "eukaryote", fontsize=10.5, color=MUTED, va="center")
icon(13.9, 8.78, "pro", s=0.09, color=MUTED)
ax.text(14.15, 8.78, "prokaryote", fontsize=10.5, color=MUTED, va="center")

# Section 1: mammal (three CNNProm sets).
section(0.4, 4.5, 4.4, 3.95, "mammal", "cnnprom-mammal", "single study · 3 datasets")
cx, cy, r = 2.6, 5.95, 0.8
disc(cx - 0.52, cy + 0.32, r, "CNNProm", "Human non-TATA", "euk", 0.62, 7.35)
disc(cx + 0.52, cy + 0.32, r, "CNNProm", "Mouse non-TATA", "euk", 2.95, 7.35)
disc(cx, cy - 0.5, r, "CNNProm", "Mouse TATA", "euk", 3.45, 4.85)
count(cx, cy + 0.72, 3630)
count(cx + 0.55, cy - 0.25, 1366)
count(cx - 0.55, cy - 0.25, 63)

# Section 2: arabidopsis (two CNNProm sets).
section(5.0, 4.5, 3.2, 3.95, "arabidopsis", "cnnprom-arabidopsis", "single study · 2 datasets")
disc(6.2, 5.9, 0.82, "CNNProm", "non-TATA", "euk", 5.3, 7.35)
disc(7.0, 5.9, 0.82, "CNNProm", "TATA", "euk", 7.05, 7.35)
count(6.6, 5.9, 149)
ax.text(6.6, 4.75, "Arabidopsis thaliana", fontsize=10, style="italic", color=MUTED, ha="center")

# Section 3: enteric (cross-study).
section(8.4, 4.5, 3.9, 3.95, "enteric", "enteric-cross-source", "cross-study · 3 datasets")
ex, ey = 10.35, 5.95
disc(ex - 0.52, ey + 0.32, 0.8, "CDBProm", "S. Typhimurium", "pro", 8.75, 7.35)
disc(ex + 0.52, ey + 0.32, 0.8, "CNNProm", "E. coli", "pro", 10.9, 7.35)
disc(ex, ey - 0.5, 0.8, "CDBProm", "K. pneumoniae", "pro", 10.95, 4.85)
count(ex, ey + 0.72, 294)
count(ex - 0.55, ey - 0.2, 214, new=True)
count(ex + 0.55, ey - 0.2, 173, new=True)

# Section 4: bacillus (cross-study, new in v3).
section(12.5, 4.5, 3.1, 3.95, "bacillus", "bacillus-cross-source", "cross-study · new in v3")
disc(13.65, 5.9, 0.72, "CDBProm", "B. amyloliquefaciens", "pro", 12.8, 7.35)
disc(14.45, 5.9, 0.72, "CNNProm", "B. subtilis", "pro", 13.75, 4.85)
count(14.05, 5.9, 72, new=True)

# Section 5: singletons.
section(0.4, 1.35, 15.2, 2.9, "single", "8 singleton clusters",
        "one CDBProm dataset each · no pair above the 10-record threshold")
names = ["Anabaena sp.", "Synechocystis", "C. pneumoniae", "C. glutamicum",
         "H. pylori", "M. tuberculosis", "P. aeruginosa", "S. coelicolor"]
for i, name in enumerate(names):
    x = 1.35 + i * 1.88
    disc(x, 2.25, 0.55, "CDBProm")
    icon(x, 2.25, "pro", s=0.14, color=STUDY["CDBProm"])
    ax.text(x, 1.55, name, fontsize=10, style="italic", color=INK, ha="center", zorder=10)
ax.annotate("", xy=(1.35 + 1.88 - 0.6, 2.25), xytext=(1.35 + 0.6, 2.25),
            arrowprops=dict(arrowstyle="-", ls=":", color=MUTED, lw=1.4))
ax.text(1.35 + 0.94, 2.42, "6", fontsize=10, color=MUTED, ha="center")

# Section 6: GraphPro, excluded from confirmatory use.
def faded(x0, y0, w, h, key_color, title, subtitle):
    ax.add_patch(FancyBboxPatch((x0, y0), w, h, boxstyle="round,pad=0,rounding_size=0.12",
                                fc="#FBFAFD", ec=RULE, lw=1.2, ls=(0, (4, 3)), zorder=1))
    ax.add_patch(Rectangle((x0, y0 + h - 0.08), w, 0.08, fc=key_color, ec="none", alpha=0.6, zorder=2))
    ax.text(x0 + 0.22, y0 + h - 0.38, title, fontsize=13, weight="bold", color=INK, va="center")
    ax.text(x0 + 0.22, y0 + h - 0.72, subtitle, fontsize=9.5, color=MUTED, va="center")


faded(0.4, -3.75, 7.3, 4.65, STUDY["GraphPro"], "GraphPro: 8 datasets excluded",
      "kept for provenance; not in any cluster until rebuilt from verified references")
gp = [("Human", "euk", "negative lineage\nunverified"), ("Mouse", "euk", "negative lineage\nunverified"),
      ("B. amyloliq.", "pro", "class = strand;\n535 negatives are\nCDBProm promoters"),
      ("C. jejuni", "pro", "class = strand"),
      ("C. pneumoniae", "pro", "class = strand;\norganism mislabelled"),
      ("E. coli", "pro", "1,345 records\nin both classes"),
      ("L. interrogans", "pro", "class = strand"), ("R. capsulatus", "pro", "class = strand")]
for i, (name, kind, why) in enumerate(gp):
    x, y = 1.25 + (i % 4) * 1.78, -0.75 - (i // 4) * 1.95
    c = STUDY["GraphPro"]
    ax.add_patch(Circle((x, y + 0.2), 0.42, fc=c, alpha=0.12, ec="none", zorder=3))
    ax.add_patch(Circle((x, y + 0.2), 0.42, fill=False, ec=c, lw=1.6, ls=(0, (3, 2)), zorder=4))
    icon(x, y + 0.2, kind, s=0.11, color=c)
    ax.text(x, y - 0.37, name, fontsize=9.5, weight="bold", style="italic" if kind == "pro" else "normal",
            color=INK, ha="center", va="center")
    ax.text(x, y - 0.55, why, fontsize=7.8, color=MUTED, ha="center", va="top", linespacing=1.1)

# Section 7: external training resources against eligible test sets.
faded(7.9, -3.75, 7.7, 4.65, STUDY["external"], "External resources: overlap with eligible test sets",
      "test positives with a neighbour in the resource · bar colour = study of the test set")
rows = [("iPro-MP", "Anabaena sp.", "CDBProm", 503, 503), ("iPro-MP", "C. glutamicum", "CDBProm", 112, 112),
        ("iPro-MP", "E. coli", "CNNProm", 168, 168), ("iPro-MP", "B. subtilis", "CNNProm", 75, 75),
        ("iPro-MP", "H. pylori", "CDBProm", 119, 141), ("iPro-MP", "S. Typhimurium", "CDBProm", 53, 196),
        ("iPro-MP", "K. pneumoniae", "CDBProm", 41, 266), ("GUE", "Human non-TATA", "CNNProm", 2728, 3956),
        ("GUE", "Mouse TATA", "CNNProm", 67, 250), ("GUE", "Mouse non-TATA", "CNNProm", 677, 3253)]
bx, bw, top = 11.0, 2.6, -0.25
for i, (res, name, study, k, n) in enumerate(rows):
    y = top - i * 0.33 - (0.2 if res == "GUE" else 0)
    if i == 0 or rows[i - 1][0] != res:
        ax.text(8.15, y, res, fontsize=10, weight="bold", color=STUDY["external"], va="center")
    ax.text(9.25, y, name, fontsize=9.5, color=INK, va="center",
            style="italic" if "TATA" not in name else "normal")
    ax.add_patch(Rectangle((bx, y - 0.1), bw, 0.2, fc="#EEF2F6", ec="none", zorder=2))
    ax.add_patch(Rectangle((bx, y - 0.1), bw * k / n, 0.2, fc=STUDY[study], ec="none", alpha=0.85, zorder=3))
    ax.text(bx + bw + 0.12, y, f"{k:,}/{n:,}  ({100 * k / n:.0f}%)", fontsize=9, color=INK, va="center")

# Footnote.
ax.text(0.4, -4.2, "Numbers in overlaps: records with a neighbour in the other dataset "
        "(MMseqs2, ≥80% identity, ≥80% coverage, either strand; train and test pooled).",
        fontsize=9.5, color=MUTED)
ax.text(0.4, -4.55, "Pairs with more than 10 such records share a cluster. Circle areas are not proportional "
        "to dataset size. Sources: F-108, F-109, F-114, R-033, dataset eligibility manifest.", fontsize=9.5, color=MUTED)

base = sys.argv[1]
for ext in ("svg", "pdf", "png"):
    fig.savefig(f"{base}.{ext}", facecolor=BG, dpi=200 if ext == "png" else None, bbox_inches="tight")
