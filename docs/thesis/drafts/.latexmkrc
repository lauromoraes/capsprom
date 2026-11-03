# Bibliographies live in this folder (draft_references.bib) and in the thesis
# folder (references.bib); bibtex runs inside build/, so search both.
use File::Spec;
ensure_path('BIBINPUTS', File::Spec->rel2abs('.'), File::Spec->rel2abs('..'));
