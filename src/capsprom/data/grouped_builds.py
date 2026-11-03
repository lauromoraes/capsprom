"""Filtering of canonical records before homology-grouped partitioning.

Applies the v3 filter stages to canonical collection rows, in order: length
exclusion, strict DNA, removal of every occurrence of a sequence carried by
both classes, then one record per sequence within a class (first in
``record_index`` order).  Identity is forward exact, as in the v3 builds;
reverse-complement copies are joined later by homology grouping.
"""

from __future__ import annotations

import collections
from typing import Iterable, Mapping


def filter_canonical_rows(rows: Iterable[Mapping[str, str]]) -> tuple[list[dict[str, str]], dict[str, int]]:
    """Return kept rows (sequence upper-cased) and per-stage removal counts."""

    counts = collections.Counter()
    staged = []
    for row in sorted(rows, key=lambda r: int(r["record_index"])):
        counts["input"] += 1
        if row["length_matches_expected"] != "true":
            counts["length_excluded"] += 1
            continue
        if row["strict_dna"] != "true":
            counts["not_strict_dna"] += 1
            continue
        staged.append({**row, "sequence": row["sequence"].upper()})
    labels = collections.defaultdict(set)
    for row in staged:
        labels[row["sequence"]].add(row["label"])
    collisions = {sequence for sequence, found in labels.items() if len(found) > 1}
    seen, kept = set(), []
    for row in staged:
        if row["sequence"] in collisions:
            counts["cross_label_collision_removed"] += 1
            continue
        key = (row["label"], row["sequence"])
        if key in seen:
            counts["within_class_duplicate_removed"] += 1
            continue
        seen.add(key)
        kept.append(row)
    counts["kept"] = len(kept)
    return kept, dict(counts)
