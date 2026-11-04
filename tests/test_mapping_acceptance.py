from capsprom.data.mapping_acceptance import (
    ECOLI_NC_000913_2_LENGTH,
    b1_cnnprom_ecoli,
    coverage_and_consistency,
    declared_integer,
    expected_cnnprom_ecoli_integer,
    stratified_sample,
)


def _record(rid, label, status, text, n="1"):
    return {"record_id": rid, "label": str(label), "status": status, "declared_coordinate_text": text,
            "n_candidates": n, "n_candidates_truncated": "false"}


def _locus(rid, start, strand, rank="1"):
    return {"record_id": rid, "locus_rank": rank, "start": str(start), "end": str(start + 81), "strand": strand}


def test_declared_integer():
    assert declared_integer("ECK120010467__accAp__forward__208411") == 208411
    assert declared_integer("6400") == 6400
    assert declared_integer("geneX") is None


def test_f098_rule_both_strands():
    assert expected_cnnprom_ecoli_integer(1, 100, 181, "+") == 161
    assert expected_cnnprom_ecoli_integer(1, 100, 181, "-") == 121
    assert expected_cnnprom_ecoli_integer(0, 6340, 6421, "+") == 6400
    assert expected_cnnprom_ecoli_integer(0, 0, 81, "-") == ECOLI_NC_000913_2_LENGTH - 81 + 60


def test_b1_counts_matches_mismatches_and_strand():
    records = [
        _record("p", 1, "verified", "id__g__forward__161"),
        _record("q", 1, "verified", "id__g__forward__121"),
        _record("n", 0, "verified", "6400"),
        _record("a", 0, "ambiguous", "1", n="2"),
    ]
    loci = [_locus("p", 100, "+"), _locus("q", 100, "-"), _locus("n", 6340, "+")]
    result = b1_cnnprom_ecoli(records, loci)
    assert result["counts"] == {
        "negative_match": 1, "positive_match": 2, "positive_strand_match": 1,
        "positive_strand_mismatch": 1, "skipped_ambiguous": 1,
    }
    assert result["mismatches"] == []


def test_consistency_flags_violations():
    records = [_record("a", 1, "verified", "", n="1"), _record("b", 0, "ambiguous", "", n="2")]
    loci = [_locus("a", 0, "+"), _locus("b", 0, "+"), _locus("b", 9, "-", rank="2")]
    assert coverage_and_consistency(records, loci)["violations"] == {}
    loci.append(_locus("a", 5, "+", rank="2"))
    assert coverage_and_consistency(records, loci)["violations"] == {"n_candidates_ne_locus_rows": 1}


def test_sample_is_deterministic_and_stratified():
    rows = {"c": [_record(f"r{i}", i % 2, "verified", "") for i in range(10)]}
    first = stratified_sample(rows, 2)
    assert len(first) == 4 and first == stratified_sample(rows, 2)
