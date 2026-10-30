# Dataset Reconstruction Sources and Publication Consistency Audit

Audit date: 2026-10-27.

## Scope

This document defines the upstream reference sources from which each raw
dataset in `data/raw/` could be reconstructed, and compares what each
publication states with what the local directory actually contains. GraphPro is
covered only by cross-reference because its reconstruction contract is already
frozen in `specs/graphpro_dataset_reconstruction.md` and
`configs/graphpro_source_registry_v1.yaml`.

The audit is source-only. No model output was consulted, no processed dataset
was changed, and no configuration or state file was created. Downloads used for
comparison were kept in a session scratch directory and are not part of the
repository.

## Method

- Local counts are FASTA records (or non-empty lines for headerless files),
  exact unique sequences, and the modal sequence length.
- Upstream identity was checked by downloading the published file and comparing
  MD5 digests after removing carriage returns and joining wrapped FASTA lines.
  "Identical" below means identical sequence content in identical order.
- Publication claims come from the article full text (PMC, PeerJ preprint,
  NAR Genomics and Bioinformatics). Inaccessible details are stated as such.

## Summary

| Directory | Publication | Local copy equals published release | Publication equals released data | Reconstructable from primary sources |
| --- | --- | --- | --- | --- |
| `Bhandari_etal` | Bhandari et al., PeerJ CS 7:e365 (2021) | Yes (same Drive file names; headers decoded) | No for `Plant_promoters` (mouse, F-063); the described *A. thaliana* set is in the repository history (F-064 to F-066) | Human and Yeast: yes (coordinates in headers). Plant: the Drive file as mouse only; *A. thaliana* by genome location of the historical file |
| `CDBProm` | Martinez et al., NAR Genom. Bioinform. 6(1):lqae018 (2024) | Yes (22/22 files identical to the website zip) | Partially (counts yes, window no) | Positives: only via sequence mapping to GenBank; negatives: no seed |
| `CNNProm` | Umarov & Solovyev, PLOS One 12(2):e0171410 (2017) | Yes (files renamed; content identical) | Partially (Bacillus counts, Human TATA missing) | Per resource, requires dated releases |
| `iPro-MP` | Su et al., Genome Biol. 26:353 (2025) | Yes (`Dataset/` = upstream `Benchmark Dataset/`) | Yes (all 23 species, every count) | Positives via PPD; negatives need the sampling seed |
| `EDP` | Meylan et al., NAR 48(D1):D65 (2020) | Close (4,796 of 4,809 entries) | Yes for the window | Yes, from the EPD FTP views |
| `Fuitfly` | No README; BDGP promoter datasets | Yes (3/3 files identical to BDGP) | Publication not confirmed | Yes, by direct download |
| `GraphPro` | Zhang, Wei & Liu, Comput. Biol. Med. 180:108974 (2024) | See GraphPro spec | See GraphPro spec | See GraphPro spec |

## Bhandari et al. (2021)

### Publication claims

The PeerJ preprint (arXiv:2105.07659) states that promoter regions from -700 to
+300 bp around the TSS (1,000 bp) were extracted with the UCSC Genome Browser.
It reports 41,671 *A. thaliana* sequences (UCSC `araTha1`), 61,546 human
sequences (`hg38`), and 6,125 yeast sequences (`sacCer3`). After duplicate
removal it reports about 35,000 promoters each for *A. thaliana* and human and
about 6,000 for yeast. Negatives were generated synthetically by shuffling
promoter sequences at a 1:1 ratio. The data-availability section points to
`https://github.com/nikitabhandari-dl/Dataset`, whose README links the same
Google Drive folder recorded locally.

### Local directory

| File | Records | Unique | Length | Header assembly |
| --- | ---: | ---: | --- | --- |
| `Human_promoter.fa` | 61,546 | 34,969 | 1,000 (61,516 records) | `hg38`, `ncbiRefSeqCurated` |
| `Yeast_promoter.fa` | 6,125 | 6,045 | 1,000 (6,122 records) | `sacCer3`, `ncbiRefSeq` |
| `Plant_promoters.fa` | 106,520 | 74,450 | 1,000 (106,515 records) | `mm10`, `ncbiRefSeq` |

The Drive folder (`Raw Data` subfolder) contains exactly `Human_promoter.gz`,
`Plant_promoters.gz`, and `Yeast_promoter.gz`, dated 2021-01-21; the local
`.gz` files decompress to the same record counts and headers as the local `.fa`
files. Headers encode `up_700` and `3'pad=300`, which matches the declared
window.

### Consistency

- Human and Yeast agree with the publication in assembly, window, raw count,
  and approximate deduplicated count.
- `Plant_promoters` disagrees in organism (`mm10` mouse coordinates rather than
  `araTha1`), raw count (106,520 rather than 41,671), and deduplicated count
  (74,450 rather than about 35,000). The upstream file itself carries the
  mismatch; it was not introduced locally. This confirms the conflict already
  recorded in `docs/control_coordinate_feasibility_inventory.md`.
- The repository history holds `Promoter_ArabidopsisThaliana.csv` (41,671
  records, 2020-04-23 to 2021-01-21), whose sequences occur in TAIR10.1
  (F-064 to F-066). It matches the publication's description in count, organism,
  and window length; whether the published results used it is open (F-071). See
  `docs/bhandari_nominal_plant_assessment.md`.
- Negatives are not distributed. The published shuffling function splits a
  sequence into blocks of `k_let` bases and permutes them, but the README leaves
  `k_let` unspecified (`k_let = #`) and gives no seed.

### Reconstruction sources

| Component | Source |
| --- | --- |
| Human TSS annotation | UCSC Table Browser, track NCBI RefSeq Curated, `hg38`: https://genome.ucsc.edu/cgi-bin/hgTables |
| Yeast TSS annotation | UCSC Table Browser, NCBI RefSeq, `sacCer3` |
| Mouse annotation (what the nominal Plant file actually contains) | UCSC Table Browser, NCBI RefSeq, `mm10` |
| *A. thaliana* (what the paper describes) | Repository commit `c1c97ee`, `Promoter_ArabidopsisThaliana.csv` (`configs/bhandari_history_acquisition_v1.yaml`); reference TAIR10.1, UCSC GenArk GCF_000001735.4 (`araTha1` is no longer served, F-069) |
| Genomes | https://hgdownload.soe.ucsc.edu/goldenPath/hg38/bigZips/hg38.2bit, https://hgdownload.soe.ucsc.edu/goldenPath/sacCer3/bigZips/sacCer3.2bit, https://hgdownload.soe.ucsc.edu/goldenPath/mm10/bigZips/mm10.2bit |
| Negative procedure | Block-shuffle code in https://github.com/nikitabhandari-dl/Dataset (README); `k_let` and seed undocumented |
| Human random-genome test negatives | `random_sequences.fasta` in the same repository (not present locally) |

Each header already contains the chromosome, range, and strand, so Human and
Yeast positives can be recreated exactly against the stated assemblies. The
RefSeq table snapshot date is not recorded; the integers in the header (`7401`,
`7481`) are Table Browser custom-track identifiers, not release numbers.

## CDBProm (2024)

### Publication claims

Table 1 lists 11 organisms, their GenBank accessions, and 15,654 promoters in
total. The text says the region from -60 to +1 relative to the TSS was used and
that each negative is "a same-sized sequence (i.e. 60 nucleotides sequence)"
taken from a random position between +1 and +500 downstream of its promoter,
for a 1:1 ratio. Encoding is DNA duplex stability (DDS) per dinucleotide. Data
and code are cited at Zenodo DOI 10.5281/zenodo.10581808 and
`https://github.com/gustavsganzerla/cdbprom`.

### Local directory

All 22 per-organism text files are identical to the files in the website
archive `https://aw.iimas.unam.mx/cdbprom/descargasFiles/training_sequences.zip`
(MD5 of the archive `68bf4c0d94190cbcf3f28eec049905ab`; the same archive is kept
in `data/raw/Nova pasta (2)/`). `training_data.csv` is identical in content to
the GitHub copy.

| Organism (local file) | GenBank (paper) | Paper | Local positives | Local negatives |
| --- | --- | ---: | ---: | ---: |
| *Anabaena* sp. | CP034058.1 | 2,517 | 2,517 | 2,517 |
| *B. amyloliquefaciens* XH7 | CP002927.1 | 1,059 | 1,059 | 1,059 |
| *C. pneumoniae* CWL029 | AE001363.1 | 404 | 404 | 404 |
| *C. glutamicum* ATCC 13032 | BA000036.3 | 575 | 575 | 575 |
| *H. pylori* 26695 | CP003904.1 | 713 | **714** | 714 |
| *K. pneumoniae* MGH 78578 | CP000647.1 | 1,329 | 1,329 | 1,329 |
| *M. tuberculosis* H37Rv | CP110619.1 | 1,772 | 1,772 | 1,772 |
| *P. aeruginosa* UCBPP-PA14 | CP034244.1 | 2,054 | **2,055** | 2,055 |
| *S. enterica* Typhimurium SL1344 | CP133487.1 | 981 | 981 | 981 |
| *S. coelicolor* A3(2) | AL939104.1 | 2,611 | 2,611 | 2,611 |
| *Synechocistis* sp. PCC 6803 | AP012276.1 | 1,639 | 1,639 | 1,639 |

### Consistency

- Counts agree except for one extra positive each in *H. pylori* and
  *P. aeruginosa*; the per-organism files total 15,656, while the CSV has 15,654
  positives.
- Window lengths disagree with the text. Local positives are 1,001 nt and local
  negatives are 100 nt (51 are 99 nt), not 61 and 60 nt.
- `training_data.csv` does not contain nucleotides, contrary to the repository
  README; it contains 99 DDS values per row. Re-encoding the first 200 local
  positives of *Anabaena* and *C. pneumoniae* showed that each one appears in
  the CSV as
  the DDS of positions 421-520 of the 1,001-nt sequence, i.e. 80 nt upstream to
  20 nt downstream if the TSS is the central base. `predictor.py` then keeps
  columns 21-99 and labels them -59 to +20. The model therefore used a -60..+20
  window, not -60..+1. The *H. pylori* sample matched at offset 421 for only
  53/200 sequences (5 at offset 423), so the alignment is not uniform.
- The CSV has 15,605 negatives rather than 15,654. This equals the 15,656 local
  negatives minus the 51 that are 99 nt long, so the short negatives were
  dropped from the matrix.
- File names keep upstream misspellings (`klebisiella`, `mycrobacterium`,
  `pseudonomas`).

### Reconstruction sources

| Component | Source |
| --- | --- |
| Released sequences | https://aw.iimas.unam.mx/cdbprom/descargasFiles/training_sequences.zip |
| Released encoded matrix and code | https://github.com/gustavsganzerla/cdbprom; Zenodo version DOI 10.5281/zenodo.10581809 (concept 10.5281/zenodo.10581808) |
| Genomes | NCBI Nucleotide, one accession per organism from the table above: `https://www.ncbi.nlm.nih.gov/nuccore/<accession>` |
| Primary TSS maps | References 24-28 of the article for *B. amyloliquefaciens*, *C. pneumoniae*, *K. pneumoniae*, *S. coelicolor*, and *Synechocistis*; the other six organisms are listed as unpublished |

No row-level coordinates or strands are released. Positives can be placed on a
genome only by exact sequence mapping to the declared accession; ambiguous and
missing matches must be counted under a new versioned mapping contract, as the
feasibility inventory already requires. Negatives cannot be regenerated exactly
because no seed is released.

## CNNProm (Umarov & Solovyev, 2017)

### Publication claims (Table 1)

| Dataset | Promoters | Non-promoters | Length | Window |
| --- | ---: | ---: | ---: | --- |
| *E. coli* sigma70 | 839 | 3,000 | 81 | -60..+20 |
| *B. subtilis* | 746 | 2,000 | 81 | -60..+20 |
| Human TATA | 1,426 | 8,256 | 251 | -200..+50 |
| Human non-TATA | 19,811 | 27,731 | 251 | -200..+50 |
| Mouse TATA | 1,255 | 3,530 | 251 | -200..+50 |
| Mouse non-TATA | 16,283 | 24,822 | 251 | -200..+50 |
| *Arabidopsis* TATA | 1,497 | 2,879 | 251 | -200..+50 |
| *Arabidopsis* non-TATA | 5,905 | 11,459 | 251 | -200..+50 |

A separate mouse TATA set of 1,083 DBTSS training and 271 test promoters is
also described. Sources: RegulonDB 9.0 (*E. coli*), DBTBS (*B. subtilis*),
EPDnew (eukaryotic promoters), DBTSS (extra mouse TATA set). Eukaryotic
negatives are random gene fragments after the first exon; bacterial negatives
are opposite-strand fragments of protein-coding genes.

### Local directory and upstream mapping

The local files are renamed copies of `https://github.com/solovictor/CNNPromoterData`.
Sequence identity was confirmed directly for six files; the remaining files
differ from upstream in byte size by exactly their line count (CRLF
conversion).

| Local file | Upstream file | Local records | Matches Table 1 |
| --- | --- | ---: | --- |
| `Ecoli_pos.fa` | `Ecoli_prom.fa` | 839 | Yes |
| `Ecoli_neg.fa` | `Ecoli_non_prom.fa` | 3,000 | Yes |
| `Bacillus_pos.fa` | `Bacillus_prom.fa` | 373 | **No (746)** |
| `Bacillus_neg.fa` | `Bacillus_non_prom.fa` | 1,000 | **No (2,000)** |
| `Human_non_tata_pos.fa` | `human_non_tata.fa` | 19,811 | Yes |
| `Human_non_tata_neg.fa` | `human_nonprom_big.fa` | 27,731 | Yes |
| `Mouse_non_tata_pos.fa` | `Mouse_non_tata.fa` | 16,283 | Yes |
| `Mouse_non_tata_neg.fa` | `Mouse_non_nonprom_big.fa` | 24,822 | Yes |
| `Mouse_tata_pos.fa` | `Mouse_tata.fa` | 1,255 | Yes |
| `Mouse_tata_neg.fa` | `Mouse_nonprom.fa` | 3,530 | Yes |
| `Mouse_tata_dbtss.fa` | `Mouse_tata_dbtss.fa` | 1,354 | Yes (1,083 + 271) |
| `Arabidopsis_tata_pos.fa` | `Arabidopsis_tata.fa` | 1,497 | Yes |
| `Arabidopsis_tata_neg.fa` | `Arabidopsis_non_prom.fa` | 2,879 | Yes |
| `Arabidopsis_non_tata_pos.fa` | `Arabidopsis_non_tata.fa` | 5,905 | Yes |
| `Arabidopsis_non_tata_neg.fa` | `Arabidopsis_non_prom_big.fa` | 11,459 | Yes |

### Consistency

- The Bacillus counts reported in the paper are exactly twice the released
  record counts, which equal the released line counts (746 and 2,000). The
  release, not the table, is the usable reference.
- Human TATA (1,426/8,256) is described in the paper but is absent from both the
  upstream repository and the local directory.
- The upstream file names do not encode the TATA/non-TATA pairing of the
  negatives; the pairing above follows from the Table 1 counts.

### Reconstruction sources

| Component | Source |
| --- | --- |
| Released data | https://github.com/solovictor/CNNPromoterData |
| *E. coli* sigma70 promoters | RegulonDB 9.0 (https://regulondb.ccg.unam.mx/); headers carry `ECK12` identifiers, strand, and position on K-12 MG1655 (NC_000913) |
| *B. subtilis* promoters | DBTBS (https://dbtbs.hgc.jp/); headers expose gene names, not coordinates; genome NC_000964 |
| Human, mouse, *Arabidopsis* promoters | EPDnew (https://epd.expasy.org/epdnew/); headers carry EPD `FP` identifiers; the EPDnew release used is not stated |
| Extra mouse TATA set | DBTSS (https://dbtss.hgc.jp/) |
| Negatives | No coordinates or seed released; regeneration would be a new resource |

The Softberry page recorded in the local README now returns HTTP 404.

## iPro-MP (Su et al., 2025)

### Publication claims

Positives come from the Prokaryotic Promoter Database (PPD,
https://lin-group.cn/database/ppd/, version not stated), restricted to species
with more than 1,000 experimentally validated promoters plus *B. subtilis*,
deduplicated with CD-HIT at 0.8 identity, as 81-bp windows from -60 to +20.
Negatives are equal numbers of 81-bp windows from CDS longer than 2,000 bp and
from convergent intergenic regions longer than 81 bp (1:2 overall), also
CD-HIT filtered. Train and test sets are split 4:1. Table 3 lists the 23
species, GenBank accessions, and per-split counts. The article DOI is
10.1186/s13059-025-03819-9 (PMC12516880). Pretrained models are on Zenodo
(10.5281/zenodo.15180139; concept 10.5281/zenodo.15180138).

### Local directory

`repo/Dataset/{Train,Test}` is the upstream `Benchmark Dataset/` folder under a
different name; three sampled files are identical. For all 23 species, the
local counts of positives, `CDS` negatives, and `Convergent` negatives in both
splits match Table 3 exactly, and every sequence is 81 bp. Labels are encoded in
the header suffix (`<species>--<n>`, `<species> CDS--<n>`,
`<species> Convergent--<n>`).

### Consistency

Data agree with the publication. The local README labels the Zenodo DOI as
"Paper"; that DOI holds the models, and the paper DOI is the one given above.

### Reconstruction sources

| Component | Source |
| --- | --- |
| Released data | https://github.com/Jackie-Suv/iPro-MP/tree/main/Benchmark%20Dataset |
| Positives | PPD: https://lin-group.cn/database/ppd/ |
| Genomes and CDS annotation | NCBI Nucleotide by the Table 3 accessions (for example NC_000913.3 for *E. coli* K-12 MG1655 and NC_000964.3 for *B. subtilis* 168) |
| Negatives | Procedure is described, but the sampling seed and the CD-HIT output are not released |

## EPD (`EDP` directory)

The directory name is a misspelling of EPD. Its README cites the EPD 2020
article and copies the taxonomy shown on
https://epd.expasy.org/epd/EPD_download.php ("All promoters (4809)", last update
October 2019). The local `edp_all.fa` holds 4,796 entries (`EP17001` to
`EP26010`), all but one 301 nt long with headers stating "range -250 to 50".
The window matches the header; 13 entries of the 4,809 total are not present,
and the reason is not recorded.

Reconstruction source: the EPD selection page above or the FTP views at
https://epd.expasy.org/ftp/epd/views/ (FASTA `epd*.seq`), using -250..+50. No
negatives are part of this resource.

## Fruitfly (`Fuitfly` directory)

The directory has no README and its name is misspelled. All three files match
the Berkeley Drosophila Genome Project promoter datasets: the 1,941-record file
is identical in order, and the other two contain exactly the same sequences as
the concatenated BDGP parts:

| Local file | Records | BDGP source |
| --- | ---: | --- |
| `Drosophila_promoter_all_1941.fa` | 1,941 | https://www.fruitfly.org/seq_tools/datasets/Drosophila/promoter/prom/promoter_all_1941.fa |
| `drosophila.fa` | 256 | Concatenation of `drosophila.0`-`drosophila.2` in https://www.fruitfly.org/seq_tools/datasets/Drosophila/promoter/1998/prom/ |
| `human.fa` | 565 | Concatenation of `vertebrate.0`-`vertebrate.4` in https://www.fruitfly.org/seq_tools/datasets/Human/promoter/prom/ |

All sequences are 300 nt (-250..+50); the 256- and 565-record sets carry EPD
identifiers. The same BDGP directories also provide matching `CDS/` and
`intron/` negative sets, which are not present locally. The publication
associated with each set was not confirmed in this audit and should be
established before the data are cited.

## Other raw folders

- `data/raw/Nova pasta (2)/training_sequences.zip` is the CDBProm website
  archive (MD5 above).
- `data/raw/Nova pasta/predictions_ecoli.zip` holds a `predictions_ecoli/`
  folder of per-assembly upstream tables (the first is
  `Escherichia_coli_GCF_001615615.1_ASM161561v1_upstream.txt`). It looks like a
  CDBProm prediction product rather than training data; its origin is not
  documented and was not verified.

## GraphPro

See `specs/graphpro_dataset_reconstruction.md`. One discrepancy belongs in the
local README: `data/raw/GraphPro/README` lists *Clostridium phytofermentans*,
but neither the upstream `Datasets/` folder nor the local copy has that
organism. Both contain `Cpne`, whose headers identify *Chlamydophila
pneumoniae* CWL029 (`NC_000922.1`).

## Open actions

1. Keep the Bhandari `Plant_promoters` identity blocked as a plant set; the
   upstream release contradicts the publication. The file is *Mus musculus*
   `mm10` (F-063); its permitted uses as a mouse dataset, and the evidence
   still pending, are in `docs/bhandari_nominal_plant_assessment.md`.
2. Record the CDBProm -60..+20 effective window and the 1,001/100-nt raw
   lengths wherever CDBProm windows are described in the thesis.
3. Describe CNNProm Bacillus with the released 373/1,000 counts and note that
   Human TATA is unavailable.
4. Correct the iPro-MP, GraphPro, EPD, and Fruitfly README notes in `data/raw/`
   if those folders become active sources.
