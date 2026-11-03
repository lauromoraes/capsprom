from capsprom.data.grouped_builds import filter_canonical_rows


def _row(index, label, sequence, length_ok="true", strict="true"):
    return {"record_index": str(index), "label": label, "sequence": sequence, "length_matches_expected": length_ok, "strict_dna": strict}


def test_filter_applies_v3_stages_in_order():
    rows = [
        _row(3, "1", "acgt"),
        _row(0, "1", "ACGT"),  # same sequence after upper-casing: duplicate of index 0
        _row(1, "1", "GGGG"),
        _row(2, "0", "GGGG"),  # collides with a positive: both removed
        _row(4, "0", "TTTT", length_ok="false"),
        _row(5, "0", "NNNN", strict="false"),
        _row(6, "0", "CCCC"),
    ]

    kept, counts = filter_canonical_rows(rows)

    assert [(r["record_index"], r["sequence"]) for r in kept] == [("0", "ACGT"), ("6", "CCCC")]
    assert counts == {
        "input": 7,
        "length_excluded": 1,
        "not_strict_dna": 1,
        "cross_label_collision_removed": 2,
        "within_class_duplicate_removed": 1,
        "kept": 2,
    }
