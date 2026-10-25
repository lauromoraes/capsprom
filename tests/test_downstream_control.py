from capsprom.data.downstream_control import (
    filter_controls_matching_external_positives,
    filter_controls_near_known_tss,
    filter_strand_invariant_duplicates,
    index_known_tss,
    treat_strand_invariant_pair,
)
from capsprom.data.epd_resolution import EpdCoordinate
from capsprom.data.sequences import SequenceRecord


def _coordinate(identifier="PROM_1", start=100, strand="+"):
    return EpdCoordinate("fixture", "chr1", start, start + 60, identifier, 900, strand)


def test_reverse_complement_duplicate_retains_first_record():
    records = [
        SequenceRecord("FP1|PROM_1", "AACG"),
        SequenceRecord("FP2|PROM_2", "CGTT"),
    ]

    kept, removed = filter_strand_invariant_duplicates(
        records, organism="fixture", class_name="positive"
    )

    assert [record.identifier for record in kept] == ["FP1|PROM_1"]
    assert removed[0].reason == "within_class_reverse_complement_duplicate_after_first"


def test_strand_invariant_cross_class_collision_is_removed_bilaterally():
    positive = [SequenceRecord("FP1|PROM_1", "AACG"), SequenceRecord("FP2|PROM_2", "AAAA")]
    negative = [SequenceRecord("FP3|PROM_3", "CGTT"), SequenceRecord("FP4|PROM_4", "CCCC")]

    kept_positive, kept_negative, removed = treat_strand_invariant_pair(
        positive, negative, organism="fixture"
    )

    assert [record.identifier for record in kept_positive] == ["FP2|PROM_2"]
    assert [record.identifier for record in kept_negative] == ["FP4|PROM_4"]
    assert len(removed) == 2
    assert {item.reason for item in removed} == {
        "cross_label_reverse_complement_collision_bilateral_removal"
    }


def test_control_filter_records_exact_and_margin_tss_hits():
    primary = {"PROM_1": _coordinate()}
    other = {
        "OTHER_EXACT": _coordinate("OTHER_EXACT", 1100),
        "OTHER_MARGIN": _coordinate("OTHER_MARGIN", 1231),
    }
    known = index_known_tss([primary, other])

    kept, removed = filter_controls_near_known_tss(
        [SequenceRecord("FP1|PROM_1", "A" * 81)],
        organism="fixture",
        primary_coordinates=primary,
        known_tss=known,
        relative_start=1000,
        relative_end=1081,
        exclusion_margin=100,
    )

    assert kept == []
    assert removed[0].control_start == 1149
    assert removed[0].exact_tss_overlap is True
    assert removed[0].nearby_tss_count == 2
    assert removed[0].closest_tss_distance == 0


def test_external_positive_filter_removes_only_matching_control():
    records = [
        SequenceRecord("FP1|PROM_1", "AACG"),
        SequenceRecord("FP2|PROM_2", "AAAA"),
    ]

    kept, removed = filter_controls_matching_external_positives(
        records,
        organism="mouse",
        external_positive_sequences=["CGTT", "CCCC"],
        external_dataset_id="external-positive-source",
    )

    assert [record.identifier for record in kept] == ["FP2|PROM_2"]
    assert [item.identifier for item in removed] == ["FP1|PROM_1"]
    assert removed[0].reason == "external_positive_strand_invariant_identity"
    assert removed[0].match_orientation == "reverse_complement"
