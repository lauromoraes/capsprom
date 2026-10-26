# GraphPro Dataset Logo Report

`main.tex` is a standalone report. It references the version-2 figures under
`outputs/reports/graphpro_dataset_logo_audit_v2/figures/` and compiles to a PDF
containing only this report.

From this directory:

```bash
mkdir -p ../../../outputs/reports/graphpro_dataset_logo_report_v1
pdflatex -interaction=nonstopmode -halt-on-error \
  -output-directory=../../../outputs/reports/graphpro_dataset_logo_report_v1 \
  main.tex
pdflatex -interaction=nonstopmode -halt-on-error \
  -output-directory=../../../outputs/reports/graphpro_dataset_logo_report_v1 \
  main.tex
```
