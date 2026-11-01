import gzip

from capsprom.data.exact_mapping import Locus, extract, find_exact, map_sequence, read_fasta, reverse_complement


def test_reads_gzipped_multi_contig_fasta(tmp_path):
    path = tmp_path / "genome.fna.gz"
    with gzip.open(path, "wt") as handle:
        handle.write(">NC_1.1 chromosome\nacgt\nACGT\n>NC_2.1 plasmid\nGGGG\n")
    assert read_fasta(path) == {"NC_1.1": "ACGTACGT", "NC_2.1": "GGGG"}


def test_finds_planted_loci_on_both_strands_and_plasmids():
    query = "AACCGTT" + "A"
    chromosome = "TTTT" + query + "GGGG" + reverse_complement(query) + "CC"
    contigs = {"chr": chromosome, "plasmid": "GG" + query}
    assert find_exact(query, contigs) == (
        Locus("chr", 4, 12, "+"),
        Locus("chr", 16, 24, "-"),
        Locus("plasmid", 2, 10, "+"),
    )


def test_reports_overlapping_occurrences():
    assert [locus.start for locus in find_exact("AAA", {"c": "TAAAAT"})] == [1, 2]


def test_palindrome_is_one_locus_with_dot_strand():
    assert find_exact("GAATTC", {"c": "TTGAATTCTT"}) == (Locus("c", 2, 8, "."),)


def test_iupac_reference_bases_give_compatible_class_on_both_strands():
    contigs = {"c": "TTACNTTT" + "GG" + reverse_complement("ACRT") + "GG"}
    assert find_exact("CCCC", contigs) == ()
    assert find_exact("ACAT", contigs) == (
        Locus("c", 2, 6, "+", "iupac_compatible"),
        Locus("c", 10, 14, "-", "iupac_compatible"),
    )


def test_exact_hit_keeps_exact_class_on_contig_with_ambiguity():
    assert find_exact("ACGT", {"c": "ACGTNN"}) == (Locus("c", 0, 4, ".", "exact"),)


def test_status_and_round_trip():
    contigs = {"c": "CCCC" + reverse_complement("ACGTTT") + "GGGG"}
    result = map_sequence("ACGTTT", contigs)
    assert result.status == "verified"
    assert extract(contigs, result.loci[0]) == "ACGTTT"
    assert map_sequence("TTTTTTTT", contigs).status == "unmapped"
    assert map_sequence("CC", contigs).status == "ambiguous"
