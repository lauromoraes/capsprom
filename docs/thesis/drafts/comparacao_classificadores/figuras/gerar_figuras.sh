#!/usr/bin/env bash
# Gera PDF vetorial, SVG (glifos convertidos em contornos) e PNG a 600 dpi
# para cada figura TikZ deste diretório. Requer TeX Live (pdflatex, latex,
# dvisvgm) e pdftoppm (poppler). Arquivos intermediários vão para _aux/.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p _aux
for fig in fig_5x2cv fig_kfold_repetido fig_fluxo_comparacao; do
  pdflatex -interaction=nonstopmode -halt-on-error -output-directory=_aux "$fig.tex" >/dev/null
  cp "_aux/$fig.pdf" "$fig.pdf"
  latex -interaction=nonstopmode -halt-on-error -output-directory=_aux "$fig.tex" >/dev/null
  dvisvgm --no-fonts --exact-bbox --output="$fig.svg" "_aux/$fig.dvi" 2>/dev/null
  pdftoppm -png -r 600 -singlefile "$fig.pdf" "$fig"
  echo "ok: $fig (.pdf .svg .png)"
done
