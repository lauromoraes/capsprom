from capsprom.data.integrity_treatment import treat_labeled_sequences
from capsprom.data.sequences import SequenceRecord


def _record(identifier: str, sequence: str) -> SequenceRecord:
    return SequenceRecord(identifier, sequence, "fixture")


def test_integrity_treatment_records_each_declared_removal_reason():
    collision = "A" * 81
    duplicate = "C" * 81
    result = treat_labeled_sequences(
        [
            _record("collision-positive", collision),
            _record("kept-positive", duplicate),
            _record("duplicate-positive", duplicate),
            _record("short-positive", "G" * 80),
        ],
        [
            _record("collision-negative", collision),
            _record("kept-negative", "T" * 81),
            _record("invalid-negative", "N" * 81),
        ],
        dataset="fixture",
        organism="fixture",
    )

    assert [record.identifier for record in result.positive] == ["kept-positive"]
    assert [record.identifier for record in result.negative] == ["kept-negative"]
    assert {item.reason for item in result.removed} == {
        "cross_label_exact_collision_bilateral_removal",
        "within_class_exact_duplicate_after_first",
        "sequence_length_not_81",
        "non_strict_dna",
    }
    assert len(result.removed) == 5
