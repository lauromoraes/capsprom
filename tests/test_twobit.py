from pathlib import Path
import struct

import pytest

from capsprom.data.twobit import TwoBitGenome
from capsprom.data.epd_resolution import EpdCoordinate, epd_tss_zero_based, oriented_interval


def _write_twobit(path: Path, sequence: str, n_blocks=(), mask_blocks=()):
    name = b"chrFixture"
    index_size = 1 + len(name) + 4
    offset = 16 + index_size
    clean = sequence.upper().replace("N", "T")
    codes = {base: index for index, base in enumerate("TCAG")}
    packed = bytearray((len(clean) + 3) // 4)
    for position, base in enumerate(clean):
        packed[position // 4] |= codes[base] << (6 - 2 * (position % 4))
    with path.open("wb") as handle:
        handle.write(struct.pack(">IIII", 0x1A412743, 0, 1, 0))
        handle.write(bytes([len(name)]))
        handle.write(name)
        handle.write(struct.pack(">I", offset))
        handle.write(struct.pack(">I", len(sequence)))
        handle.write(struct.pack(">I", len(n_blocks)))
        for values in zip(*n_blocks):
            handle.write(struct.pack(f">{len(values)}I", *values))
        handle.write(struct.pack(">I", len(mask_blocks)))
        for values in zip(*mask_blocks):
            handle.write(struct.pack(f">{len(values)}I", *values))
        handle.write(struct.pack(">I", 0))
        handle.write(packed)


def test_twobit_fetch_handles_slices_n_blocks_masks_and_reverse_complement(tmp_path: Path):
    path = tmp_path / "fixture.2bit"
    _write_twobit(path, "ACGTACGTAC", n_blocks=((4, 2),), mask_blocks=((1, 2),))

    with TwoBitGenome(path) as genome:
        assert genome.sequence_names == ("chrFixture",)
        assert genome.fetch("chrFixture", 0, 10) == "AcgTNNGTAC"
        assert genome.fetch("chrFixture", 2, 8, reverse_complement=True) == "ACNNAc"


def test_twobit_fetch_rejects_invalid_interval(tmp_path: Path):
    path = tmp_path / "fixture.2bit"
    _write_twobit(path, "ACGT")

    with TwoBitGenome(path) as genome, pytest.raises(ValueError, match="invalid interval"):
        genome.fetch("chrFixture", -1, 3)


def test_twobit_fetch_skips_distant_blocks(tmp_path: Path):
    path = tmp_path / "fixture.2bit"
    _write_twobit(
        path,
        "ACGT" * 10,
        n_blocks=((0, 2), (35, 2)),
        mask_blocks=((4, 2), (30, 2)),
    )

    with TwoBitGenome(path) as genome:
        assert genome.fetch("chrFixture", 16, 24) == "ACGTACGT"


@pytest.mark.parametrize(
    ("strand", "expected_tss", "positive", "negative"),
    [
        ("+", 149, (69, 150), (1149, 1230)),
        ("-", 110, (110, 191), (-970, -889)),
    ],
)
def test_epd_relative_intervals_are_strand_aware(strand, expected_tss, positive, negative):
    coordinate = EpdCoordinate("fixture", "chr1", 100, 160, "PROM_1", 900, strand)

    assert epd_tss_zero_based(coordinate) == expected_tss
    assert oriented_interval(coordinate, -80, 1) == positive
    assert oriented_interval(coordinate, 1000, 1081) == negative
