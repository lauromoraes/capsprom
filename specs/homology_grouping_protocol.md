# Homology Grouping Protocol

## Status and scope

Design (2026-10-30, log R-027). Machine-readable contract:
`configs/homology_grouping_v1.yaml`. This protocol adds one pipeline stage
between filtering and partitioning. It changes no existing build, partition,
or run. It becomes binding for confirmatory data only through a successor of
`configs/evaluation_protocol_v3.yaml` (planned v4), which must replace the
`deterministic_unique_sequence_groups` partition policy.

Motivation: exact-identity grouping leaves shifted-window and repeat-copy
dependence across partitions, up to 67% of test negatives in CNNProm Human
non-TATA (F-084 to F-088; `docs/cnnprom_overlap_leakage_finding.md`).

## 1. Principle

Records that align above a declared threshold are dependent. Every connected
component of the dependency graph is one group, and a group is never split
across train/test or across inner cross-validation folds. This is the
partitioning (rather than reduction) principle of GraphPart (Teufel et al.,
2023). Petti and Eddy (2022) motivate the same separation for benchmark
construction. No record is removed by this stage.

## 2. Pipeline position

```text
crop to domain window -> cross-label collision removal -> within-class
deduplication -> strict DNA -> [homology grouping] -> group-safe split
-> group-aware inner folds
```

Grouping runs on the sequences the model sees, after cropping (decision of
log R-026), once per dataset pair, on train and test candidates together, and
label-blind.

## 3. Method

1. Write all records of the dataset pair to one FASTA with stable row IDs.
2. All-versus-all search with MMseqs2 `easy-search` (Steinegger and Söding,
   2017), query = target = the pair's records; drop self-hits.
3. An edge joins two records when the hit satisfies the identity and coverage
   thresholds (§4), or when their Hamming distance is at most ⌊0.20 × L⌋ on either
   strand, the ungapped equivalent of 80% identity (16 for L = 81 nt, 50 for
   251 nt), computed
   exactly with the pigeonhole index of `near_duplicate_audit.py`. Edges are
   undirected. The Hamming edges recover boundary pairs that local alignment
   trims below the thresholds (6 of 280 in F-090); each pair reports edges found
   by alignment only, Hamming only, and both.
   A third source, genomic overlap, joins two records whose windows overlap on
   the same assembly on either strand. It applies only to records with a
   unique, exact, both-strand genome match supported by a finding of status
   Fact. Records that match at several loci keep only sequence edges. It is
   required in the `recon` condition and enabled per dataset in `orig-common`
   where coordinates are verified. It adds edges and never replaces the
   sequence edges. Coordinates used this way are descriptive metadata, so an
   `orig` dataset stays `orig` (`specs/dataset_condition_policy.md` §2). Each
   pair reports its coordinate coverage and the edges contributed only by
   this source. Grouping windows within one window length of each other is a
   sensitivity analysis.
4. Groups are the connected components (single linkage); singletons are
   groups.
5. Partition: shuffle groups with the dataset RNG of the existing builder;
   assign them to test until each class reaches its 20% target as closely as
   whole groups allow; report the realised fractions.
6. Inner folds: stratified group k-fold (five folds, seed 42) over the
   training groups.
7. Uncertainty: the group bootstrap replaces the record bootstrap, as already
   foreseen in the statistical protocol (`use_group_bootstrap_when_available`).

`easy-cluster` is not used for grouping. Its greedy representative clustering
does not guarantee that members of different clusters stay below the
threshold. For nucleotide input it also compares the forward strand only.
Search plus connected components gives the guarantee directly.

## 4. Parameters and rationale

| Parameter | Value | Rationale |
| --- | --- | --- |
| Tool | MMseqs2, pinned release; binary SHA-256 recorded | Sensitive, fast all-vs-all search at the scale of the largest pair (~47,000 records) on a workstation. |
| `--search-type` | `3` (nucleotide) | DNA input; no translation. |
| `--strand` | `2` (both) | Bacterial CNNProm negatives are opposite-strand windows of coding genes. A reverse-complement copy carries the same locus information, and k-mer features of a sequence and its reverse complement are mirror images. |
| `--min-seq-id` | `0.80` | Identity is a fraction of aligned columns. At ≥95% the affected share barely changes (F-084), so the primary signal (shifted copies at identity 1.00) is insensitive to this choice. The value is low enough to also join repeat copies (~85%, F-087/F-088). Random 81-nt DNA does not reach 80% identity over 65 nt, so the threshold does not create chance edges. |
| `-c`, `--cov-mode` | `0.80`, `0` (both sequences) | Requires an overlap of ≥65 of 81 nt (≥201 of 251 nt), i.e. shifts up to 20% of the window. Coverage of both sequences prevents a short local match (a single motif) from joining records. |
| `-k` | `9` | Short nucleotide queries need short seeds. The default k-mer size exhausted the 6 GB memory of the audit host; `-k 9` runs within it. `k` sets search recall, not the dependence criterion. Against exact Hamming neighbours it found 96/96 at distance ≤8 and 274/280 at ≤16; `-k 9` added ≤1% of affected queries (F-090). |
| `-e` | MMseqs2 default (`0.001`) | Recorded explicitly so a release change cannot alter it. Identity and coverage are the decision criteria; the E-value only prefilters. |
| `--max-seqs` | `1000` | Above the largest observed neighbourhood (65). The run fails if any query reaches the cap, since edges would then be missing. |
| `--split-memory-limit` | `3G` | Host constraint only; it does not change results. |

## 5. Predeclared sensitivity analyses

Fixed before any grouped run is evaluated on test data:

- identity 0.90 and 0.95 at coverage 0.80;
- coverage 0.50 (≥41 of 81 nt) at identity 0.80, which captures half-window
  overlaps that the primary setting misses;
- record-level (v3) versus grouped partition, per dataset and model, reported
  side by side. This quantifies the memorisation component (§4 of the finding
  document).

## 6. Gates and reports

- Each pair reports the following:
  - number of groups and the largest component, by class;
  - mixed-label components;
  - realised test fraction and class balance;
  - the number of cross-partition edges, which must be 0 for train/test and
    within each inner fold boundary.
- If the largest component exceeds 20% of a pair's records, the pair is not
  partitioned automatically. A single-linkage chain through repeats can do this,
  and it must be reviewed: report the component, and decide on repeat masking
  in a new version.
- Mixed-label components stay intact and are counted. They are not treated as
  label conflicts unless a verbatim match exists (F-087).
- Artifacts: hit table, edge list, component table with SHA-256, MMseqs2 version
  and full command line, config hash. They are generated, so they are not
  committed.

## 7. Limitations

- Coverage 0.80 misses overlaps shorter than 65 nt; the 0.50 sensitivity run
  bounds this.
- Single linkage can merge distant records through intermediates. This is
  conservative for leakage but can reduce the number of groups.
- Repeats are joined by similarity, not by annotation; F-088 is unconfirmed.

## References

See `docs/cnnprom_overlap_leakage_finding.md` §5 (Petti and Eddy, 2022;
Steinegger and Söding, 2017; Teufel et al., 2023).
