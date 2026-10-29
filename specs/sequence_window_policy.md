# Sequence Window Policy

## Status and scope

Decided by the project owner on 2026-10-29 (log R-021). This policy fixes the
model-ready window of every dataset by the taxonomic domain of its organism. It
supersedes the single 81 nt window of earlier contracts for eukaryotic data.
It changes no acquired, canonical, or processed file. Builds made under earlier
configs remain valid provenance for the experiments that used them.

## Windows

Offsets are counted relative to the TSS base, which is offset 0. Both ends are
inclusive, and the window is oriented 5' to 3' relative to transcription.

| Domain | Offsets | Upstream | TSS | Downstream | Length | Zero-based TSS index |
| --- | --- | --- | --- | --- | --- | --- |
| Eukaryota | -200..+50 | 200 | 1 | 50 | 251 nt | 200 |
| Prokaryota (Bacteria and Archaea) | -60..+20 | 60 | 1 | 20 | 81 nt | 60 |

The 251 nt window equals the declared CNNProm eukaryotic window (-200..+50,
251 nt). The 81 nt window is the existing project window.

## Domain assignment

The domain is a property of the collection. It is declared in each build
config, with the organism and its evidence level from the reference registry
(`specs/reference_coordinate_mapping_protocol.md`, Stage A). It is never
inferred from a filename, a sequence length, or model output. Archaea are
prokaryotes under this policy: `ipro-mp-11-haloferax-volcanii-ds2` and
`ipro-mp-21-thermococcus-kodakarensis-kod1` use 81 nt.

A collection whose organism evidence is `conflicting` has no domain until the
conflict is resolved. This applies to `bhandari-nominal-plant` (F-016): its
declared organism is a plant and its headers point to mouse, so both possible
domains are eukaryotic, but the collection stays blocked by its own conflict.

## Allowed derivations

A model-ready window is obtained in one of three ways, in this order of
preference:

1. **Native.** The released sequence already equals the domain window, with the
   TSS at the domain index declared by the source.
2. **Crop.** The released sequence is longer and contains the whole domain
   window, and its TSS index is `declared` or `verified`. The crop keeps
   offsets -U..+D around that index.
3. **Genomic re-extraction.** The TSS is located on a reference genome with
   status `verified` under the coordinate mapping protocol, and the window is
   extracted from that reference.

The following are not allowed: padding, extension with neighboring sequence
that is not taken from a verified locus, cropping around an undocumented TSS
index, and deriving a longer window from a shorter released sequence. A record
whose length differs from its release declaration is excluded, as in
`specs/dataset_integrity_audit.md` (Length exclusion), before any crop.

## Non-promoters

Non-promoters have no TSS, so the policy fixes only their length: the domain
length of the collection. Each build config declares, before any build or model
result, how each non-promoter window is taken:

- **same-construction sources** (one sampling rule and one window for both
  classes, such as CNNProm eukaryotes and Bhandari random genomic regions) use
  the same offsets as the promoters of that collection;
- **shorter or unrelated sources** (CDBProm 100 nt negatives, GenBank-entry
  negatives, CDS and intron fragments) record the chosen sub-window as a
  `construction_rule` with evidence `project_defined`; a source shorter than the
  domain length cannot be used;
- **generated controls** (`specs/negative_control_protocol.md`) are built at the
  domain length from the start.

Each choice is recorded in the filtering ledger. A sub-window choice is never
tuned against model outcomes.

## Collection feasibility

Status at `can-v1`. "Pending" means the derivation needs evidence that does
not yet exist; it is not a decision to exclude.

| Collections | Domain | Released length | Derivation | Status |
| --- | --- | --- | --- | --- |
| `cnnprom-human-non-tata`, `-mouse-non-tata`, `-mouse-tata`, `-mouse-tata-dbtss`, `-arabidopsis-tata`, `-arabidopsis-non-tata` | Eukaryota | 251 | native | ready |
| `bhandari-human`, `bhandari-yeast` | Eukaryota | 1,000 (TSS index 700) | crop to indexes 500..750 | ready for records whose TSS status is verified (F-055); the rest follow F-056 |
| `bhandari-nominal-plant` | conflicting | 1,000 | crop | blocked by F-016 |
| `bhandari-human-random-genomic` | Eukaryota (negatives) | 1,000 | same offsets as Bhandari positives | ready |
| `epd-128` | Eukaryota | 600 (-499..+100) | crop to indexes 299..549 | ready after per-entry organism resolution |
| `graphpro-human`, `graphpro-mouse` | Eukaryota | 81 | genomic re-extraction from the verified EPDnew loci | pending: new reconstruction; negatives rebuilt |
| `bdgp-drosophila-1941`, `-1998`, `bdgp-human` | Eukaryota | 300 | crop | pending: TSS index unknown |
| `cnnprom-ecoli-sigma70`, `cnnprom-bacillus-subtilis` | Prokaryota | 81 | native | ready |
| `graphpro-{bamy,cje,cpne,ecol,lint,rcap}` | Prokaryota | 81 | native or re-extraction | governed by `specs/graphpro_dataset_reconstruction.md` |
| `ipro-mp-*` (23) | Prokaryota | 81 | native | ready |
| `cdbprom-*` (11) | Prokaryota | 1,001 positives, 100 negatives | crop | positives pending: the TSS index 500 used by the regenerated builds is undocumented (F-018); negatives need a declared sub-window |
| `promotech-*` (6) | Prokaryota | 40 | genomic re-extraction | pending: verified loci |

## Consequences for models and analysis

- **Input contracts are per length.** A model, feature set, or frozen
  architecture is defined for one window length. CapsProm at 251 nt is a new
  model contract, not a reuse of the 81 nt contract, because capsule counts and
  decoder size depend on the length.
- **No cross-length mixing.** Sequences of different domains are never pooled
  into one training or evaluation set. Cross-dataset inference stays at the
  dataset level (`specs/statistical_evaluation_protocol.md`) and is reported
  separately for each domain.
- **Feature cost.** One-hot k-mer matrices have `(L - k + 1) x 4^k` values; at
  `L = 251` and `k = 6` this is 1,007,616 values per sequence. Feature configs
  must state the length they were sized for.
- **Earlier results.** Eukaryotic results built on 81 nt windows (for example
  the regenerated-v3 CNNProm eukaryotic datasets) are labeled `window_81nt`
  provenance. They are not compared with 251 nt results as if they measured the
  same task.

## Versioning

Applying this policy creates new versioned build configs, dataset directories,
eligibility manifests, and model contracts. Earlier configs, specs, manifests,
and provenance records are not edited or deleted. Processed data superseded by
the new builds may be archived as described in `docs/legacy_data_archive_plan.md`.

## Implementation points

The current code fixes 81 nt in these places, which must take the window from
the build or model config instead:

- `capsprom.data.dataset_builders.DEFAULT_TSS_POSITIONS` and
  `crop_fasta_directory` (one global upstream and downstream length; CNNProm
  eukaryotes are cropped from 251 to 81);
- the 60/20 defaults of `capsprom.data.sequences.crop_sequence`,
  `graphpro_reconstruction`, and `epd_genomic_controls`;
- `sequence_length=81` in `baseline_batch`, `xgboost_replication`,
  `canonical_neural`, `data.batch_audit`, `data.integrity_treatment`,
  `data.near_duplicate_audit`, and `eda.feature_exploration`;
- the 81 bp axis and caption in `eda.plots`.

`capsprom.models.capsprom` and `models.sequence_cnn` already take
`sequence_length` as a parameter. The 251 nt configuration still needs tests.
