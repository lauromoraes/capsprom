# Experimental-Design Review (v1)

`main.tex` is a standalone Portuguese report that critically evaluates a
proposed two-level design for CapsProm: repeated K-fold with a corrected
resampled t-test at the outer level, and 5x2cv with Alpaydin's combined F-test
at the inner level. It changes no protocol and starts no experiment.

Contents:

- `main.tex`: report source.
- `references.bib`: BibTeX bibliography (`plainnat`, author-year).
- `figures/*.tex`: editable TikZ figures. Each one compiles on its own with
  the `standalone` class and is included in the report through
  `\includestandalone`. `figures/estilo.tex` holds the shared colours
  (Okabe-Ito palette) and styles.

The local TeX Live has no Portuguese hyphenation patterns, so the report is set
without hyphenation. LuaLaTeX is unavailable on the build host (no
`luaotfload`), so the build uses pdfLaTeX.

From this directory:

```bash
out=../../../outputs/reports/experimental_design_review_v1
mkdir -p "$out"
pdflatex -interaction=nonstopmode -halt-on-error -output-directory="$out" main.tex
BIBINPUTS=.: bibtex "$out/main"
pdflatex -interaction=nonstopmode -halt-on-error -output-directory="$out" main.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory="$out" main.tex
```

A single figure, from `figures/`:

```bash
pdflatex -interaction=nonstopmode fig_aninhamento.tex
```
