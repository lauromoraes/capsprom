from pathlib import Path

import pytest

from capsprom.data.epd_resolution import load_epd_bed, parse_graphpro_header


def test_parse_graphpro_header_preserves_identifier_and_embedded_label():
    parsed = parse_graphpro_header(">FP001101|PCAT1_1\t1")

    assert parsed.source_identifier == "FP001101"
    assert parsed.epd_identifier == "PCAT1_1"
    assert parsed.embedded_label == 1


@pytest.mark.parametrize("header", ["FP001101|PCAT1_1 1", ">FP001101 1", ">FP1|X 2"])
def test_parse_graphpro_header_rejects_invalid_input(header):
    with pytest.raises(ValueError):
        parse_graphpro_header(header)


def test_load_epd_bed_requires_unique_valid_bed6(tmp_path: Path):
    path = tmp_path / "epd.bed"
    path.write_text("chr1 10 70 PROM_1 900 +\n", encoding="utf-8")

    records = load_epd_bed(path, "test-v1")

    assert records["PROM_1"].start == 10
    assert records["PROM_1"].collection == "test-v1"


def test_load_epd_bed_rejects_duplicate_identifier(tmp_path: Path):
    path = tmp_path / "epd.bed"
    path.write_text("chr1 10 70 PROM_1 900 +\nchr2 20 80 PROM_1 900 -\n", encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate identifier"):
        load_epd_bed(path, "test-v1")
