from capsprom.data.ecoli_source_audit import (
    PublishedPaaRow,
    compare_promotech_bed_to_paa_source,
    expected_source_window,
)
from capsprom.data.primary_tss_audit import TssBedRow


def test_expected_source_window_respects_strand() -> None:
    reference = "A" * 60 + "C" + "G" * 60

    assert expected_source_window(reference, 61, "+") == "A" * 50 + "C"
    assert expected_source_window(reference, 61, "-") == "C" * 50 + "G"


def test_audit_separates_row_identity_from_contig_identity() -> None:
    reference = "A" * 60 + "C" + "G" * 60
    source = PublishedPaaRow(61, "+", "gene", "A" * 50 + "C", 4)
    bed = TssBedRow("wrong_contig", 60, 61, "gene", "0", "+", 1)

    row = compare_promotech_bed_to_paa_source(
        [bed], [source], paa_reference=reference, expected_paa_accession="pAA"
    )[0]

    assert row["coordinate_match"] is True
    assert row["strand_match"] is True
    assert row["locus_match"] is True
    assert row["published_sequence_matches_paa"] is True
    assert row["contig_match"] is False
