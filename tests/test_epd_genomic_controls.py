from capsprom.data.epd_genomic_controls import reconstruct_epd_gc_matched_controls
from capsprom.data.epd_resolution import EpdCoordinate


class FixtureGenome:
    def __init__(self, sequences):
        self.sequences = sequences

    def sequence_size(self, name):
        return len(self.sequences[name])

    def fetch(self, name, start, end, *, reverse_complement=False):
        sequence = self.sequences[name][start:end]
        if reverse_complement:
            sequence = sequence.translate(str.maketrans("ACGT", "TGCA"))[::-1]
        return sequence


def _coordinate(identifier, start, strand="+"):
    return EpdCoordinate("fixture", "chr1", start, start + 60, identifier, 900, strand)


def test_epd_controls_are_deterministic_paired_and_exactly_gc_matched():
    genome = FixtureGenome({"chr1": ("AACCGGTT" * 1000)})
    coordinates = [_coordinate("PROM_1", 200), _coordinate("PROM_2", 600, "-")]
    known_tss = {"chr1": ((249, "PROM_1"), (610, "PROM_2"))}
    kwargs = {
        "upstream": 6,
        "downstream": 2,
        "exclusion_margin": 10,
        "maximum_gc_count_difference": 0,
        "seed": 17,
    }

    first = reconstruct_epd_gc_matched_controls(genome, coordinates, known_tss, **kwargs)
    second = reconstruct_epd_gc_matched_controls(genome, coordinates, known_tss, **kwargs)

    assert first == second
    assert len(first) == 2
    assert all(pair.positive_gc == pair.negative_gc for pair in first)
    assert [pair.negative_strand for pair in first] == ["+", "-"]
    assert all("pair_id=" in pair.negative.description for pair in first)


def test_epd_controls_exclude_external_positive_identity():
    reference = "A" * 100 + "CCCCCCCCC" + "A" * 200
    genome = FixtureGenome({"chr1": reference})
    coordinate = _coordinate("PROM_1", 130)
    pairs = reconstruct_epd_gc_matched_controls(
        genome,
        [coordinate],
        {"chr1": ((179, "PROM_1"),)},
        external_positive_sequences=["CCCCCCCCC"],
        upstream=6,
        downstream=2,
        exclusion_margin=10,
        maximum_gc_count_difference=9,
        seed=2,
    )

    assert pairs[0].negative.sequence != "CCCCCCCCC"


def test_epd_controls_can_fall_back_to_exhaustive_gc_search():
    genome = FixtureGenome({"chr1": "A" * 100 + "CCCCCCCCC" + "A" * 200})
    coordinate = _coordinate("PROM_1", 130)

    pairs = reconstruct_epd_gc_matched_controls(
        genome,
        [coordinate],
        {"chr1": ((179, "PROM_1"),)},
        upstream=6,
        downstream=2,
        exclusion_margin=0,
        maximum_gc_count_difference=9,
        seed=2,
        max_attempts_per_positive=1,
        exhaustive_fallback_on_random_exhaustion=True,
        exhaustive_chunk_size=37,
    )

    assert pairs[0].search_mode == "exhaustive_fallback"
    assert pairs[0].exhaustive_windows_scanned == len(genome.sequences["chr1"]) - 8
    assert pairs[0].sampling_attempts == 1
