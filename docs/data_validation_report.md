# Biological Data Validation Report

This report validates sequence-bearing files in `data/` for DNA alphabet constraints, expected 81 bp processed CSV sequences, binary labels, and filename count consistency where available.

## Summary

- Total files inspected: 982
- Sequence-bearing files validated: 331
- Sequence-bearing files passed: 242
- Sequence-bearing files failed: 89
- Files requiring manual review: 1
- Valid sequence records in passed files: 1640841

## Status Counts

- `fail`: 89
- `not_applicable`: 650
- `pass`: 242
- `review`: 1

## File Kind Counts

- `fasta`: 163
- `fasta_gzip`: 3
- `fasta_txt`: 46
- `line_sequence_txt`: 61
- `non_sequence_artifact`: 33
- `non_sequence_csv`: 617
- `sequence_csv`: 58
- `zip`: 1

## Failures

### `interim/aligned_fasta/prom-bhandari-eukaryotic-Human_promoter-61516-81.fa`

- Kind: `fasta`
- Records read: 246064
- Length range: 1883-1883
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NR_031705.1_up_700_chr1_220200620_r range=chr1:220200320-220201319: invalid DNA symbols -
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NR_031705.1_up_700_chr1_220200620_r range=chr1:220200320-220201319: length 1883, expected 81 from filename
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NR_002994.2_up_700_chr1_220200677_r range=chr1:220200377-220201376: invalid DNA symbols -
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NR_002994.2_up_700_chr1_220200677_r range=chr1:220200377-220201376: length 1883, expected 81 from filename
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_153254.2_up_700_chr1_1178997_f range=chr1:1178997-1179996 5'pad: invalid DNA symbols -
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_153254.2_up_700_chr1_1178997_f range=chr1:1178997-1179996 5'pad: length 1883, expected 81 from filename
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_003036.3_up_700_chr1_2227995_f range=chr1:2227995-2228994 5'pad: invalid DNA symbols -
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_003036.3_up_700_chr1_2227995_f range=chr1:2227995-2228994 5'pad: length 1883, expected 81 from filename
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_024676.4_up_700_chr1_36306407_f range=chr1:36306407-36307406 5': invalid DNA symbols -
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_024676.4_up_700_chr1_36306407_f range=chr1:36306407-36307406 5': length 1883, expected 81 from filename
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001198850.1_up_700_chr1_42335878_r range=chr1:42335578-42336577: invalid DNA symbols -
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001198850.1_up_700_chr1_42335878_r range=chr1:42335578-42336577: length 1883, expected 81 from filename
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_032852.3_up_700_chr1_62783406_f range=chr1:62783406-62784405 5': invalid DNA symbols -
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_032852.3_up_700_chr1_62783406_f range=chr1:62783406-62784405 5': length 1883, expected 81 from filename
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_178221.2_up_700_chr1_62783406_f range=chr1:62783406-62784405 5': invalid DNA symbols -
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_178221.2_up_700_chr1_62783406_f range=chr1:62783406-62784405 5': length 1883, expected 81 from filename
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001308251.1_up_700_chr1_93585163_r range=chr1:93584863-93585862: invalid DNA symbols -
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001308251.1_up_700_chr1_93585163_r range=chr1:93584863-93585862: length 1883, expected 81 from filename
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001261408.1_up_700_chr1_93847151_r range=chr1:93846851-93847850: invalid DNA symbols -
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001261408.1_up_700_chr1_93847151_r range=chr1:93846851-93847850: length 1883, expected 81 from filename
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NR_003928.2_up_700_chr1_111279824_f range=chr1:111279824-111280823: invalid DNA symbols -
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NR_003928.2_up_700_chr1_111279824_f range=chr1:111279824-111280823: length 1883, expected 81 from filename
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001039703.5_up_700_chr1_146144805_r range=chr1:146144505-146145: invalid DNA symbols -
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001039703.5_up_700_chr1_146144805_r range=chr1:146144505-146145: length 1883, expected 81 from filename
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001302371.1_up_700_chr1_146144805_r range=chr1:146144505-146145: invalid DNA symbols -

### `interim/aligned_fasta/prom-bhandari-prokaryotic-Yeast_promoter-6122-81.fa`

- Kind: `fasta`
- Records read: 18366
- Length range: 751-751
- Issue: sacCer3_ct_tbncbiRefSeq_7481_NM_001184582.1_up_700_chrI_1780_f range=chrI:1780-2779 5'pad=0 3'pad=3: invalid DNA symbols -
- Issue: sacCer3_ct_tbncbiRefSeq_7481_NM_001184582.1_up_700_chrI_1780_f range=chrI:1780-2779 5'pad=0 3'pad=3: length 751, expected 81 from filename
- Issue: sacCer3_ct_tbncbiRefSeq_7481_NM_001180043.1_up_700_chrI_2170_r range=chrI:1870-2869 5'pad=0 3'pad=3: invalid DNA symbols -
- Issue: sacCer3_ct_tbncbiRefSeq_7481_NM_001180043.1_up_700_chrI_2170_r range=chrI:1870-2869 5'pad=0 3'pad=3: length 751, expected 81 from filename
- Issue: sacCer3_ct_tbncbiRefSeq_7481_NM_001178208.1_up_700_chrI_9017_r range=chrI:8717-9716 5'pad=0 3'pad=3: invalid DNA symbols -
- Issue: sacCer3_ct_tbncbiRefSeq_7481_NM_001178208.1_up_700_chrI_9017_r range=chrI:8717-9716 5'pad=0 3'pad=3: length 751, expected 81 from filename
- Issue: sacCer3_ct_tbncbiRefSeq_7481_NM_001180042.1_up_700_chrI_11346_f range=chrI:11346-12345 5'pad=0 3'pa: invalid DNA symbols -
- Issue: sacCer3_ct_tbncbiRefSeq_7481_NM_001180042.1_up_700_chrI_11346_f range=chrI:11346-12345 5'pad=0 3'pa: length 751, expected 81 from filename
- Issue: sacCer3_ct_tbncbiRefSeq_7481_NM_001179897.1_up_700_chrI_11952_r range=chrI:11652-12651 5'pad=0 3'pa: invalid DNA symbols -
- Issue: sacCer3_ct_tbncbiRefSeq_7481_NM_001179897.1_up_700_chrI_11952_r range=chrI:11652-12651 5'pad=0 3'pa: length 751, expected 81 from filename
- Issue: sacCer3_ct_tbncbiRefSeq_7481_NM_001180041.1_up_700_chrI_13744_r range=chrI:13444-14443 5'pad=0 3'pa: invalid DNA symbols -
- Issue: sacCer3_ct_tbncbiRefSeq_7481_NM_001180041.1_up_700_chrI_13744_r range=chrI:13444-14443 5'pad=0 3'pa: length 751, expected 81 from filename
- Issue: sacCer3_ct_tbncbiRefSeq_7481_NM_001178206.2_up_700_chrI_20866_f range=chrI:20866-21865 5'pad=0 3'pa: invalid DNA symbols -
- Issue: sacCer3_ct_tbncbiRefSeq_7481_NM_001178206.2_up_700_chrI_20866_f range=chrI:20866-21865 5'pad=0 3'pa: length 751, expected 81 from filename
- Issue: sacCer3_ct_tbncbiRefSeq_7481_NM_001184642.1_up_700_chrI_22686_r range=chrI:22386-23385 5'pad=0 3'pa: invalid DNA symbols -
- Issue: sacCer3_ct_tbncbiRefSeq_7481_NM_001184642.1_up_700_chrI_22686_r range=chrI:22386-23385 5'pad=0 3'pa: length 751, expected 81 from filename
- Issue: sacCer3_ct_tbncbiRefSeq_7481_NM_001178205.1_up_700_chrI_27969_r range=chrI:27669-28668 5'pad=0 3'pa: invalid DNA symbols -
- Issue: sacCer3_ct_tbncbiRefSeq_7481_NM_001178205.1_up_700_chrI_27969_r range=chrI:27669-28668 5'pad=0 3'pa: length 751, expected 81 from filename
- Issue: sacCer3_ct_tbncbiRefSeq_7481_NM_001178204.1_up_700_chrI_30867_f range=chrI:30867-31866 5'pad=0 3'pa: invalid DNA symbols -
- Issue: sacCer3_ct_tbncbiRefSeq_7481_NM_001178204.1_up_700_chrI_30867_f range=chrI:30867-31866 5'pad=0 3'pa: length 751, expected 81 from filename
- Issue: sacCer3_ct_tbncbiRefSeq_7481_NM_001178203.1_up_700_chrI_32748_f range=chrI:32748-33747 5'pad=0 3'pa: invalid DNA symbols -
- Issue: sacCer3_ct_tbncbiRefSeq_7481_NM_001178203.1_up_700_chrI_32748_f range=chrI:32748-33747 5'pad=0 3'pa: length 751, expected 81 from filename
- Issue: sacCer3_ct_tbncbiRefSeq_7481_NM_001178202.2_up_700_chrI_34455_f range=chrI:34455-35454 5'pad=0 3'pa: invalid DNA symbols -
- Issue: sacCer3_ct_tbncbiRefSeq_7481_NM_001178202.2_up_700_chrI_34455_f range=chrI:34455-35454 5'pad=0 3'pa: length 751, expected 81 from filename
- Issue: sacCer3_ct_tbncbiRefSeq_7481_NM_001178201.2_up_700_chrI_35809_f range=chrI:35809-36808 5'pad=0 3'pa: invalid DNA symbols -

### `interim/aligned_fasta/prom-cdbprom-prokaryotic-anabaena_sp-2517-81.fa`

- Kind: `fasta`
- Records read: 7551
- Length range: 550-550
- Issue: 0 prom prokaryotic sequence 0: invalid DNA symbols -
- Issue: 0 prom prokaryotic sequence 0: length 550, expected 81 from filename
- Issue: 1 prom prokaryotic sequence 1: invalid DNA symbols -
- Issue: 1 prom prokaryotic sequence 1: length 550, expected 81 from filename
- Issue: 2 prom prokaryotic sequence 2: invalid DNA symbols -
- Issue: 2 prom prokaryotic sequence 2: length 550, expected 81 from filename
- Issue: 3 prom prokaryotic sequence 3: invalid DNA symbols -
- Issue: 3 prom prokaryotic sequence 3: length 550, expected 81 from filename
- Issue: 4 prom prokaryotic sequence 4: invalid DNA symbols -
- Issue: 4 prom prokaryotic sequence 4: length 550, expected 81 from filename
- Issue: 5 prom prokaryotic sequence 5: invalid DNA symbols -
- Issue: 5 prom prokaryotic sequence 5: length 550, expected 81 from filename
- Issue: 6 prom prokaryotic sequence 6: invalid DNA symbols -
- Issue: 6 prom prokaryotic sequence 6: length 550, expected 81 from filename
- Issue: 7 prom prokaryotic sequence 7: invalid DNA symbols -
- Issue: 7 prom prokaryotic sequence 7: length 550, expected 81 from filename
- Issue: 8 prom prokaryotic sequence 8: invalid DNA symbols -
- Issue: 8 prom prokaryotic sequence 8: length 550, expected 81 from filename
- Issue: 9 prom prokaryotic sequence 9: invalid DNA symbols -
- Issue: 9 prom prokaryotic sequence 9: length 550, expected 81 from filename
- Issue: 10 prom prokaryotic sequence 10: invalid DNA symbols -
- Issue: 10 prom prokaryotic sequence 10: length 550, expected 81 from filename
- Issue: 11 prom prokaryotic sequence 11: invalid DNA symbols -
- Issue: 11 prom prokaryotic sequence 11: length 550, expected 81 from filename
- Issue: 12 prom prokaryotic sequence 12: invalid DNA symbols -

### `interim/aligned_fasta/prom-cdbprom-prokaryotic-bacillus_amyloliquefaciens-1059-81.fa`

- Kind: `fasta`
- Records read: 3177
- Length range: 464-464
- Issue: 0 prom prokaryotic sequence 0: invalid DNA symbols -
- Issue: 0 prom prokaryotic sequence 0: length 464, expected 81 from filename
- Issue: 1 prom prokaryotic sequence 1: invalid DNA symbols -
- Issue: 1 prom prokaryotic sequence 1: length 464, expected 81 from filename
- Issue: 2 prom prokaryotic sequence 2: invalid DNA symbols -
- Issue: 2 prom prokaryotic sequence 2: length 464, expected 81 from filename
- Issue: 3 prom prokaryotic sequence 3: invalid DNA symbols -
- Issue: 3 prom prokaryotic sequence 3: length 464, expected 81 from filename
- Issue: 4 prom prokaryotic sequence 4: invalid DNA symbols -
- Issue: 4 prom prokaryotic sequence 4: length 464, expected 81 from filename
- Issue: 5 prom prokaryotic sequence 5: invalid DNA symbols -
- Issue: 5 prom prokaryotic sequence 5: length 464, expected 81 from filename
- Issue: 6 prom prokaryotic sequence 6: invalid DNA symbols -
- Issue: 6 prom prokaryotic sequence 6: length 464, expected 81 from filename
- Issue: 7 prom prokaryotic sequence 7: invalid DNA symbols -
- Issue: 7 prom prokaryotic sequence 7: length 464, expected 81 from filename
- Issue: 8 prom prokaryotic sequence 8: invalid DNA symbols -
- Issue: 8 prom prokaryotic sequence 8: length 464, expected 81 from filename
- Issue: 9 prom prokaryotic sequence 9: invalid DNA symbols -
- Issue: 9 prom prokaryotic sequence 9: length 464, expected 81 from filename
- Issue: 10 prom prokaryotic sequence 10: invalid DNA symbols -
- Issue: 10 prom prokaryotic sequence 10: length 464, expected 81 from filename
- Issue: 11 prom prokaryotic sequence 11: invalid DNA symbols -
- Issue: 11 prom prokaryotic sequence 11: length 464, expected 81 from filename
- Issue: 12 prom prokaryotic sequence 12: invalid DNA symbols -

### `interim/aligned_fasta/prom-cdbprom-prokaryotic-chlamydophila_pneumoniae-404-81.fa`

- Kind: `fasta`
- Records read: 1212
- Length range: 414-414
- Issue: 0 prom prokaryotic sequence 0: invalid DNA symbols -
- Issue: 0 prom prokaryotic sequence 0: length 414, expected 81 from filename
- Issue: 1 prom prokaryotic sequence 1: invalid DNA symbols -
- Issue: 1 prom prokaryotic sequence 1: length 414, expected 81 from filename
- Issue: 2 prom prokaryotic sequence 2: invalid DNA symbols -
- Issue: 2 prom prokaryotic sequence 2: length 414, expected 81 from filename
- Issue: 3 prom prokaryotic sequence 3: invalid DNA symbols -
- Issue: 3 prom prokaryotic sequence 3: length 414, expected 81 from filename
- Issue: 4 prom prokaryotic sequence 4: invalid DNA symbols -
- Issue: 4 prom prokaryotic sequence 4: length 414, expected 81 from filename
- Issue: 5 prom prokaryotic sequence 5: invalid DNA symbols -
- Issue: 5 prom prokaryotic sequence 5: length 414, expected 81 from filename
- Issue: 6 prom prokaryotic sequence 6: invalid DNA symbols -
- Issue: 6 prom prokaryotic sequence 6: length 414, expected 81 from filename
- Issue: 7 prom prokaryotic sequence 7: invalid DNA symbols -
- Issue: 7 prom prokaryotic sequence 7: length 414, expected 81 from filename
- Issue: 8 prom prokaryotic sequence 8: invalid DNA symbols -
- Issue: 8 prom prokaryotic sequence 8: length 414, expected 81 from filename
- Issue: 9 prom prokaryotic sequence 9: invalid DNA symbols -
- Issue: 9 prom prokaryotic sequence 9: length 414, expected 81 from filename
- Issue: 10 prom prokaryotic sequence 10: invalid DNA symbols -
- Issue: 10 prom prokaryotic sequence 10: length 414, expected 81 from filename
- Issue: 11 prom prokaryotic sequence 11: invalid DNA symbols -
- Issue: 11 prom prokaryotic sequence 11: length 414, expected 81 from filename
- Issue: 12 prom prokaryotic sequence 12: invalid DNA symbols -

### `interim/aligned_fasta/prom-cdbprom-prokaryotic-corynebacterium_glutamicum-575-81.fa`

- Kind: `fasta`
- Records read: 1725
- Length range: 387-387
- Issue: 0 prom prokaryotic sequence 0: invalid DNA symbols -
- Issue: 0 prom prokaryotic sequence 0: length 387, expected 81 from filename
- Issue: 1 prom prokaryotic sequence 1: invalid DNA symbols -
- Issue: 1 prom prokaryotic sequence 1: length 387, expected 81 from filename
- Issue: 2 prom prokaryotic sequence 2: invalid DNA symbols -
- Issue: 2 prom prokaryotic sequence 2: length 387, expected 81 from filename
- Issue: 3 prom prokaryotic sequence 3: invalid DNA symbols -
- Issue: 3 prom prokaryotic sequence 3: length 387, expected 81 from filename
- Issue: 4 prom prokaryotic sequence 4: invalid DNA symbols -
- Issue: 4 prom prokaryotic sequence 4: length 387, expected 81 from filename
- Issue: 5 prom prokaryotic sequence 5: invalid DNA symbols -
- Issue: 5 prom prokaryotic sequence 5: length 387, expected 81 from filename
- Issue: 6 prom prokaryotic sequence 6: invalid DNA symbols -
- Issue: 6 prom prokaryotic sequence 6: length 387, expected 81 from filename
- Issue: 7 prom prokaryotic sequence 7: invalid DNA symbols -
- Issue: 7 prom prokaryotic sequence 7: length 387, expected 81 from filename
- Issue: 8 prom prokaryotic sequence 8: invalid DNA symbols -
- Issue: 8 prom prokaryotic sequence 8: length 387, expected 81 from filename
- Issue: 9 prom prokaryotic sequence 9: invalid DNA symbols -
- Issue: 9 prom prokaryotic sequence 9: length 387, expected 81 from filename
- Issue: 10 prom prokaryotic sequence 10: invalid DNA symbols -
- Issue: 10 prom prokaryotic sequence 10: length 387, expected 81 from filename
- Issue: 11 prom prokaryotic sequence 11: invalid DNA symbols -
- Issue: 11 prom prokaryotic sequence 11: length 387, expected 81 from filename
- Issue: 12 prom prokaryotic sequence 12: invalid DNA symbols -

### `interim/aligned_fasta/prom-cdbprom-prokaryotic-helicobacter_pylori-714-81.fa`

- Kind: `fasta`
- Records read: 2142
- Length range: 410-410
- Issue: 0 prom prokaryotic sequence 0: invalid DNA symbols -
- Issue: 0 prom prokaryotic sequence 0: length 410, expected 81 from filename
- Issue: 1 prom prokaryotic sequence 1: invalid DNA symbols -
- Issue: 1 prom prokaryotic sequence 1: length 410, expected 81 from filename
- Issue: 2 prom prokaryotic sequence 2: invalid DNA symbols -
- Issue: 2 prom prokaryotic sequence 2: length 410, expected 81 from filename
- Issue: 3 prom prokaryotic sequence 3: invalid DNA symbols -
- Issue: 3 prom prokaryotic sequence 3: length 410, expected 81 from filename
- Issue: 4 prom prokaryotic sequence 4: invalid DNA symbols -
- Issue: 4 prom prokaryotic sequence 4: length 410, expected 81 from filename
- Issue: 5 prom prokaryotic sequence 5: invalid DNA symbols -
- Issue: 5 prom prokaryotic sequence 5: length 410, expected 81 from filename
- Issue: 6 prom prokaryotic sequence 6: invalid DNA symbols -
- Issue: 6 prom prokaryotic sequence 6: length 410, expected 81 from filename
- Issue: 7 prom prokaryotic sequence 7: invalid DNA symbols -
- Issue: 7 prom prokaryotic sequence 7: length 410, expected 81 from filename
- Issue: 8 prom prokaryotic sequence 8: invalid DNA symbols -
- Issue: 8 prom prokaryotic sequence 8: length 410, expected 81 from filename
- Issue: 9 prom prokaryotic sequence 9: invalid DNA symbols -
- Issue: 9 prom prokaryotic sequence 9: length 410, expected 81 from filename
- Issue: 10 prom prokaryotic sequence 10: invalid DNA symbols -
- Issue: 10 prom prokaryotic sequence 10: length 410, expected 81 from filename
- Issue: 11 prom prokaryotic sequence 11: invalid DNA symbols -
- Issue: 11 prom prokaryotic sequence 11: length 410, expected 81 from filename
- Issue: 12 prom prokaryotic sequence 12: invalid DNA symbols -

### `interim/aligned_fasta/prom-cdbprom-prokaryotic-klebisiella_pneumoniae-1329-81.fa`

- Kind: `fasta`
- Records read: 3987
- Length range: 449-449
- Issue: 0 prom prokaryotic sequence 0: invalid DNA symbols -
- Issue: 0 prom prokaryotic sequence 0: length 449, expected 81 from filename
- Issue: 1 prom prokaryotic sequence 1: invalid DNA symbols -
- Issue: 1 prom prokaryotic sequence 1: length 449, expected 81 from filename
- Issue: 2 prom prokaryotic sequence 2: invalid DNA symbols -
- Issue: 2 prom prokaryotic sequence 2: length 449, expected 81 from filename
- Issue: 3 prom prokaryotic sequence 3: invalid DNA symbols -
- Issue: 3 prom prokaryotic sequence 3: length 449, expected 81 from filename
- Issue: 4 prom prokaryotic sequence 4: invalid DNA symbols -
- Issue: 4 prom prokaryotic sequence 4: length 449, expected 81 from filename
- Issue: 5 prom prokaryotic sequence 5: invalid DNA symbols -
- Issue: 5 prom prokaryotic sequence 5: length 449, expected 81 from filename
- Issue: 6 prom prokaryotic sequence 6: invalid DNA symbols -
- Issue: 6 prom prokaryotic sequence 6: length 449, expected 81 from filename
- Issue: 7 prom prokaryotic sequence 7: invalid DNA symbols -
- Issue: 7 prom prokaryotic sequence 7: length 449, expected 81 from filename
- Issue: 8 prom prokaryotic sequence 8: invalid DNA symbols -
- Issue: 8 prom prokaryotic sequence 8: length 449, expected 81 from filename
- Issue: 9 prom prokaryotic sequence 9: invalid DNA symbols -
- Issue: 9 prom prokaryotic sequence 9: length 449, expected 81 from filename
- Issue: 10 prom prokaryotic sequence 10: invalid DNA symbols -
- Issue: 10 prom prokaryotic sequence 10: length 449, expected 81 from filename
- Issue: 11 prom prokaryotic sequence 11: invalid DNA symbols -
- Issue: 11 prom prokaryotic sequence 11: length 449, expected 81 from filename
- Issue: 12 prom prokaryotic sequence 12: invalid DNA symbols -

### `interim/aligned_fasta/prom-cdbprom-prokaryotic-mycrobacterium_tuberculosis-1772-81.fa`

- Kind: `fasta`
- Records read: 5316
- Length range: 518-518
- Issue: 0 prom prokaryotic sequence 0: invalid DNA symbols -
- Issue: 0 prom prokaryotic sequence 0: length 518, expected 81 from filename
- Issue: 1 prom prokaryotic sequence 1: invalid DNA symbols -
- Issue: 1 prom prokaryotic sequence 1: length 518, expected 81 from filename
- Issue: 2 prom prokaryotic sequence 2: invalid DNA symbols -
- Issue: 2 prom prokaryotic sequence 2: length 518, expected 81 from filename
- Issue: 3 prom prokaryotic sequence 3: invalid DNA symbols -
- Issue: 3 prom prokaryotic sequence 3: length 518, expected 81 from filename
- Issue: 4 prom prokaryotic sequence 4: invalid DNA symbols -
- Issue: 4 prom prokaryotic sequence 4: length 518, expected 81 from filename
- Issue: 5 prom prokaryotic sequence 5: invalid DNA symbols -
- Issue: 5 prom prokaryotic sequence 5: length 518, expected 81 from filename
- Issue: 6 prom prokaryotic sequence 6: invalid DNA symbols -
- Issue: 6 prom prokaryotic sequence 6: length 518, expected 81 from filename
- Issue: 7 prom prokaryotic sequence 7: invalid DNA symbols -
- Issue: 7 prom prokaryotic sequence 7: length 518, expected 81 from filename
- Issue: 8 prom prokaryotic sequence 8: invalid DNA symbols -
- Issue: 8 prom prokaryotic sequence 8: length 518, expected 81 from filename
- Issue: 9 prom prokaryotic sequence 9: invalid DNA symbols -
- Issue: 9 prom prokaryotic sequence 9: length 518, expected 81 from filename
- Issue: 10 prom prokaryotic sequence 10: invalid DNA symbols -
- Issue: 10 prom prokaryotic sequence 10: length 518, expected 81 from filename
- Issue: 11 prom prokaryotic sequence 11: invalid DNA symbols -
- Issue: 11 prom prokaryotic sequence 11: length 518, expected 81 from filename
- Issue: 12 prom prokaryotic sequence 12: invalid DNA symbols -

### `interim/aligned_fasta/prom-cdbprom-prokaryotic-pseudonomas_aeruginosa-2055-81.fa`

- Kind: `fasta`
- Records read: 6165
- Length range: 486-486
- Issue: 0 prom prokaryotic sequence 0: invalid DNA symbols -
- Issue: 0 prom prokaryotic sequence 0: length 486, expected 81 from filename
- Issue: 1 prom prokaryotic sequence 1: invalid DNA symbols -
- Issue: 1 prom prokaryotic sequence 1: length 486, expected 81 from filename
- Issue: 2 prom prokaryotic sequence 2: invalid DNA symbols -
- Issue: 2 prom prokaryotic sequence 2: length 486, expected 81 from filename
- Issue: 3 prom prokaryotic sequence 3: invalid DNA symbols -
- Issue: 3 prom prokaryotic sequence 3: length 486, expected 81 from filename
- Issue: 4 prom prokaryotic sequence 4: invalid DNA symbols -
- Issue: 4 prom prokaryotic sequence 4: length 486, expected 81 from filename
- Issue: 5 prom prokaryotic sequence 5: invalid DNA symbols -
- Issue: 5 prom prokaryotic sequence 5: length 486, expected 81 from filename
- Issue: 6 prom prokaryotic sequence 6: invalid DNA symbols -
- Issue: 6 prom prokaryotic sequence 6: length 486, expected 81 from filename
- Issue: 7 prom prokaryotic sequence 7: invalid DNA symbols -
- Issue: 7 prom prokaryotic sequence 7: length 486, expected 81 from filename
- Issue: 8 prom prokaryotic sequence 8: invalid DNA symbols -
- Issue: 8 prom prokaryotic sequence 8: length 486, expected 81 from filename
- Issue: 9 prom prokaryotic sequence 9: invalid DNA symbols -
- Issue: 9 prom prokaryotic sequence 9: length 486, expected 81 from filename
- Issue: 10 prom prokaryotic sequence 10: invalid DNA symbols -
- Issue: 10 prom prokaryotic sequence 10: length 486, expected 81 from filename
- Issue: 11 prom prokaryotic sequence 11: invalid DNA symbols -
- Issue: 11 prom prokaryotic sequence 11: length 486, expected 81 from filename
- Issue: 12 prom prokaryotic sequence 12: invalid DNA symbols -

### `interim/aligned_fasta/prom-cdbprom-prokaryotic-salmonella_typhimurium-981-81.fa`

- Kind: `fasta`
- Records read: 2943
- Length range: 496-496
- Issue: 0 prom prokaryotic sequence 0: invalid DNA symbols -
- Issue: 0 prom prokaryotic sequence 0: length 496, expected 81 from filename
- Issue: 1 prom prokaryotic sequence 1: invalid DNA symbols -
- Issue: 1 prom prokaryotic sequence 1: length 496, expected 81 from filename
- Issue: 2 prom prokaryotic sequence 2: invalid DNA symbols -
- Issue: 2 prom prokaryotic sequence 2: length 496, expected 81 from filename
- Issue: 3 prom prokaryotic sequence 3: invalid DNA symbols -
- Issue: 3 prom prokaryotic sequence 3: length 496, expected 81 from filename
- Issue: 4 prom prokaryotic sequence 4: invalid DNA symbols -
- Issue: 4 prom prokaryotic sequence 4: length 496, expected 81 from filename
- Issue: 5 prom prokaryotic sequence 5: invalid DNA symbols -
- Issue: 5 prom prokaryotic sequence 5: length 496, expected 81 from filename
- Issue: 6 prom prokaryotic sequence 6: invalid DNA symbols -
- Issue: 6 prom prokaryotic sequence 6: length 496, expected 81 from filename
- Issue: 7 prom prokaryotic sequence 7: invalid DNA symbols -
- Issue: 7 prom prokaryotic sequence 7: length 496, expected 81 from filename
- Issue: 8 prom prokaryotic sequence 8: invalid DNA symbols -
- Issue: 8 prom prokaryotic sequence 8: length 496, expected 81 from filename
- Issue: 9 prom prokaryotic sequence 9: invalid DNA symbols -
- Issue: 9 prom prokaryotic sequence 9: length 496, expected 81 from filename
- Issue: 10 prom prokaryotic sequence 10: invalid DNA symbols -
- Issue: 10 prom prokaryotic sequence 10: length 496, expected 81 from filename
- Issue: 11 prom prokaryotic sequence 11: invalid DNA symbols -
- Issue: 11 prom prokaryotic sequence 11: length 496, expected 81 from filename
- Issue: 12 prom prokaryotic sequence 12: invalid DNA symbols -

### `interim/aligned_fasta/prom-cdbprom-prokaryotic-streptomyces_coelicolor-2611-81.fa`

- Kind: `fasta`
- Records read: 7833
- Length range: 531-531
- Issue: 0 prom prokaryotic sequence 0: invalid DNA symbols -
- Issue: 0 prom prokaryotic sequence 0: length 531, expected 81 from filename
- Issue: 1 prom prokaryotic sequence 1: invalid DNA symbols -
- Issue: 1 prom prokaryotic sequence 1: length 531, expected 81 from filename
- Issue: 2 prom prokaryotic sequence 2: invalid DNA symbols -
- Issue: 2 prom prokaryotic sequence 2: length 531, expected 81 from filename
- Issue: 3 prom prokaryotic sequence 3: invalid DNA symbols -
- Issue: 3 prom prokaryotic sequence 3: length 531, expected 81 from filename
- Issue: 4 prom prokaryotic sequence 4: invalid DNA symbols -
- Issue: 4 prom prokaryotic sequence 4: length 531, expected 81 from filename
- Issue: 5 prom prokaryotic sequence 5: invalid DNA symbols -
- Issue: 5 prom prokaryotic sequence 5: length 531, expected 81 from filename
- Issue: 6 prom prokaryotic sequence 6: invalid DNA symbols -
- Issue: 6 prom prokaryotic sequence 6: length 531, expected 81 from filename
- Issue: 7 prom prokaryotic sequence 7: invalid DNA symbols -
- Issue: 7 prom prokaryotic sequence 7: length 531, expected 81 from filename
- Issue: 8 prom prokaryotic sequence 8: invalid DNA symbols -
- Issue: 8 prom prokaryotic sequence 8: length 531, expected 81 from filename
- Issue: 9 prom prokaryotic sequence 9: invalid DNA symbols -
- Issue: 9 prom prokaryotic sequence 9: length 531, expected 81 from filename
- Issue: 10 prom prokaryotic sequence 10: invalid DNA symbols -
- Issue: 10 prom prokaryotic sequence 10: length 531, expected 81 from filename
- Issue: 11 prom prokaryotic sequence 11: invalid DNA symbols -
- Issue: 11 prom prokaryotic sequence 11: length 531, expected 81 from filename
- Issue: 12 prom prokaryotic sequence 12: invalid DNA symbols -

### `interim/aligned_fasta/prom-cdbprom-prokaryotic-synechocistis-1639-81.fa`

- Kind: `fasta`
- Records read: 4917
- Length range: 620-620
- Issue: 0 prom prokaryotic sequence 0: invalid DNA symbols -
- Issue: 0 prom prokaryotic sequence 0: length 620, expected 81 from filename
- Issue: 1 prom prokaryotic sequence 1: invalid DNA symbols -
- Issue: 1 prom prokaryotic sequence 1: length 620, expected 81 from filename
- Issue: 2 prom prokaryotic sequence 2: invalid DNA symbols -
- Issue: 2 prom prokaryotic sequence 2: length 620, expected 81 from filename
- Issue: 3 prom prokaryotic sequence 3: invalid DNA symbols -
- Issue: 3 prom prokaryotic sequence 3: length 620, expected 81 from filename
- Issue: 4 prom prokaryotic sequence 4: invalid DNA symbols -
- Issue: 4 prom prokaryotic sequence 4: length 620, expected 81 from filename
- Issue: 5 prom prokaryotic sequence 5: invalid DNA symbols -
- Issue: 5 prom prokaryotic sequence 5: length 620, expected 81 from filename
- Issue: 6 prom prokaryotic sequence 6: invalid DNA symbols -
- Issue: 6 prom prokaryotic sequence 6: length 620, expected 81 from filename
- Issue: 7 prom prokaryotic sequence 7: invalid DNA symbols -
- Issue: 7 prom prokaryotic sequence 7: length 620, expected 81 from filename
- Issue: 8 prom prokaryotic sequence 8: invalid DNA symbols -
- Issue: 8 prom prokaryotic sequence 8: length 620, expected 81 from filename
- Issue: 9 prom prokaryotic sequence 9: invalid DNA symbols -
- Issue: 9 prom prokaryotic sequence 9: length 620, expected 81 from filename
- Issue: 10 prom prokaryotic sequence 10: invalid DNA symbols -
- Issue: 10 prom prokaryotic sequence 10: length 620, expected 81 from filename
- Issue: 11 prom prokaryotic sequence 11: invalid DNA symbols -
- Issue: 11 prom prokaryotic sequence 11: length 620, expected 81 from filename
- Issue: 12 prom prokaryotic sequence 12: invalid DNA symbols -

### `interim/aligned_fasta/prom-cnnprom-eukaryotic-Arabidopsis_non_tata-5905-81.fa`

- Kind: `fasta`
- Records read: 17715
- Length range: 984-984
- Issue: FP000001 AT1G01020_1         :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP000001 AT1G01020_1         :+U  EU:NC; range  -200 to    50.: length 984, expected 81 from filename
- Issue: FP000002 AT1G01030_1         :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP000002 AT1G01030_1         :+U  EU:NC; range  -200 to    50.: length 984, expected 81 from filename
- Issue: FP000003 AT1G01040_1         :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP000003 AT1G01040_1         :+U  EU:NC; range  -200 to    50.: length 984, expected 81 from filename
- Issue: FP000004 AT1G01130_1         :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP000004 AT1G01130_1         :+U  EU:NC; range  -200 to    50.: length 984, expected 81 from filename
- Issue: FP000005 AT1G01140_1         :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP000005 AT1G01140_1         :+U  EU:NC; range  -200 to    50.: length 984, expected 81 from filename
- Issue: FP000006 AT1G01160_1         :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP000006 AT1G01160_1         :+U  EU:NC; range  -200 to    50.: length 984, expected 81 from filename
- Issue: FP000007 AT1G01180_1         :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP000007 AT1G01180_1         :+U  EU:NC; range  -200 to    50.: length 984, expected 81 from filename
- Issue: FP000008 AT1G01200_1         :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP000008 AT1G01200_1         :+U  EU:NC; range  -200 to    50.: length 984, expected 81 from filename
- Issue: FP000009 AT1G01210_1         :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP000009 AT1G01210_1         :+U  EU:NC; range  -200 to    50.: length 984, expected 81 from filename
- Issue: FP000010 AT1G01225_1         :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP000010 AT1G01225_1         :+U  EU:NC; range  -200 to    50.: length 984, expected 81 from filename
- Issue: FP000011 AT1G01230_1         :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP000011 AT1G01230_1         :+U  EU:NC; range  -200 to    50.: length 984, expected 81 from filename
- Issue: FP000012 AT1G01290_1         :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP000012 AT1G01290_1         :+U  EU:NC; range  -200 to    50.: length 984, expected 81 from filename
- Issue: FP000013 AT1G01340_1         :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -

### `interim/aligned_fasta/prom-cnnprom-eukaryotic-Arabidopsis_tata-1497-81.fa`

- Kind: `fasta`
- Records read: 4491
- Length range: 609-609
- Issue: FP000001 AT1G01050_1         :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP000001 AT1G01050_1         :+U  EU:NC; range  -200 to    50.: length 609, expected 81 from filename
- Issue: FP000002 AT1G01170_1         :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP000002 AT1G01170_1         :+U  EU:NC; range  -200 to    50.: length 609, expected 81 from filename
- Issue: FP000003 AT1G01480_1         :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP000003 AT1G01480_1         :+U  EU:NC; range  -200 to    50.: length 609, expected 81 from filename
- Issue: FP000004 AT1G01550_1         :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP000004 AT1G01550_1         :+U  EU:NC; range  -200 to    50.: length 609, expected 81 from filename
- Issue: FP000005 AT1G02000_1         :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP000005 AT1G02000_1         :+U  EU:NC; range  -200 to    50.: length 609, expected 81 from filename
- Issue: FP000006 AT1G02205_1         :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP000006 AT1G02205_1         :+U  EU:NC; range  -200 to    50.: length 609, expected 81 from filename
- Issue: FP000007 AT1G02660_1         :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP000007 AT1G02660_1         :+U  EU:NC; range  -200 to    50.: length 609, expected 81 from filename
- Issue: FP000008 AT1G03030_1         :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP000008 AT1G03030_1         :+U  EU:NC; range  -200 to    50.: length 609, expected 81 from filename
- Issue: FP000009 AT1G03160_1         :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP000009 AT1G03160_1         :+U  EU:NC; range  -200 to    50.: length 609, expected 81 from filename
- Issue: FP000010 AT1G03470_1         :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP000010 AT1G03470_1         :+U  EU:NC; range  -200 to    50.: length 609, expected 81 from filename
- Issue: FP000011 AT1G03770_1         :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP000011 AT1G03770_1         :+U  EU:NC; range  -200 to    50.: length 609, expected 81 from filename
- Issue: FP000012 AT1G03790_1         :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP000012 AT1G03790_1         :+U  EU:NC; range  -200 to    50.: length 609, expected 81 from filename
- Issue: FP000013 AT1G03905_1         :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -

### `interim/aligned_fasta/prom-cnnprom-eukaryotic-Human_non_tata-19811-81.fa`

- Kind: `fasta`
- Records read: 59433
- Length range: 1222-1222
- Issue: FP000001 SAMD11_1            :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP000001 SAMD11_1            :+U  EU:NC; range  -200 to    50.: length 1222, expected 81 from filename
- Issue: FP000002 SAMD11_2            :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP000002 SAMD11_2            :+U  EU:NC; range  -200 to    50.: length 1222, expected 81 from filename
- Issue: FP000003 NOC2L_1             :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP000003 NOC2L_1             :+U  EU:NC; range  -200 to    50.: length 1222, expected 81 from filename
- Issue: FP000004 KLHL17_1            :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP000004 KLHL17_1            :+U  EU:NC; range  -200 to    50.: length 1222, expected 81 from filename
- Issue: FP000005 PLEKHN1_1           :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP000005 PLEKHN1_1           :+U  EU:NC; range  -200 to    50.: length 1222, expected 81 from filename
- Issue: FP000006 HES4_1              :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP000006 HES4_1              :+U  EU:NC; range  -200 to    50.: length 1222, expected 81 from filename
- Issue: FP000007 AGRN_1              :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP000007 AGRN_1              :+U  EU:NC; range  -200 to    50.: length 1222, expected 81 from filename
- Issue: FP000008 C1orf159_1          :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP000008 C1orf159_1          :+U  EU:NC; range  -200 to    50.: length 1222, expected 81 from filename
- Issue: FP000009 TTLL10_1            :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP000009 TTLL10_1            :+U  EU:NC; range  -200 to    50.: length 1222, expected 81 from filename
- Issue: FP000010 TNFRSF18_2          :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP000010 TNFRSF18_2          :+U  EU:NC; range  -200 to    50.: length 1222, expected 81 from filename
- Issue: FP000011 TNFRSF18_1          :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP000011 TNFRSF18_1          :+U  EU:NC; range  -200 to    50.: length 1222, expected 81 from filename
- Issue: FP000012 TNFRSF4_1           :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP000012 TNFRSF4_1           :+U  EU:NC; range  -200 to    50.: length 1222, expected 81 from filename
- Issue: FP000013 SDF4_1              :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -

### `interim/aligned_fasta/prom-cnnprom-eukaryotic-Mouse_non_tata-16283-81.fa`

- Kind: `fasta`
- Records read: 48849
- Length range: 1189-1189
- Issue: FP002201 Gmeb2_1             :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP002201 Gmeb2_1             :+U  EU:NC; range  -200 to    50.: length 1189, expected 81 from filename
- Issue: FP011961 Zfp366_1            :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP011961 Zfp366_1            :+U  EU:NC; range  -200 to    50.: length 1189, expected 81 from filename
- Issue: FP011166 Zbtb1_2             :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP011166 Zbtb1_2             :+U  EU:NC; range  -200 to    50.: length 1189, expected 81 from filename
- Issue: FP015245 Naa40_1             :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP015245 Naa40_1             :+U  EU:NC; range  -200 to    50.: length 1189, expected 81 from filename
- Issue: FP013765 Scaf4_2             :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP013765 Scaf4_2             :+U  EU:NC; range  -200 to    50.: length 1189, expected 81 from filename
- Issue: FP002831 Cnn3_1              :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP002831 Cnn3_1              :+U  EU:NC; range  -200 to    50.: length 1189, expected 81 from filename
- Issue: FP015627 Nhlrc2_1            :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP015627 Nhlrc2_1            :+U  EU:NC; range  -200 to    50.: length 1189, expected 81 from filename
- Issue: FP008008 Zfp846_1            :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP008008 Zfp846_1            :+U  EU:NC; range  -200 to    50.: length 1189, expected 81 from filename
- Issue: FP005391 Wbp1_1              :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP005391 Wbp1_1              :+U  EU:NC; range  -200 to    50.: length 1189, expected 81 from filename
- Issue: FP009343 Mobkl2a_1           :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP009343 Mobkl2a_1           :+U  EU:NC; range  -200 to    50.: length 1189, expected 81 from filename
- Issue: FP004957 2810453I06Rik_1     :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP004957 2810453I06Rik_1     :+U  EU:NC; range  -200 to    50.: length 1189, expected 81 from filename
- Issue: FP011808 Zfp759_1            :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: FP011808 Zfp759_1            :+U  EU:NC; range  -200 to    50.: length 1189, expected 81 from filename
- Issue: FP013061 Nfam1_1             :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -

### `interim/aligned_fasta/prom-cnnprom-eukaryotic-Mouse_tata-1255-81.fa`

- Kind: `fasta`
- Records read: 3765
- Length range: 502-502
- Issue: gt;FP000970 Tsc22d1_1           :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: gt;FP000970 Tsc22d1_1           :+U  EU:NC; range  -200 to    50.: length 502, expected 81 from filename
- Issue: gt;FP000885 Sox4_1              :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: gt;FP000885 Sox4_1              :+U  EU:NC; range  -200 to    50.: length 502, expected 81 from filename
- Issue: gt;FP000421 Clec4b1_1           :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: gt;FP000421 Clec4b1_1           :+U  EU:NC; range  -200 to    50.: length 502, expected 81 from filename
- Issue: gt;FP000536 Nlrp6_1             :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: gt;FP000536 Nlrp6_1             :+U  EU:NC; range  -200 to    50.: length 502, expected 81 from filename
- Issue: gt;FP001151 Npas4_1             :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: gt;FP001151 Npas4_1             :+U  EU:NC; range  -200 to    50.: length 502, expected 81 from filename
- Issue: gt;FP000219 Gpsm2_1             :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: gt;FP000219 Gpsm2_1             :+U  EU:NC; range  -200 to    50.: length 502, expected 81 from filename
- Issue: gt;FP000001 Msc_1               :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: gt;FP000001 Msc_1               :+U  EU:NC; range  -200 to    50.: length 502, expected 81 from filename
- Issue: gt;FP000694 Madcam1_1           :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: gt;FP000694 Madcam1_1           :+U  EU:NC; range  -200 to    50.: length 502, expected 81 from filename
- Issue: gt;FP000642 Gcnt3_1             :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: gt;FP000642 Gcnt3_1             :+U  EU:NC; range  -200 to    50.: length 502, expected 81 from filename
- Issue: gt;FP000098 Nr4a2_1             :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: gt;FP000098 Nr4a2_1             :+U  EU:NC; range  -200 to    50.: length 502, expected 81 from filename
- Issue: gt;FP000450 2810007J24Rik_1     :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: gt;FP000450 2810007J24Rik_1     :+U  EU:NC; range  -200 to    50.: length 502, expected 81 from filename
- Issue: gt;FP000413 Magi1_2             :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -
- Issue: gt;FP000413 Magi1_2             :+U  EU:NC; range  -200 to    50.: length 502, expected 81 from filename
- Issue: gt;FP000380 Pds5b_3             :+U  EU:NC; range  -200 to    50.: invalid DNA symbols -

### `interim/aligned_fasta/prom-cnnprom-eukaryotic-Mouse_tata_dbtss-1354-81.fa`

- Kind: `fasta`
- Records read: 4062
- Length range: 484-484
- Issue: 35,1 11640 1 2 NM_009648,NM_001042541 chr11 0 88712817,88725900 16 16 5 88725831 88707148,88707148: invalid DNA symbols -
- Issue: 35,1 11640 1 2 NM_009648,NM_001042541 chr11 0 88712817,88725900 16 16 5 88725831 88707148,88707148: length 484, expected 81 from filename
- Issue: 85,2 380714 2 3 NM_029548 chr11 0 75724528 1 1 1 75751199 75724528: invalid DNA symbols -
- Issue: 85,2 380714 2 3 NM_029548 chr11 0 75724528 1 1 1 75751199 75724528: length 484, expected 81 from filename
- Issue: 104,1 16666 1 1 NM_008470 chr11 0 100110216 1 1 1 100110277 100110204: invalid DNA symbols -
- Issue: 104,1 16666 1 1 NM_008470 chr11 0 100110216 1 1 1 100110277 100110204: length 484, expected 81 from filename
- Issue: 113,1 20304 1 1 NM_013653 chr11 0 83344020 5 5 2 83344019 83343963: invalid DNA symbols -
- Issue: 113,1 20304 1 1 NM_013653 chr11 0 83344020 5 5 2 83344019 83343963: length 484, expected 81 from filename
- Issue: 118,1 16189 1 1 NM_021283 chr11 0 53432167 1 1 1 53430842 53432108: invalid DNA symbols -
- Issue: 118,1 16189 1 1 NM_021283 chr11 0 53432167 1 1 1 53430842 53432108: length 484, expected 81 from filename
- Issue: 153,1 214384 1 2 NM_145136,NM_146386 chr11 0 65083491,65083491 1 2 2 65083491 65083200,65083200: invalid DNA symbols -
- Issue: 153,1 214384 1 2 NM_145136,NM_146386 chr11 0 65083491,65083491 1 2 2 65083491 65083200,65083200: length 484, expected 81 from filename
- Issue: 170,1 665891 1 1 NM_001048196 chr11 0 99489553 0 1 1 99489552 99489496: invalid DNA symbols -
- Issue: 170,1 665891 1 1 NM_001048196 chr11 0 99489553 0 1 1 99489552 99489496: length 484, expected 81 from filename
- Issue: 188,1 18453 1 1 NM_011032 chr11 0 120434250 451 455 193 120434185 120434121: invalid DNA symbols -
- Issue: 188,1 18453 1 1 NM_011032 chr11 0 120434250 451 455 193 120434185 120434121: length 484, expected 81 from filename
- Issue: 221,1 268482 1 1 NM_010661 chr11 0 99283573 1 1 1 99283565 99283530: invalid DNA symbols -
- Issue: 221,1 268482 1 1 NM_010661 chr11 0 99283573 1 1 1 99283565 99283530: length 484, expected 81 from filename
- Issue: 269,1 22373 1 1 NM_011709 chr11 0 6538652 2 3 2 6538649 6538625: invalid DNA symbols -
- Issue: 269,1 22373 1 1 NM_011709 chr11 0 6538652 2 3 2 6538649 6538625: length 484, expected 81 from filename
- Issue: 273,1 12957 1 1 NM_009965 chr11 0 77538795 10 10 10 77538785 77538783: invalid DNA symbols -
- Issue: 273,1 12957 1 1 NM_009965 chr11 0 77538795 10 10 10 77538785 77538783: length 484, expected 81 from filename
- Issue: 274,1 16869 1 2 NM_008498 chr11 0 84339036 0 1 1 84339036 84337677: invalid DNA symbols -
- Issue: 274,1 16869 1 2 NM_008498 chr11 0 84339036 0 1 1 84339036 84337677: length 484, expected 81 from filename
- Issue: 303,1 17285 1 2 NM_010791 chr11 0 101755668 0 3 1 101755676 101755319: invalid DNA symbols -

### `interim/aligned_fasta/prom-cnnprom-prokaryotic-Bacillus-373-81.fa`

- Kind: `fasta`
- Records read: 1119
- Length range: 320-320
- Issue: abnA: invalid DNA symbols -
- Issue: abnA: length 320, expected 81 from filename
- Issue: abrB: invalid DNA symbols -
- Issue: abrB: length 320, expected 81 from filename
- Issue: abrB: invalid DNA symbols -
- Issue: abrB: length 320, expected 81 from filename
- Issue: ackA: invalid DNA symbols -
- Issue: ackA: length 320, expected 81 from filename
- Issue: acsA: invalid DNA symbols -
- Issue: acsA: length 320, expected 81 from filename
- Issue: acuA: invalid DNA symbols -
- Issue: acuA: length 320, expected 81 from filename
- Issue: adaA: invalid DNA symbols -
- Issue: adaA: length 320, expected 81 from filename
- Issue: addB: invalid DNA symbols -
- Issue: addB: length 320, expected 81 from filename
- Issue: ahpC: invalid DNA symbols -
- Issue: ahpC: length 320, expected 81 from filename
- Issue: ald: invalid DNA symbols -
- Issue: ald: length 320, expected 81 from filename
- Issue: alkA: invalid DNA symbols -
- Issue: alkA: length 320, expected 81 from filename
- Issue: alsS: invalid DNA symbols -
- Issue: alsS: length 320, expected 81 from filename
- Issue: amhX: invalid DNA symbols -

### `interim/aligned_fasta/prom-cnnprom-prokaryotic-Ecoli-839-81.fa`

- Kind: `fasta`
- Records read: 2517
- Length range: 426-426
- Issue: ECK120010467__accAp__forward__208411: invalid DNA symbols -
- Issue: ECK120010467__accAp__forward__208411: length 426, expected 81 from filename
- Issue: ECK120010469__accBp__forward__3403162: invalid DNA symbols -
- Issue: ECK120010469__accBp__forward__3403162: length 426, expected 81 from filename
- Issue: ECK120010470__accDp__reverse__2432037: invalid DNA symbols -
- Issue: ECK120010470__accDp__reverse__2432037: length 426, expected 81 from filename
- Issue: ECK120010987__aceBp__forward__4213425: invalid DNA symbols -
- Issue: ECK120010987__aceBp__forward__4213425: length 426, expected 81 from filename
- Issue: ECK120010281__aceEp__forward__122969: invalid DNA symbols -
- Issue: ECK120010281__aceEp__forward__122969: length 426, expected 81 from filename
- Issue: ECK120010670__acnAp2__forward__1333805: invalid DNA symbols -
- Issue: ECK120010670__acnAp2__forward__1333805: length 426, expected 81 from filename
- Issue: ECK120010671__acnBp__forward__131519: invalid DNA symbols -
- Issue: ECK120010671__acnBp__forward__131519: length 426, expected 81 from filename
- Issue: ECK120010720__acpPp__forward__1150798: invalid DNA symbols -
- Issue: ECK120010720__acpPp__forward__1150798: length 426, expected 81 from filename
- Issue: ECK120010736__acrAp__reverse__484922: invalid DNA symbols -
- Issue: ECK120010736__acrAp__reverse__484922: length 426, expected 81 from filename
- Issue: ECK125158030__acrZp__forward__793974: invalid DNA symbols -
- Issue: ECK125158030__acrZp__forward__793974: length 426, expected 81 from filename
- Issue: ECK125134720__adep__forward__3841933: invalid DNA symbols -
- Issue: ECK125134720__adep__forward__3841933: length 426, expected 81 from filename
- Issue: ECK120010777__adiAp__reverse__4338579: invalid DNA symbols -
- Issue: ECK120010777__adiAp__reverse__4338579: length 426, expected 81 from filename
- Issue: ECK120010095__agaRp__reverse__3276725: invalid DNA symbols -

### `interim/aligned_fasta/prom-graphpro-eukaryotic-Human-2339-81.fa`

- Kind: `fasta`
- Records read: 7017
- Length range: 607-607
- Issue: FP001101|PCAT1_1	1: invalid DNA symbols -
- Issue: FP001101|PCAT1_1	1: length 607, expected 81 from filename
- Issue: FP001145|FAM242E_1	1: invalid DNA symbols -
- Issue: FP001145|FAM242E_1	1: length 607, expected 81 from filename
- Issue: FP000461|LINC00870_2	1: invalid DNA symbols -
- Issue: FP000461|LINC00870_2	1: length 607, expected 81 from filename
- Issue: FP000705|C5orf17_1	1: invalid DNA symbols -
- Issue: FP000705|C5orf17_1	1: length 607, expected 81 from filename
- Issue: FP000167|ERLNC1_1	1: invalid DNA symbols -
- Issue: FP000167|ERLNC1_1	1: length 607, expected 81 from filename
- Issue: FP000276|DGUOK-AS1_1	1: invalid DNA symbols -
- Issue: FP000276|DGUOK-AS1_1	1: length 607, expected 81 from filename
- Issue: FP001489|LINC02356_1	1: invalid DNA symbols -
- Issue: FP001489|LINC02356_1	1: length 607, expected 81 from filename
- Issue: FP000452|ADAMTS9-AS2_2	1: invalid DNA symbols -
- Issue: FP000452|ADAMTS9-AS2_2	1: length 607, expected 81 from filename
- Issue: FP002013|LINC01775_1	1: invalid DNA symbols -
- Issue: FP002013|LINC01775_1	1: length 607, expected 81 from filename
- Issue: FP000093|RTCA-AS1_1	1: invalid DNA symbols -
- Issue: FP000093|RTCA-AS1_1	1: length 607, expected 81 from filename
- Issue: FP001698|LINC02249_2	1: invalid DNA symbols -
- Issue: FP001698|LINC02249_2	1: length 607, expected 81 from filename
- Issue: FP002280|LINC01560_1	1: invalid DNA symbols -
- Issue: FP002280|LINC01560_1	1: length 607, expected 81 from filename
- Issue: FP002125|OSER1-DT_1	1: invalid DNA symbols -

### `interim/aligned_fasta/prom-graphpro-eukaryotic-Mouse-1846-81.fa`

- Kind: `fasta`
- Records read: 5538
- Length range: 615-615
- Issue: FP002427|4930594M22Rik_1	1: invalid DNA symbols -
- Issue: FP002427|4930594M22Rik_1	1: length 615, expected 81 from filename
- Issue: FP002184|BB123696_1	1: invalid DNA symbols -
- Issue: FP002184|BB123696_1	1: length 615, expected 81 from filename
- Issue: FP001943|Gm11732_1	1: invalid DNA symbols -
- Issue: FP001943|Gm11732_1	1: length 615, expected 81 from filename
- Issue: FP000938|Gm36406_1	1: invalid DNA symbols -
- Issue: FP000938|Gm36406_1	1: length 615, expected 81 from filename
- Issue: FP000704|1700045H11Rik_1	1: invalid DNA symbols -
- Issue: FP000704|1700045H11Rik_1	1: length 615, expected 81 from filename
- Issue: FP001286|Gm45889_1	1: invalid DNA symbols -
- Issue: FP001286|Gm45889_1	1: length 615, expected 81 from filename
- Issue: FP001112|Gm44659_1	1: invalid DNA symbols -
- Issue: FP001112|Gm44659_1	1: length 615, expected 81 from filename
- Issue: FP001404|Gm31518_1	1: invalid DNA symbols -
- Issue: FP001404|Gm31518_1	1: length 615, expected 81 from filename
- Issue: FP000637|Junos_2	1: invalid DNA symbols -
- Issue: FP000637|Junos_2	1: length 615, expected 81 from filename
- Issue: FP002194|4930451E10Rik_1	1: invalid DNA symbols -
- Issue: FP002194|4930451E10Rik_1	1: length 615, expected 81 from filename
- Issue: FP002814|Six3os1_1	1: invalid DNA symbols -
- Issue: FP002814|Six3os1_1	1: length 615, expected 81 from filename
- Issue: FP002169|Gm34084_1	1: invalid DNA symbols -
- Issue: FP002169|Gm34084_1	1: length 615, expected 81 from filename
- Issue: FP000724|Gm10482_1	1: invalid DNA symbols -

### `interim/aligned_fasta/prom-graphpro-prokaryotic-bacillus_amyloliquefaciens-928-81.fa`

- Kind: `fasta`
- Records read: 2784
- Length range: 464-464
- Issue: CP002927.1 Bacillus amyloliquefaciens XH7, complete genome 396289 (+): invalid DNA symbols -
- Issue: CP002927.1 Bacillus amyloliquefaciens XH7, complete genome 396289 (+): length 464, expected 81 from filename
- Issue: CP002927.1 Bacillus amyloliquefaciens XH7, complete genome 406521 (+): invalid DNA symbols -
- Issue: CP002927.1 Bacillus amyloliquefaciens XH7, complete genome 406521 (+): length 464, expected 81 from filename
- Issue: CP002927.1 Bacillus amyloliquefaciens XH7, complete genome 412016 (+): invalid DNA symbols -
- Issue: CP002927.1 Bacillus amyloliquefaciens XH7, complete genome 412016 (+): length 464, expected 81 from filename
- Issue: CP002927.1 Bacillus amyloliquefaciens XH7, complete genome 413563 (+): invalid DNA symbols -
- Issue: CP002927.1 Bacillus amyloliquefaciens XH7, complete genome 413563 (+): length 464, expected 81 from filename
- Issue: CP002927.1 Bacillus amyloliquefaciens XH7, complete genome 414875 (+): invalid DNA symbols -
- Issue: CP002927.1 Bacillus amyloliquefaciens XH7, complete genome 414875 (+): length 464, expected 81 from filename
- Issue: CP002927.1 Bacillus amyloliquefaciens XH7, complete genome 422499 (+): invalid DNA symbols -
- Issue: CP002927.1 Bacillus amyloliquefaciens XH7, complete genome 422499 (+): length 464, expected 81 from filename
- Issue: CP002927.1 Bacillus amyloliquefaciens XH7, complete genome 424970 (+): invalid DNA symbols -
- Issue: CP002927.1 Bacillus amyloliquefaciens XH7, complete genome 424970 (+): length 464, expected 81 from filename
- Issue: CP002927.1 Bacillus amyloliquefaciens XH7, complete genome 427200 (+): invalid DNA symbols -
- Issue: CP002927.1 Bacillus amyloliquefaciens XH7, complete genome 427200 (+): length 464, expected 81 from filename
- Issue: CP002927.1 Bacillus amyloliquefaciens XH7, complete genome 430332 (+): invalid DNA symbols -
- Issue: CP002927.1 Bacillus amyloliquefaciens XH7, complete genome 430332 (+): length 464, expected 81 from filename
- Issue: CP002927.1 Bacillus amyloliquefaciens XH7, complete genome 433008 (+): invalid DNA symbols -
- Issue: CP002927.1 Bacillus amyloliquefaciens XH7, complete genome 433008 (+): length 464, expected 81 from filename
- Issue: CP002927.1 Bacillus amyloliquefaciens XH7, complete genome 437547 (+): invalid DNA symbols -
- Issue: CP002927.1 Bacillus amyloliquefaciens XH7, complete genome 437547 (+): length 464, expected 81 from filename
- Issue: CP002927.1 Bacillus amyloliquefaciens XH7, complete genome 440088 (+): invalid DNA symbols -
- Issue: CP002927.1 Bacillus amyloliquefaciens XH7, complete genome 440088 (+): length 464, expected 81 from filename
- Issue: CP002927.1 Bacillus amyloliquefaciens XH7, complete genome 440648 (+): invalid DNA symbols -

### `interim/aligned_fasta/prom-graphpro-prokaryotic-campylobacter_jejuni-1346-81.fa`

- Kind: `fasta`
- Records read: 4038
- Length range: 599-599
- Issue: NC_002163.1 Campylobacter jejuni subsp. jejuni NCTC 11168 = ATCC 700819 chromosome, complete genome: invalid DNA symbols -
- Issue: NC_002163.1 Campylobacter jejuni subsp. jejuni NCTC 11168 = ATCC 700819 chromosome, complete genome: length 599, expected 81 from filename
- Issue: NC_002163.1 Campylobacter jejuni subsp. jejuni NCTC 11168 = ATCC 700819 chromosome, complete genome: invalid DNA symbols -
- Issue: NC_002163.1 Campylobacter jejuni subsp. jejuni NCTC 11168 = ATCC 700819 chromosome, complete genome: length 599, expected 81 from filename
- Issue: NC_002163.1 Campylobacter jejuni subsp. jejuni NCTC 11168 = ATCC 700819 chromosome, complete genome: invalid DNA symbols -
- Issue: NC_002163.1 Campylobacter jejuni subsp. jejuni NCTC 11168 = ATCC 700819 chromosome, complete genome: length 599, expected 81 from filename
- Issue: NC_002163.1 Campylobacter jejuni subsp. jejuni NCTC 11168 = ATCC 700819 chromosome, complete genome: invalid DNA symbols -
- Issue: NC_002163.1 Campylobacter jejuni subsp. jejuni NCTC 11168 = ATCC 700819 chromosome, complete genome: length 599, expected 81 from filename
- Issue: NC_002163.1 Campylobacter jejuni subsp. jejuni NCTC 11168 = ATCC 700819 chromosome, complete genome: invalid DNA symbols -
- Issue: NC_002163.1 Campylobacter jejuni subsp. jejuni NCTC 11168 = ATCC 700819 chromosome, complete genome: length 599, expected 81 from filename
- Issue: NC_002163.1 Campylobacter jejuni subsp. jejuni NCTC 11168 = ATCC 700819 chromosome, complete genome: invalid DNA symbols -
- Issue: NC_002163.1 Campylobacter jejuni subsp. jejuni NCTC 11168 = ATCC 700819 chromosome, complete genome: length 599, expected 81 from filename
- Issue: NC_002163.1 Campylobacter jejuni subsp. jejuni NCTC 11168 = ATCC 700819 chromosome, complete genome: invalid DNA symbols -
- Issue: NC_002163.1 Campylobacter jejuni subsp. jejuni NCTC 11168 = ATCC 700819 chromosome, complete genome: length 599, expected 81 from filename
- Issue: NC_002163.1 Campylobacter jejuni subsp. jejuni NCTC 11168 = ATCC 700819 chromosome, complete genome: invalid DNA symbols -
- Issue: NC_002163.1 Campylobacter jejuni subsp. jejuni NCTC 11168 = ATCC 700819 chromosome, complete genome: length 599, expected 81 from filename
- Issue: NC_002163.1 Campylobacter jejuni subsp. jejuni NCTC 11168 = ATCC 700819 chromosome, complete genome: invalid DNA symbols -
- Issue: NC_002163.1 Campylobacter jejuni subsp. jejuni NCTC 11168 = ATCC 700819 chromosome, complete genome: length 599, expected 81 from filename
- Issue: NC_002163.1 Campylobacter jejuni subsp. jejuni NCTC 11168 = ATCC 700819 chromosome, complete genome: invalid DNA symbols -
- Issue: NC_002163.1 Campylobacter jejuni subsp. jejuni NCTC 11168 = ATCC 700819 chromosome, complete genome: length 599, expected 81 from filename
- Issue: NC_002163.1 Campylobacter jejuni subsp. jejuni NCTC 11168 = ATCC 700819 chromosome, complete genome: invalid DNA symbols -
- Issue: NC_002163.1 Campylobacter jejuni subsp. jejuni NCTC 11168 = ATCC 700819 chromosome, complete genome: length 599, expected 81 from filename
- Issue: NC_002163.1 Campylobacter jejuni subsp. jejuni NCTC 11168 = ATCC 700819 chromosome, complete genome: invalid DNA symbols -
- Issue: NC_002163.1 Campylobacter jejuni subsp. jejuni NCTC 11168 = ATCC 700819 chromosome, complete genome: length 599, expected 81 from filename
- Issue: NC_002163.1 Campylobacter jejuni subsp. jejuni NCTC 11168 = ATCC 700819 chromosome, complete genome: invalid DNA symbols -

### `interim/aligned_fasta/prom-graphpro-prokaryotic-clostridium_phytofermentans-503-81.fa`

- Kind: `fasta`
- Records read: 1509
- Length range: 405-405
- Issue: NC_000922.1 Chlamydophila pneumoniae CWL029 chromosome, complete genome 389390 (+): invalid DNA symbols -
- Issue: NC_000922.1 Chlamydophila pneumoniae CWL029 chromosome, complete genome 389390 (+): length 405, expected 81 from filename
- Issue: NC_000922.1 Chlamydophila pneumoniae CWL029 chromosome, complete genome 771173 (+): invalid DNA symbols -
- Issue: NC_000922.1 Chlamydophila pneumoniae CWL029 chromosome, complete genome 771173 (+): length 405, expected 81 from filename
- Issue: NC_000922.1 Chlamydophila pneumoniae CWL029 chromosome, complete genome 1083885 (+): invalid DNA symbols -
- Issue: NC_000922.1 Chlamydophila pneumoniae CWL029 chromosome, complete genome 1083885 (+): length 405, expected 81 from filename
- Issue: NC_000922.1 Chlamydophila pneumoniae CWL029 chromosome, complete genome 466449 (+): invalid DNA symbols -
- Issue: NC_000922.1 Chlamydophila pneumoniae CWL029 chromosome, complete genome 466449 (+): length 405, expected 81 from filename
- Issue: NC_000922.1 Chlamydophila pneumoniae CWL029 chromosome, complete genome 742882 (+): invalid DNA symbols -
- Issue: NC_000922.1 Chlamydophila pneumoniae CWL029 chromosome, complete genome 742882 (+): length 405, expected 81 from filename
- Issue: NC_000922.1 Chlamydophila pneumoniae CWL029 chromosome, complete genome 334669 (+): invalid DNA symbols -
- Issue: NC_000922.1 Chlamydophila pneumoniae CWL029 chromosome, complete genome 334669 (+): length 405, expected 81 from filename
- Issue: NC_000922.1 Chlamydophila pneumoniae CWL029 chromosome, complete genome 265864 (+): invalid DNA symbols -
- Issue: NC_000922.1 Chlamydophila pneumoniae CWL029 chromosome, complete genome 265864 (+): length 405, expected 81 from filename
- Issue: NC_000922.1 Chlamydophila pneumoniae CWL029 chromosome, complete genome 400970 (+): invalid DNA symbols -
- Issue: NC_000922.1 Chlamydophila pneumoniae CWL029 chromosome, complete genome 400970 (+): length 405, expected 81 from filename
- Issue: NC_000922.1 Chlamydophila pneumoniae CWL029 chromosome, complete genome 28512 (+): invalid DNA symbols -
- Issue: NC_000922.1 Chlamydophila pneumoniae CWL029 chromosome, complete genome 28512 (+): length 405, expected 81 from filename
- Issue: NC_000922.1 Chlamydophila pneumoniae CWL029 chromosome, complete genome 345241 (+): invalid DNA symbols -
- Issue: NC_000922.1 Chlamydophila pneumoniae CWL029 chromosome, complete genome 345241 (+): length 405, expected 81 from filename
- Issue: NC_000922.1 Chlamydophila pneumoniae CWL029 chromosome, complete genome 1020551 (+): invalid DNA symbols -
- Issue: NC_000922.1 Chlamydophila pneumoniae CWL029 chromosome, complete genome 1020551 (+): length 405, expected 81 from filename
- Issue: NC_000922.1 Chlamydophila pneumoniae CWL029 chromosome, complete genome 815043 (+): invalid DNA symbols -
- Issue: NC_000922.1 Chlamydophila pneumoniae CWL029 chromosome, complete genome 815043 (+): length 405, expected 81 from filename
- Issue: NC_000922.1 Chlamydophila pneumoniae CWL029 chromosome, complete genome 371467 (+): invalid DNA symbols -

### `interim/aligned_fasta/prom-graphpro-prokaryotic-escherichia_coli-2519-81.fa`

- Kind: `fasta`
- Records read: 7557
- Length range: 735-735
- Issue: NC_000913.3 Escherichia coli str. K-12 substr. MG1655, complete genome 2363410 (+): invalid DNA symbols -
- Issue: NC_000913.3 Escherichia coli str. K-12 substr. MG1655, complete genome 2363410 (+): length 735, expected 81 from filename
- Issue: NC_000913.3 Escherichia coli str. K-12 substr. MG1655, complete genome 3019259 (+): invalid DNA symbols -
- Issue: NC_000913.3 Escherichia coli str. K-12 substr. MG1655, complete genome 3019259 (+): length 735, expected 81 from filename
- Issue: NC_000913.3 Escherichia coli str. K-12 substr. MG1655, complete genome 1876476 (+): invalid DNA symbols -
- Issue: NC_000913.3 Escherichia coli str. K-12 substr. MG1655, complete genome 1876476 (+): length 735, expected 81 from filename
- Issue: NC_000913.3 Escherichia coli str. K-12 substr. MG1655, complete genome 452402 (+): invalid DNA symbols -
- Issue: NC_000913.3 Escherichia coli str. K-12 substr. MG1655, complete genome 452402 (+): length 735, expected 81 from filename
- Issue: NC_000913.3 Escherichia coli str. K-12 substr. MG1655, complete genome 4609589 (+): invalid DNA symbols -
- Issue: NC_000913.3 Escherichia coli str. K-12 substr. MG1655, complete genome 4609589 (+): length 735, expected 81 from filename
- Issue: NC_000913.3 Escherichia coli str. K-12 substr. MG1655, complete genome 1668722 (+): invalid DNA symbols -
- Issue: NC_000913.3 Escherichia coli str. K-12 substr. MG1655, complete genome 1668722 (+): length 735, expected 81 from filename
- Issue: NC_000913.3 Escherichia coli str. K-12 substr. MG1655, complete genome 1104050 (+): invalid DNA symbols -
- Issue: NC_000913.3 Escherichia coli str. K-12 substr. MG1655, complete genome 1104050 (+): length 735, expected 81 from filename
- Issue: NC_000913.3 Escherichia coli str. K-12 substr. MG1655, complete genome 3830237 (+): invalid DNA symbols -
- Issue: NC_000913.3 Escherichia coli str. K-12 substr. MG1655, complete genome 3830237 (+): length 735, expected 81 from filename
- Issue: NC_000913.3 Escherichia coli str. K-12 substr. MG1655, complete genome 158206 (+): invalid DNA symbols -
- Issue: NC_000913.3 Escherichia coli str. K-12 substr. MG1655, complete genome 158206 (+): length 735, expected 81 from filename
- Issue: NC_000913.3 Escherichia coli str. K-12 substr. MG1655, complete genome 4111794 (+): invalid DNA symbols -
- Issue: NC_000913.3 Escherichia coli str. K-12 substr. MG1655, complete genome 4111794 (+): length 735, expected 81 from filename
- Issue: NC_000913.3 Escherichia coli str. K-12 substr. MG1655, complete genome 2227949 (+): invalid DNA symbols -
- Issue: NC_000913.3 Escherichia coli str. K-12 substr. MG1655, complete genome 2227949 (+): length 735, expected 81 from filename
- Issue: NC_000913.3 Escherichia coli str. K-12 substr. MG1655, complete genome 1982115 (+): invalid DNA symbols -
- Issue: NC_000913.3 Escherichia coli str. K-12 substr. MG1655, complete genome 1982115 (+): length 735, expected 81 from filename
- Issue: NC_000913.3 Escherichia coli str. K-12 substr. MG1655, complete genome 2136501 (+): invalid DNA symbols -

### `interim/aligned_fasta/prom-graphpro-prokaryotic-leptospira_interrogans-2847-81.fa`

- Kind: `fasta`
- Records read: 8541
- Length range: 624-624
- Issue: NZ_LT962963.1 Leptospira interrogans serovar Manilae isolate L495 chromosome LMANV2, whole genome s: invalid DNA symbols -
- Issue: NZ_LT962963.1 Leptospira interrogans serovar Manilae isolate L495 chromosome LMANV2, whole genome s: length 624, expected 81 from filename
- Issue: NZ_LT962963.1 Leptospira interrogans serovar Manilae isolate L495 chromosome LMANV2, whole genome s: invalid DNA symbols -
- Issue: NZ_LT962963.1 Leptospira interrogans serovar Manilae isolate L495 chromosome LMANV2, whole genome s: length 624, expected 81 from filename
- Issue: NZ_LT962963.1 Leptospira interrogans serovar Manilae isolate L495 chromosome LMANV2, whole genome s: invalid DNA symbols -
- Issue: NZ_LT962963.1 Leptospira interrogans serovar Manilae isolate L495 chromosome LMANV2, whole genome s: length 624, expected 81 from filename
- Issue: NZ_LT962963.1 Leptospira interrogans serovar Manilae isolate L495 chromosome LMANV2, whole genome s: invalid DNA symbols -
- Issue: NZ_LT962963.1 Leptospira interrogans serovar Manilae isolate L495 chromosome LMANV2, whole genome s: length 624, expected 81 from filename
- Issue: NZ_LT962963.1 Leptospira interrogans serovar Manilae isolate L495 chromosome LMANV2, whole genome s: invalid DNA symbols -
- Issue: NZ_LT962963.1 Leptospira interrogans serovar Manilae isolate L495 chromosome LMANV2, whole genome s: length 624, expected 81 from filename
- Issue: NZ_LT962963.1 Leptospira interrogans serovar Manilae isolate L495 chromosome LMANV2, whole genome s: invalid DNA symbols -
- Issue: NZ_LT962963.1 Leptospira interrogans serovar Manilae isolate L495 chromosome LMANV2, whole genome s: length 624, expected 81 from filename
- Issue: NZ_LT962963.1 Leptospira interrogans serovar Manilae isolate L495 chromosome LMANV2, whole genome s: invalid DNA symbols -
- Issue: NZ_LT962963.1 Leptospira interrogans serovar Manilae isolate L495 chromosome LMANV2, whole genome s: length 624, expected 81 from filename
- Issue: NZ_LT962963.1 Leptospira interrogans serovar Manilae isolate L495 chromosome LMANV2, whole genome s: invalid DNA symbols -
- Issue: NZ_LT962963.1 Leptospira interrogans serovar Manilae isolate L495 chromosome LMANV2, whole genome s: length 624, expected 81 from filename
- Issue: NZ_LT962963.1 Leptospira interrogans serovar Manilae isolate L495 chromosome LMANV2, whole genome s: invalid DNA symbols -
- Issue: NZ_LT962963.1 Leptospira interrogans serovar Manilae isolate L495 chromosome LMANV2, whole genome s: length 624, expected 81 from filename
- Issue: NZ_LT962963.1 Leptospira interrogans serovar Manilae isolate L495 chromosome LMANV2, whole genome s: invalid DNA symbols -
- Issue: NZ_LT962963.1 Leptospira interrogans serovar Manilae isolate L495 chromosome LMANV2, whole genome s: length 624, expected 81 from filename
- Issue: NZ_LT962963.1 Leptospira interrogans serovar Manilae isolate L495 chromosome LMANV2, whole genome s: invalid DNA symbols -
- Issue: NZ_LT962963.1 Leptospira interrogans serovar Manilae isolate L495 chromosome LMANV2, whole genome s: length 624, expected 81 from filename
- Issue: NZ_LT962963.1 Leptospira interrogans serovar Manilae isolate L495 chromosome LMANV2, whole genome s: invalid DNA symbols -
- Issue: NZ_LT962963.1 Leptospira interrogans serovar Manilae isolate L495 chromosome LMANV2, whole genome s: length 624, expected 81 from filename
- Issue: NZ_LT962963.1 Leptospira interrogans serovar Manilae isolate L495 chromosome LMANV2, whole genome s: invalid DNA symbols -

### `interim/aligned_fasta/prom-graphpro-prokaryotic-rhodobacter_capsulatus-3607-81.fa`

- Kind: `fasta`
- Records read: 10821
- Length range: 721-721
- Issue: NC_014034.1 Rhodobacter capsulatus SB 1003, complete genome 2641867 (+): invalid DNA symbols -
- Issue: NC_014034.1 Rhodobacter capsulatus SB 1003, complete genome 2641867 (+): length 721, expected 81 from filename
- Issue: NC_014034.1 Rhodobacter capsulatus SB 1003, complete genome 3703907 (+): invalid DNA symbols -
- Issue: NC_014034.1 Rhodobacter capsulatus SB 1003, complete genome 3703907 (+): length 721, expected 81 from filename
- Issue: NC_014034.1 Rhodobacter capsulatus SB 1003, complete genome 3351025 (+): invalid DNA symbols -
- Issue: NC_014034.1 Rhodobacter capsulatus SB 1003, complete genome 3351025 (+): length 721, expected 81 from filename
- Issue: NC_014034.1 Rhodobacter capsulatus SB 1003, complete genome 1872972 (+): invalid DNA symbols -
- Issue: NC_014034.1 Rhodobacter capsulatus SB 1003, complete genome 1872972 (+): length 721, expected 81 from filename
- Issue: NC_014034.1 Rhodobacter capsulatus SB 1003, complete genome 47781 (+): invalid DNA symbols -
- Issue: NC_014034.1 Rhodobacter capsulatus SB 1003, complete genome 47781 (+): length 721, expected 81 from filename
- Issue: NC_014034.1 Rhodobacter capsulatus SB 1003, complete genome 1726455 (+): invalid DNA symbols -
- Issue: NC_014034.1 Rhodobacter capsulatus SB 1003, complete genome 1726455 (+): length 721, expected 81 from filename
- Issue: NC_014034.1 Rhodobacter capsulatus SB 1003, complete genome 107468 (+): invalid DNA symbols -
- Issue: NC_014034.1 Rhodobacter capsulatus SB 1003, complete genome 107468 (+): length 721, expected 81 from filename
- Issue: NC_014034.1 Rhodobacter capsulatus SB 1003, complete genome 2400737 (+): invalid DNA symbols -
- Issue: NC_014034.1 Rhodobacter capsulatus SB 1003, complete genome 2400737 (+): length 721, expected 81 from filename
- Issue: NC_014034.1 Rhodobacter capsulatus SB 1003, complete genome 3089312 (+): invalid DNA symbols -
- Issue: NC_014034.1 Rhodobacter capsulatus SB 1003, complete genome 3089312 (+): length 721, expected 81 from filename
- Issue: NC_014034.1 Rhodobacter capsulatus SB 1003, complete genome 2438116 (+): invalid DNA symbols -
- Issue: NC_014034.1 Rhodobacter capsulatus SB 1003, complete genome 2438116 (+): length 721, expected 81 from filename
- Issue: NC_014034.1 Rhodobacter capsulatus SB 1003, complete genome 2055599 (+): invalid DNA symbols -
- Issue: NC_014034.1 Rhodobacter capsulatus SB 1003, complete genome 2055599 (+): length 721, expected 81 from filename
- Issue: NC_014034.1 Rhodobacter capsulatus SB 1003, complete genome 295619 (+): invalid DNA symbols -
- Issue: NC_014034.1 Rhodobacter capsulatus SB 1003, complete genome 295619 (+): length 721, expected 81 from filename
- Issue: NC_014034.1 Rhodobacter capsulatus SB 1003, complete genome 583270 (+): invalid DNA symbols -

### `interim/cropped_fasta/nonprom-cnnprom-eukaryotic-Arabidopsis_non_tata-11459-81.fa`

- Kind: `fasta`
- Records read: 45836
- Length range: 81-81
- Issue: hypothetical protein, T1E4.10                                                 [AC069299 ]: invalid DNA symbols N
- Issue: hypothetical protein, T1E4.10                                                 [AC069299 ]: invalid DNA symbols N
- Issue: hypothetical protein, T1E4.10                                                 [AC069299 ]: invalid DNA symbols N
- Issue: hypothetical protein, T1E4.10                                                 [AC069299 ]: invalid DNA symbols N

### `interim/cropped_fasta/nonprom-graphpro-prokaryotic-leptospira_interrogans-2116-81.fa`

- Kind: `fasta`
- Records read: 8464
- Length range: 81-81
- Issue: NZ_LT962963.1:c4614703-1 Leptospira interrogans serovar Manilae isolate L495 chromosome LMANV2, who: invalid DNA symbols N
- Issue: NZ_LT962963.1:c4614703-1 Leptospira interrogans serovar Manilae isolate L495 chromosome LMANV2, who: invalid DNA symbols N
- Issue: NZ_LT962963.1:c4614703-1 Leptospira interrogans serovar Manilae isolate L495 chromosome LMANV2, who: invalid DNA symbols N
- Issue: NZ_LT962963.1:c4614703-1 Leptospira interrogans serovar Manilae isolate L495 chromosome LMANV2, who: invalid DNA symbols N

### `interim/cropped_fasta/prom-bhandari-eukaryotic-Human_promoter-61516-81.fa`

- Kind: `fasta`
- Records read: 246064
- Length range: 81-81
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_152230.4_up_700_chr10_58267935_r range=chr10:58267635-58268634 : invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001109809.2_up_700_chr6_GL000250v2_alt_938842_r range=chr6_GL00: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001286633.1_up_700_chr6_GL000250v2_alt_1393524_f range=chr6_GL0: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_005803.3_up_700_chr6_GL000250v2_alt_2060007_r range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001318875.1_up_700_chr6_GL000250v2_alt_2060007_r range=chr6_GL0: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001202523.1_up_700_chr6_GL000250v2_alt_2213865_f range=chr6_GL0: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_004640.6_up_700_chr6_GL000250v2_alt_2871734_r range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_080598.5_up_700_chr6_GL000250v2_alt_2871734_r range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NR_037853.1_up_700_chr6_GL000250v2_alt_2871734_r range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_005104.3_up_700_chr6_GL000252v2_alt_4220680_f range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001113182.2_up_700_chr6_GL000252v2_alt_4220680_f range=chr6_GL0: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001199456.1_up_700_chr6_GL000252v2_alt_4220680_f range=chr6_GL0: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001291986.1_up_700_chr6_GL000252v2_alt_4220680_f range=chr6_GL0: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001242783.1_up_700_chr6_GL000254v2_alt_1557368_r range=chr6_GL0: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_003449.4_up_700_chr6_GL000254v2_alt_1557368_r range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NR_040662.1_up_700_chr6_GL000254v2_alt_2805619_f range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_021177.4_up_700_chr6_GL000254v2_alt_3148875_r range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_004159.4_up_700_chr6_GL000254v2_alt_4143995_r range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001318908.1_up_700_chr6_GL000256v2_alt_2461239_f range=chr6_GL0: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_007109.2_up_700_chr6_GL000256v2_alt_2461241_f range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001077511.1_up_700_chr6_GL000256v2_alt_2461241_f range=chr6_GL0: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_006295.2_up_700_chr6_GL000256v2_alt_3094271_r range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_019105.6_up_700_chr6_GL000256v2_alt_3369634_r range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001281971.1_up_700_chr19_GL949750v2_alt_818933_f range=chr19_GL: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001281972.1_up_700_chr19_GL949750v2_alt_818933_f range=chr19_GL: invalid DNA symbols N

### `interim/cropped_fasta/prom-bhandari-eukaryotic-Plant_promoters-106515-81.fa`

- Kind: `fasta`
- Records read: 319545
- Length range: 81-81
- Issue: mm10_ct_tbncbiRefSeq_7481_XR_880814.1_up_700_chr1_183063133_r range=chr1:183062833-183063832 5'pad=: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XR_880812.1_up_700_chr1_183063133_r range=chr1:183062833-183063832 5'pad=: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_011249734.2_up_700_chr1_183413223_f range=chr1:183413223-183414222 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_011249736.2_up_700_chr1_183413223_f range=chr1:183413223-183414222 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_011249735.2_up_700_chr1_183413223_f range=chr1:183413223-183414222 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XR_390305.3_up_700_chr2_176319923_r range=chr2:176319623-176320622 5'pad=: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XR_001784558.1_up_700_chr4_42386158_r range=chr4:42385858-42386857 5'pad=: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_006538844.3_up_700_chr4_156253425_r range=chr4:156253125-156254124 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_006538839.3_up_700_chr4_156256012_r range=chr4:156255712-156256711 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_011240922.1_up_700_chr5_137177038_r range=chr5:137176738-137177737 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_011249870.2_up_700_chr9_124442901_r range=chr9:124442601-124443600 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_NM_001308488.1_up_700_chrX_170671944_f range=chrX:170671944-170672943 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XR_880814.1_up_700_chr1_183063133_r range=chr1:183062833-183063832 5'pad=: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XR_880812.1_up_700_chr1_183063133_r range=chr1:183062833-183063832 5'pad=: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_011249734.2_up_700_chr1_183413223_f range=chr1:183413223-183414222 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_011249736.2_up_700_chr1_183413223_f range=chr1:183413223-183414222 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_011249735.2_up_700_chr1_183413223_f range=chr1:183413223-183414222 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XR_390305.3_up_700_chr2_176319923_r range=chr2:176319623-176320622 5'pad=: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XR_001784558.1_up_700_chr4_42386158_r range=chr4:42385858-42386857 5'pad=: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_006538844.3_up_700_chr4_156253425_r range=chr4:156253125-156254124 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_006538839.3_up_700_chr4_156256012_r range=chr4:156255712-156256711 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_011240922.1_up_700_chr5_137177038_r range=chr5:137176738-137177737 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_011249870.2_up_700_chr9_124442901_r range=chr9:124442601-124443600 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_NM_001308488.1_up_700_chrX_170671944_f range=chrX:170671944-170672943 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XR_880814.1_up_700_chr1_183063133_r range=chr1:183062833-183063832 5'pad=: invalid DNA symbols N

### `interim/cropped_fasta/prom-cdbprom-prokaryotic-helicobacter_pylori-714-81.fa`

- Kind: `fasta`
- Records read: 2142
- Length range: 81-81
- Issue: 53 prom prokaryotic sequence 53: invalid DNA symbols Y
- Issue: 220 prom prokaryotic sequence 220: invalid DNA symbols Y
- Issue: 53 prom prokaryotic sequence 53: invalid DNA symbols Y
- Issue: 220 prom prokaryotic sequence 220: invalid DNA symbols Y
- Issue: 53 prom prokaryotic sequence 53: invalid DNA symbols Y
- Issue: 220 prom prokaryotic sequence 220: invalid DNA symbols Y

### `interim/cropped_fasta/prom-cdbprom-prokaryotic-pseudonomas_aeruginosa-2055-81.fa`

- Kind: `fasta`
- Records read: 6165
- Length range: 81-81
- Issue: 363 prom prokaryotic sequence 363: invalid DNA symbols N
- Issue: 363 prom prokaryotic sequence 363: invalid DNA symbols N
- Issue: 363 prom prokaryotic sequence 363: invalid DNA symbols N

### `interim/cropped_fasta/prom-cnnprom-eukaryotic-Human_non_tata-19811-81.fa`

- Kind: `fasta`
- Records read: 59433
- Length range: 81-81
- Issue: FP009820 IPMK_1              :+U  EU:NC; range  -200 to    50.: invalid DNA symbols N
- Issue: FP009820 IPMK_1              :+U  EU:NC; range  -200 to    50.: invalid DNA symbols N
- Issue: FP009820 IPMK_1              :+U  EU:NC; range  -200 to    50.: invalid DNA symbols N

### `interim/cropped_fasta/prom-graphpro-prokaryotic-leptospira_interrogans-2847-81.fa`

- Kind: `fasta`
- Records read: 8541
- Length range: 81-81
- Issue: NZ_LT962963.1 Leptospira interrogans serovar Manilae isolate L495 chromosome LMANV2, whole genome s: invalid DNA symbols N
- Issue: NZ_LT962963.1 Leptospira interrogans serovar Manilae isolate L495 chromosome LMANV2, whole genome s: invalid DNA symbols N
- Issue: NZ_LT962963.1 Leptospira interrogans serovar Manilae isolate L495 chromosome LMANV2, whole genome s: invalid DNA symbols N
- Issue: NZ_LT962963.1 Leptospira interrogans serovar Manilae isolate L495 chromosome LMANV2, whole genome s: invalid DNA symbols N
- Issue: NZ_LT962963.1 Leptospira interrogans serovar Manilae isolate L495 chromosome LMANV2, whole genome s: invalid DNA symbols N
- Issue: NZ_LT962963.1 Leptospira interrogans serovar Manilae isolate L495 chromosome LMANV2, whole genome s: invalid DNA symbols N

### `interim/fasta/nonprom-cnnprom-eukaryotic-Arabidopsis_non_tata-11459-251.fa`

- Kind: `fasta`
- Records read: 11459
- Length range: 251-251
- Issue: hypothetical protein, T1E4.10                                                 [AC069299 ]: invalid DNA symbols N
- Issue: wall-associated kinase 4, wak4                                                [AJ009695 ]: invalid DNA symbols N

### `interim/fasta/nonprom-graphpro-prokaryotic-leptospira_interrogans-2116-81.fa`

- Kind: `fasta`
- Records read: 2116
- Length range: 81-81
- Issue: NZ_LT962963.1:c4614703-1 Leptospira interrogans serovar Manilae isolate L495 chromosome LMANV2, who: invalid DNA symbols N

### `interim/fasta/prom-bhandari-eukaryotic-Human_promoter-61516-1000.fa`

- Kind: `fasta`
- Records read: 61516
- Length range: 1000-1000
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001306068.1_up_700_chr4_190173074_f range=chr4:190173074-190174: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001293798.1_up_700_chr4_190173074_f range=chr4:190173074-190174: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_YP_003024026.1_up_700_chrM_2607_f range=chrM:2607-3606 5'pad=0 3'p: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_152230.4_up_700_chr10_58267935_r range=chr10:58267635-58268634 : invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NR_134504.1_up_700_chr20_29447817_f range=chr20:29447817-29448816 : invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NR_128711.1_up_700_chr21_8986299_f range=chr21:8986299-8987298 5'p: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NR_131192.1_up_700_chr21_42615096_r range=chr21:42614796-42615795 : invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001109809.2_up_700_chr6_GL000250v2_alt_938842_r range=chr6_GL00: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001286633.1_up_700_chr6_GL000250v2_alt_1393524_f range=chr6_GL0: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_138700.4_up_700_chr6_GL000250v2_alt_1394129_f range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_005803.3_up_700_chr6_GL000250v2_alt_2060007_r range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001318875.1_up_700_chr6_GL000250v2_alt_2060007_r range=chr6_GL0: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001202523.1_up_700_chr6_GL000250v2_alt_2213865_f range=chr6_GL0: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001954.4_up_700_chr6_GL000250v2_alt_2214420_f range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_013993.2_up_700_chr6_GL000250v2_alt_2214428_f range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_004640.6_up_700_chr6_GL000250v2_alt_2871734_r range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_080598.5_up_700_chr6_GL000250v2_alt_2871734_r range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NR_037853.1_up_700_chr6_GL000250v2_alt_2871734_r range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_000594.3_up_700_chr6_GL000250v2_alt_2908408_f range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001289413.1_up_700_chr6_GL000250v2_alt_3229829_r range=chr6_GL0: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_025256.6_up_700_chr6_GL000250v2_alt_3230330_r range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_006709.4_up_700_chr6_GL000250v2_alt_3230330_r range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_170769.2_up_700_chr6_GL000252v2_alt_1331766_r range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_025236.3_up_700_chr6_GL000252v2_alt_1331768_r range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_005104.3_up_700_chr6_GL000252v2_alt_4220680_f range=chr6_GL0002: invalid DNA symbols N

### `interim/fasta/prom-bhandari-eukaryotic-Plant_promoters-106515-1000.fa`

- Kind: `fasta`
- Records read: 106515
- Length range: 1000-1000
- Issue: mm10_ct_tbncbiRefSeq_7481_XR_880814.1_up_700_chr1_183063133_r range=chr1:183062833-183063832 5'pad=: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XR_880812.1_up_700_chr1_183063133_r range=chr1:183062833-183063832 5'pad=: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_NM_181732.4_up_700_chr1_183296360_f range=chr1:183296360-183297359 5'pad=: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_006535598.3_up_700_chr1_183296608_r range=chr1:183296308-183297307 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_011249734.2_up_700_chr1_183413223_f range=chr1:183413223-183414222 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_011249736.2_up_700_chr1_183413223_f range=chr1:183413223-183414222 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_011249735.2_up_700_chr1_183413223_f range=chr1:183413223-183414222 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XR_390305.3_up_700_chr2_176319923_r range=chr2:176319623-176320622 5'pad=: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_003688790.3_up_700_chr4_34311571_r range=chr4:34311271-34312270 5'pad=: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XR_001784558.1_up_700_chr4_42386158_r range=chr4:42385858-42386857 5'pad=: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_NM_198305.2_up_700_chr4_156234858_r range=chr4:156234558-156235557 5'pad=: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_006538844.3_up_700_chr4_156253425_r range=chr4:156253125-156254124 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_017320188.1_up_700_chr4_156254542_r range=chr4:156254242-156255241 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_017320187.1_up_700_chr4_156254542_r range=chr4:156254242-156255241 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XR_001784137.1_up_700_chr4_156254542_r range=chr4:156254242-156255241 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_006538846.3_up_700_chr4_156254580_r range=chr4:156254280-156255279 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_NM_001110516.1_up_700_chr4_156255339_r range=chr4:156255039-156256038 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_006538841.3_up_700_chr4_156255380_r range=chr4:156255080-156256079 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_006538838.3_up_700_chr4_156255382_r range=chr4:156255082-156256081 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_006538840.3_up_700_chr4_156255382_r range=chr4:156255082-156256081 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_006538843.3_up_700_chr4_156255382_r range=chr4:156255082-156256081 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_006538842.2_up_700_chr4_156255942_r range=chr4:156255642-156256641 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_006538839.3_up_700_chr4_156256012_r range=chr4:156255712-156256711 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_NR_003681.1_up_700_chr5_129793861_f range=chr5:129793861-129794860 5'pad=: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_011240925.1_up_700_chr5_137166049_r range=chr5:137165749-137166748 5'p: invalid DNA symbols N

### `interim/fasta/prom-cdbprom-prokaryotic-helicobacter_pylori-714-1001.fa`

- Kind: `fasta`
- Records read: 714
- Length range: 1001-1001
- Issue: 53 prom prokaryotic sequence 53: invalid DNA symbols RSY
- Issue: 220 prom prokaryotic sequence 220: invalid DNA symbols Y
- Issue: 242 prom prokaryotic sequence 242: invalid DNA symbols N
- Issue: 247 prom prokaryotic sequence 247: invalid DNA symbols Y
- Issue: 248 prom prokaryotic sequence 248: invalid DNA symbols Y
- Issue: 262 prom prokaryotic sequence 262: invalid DNA symbols R
- Issue: 440 prom prokaryotic sequence 440: invalid DNA symbols R
- Issue: 545 prom prokaryotic sequence 545: invalid DNA symbols S

### `interim/fasta/prom-cdbprom-prokaryotic-pseudonomas_aeruginosa-2055-1001.fa`

- Kind: `fasta`
- Records read: 2055
- Length range: 1001-1001
- Issue: 363 prom prokaryotic sequence 363: invalid DNA symbols N
- Issue: 397 prom prokaryotic sequence 397: invalid DNA symbols N

### `interim/fasta/prom-cnnprom-eukaryotic-Human_non_tata-19811-251.fa`

- Kind: `fasta`
- Records read: 19811
- Length range: 251-251
- Issue: FP009820 IPMK_1              :+U  EU:NC; range  -200 to    50.: invalid DNA symbols N

### `interim/fasta/prom-graphpro-prokaryotic-leptospira_interrogans-2847-81.fa`

- Kind: `fasta`
- Records read: 2847
- Length range: 81-81
- Issue: NZ_LT962963.1 Leptospira interrogans serovar Manilae isolate L495 chromosome LMANV2, whole genome s: invalid DNA symbols N
- Issue: NZ_LT962963.1 Leptospira interrogans serovar Manilae isolate L495 chromosome LMANV2, whole genome s: invalid DNA symbols N

### `processed/assembled_datasets/intra/bhandari-eukaryotic-Human_promoter-p-196851-n-196851-train.csv`

- Kind: `sequence_csv`
- Records read: 393702
- Length range: 81-81
- Labels: {'0': 196851, '1': 196851}
- Issue: line 2077: invalid DNA symbols N
- Issue: line 2235: invalid DNA symbols N
- Issue: line 5699: invalid DNA symbols N
- Issue: line 8013: invalid DNA symbols N
- Issue: line 10298: invalid DNA symbols N
- Issue: line 15682: invalid DNA symbols N
- Issue: line 17291: invalid DNA symbols N
- Issue: line 17764: invalid DNA symbols N
- Issue: line 19350: invalid DNA symbols N
- Issue: line 20224: invalid DNA symbols N
- Issue: line 30322: invalid DNA symbols N
- Issue: line 32268: invalid DNA symbols N
- Issue: line 32654: invalid DNA symbols N
- Issue: line 32719: invalid DNA symbols N
- Issue: line 35643: invalid DNA symbols N
- Issue: line 35785: invalid DNA symbols N
- Issue: line 36552: invalid DNA symbols N
- Issue: line 37182: invalid DNA symbols N
- Issue: line 42784: invalid DNA symbols N
- Issue: line 44987: invalid DNA symbols N
- Issue: line 46721: invalid DNA symbols N
- Issue: line 53392: invalid DNA symbols N
- Issue: line 54625: invalid DNA symbols N
- Issue: line 54643: invalid DNA symbols N
- Issue: line 55332: invalid DNA symbols N

### `processed/assembled_datasets/intra/bhandari-eukaryotic-Human_promoter-p-49213-n-49213-test.csv`

- Kind: `sequence_csv`
- Records read: 98426
- Length range: 81-81
- Labels: {'1': 49213, '0': 49213}
- Issue: line 2018: invalid DNA symbols N
- Issue: line 4784: invalid DNA symbols N
- Issue: line 6443: invalid DNA symbols N
- Issue: line 6663: invalid DNA symbols N
- Issue: line 9012: invalid DNA symbols N
- Issue: line 9337: invalid DNA symbols N
- Issue: line 10829: invalid DNA symbols N
- Issue: line 12775: invalid DNA symbols N
- Issue: line 12874: invalid DNA symbols N
- Issue: line 13209: invalid DNA symbols N
- Issue: line 14670: invalid DNA symbols N
- Issue: line 16269: invalid DNA symbols N
- Issue: line 22723: invalid DNA symbols N
- Issue: line 23767: invalid DNA symbols N
- Issue: line 24667: invalid DNA symbols N
- Issue: line 26117: invalid DNA symbols N
- Issue: line 27198: invalid DNA symbols N
- Issue: line 32232: invalid DNA symbols N
- Issue: line 34064: invalid DNA symbols N
- Issue: line 35610: invalid DNA symbols N
- Issue: line 36295: invalid DNA symbols N
- Issue: line 45669: invalid DNA symbols N
- Issue: line 46697: invalid DNA symbols N
- Issue: line 47311: invalid DNA symbols N
- Issue: line 50481: invalid DNA symbols N

### `processed/assembled_datasets/intra/bhandari-eukaryotic-Plant_promoters-p-255636-n-255636-train.csv`

- Kind: `sequence_csv`
- Records read: 511272
- Length range: 81-81
- Labels: {'0': 255636, '1': 255636}
- Issue: line 10634: invalid DNA symbols N
- Issue: line 18653: invalid DNA symbols N
- Issue: line 25574: invalid DNA symbols N
- Issue: line 27918: invalid DNA symbols N
- Issue: line 37033: invalid DNA symbols N
- Issue: line 38275: invalid DNA symbols N
- Issue: line 97023: invalid DNA symbols N
- Issue: line 97846: invalid DNA symbols N
- Issue: line 97907: invalid DNA symbols N
- Issue: line 98689: invalid DNA symbols N
- Issue: line 111412: invalid DNA symbols N
- Issue: line 120417: invalid DNA symbols N
- Issue: line 126381: invalid DNA symbols N
- Issue: line 133025: invalid DNA symbols N
- Issue: line 143972: invalid DNA symbols N
- Issue: line 167826: invalid DNA symbols N
- Issue: line 174246: invalid DNA symbols N
- Issue: line 175411: invalid DNA symbols N
- Issue: line 202829: invalid DNA symbols N
- Issue: line 204427: invalid DNA symbols N
- Issue: line 218150: invalid DNA symbols N
- Issue: line 229813: invalid DNA symbols N
- Issue: line 237764: invalid DNA symbols N
- Issue: line 262088: invalid DNA symbols N
- Issue: line 284105: invalid DNA symbols N

### `processed/assembled_datasets/intra/bhandari-eukaryotic-Plant_promoters-p-63909-n-63909-test.csv`

- Kind: `sequence_csv`
- Records read: 127818
- Length range: 81-81
- Labels: {'0': 63909, '1': 63909}
- Issue: line 12622: invalid DNA symbols N
- Issue: line 26397: invalid DNA symbols N
- Issue: line 29742: invalid DNA symbols N
- Issue: line 33421: invalid DNA symbols N
- Issue: line 34498: invalid DNA symbols N
- Issue: line 40947: invalid DNA symbols N
- Issue: line 46200: invalid DNA symbols N
- Issue: line 49221: invalid DNA symbols N
- Issue: line 58065: invalid DNA symbols N
- Issue: line 67183: invalid DNA symbols N
- Issue: line 70329: invalid DNA symbols N
- Issue: line 74885: invalid DNA symbols N
- Issue: line 99794: invalid DNA symbols N
- Issue: line 100549: invalid DNA symbols N
- Issue: line 106267: invalid DNA symbols N
- Issue: line 112229: invalid DNA symbols N
- Issue: line 120146: invalid DNA symbols N

### `processed/assembled_datasets/intra/cdbprom-prokaryotic-helicobacter_pylori-p-1713-n-2272-train.csv`

- Kind: `sequence_csv`
- Records read: 3985
- Length range: 81-81
- Labels: {'0': 2272, '1': 1713}
- Issue: line 315: invalid DNA symbols Y
- Issue: line 1002: invalid DNA symbols Y
- Issue: line 2385: invalid DNA symbols Y
- Issue: line 2907: invalid DNA symbols Y
- Issue: line 2983: invalid DNA symbols Y
- Issue: line 3896: invalid DNA symbols Y

### `processed/assembled_datasets/intra/cdbprom-prokaryotic-pseudonomas_aeruginosa-p-1233-n-1640-test.csv`

- Kind: `sequence_csv`
- Records read: 2873
- Length range: 81-81
- Labels: {'0': 1640, '1': 1233}
- Issue: line 2727: invalid DNA symbols N

### `processed/assembled_datasets/intra/cdbprom-prokaryotic-pseudonomas_aeruginosa-p-4932-n-6556-train.csv`

- Kind: `sequence_csv`
- Records read: 11488
- Length range: 81-81
- Labels: {'0': 6556, '1': 4932}
- Issue: line 483: invalid DNA symbols N
- Issue: line 660: invalid DNA symbols N

### `processed/assembled_datasets/intra/cnnprom-eukaryotic-Arabidopsis_non_tata-p-14172-n-36668-train.csv`

- Kind: `sequence_csv`
- Records read: 50840
- Length range: 81-81
- Labels: {'0': 36668, '1': 14172}
- Issue: line 45800: invalid DNA symbols N
- Issue: line 48070: invalid DNA symbols N
- Issue: line 49544: invalid DNA symbols N

### `processed/assembled_datasets/intra/cnnprom-eukaryotic-Arabidopsis_non_tata-p-3543-n-9168-test.csv`

- Kind: `sequence_csv`
- Records read: 12711
- Length range: 81-81
- Labels: {'1': 3543, '0': 9168}
- Issue: line 4749: invalid DNA symbols N

### `processed/assembled_datasets/intra/cnnprom-eukaryotic-Human_non_tata-p-47546-n-88739-train.csv`

- Kind: `sequence_csv`
- Records read: 136285
- Length range: 81-81
- Labels: {'0': 88739, '1': 47546}
- Issue: line 2210: invalid DNA symbols N
- Issue: line 10422: invalid DNA symbols N
- Issue: line 124678: invalid DNA symbols N

### `processed/assembled_datasets/intra/graphpro-prokaryotic-leptospira_interrogans-p-1708-n-1693-test.csv`

- Kind: `sequence_csv`
- Records read: 3401
- Length range: 81-81
- Labels: {'0': 1693, '1': 1708}
- Issue: line 1824: invalid DNA symbols N

### `processed/assembled_datasets/intra/graphpro-prokaryotic-leptospira_interrogans-p-6833-n-6771-train.csv`

- Kind: `sequence_csv`
- Records read: 13604
- Length range: 81-81
- Labels: {'0': 6771, '1': 6833}
- Issue: line 2813: invalid DNA symbols N
- Issue: line 3702: invalid DNA symbols N
- Issue: line 7285: invalid DNA symbols N
- Issue: line 7387: invalid DNA symbols N
- Issue: line 7715: invalid DNA symbols N
- Issue: line 10071: invalid DNA symbols N
- Issue: line 10130: invalid DNA symbols N
- Issue: line 11080: invalid DNA symbols N
- Issue: line 12881: invalid DNA symbols N

### `raw/Bhandari_etal/Human_promoter.fa`

- Kind: `fasta`
- Records read: 61546
- Length range: 302-1000
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001306068.1_up_700_chr4_190173074_f range=chr4:190173074-190174: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001293798.1_up_700_chr4_190173074_f range=chr4:190173074-190174: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_YP_003024026.1_up_700_chrM_2607_f range=chrM:2607-3606 5'pad=0 3'p: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_152230.4_up_700_chr10_58267935_r range=chr10:58267635-58268634 : invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NR_134504.1_up_700_chr20_29447817_f range=chr20:29447817-29448816 : invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NR_128711.1_up_700_chr21_8986299_f range=chr21:8986299-8987298 5'p: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NR_131192.1_up_700_chr21_42615096_r range=chr21:42614796-42615795 : invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001109809.2_up_700_chr6_GL000250v2_alt_938842_r range=chr6_GL00: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001286633.1_up_700_chr6_GL000250v2_alt_1393524_f range=chr6_GL0: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_138700.4_up_700_chr6_GL000250v2_alt_1394129_f range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_005803.3_up_700_chr6_GL000250v2_alt_2060007_r range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001318875.1_up_700_chr6_GL000250v2_alt_2060007_r range=chr6_GL0: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001202523.1_up_700_chr6_GL000250v2_alt_2213865_f range=chr6_GL0: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001954.4_up_700_chr6_GL000250v2_alt_2214420_f range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_013993.2_up_700_chr6_GL000250v2_alt_2214428_f range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_004640.6_up_700_chr6_GL000250v2_alt_2871734_r range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_080598.5_up_700_chr6_GL000250v2_alt_2871734_r range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NR_037853.1_up_700_chr6_GL000250v2_alt_2871734_r range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_000594.3_up_700_chr6_GL000250v2_alt_2908408_f range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001289413.1_up_700_chr6_GL000250v2_alt_3229829_r range=chr6_GL0: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_025256.6_up_700_chr6_GL000250v2_alt_3230330_r range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_006709.4_up_700_chr6_GL000250v2_alt_3230330_r range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_170769.2_up_700_chr6_GL000252v2_alt_1331766_r range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_025236.3_up_700_chr6_GL000252v2_alt_1331768_r range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_005104.3_up_700_chr6_GL000252v2_alt_4220680_f range=chr6_GL0002: invalid DNA symbols N

### `raw/Bhandari_etal/Human_promoter.gz`

- Kind: `fasta_gzip`
- Records read: 61546
- Length range: 302-1000
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001306068.1_up_700_chr4_190173074_f range=chr4:190173074-190174: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001293798.1_up_700_chr4_190173074_f range=chr4:190173074-190174: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_YP_003024026.1_up_700_chrM_2607_f range=chrM:2607-3606 5'pad=0 3'p: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_152230.4_up_700_chr10_58267935_r range=chr10:58267635-58268634 : invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NR_134504.1_up_700_chr20_29447817_f range=chr20:29447817-29448816 : invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NR_128711.1_up_700_chr21_8986299_f range=chr21:8986299-8987298 5'p: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NR_131192.1_up_700_chr21_42615096_r range=chr21:42614796-42615795 : invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001109809.2_up_700_chr6_GL000250v2_alt_938842_r range=chr6_GL00: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001286633.1_up_700_chr6_GL000250v2_alt_1393524_f range=chr6_GL0: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_138700.4_up_700_chr6_GL000250v2_alt_1394129_f range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_005803.3_up_700_chr6_GL000250v2_alt_2060007_r range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001318875.1_up_700_chr6_GL000250v2_alt_2060007_r range=chr6_GL0: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001202523.1_up_700_chr6_GL000250v2_alt_2213865_f range=chr6_GL0: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001954.4_up_700_chr6_GL000250v2_alt_2214420_f range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_013993.2_up_700_chr6_GL000250v2_alt_2214428_f range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_004640.6_up_700_chr6_GL000250v2_alt_2871734_r range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_080598.5_up_700_chr6_GL000250v2_alt_2871734_r range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NR_037853.1_up_700_chr6_GL000250v2_alt_2871734_r range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_000594.3_up_700_chr6_GL000250v2_alt_2908408_f range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_001289413.1_up_700_chr6_GL000250v2_alt_3229829_r range=chr6_GL0: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_025256.6_up_700_chr6_GL000250v2_alt_3230330_r range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_006709.4_up_700_chr6_GL000250v2_alt_3230330_r range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_170769.2_up_700_chr6_GL000252v2_alt_1331766_r range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_025236.3_up_700_chr6_GL000252v2_alt_1331768_r range=chr6_GL0002: invalid DNA symbols N
- Issue: hg38_ct_tbncbiRefSeqCurated_7401_NM_005104.3_up_700_chr6_GL000252v2_alt_4220680_f range=chr6_GL0002: invalid DNA symbols N

### `raw/Bhandari_etal/Plant_promoters.fa`

- Kind: `fasta`
- Records read: 106520
- Length range: 306-1000
- Issue: mm10_ct_tbncbiRefSeq_7481_XR_880814.1_up_700_chr1_183063133_r range=chr1:183062833-183063832 5'pad=: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XR_880812.1_up_700_chr1_183063133_r range=chr1:183062833-183063832 5'pad=: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_NM_181732.4_up_700_chr1_183296360_f range=chr1:183296360-183297359 5'pad=: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_006535598.3_up_700_chr1_183296608_r range=chr1:183296308-183297307 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_011249734.2_up_700_chr1_183413223_f range=chr1:183413223-183414222 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_011249736.2_up_700_chr1_183413223_f range=chr1:183413223-183414222 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_011249735.2_up_700_chr1_183413223_f range=chr1:183413223-183414222 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XR_390305.3_up_700_chr2_176319923_r range=chr2:176319623-176320622 5'pad=: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_003688790.3_up_700_chr4_34311571_r range=chr4:34311271-34312270 5'pad=: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XR_001784558.1_up_700_chr4_42386158_r range=chr4:42385858-42386857 5'pad=: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_NM_198305.2_up_700_chr4_156234858_r range=chr4:156234558-156235557 5'pad=: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_006538844.3_up_700_chr4_156253425_r range=chr4:156253125-156254124 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_017320188.1_up_700_chr4_156254542_r range=chr4:156254242-156255241 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_017320187.1_up_700_chr4_156254542_r range=chr4:156254242-156255241 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XR_001784137.1_up_700_chr4_156254542_r range=chr4:156254242-156255241 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_006538846.3_up_700_chr4_156254580_r range=chr4:156254280-156255279 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_NM_001110516.1_up_700_chr4_156255339_r range=chr4:156255039-156256038 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_006538841.3_up_700_chr4_156255380_r range=chr4:156255080-156256079 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_006538838.3_up_700_chr4_156255382_r range=chr4:156255082-156256081 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_006538840.3_up_700_chr4_156255382_r range=chr4:156255082-156256081 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_006538843.3_up_700_chr4_156255382_r range=chr4:156255082-156256081 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_006538842.2_up_700_chr4_156255942_r range=chr4:156255642-156256641 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_006538839.3_up_700_chr4_156256012_r range=chr4:156255712-156256711 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_NR_003681.1_up_700_chr5_129793861_f range=chr5:129793861-129794860 5'pad=: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_011240925.1_up_700_chr5_137166049_r range=chr5:137165749-137166748 5'p: invalid DNA symbols N

### `raw/Bhandari_etal/Plant_promoters.gz`

- Kind: `fasta_gzip`
- Records read: 106520
- Length range: 306-1000
- Issue: mm10_ct_tbncbiRefSeq_7481_XR_880814.1_up_700_chr1_183063133_r range=chr1:183062833-183063832 5'pad=: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XR_880812.1_up_700_chr1_183063133_r range=chr1:183062833-183063832 5'pad=: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_NM_181732.4_up_700_chr1_183296360_f range=chr1:183296360-183297359 5'pad=: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_006535598.3_up_700_chr1_183296608_r range=chr1:183296308-183297307 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_011249734.2_up_700_chr1_183413223_f range=chr1:183413223-183414222 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_011249736.2_up_700_chr1_183413223_f range=chr1:183413223-183414222 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_011249735.2_up_700_chr1_183413223_f range=chr1:183413223-183414222 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XR_390305.3_up_700_chr2_176319923_r range=chr2:176319623-176320622 5'pad=: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_003688790.3_up_700_chr4_34311571_r range=chr4:34311271-34312270 5'pad=: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XR_001784558.1_up_700_chr4_42386158_r range=chr4:42385858-42386857 5'pad=: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_NM_198305.2_up_700_chr4_156234858_r range=chr4:156234558-156235557 5'pad=: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_006538844.3_up_700_chr4_156253425_r range=chr4:156253125-156254124 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_017320188.1_up_700_chr4_156254542_r range=chr4:156254242-156255241 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_017320187.1_up_700_chr4_156254542_r range=chr4:156254242-156255241 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XR_001784137.1_up_700_chr4_156254542_r range=chr4:156254242-156255241 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_006538846.3_up_700_chr4_156254580_r range=chr4:156254280-156255279 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_NM_001110516.1_up_700_chr4_156255339_r range=chr4:156255039-156256038 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_006538841.3_up_700_chr4_156255380_r range=chr4:156255080-156256079 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_006538838.3_up_700_chr4_156255382_r range=chr4:156255082-156256081 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_006538840.3_up_700_chr4_156255382_r range=chr4:156255082-156256081 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_006538843.3_up_700_chr4_156255382_r range=chr4:156255082-156256081 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_006538842.2_up_700_chr4_156255942_r range=chr4:156255642-156256641 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_006538839.3_up_700_chr4_156256012_r range=chr4:156255712-156256711 5'p: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_NR_003681.1_up_700_chr5_129793861_f range=chr5:129793861-129794860 5'pad=: invalid DNA symbols N
- Issue: mm10_ct_tbncbiRefSeq_7481_XM_011240925.1_up_700_chr5_137166049_r range=chr5:137165749-137166748 5'p: invalid DNA symbols N

### `raw/CDBProm/helicobacter_pylori.txt`

- Kind: `line_sequence_txt`
- Records read: 706
- Length range: 1001-1001
- Issue: line 54: not a plain DNA sequence line
- Issue: line 221: not a plain DNA sequence line
- Issue: line 243: not a plain DNA sequence line
- Issue: line 248: not a plain DNA sequence line
- Issue: line 249: not a plain DNA sequence line
- Issue: line 263: not a plain DNA sequence line
- Issue: line 441: not a plain DNA sequence line
- Issue: line 546: not a plain DNA sequence line

### `raw/CDBProm/pseudonomas_aeruginosa.txt`

- Kind: `line_sequence_txt`
- Records read: 2053
- Length range: 1001-1001
- Issue: line 364: not a plain DNA sequence line
- Issue: line 398: not a plain DNA sequence line

### `raw/CNNProm/Arabidopsis_non_tata_neg.fa`

- Kind: `fasta`
- Records read: 11459
- Length range: 251-251
- Issue: hypothetical protein, T1E4.10                                                 [AC069299 ]: invalid DNA symbols N
- Issue: wall-associated kinase 4, wak4                                                [AJ009695 ]: invalid DNA symbols N

### `raw/CNNProm/Human_non_tata_pos.fa`

- Kind: `fasta`
- Records read: 19811
- Length range: 251-251
- Issue: FP009820 IPMK_1              :+U  EU:NC; range  -200 to    50.: invalid DNA symbols N

### `raw/EDP/edp_all.fa`

- Kind: `fasta`
- Records read: 4796
- Length range: 301-335
- Issue: EP17002 (-) Gm snRNA U1a; range -250 to 50.: invalid DNA symbols N
- Issue: EP07001 (+) Ta histone H3; range -250 to 50.: invalid DNA symbols N
- Issue: EP58010 (-) Ps legumin legB; range -250 to 50.: invalid DNA symbols N
- Issue: EP58011 (-) Ps legumin legC; range -250 to 50.: invalid DNA symbols N
- Issue: EP35020 (+) Bn oleosin P1+; range -250 to 50.: invalid DNA symbols N
- Issue: EP36001 (+) Be 2S seed protein; range -250 to 50.: invalid DNA symbols N
- Issue: EP35024 (+) Gm LHC cab3; range -250 to 50.: invalid DNA symbols N
- Issue: EP16004 (+) Ph LHC II type 2; range -250 to 50.: invalid DNA symbols N
- Issue: EP16006 (-) Gm leghem. Lbc_1; range -250 to 50.: invalid DNA symbols N
- Issue: EP29010 (-) Pv leghemoglobin; range -250 to 50.: invalid DNA symbols N
- Issue: EP31005 (+) Ph EPSP synthase P2+; range -250 to 50.: invalid DNA symbols N
- Issue: EP16010 (-) Gm RuBPCss SRS4; range -250 to 50.: invalid DNA symbols N
- Issue: EP07005 (-) Gm RuBPCss; range -250 to 50.: invalid DNA symbols N
- Issue: EP14010 (-) Ph RuBPCss 11A; range -250 to 50.: invalid DNA symbols N
- Issue: EP23011 (-) Ph RuBPCss 911; range -250 to 50.: invalid DNA symbols N
- Issue: EP23012 (-) Ph RuBPCss 611; range -250 to 50.: invalid DNA symbols N
- Issue: EP16017 (+) Hv a'-amylase 1; range -250 to 50.: invalid DNA symbols N
- Issue: EP35009 (+) Am[squamosa]; range -250 to 50.: invalid DNA symbols N
- Issue: EP14014 (+) Zm hsp 70K; range -250 to 50.: invalid DNA symbols N
- Issue: EP15002 (+) Gm protease inh. BB; range -250 to 50.: invalid DNA symbols N
- Issue: EP14007 (+) Pv[dlec2] PHA-L; range -250 to 50.: invalid DNA symbols N
- Issue: EP14015 (+) Gm nodulin 24K; range -250 to 50.: invalid DNA symbols N
- Issue: EP11028 (+) Apo chorion p. A1; range -250 to 50.: invalid DNA symbols N
- Issue: EP11029 (+) Apo chorion p. A4; range -250 to 50.: invalid DNA symbols N
- Issue: EP11030 (+) Apo chorion p. B6; range -250 to 50.: invalid DNA symbols N

### `raw/Fuitfly/Drosophila_promoter_all_1941.fa`

- Kind: `fasta`
- Records read: 1941
- Length range: 300-300
- Issue: Promoter for RH25164, -250bp and +50bp: invalid DNA symbols N
- Issue: Promoter for RE29436, -250bp and +50bp: invalid DNA symbols N
- Issue: Promoter for RE34031, -250bp and +50bp: invalid DNA symbols N
- Issue: Promoter for RH61316, -250bp and +50bp: invalid DNA symbols N
- Issue: Promoter for RH54761, -250bp and +50bp: invalid DNA symbols N

### `raw/Fuitfly/drosophila.fa`

- Kind: `fasta`
- Records read: 256
- Length range: 300-300
- Issue: EPD26037	250 UP  50 DOWN: invalid DNA symbols N
- Issue: EPD47005	250 UP  50 DOWN: invalid DNA symbols N
- Issue: EPD24020	250 UP  50 DOWN: invalid DNA symbols N
- Issue: EPD15016	250 UP  50 DOWN: invalid DNA symbols N
- Issue: EPD23033	250 UP  50 DOWN: invalid DNA symbols N
- Issue: EPD15021	250 UP  50 DOWN: invalid DNA symbols N
- Issue: EPD17018	250 UP  50 DOWN: invalid DNA symbols N
- Issue: DROBPIS	250 UP  50 DOWN: invalid DNA symbols N
- Issue: DROCYP6A2A	250 UP  50 DOWN: invalid DNA symbols N
- Issue: DME75B	250 UP  50 DOWN: invalid DNA symbols N
- Issue: DMW13	250 UP  50 DOWN: invalid DNA symbols N
- Issue: DMRNUC1	250 UP  50 DOWN: invalid DNA symbols N
- Issue: DROIAB	250 UP  50 DOWN: invalid DNA symbols N
- Issue: DMKR	250 UP  50 DOWN: invalid DNA symbols N
- Issue: DMPRUNEG	250 UP  50 DOWN: invalid DNA symbols N
- Issue: DMSCRHOM	250 UP  50 DOWN: invalid DNA symbols N
- Issue: DROSSGA	250 UP  50 DOWN: invalid DNA symbols N
- Issue: DMZ60MEX1	250 UP  50 DOWN: invalid DNA symbols N
- Issue: EPD47006	250 UP  50 DOWN: invalid DNA symbols N
- Issue: EPD15012	250 UP  50 DOWN: invalid DNA symbols N
- Issue: EPD23030	250 UP  50 DOWN: invalid DNA symbols N
- Issue: EPD11033	250 UP  50 DOWN: invalid DNA symbols N
- Issue: EPD07020	250 UP  50 DOWN: invalid DNA symbols N
- Issue: DROG6PD01	250 UP  50 DOWN: invalid DNA symbols N
- Issue: DMDRCII1	250 UP  50 DOWN: invalid DNA symbols N

### `raw/Fuitfly/human.fa`

- Kind: `fasta`
- Records read: 565
- Length range: 300-300
- Issue: EPD33018	250 UP  50 DOWN: invalid DNA symbols N
- Issue: EPD11068	250 UP  50 DOWN: invalid DNA symbols N
- Issue: EPD11072	250 UP  50 DOWN: invalid DNA symbols N
- Issue: EPD07059	250 UP  50 DOWN: invalid DNA symbols N
- Issue: EPD15026	250 UP  50 DOWN: invalid DNA symbols N
- Issue: EPD07069	250 UP  50 DOWN: invalid DNA symbols N
- Issue: EPD17051	250 UP  50 DOWN: invalid DNA symbols N
- Issue: EPD30028	250 UP  50 DOWN: invalid DNA symbols N
- Issue: EPD23015	250 UP  50 DOWN: invalid DNA symbols N
- Issue: EPD11113	250 UP  50 DOWN: invalid DNA symbols N
- Issue: EPD07102	250 UP  50 DOWN: invalid DNA symbols N
- Issue: EPD11129	250 UP  50 DOWN: invalid DNA symbols N
- Issue: EPD23005	250 UP  50 DOWN: invalid DNA symbols N
- Issue: EPD25083	250 UP  50 DOWN: invalid DNA symbols N
- Issue: EPD11145	250 UP  50 DOWN: invalid DNA symbols N
- Issue: EPD27006	250 UP  50 DOWN: invalid DNA symbols N
- Issue: EPD14075	250 UP  50 DOWN: invalid DNA symbols N
- Issue: EPD07122	250 UP  50 DOWN: invalid DNA symbols N
- Issue: EPD26023	250 UP  50 DOWN: invalid DNA symbols N
- Issue: EPD30023	250 UP  50 DOWN: invalid DNA symbols N
- Issue: EPD11177	250 UP  50 DOWN: invalid DNA symbols N
- Issue: EPD15062	250 UP  50 DOWN: invalid DNA symbols N
- Issue: EPD17028	250 UP  50 DOWN: invalid DNA symbols N
- Issue: EPD49010	250 UP  50 DOWN: invalid DNA symbols N
- Issue: EPD48014	250 UP  50 DOWN: invalid DNA symbols N

### `raw/GraphPro/Bamy/cTest.txt`

- Kind: `line_sequence_txt`
- Records read: 0
- Issue: line 1: not a plain DNA sequence line
- Issue: line 2: not a plain DNA sequence line
- Issue: line 3: not a plain DNA sequence line
- Issue: line 4: not a plain DNA sequence line
- Issue: line 5: not a plain DNA sequence line

### `raw/GraphPro/Cje/cTest.txt`

- Kind: `line_sequence_txt`
- Records read: 0
- Issue: line 1: not a plain DNA sequence line
- Issue: line 2: not a plain DNA sequence line
- Issue: line 3: not a plain DNA sequence line
- Issue: line 4: not a plain DNA sequence line
- Issue: line 5: not a plain DNA sequence line

### `raw/Nova pasta (2)/training_sequences/__MACOSX/._anabaena_sp.txt`

- Kind: `line_sequence_txt`
- Records read: 0
- Issue: line 1: not a plain DNA sequence line

### `raw/Nova pasta (2)/training_sequences/__MACOSX/._bacillus_amyloliquefaciens.txt`

- Kind: `line_sequence_txt`
- Records read: 0
- Issue: line 1: not a plain DNA sequence line

### `raw/Nova pasta (2)/training_sequences/__MACOSX/._chlamydophila_pneumoniae.txt`

- Kind: `line_sequence_txt`
- Records read: 0
- Issue: line 1: not a plain DNA sequence line

### `raw/Nova pasta (2)/training_sequences/__MACOSX/._corynebacterium_glutamicum.txt`

- Kind: `line_sequence_txt`
- Records read: 0
- Issue: line 1: not a plain DNA sequence line

### `raw/Nova pasta (2)/training_sequences/__MACOSX/._helicobacter_pylori.txt`

- Kind: `line_sequence_txt`
- Records read: 0
- Issue: line 1: not a plain DNA sequence line
- Issue: line 2: not a plain DNA sequence line

### `raw/Nova pasta (2)/training_sequences/__MACOSX/._klebisiella_pneumoniae.txt`

- Kind: `line_sequence_txt`
- Records read: 0
- Issue: line 1: not a plain DNA sequence line

### `raw/Nova pasta (2)/training_sequences/__MACOSX/._mycrobacterium_tuberculosis.txt`

- Kind: `line_sequence_txt`
- Records read: 0
- Issue: line 1: not a plain DNA sequence line

### `raw/Nova pasta (2)/training_sequences/__MACOSX/._negative_anabaena_sp.txt`

- Kind: `line_sequence_txt`
- Records read: 0
- Issue: line 1: not a plain DNA sequence line

### `raw/Nova pasta (2)/training_sequences/__MACOSX/._negative_corynebacterium_glutamicum.txt`

- Kind: `line_sequence_txt`
- Records read: 0
- Issue: line 1: not a plain DNA sequence line

### `raw/Nova pasta (2)/training_sequences/__MACOSX/._negative_mycrobacterium_tuberculosis.txt`

- Kind: `line_sequence_txt`
- Records read: 0
- Issue: line 1: not a plain DNA sequence line

### `raw/Nova pasta (2)/training_sequences/__MACOSX/._pseudonomas_aeruginosa.txt`

- Kind: `line_sequence_txt`
- Records read: 0
- Issue: line 1: not a plain DNA sequence line

### `raw/Nova pasta (2)/training_sequences/__MACOSX/._salmonella_typhimurium.txt`

- Kind: `line_sequence_txt`
- Records read: 0
- Issue: line 1: not a plain DNA sequence line
- Issue: line 2: not a plain DNA sequence line

### `raw/Nova pasta (2)/training_sequences/__MACOSX/._streptomyces_coelicolor.txt`

- Kind: `line_sequence_txt`
- Records read: 0
- Issue: line 1: not a plain DNA sequence line

### `raw/Nova pasta (2)/training_sequences/__MACOSX/._synechocistis.txt`

- Kind: `line_sequence_txt`
- Records read: 0
- Issue: line 1: not a plain DNA sequence line

### `raw/Nova pasta (2)/training_sequences/helicobacter_pylori.txt`

- Kind: `line_sequence_txt`
- Records read: 706
- Length range: 1001-1001
- Issue: line 54: not a plain DNA sequence line
- Issue: line 221: not a plain DNA sequence line
- Issue: line 243: not a plain DNA sequence line
- Issue: line 248: not a plain DNA sequence line
- Issue: line 249: not a plain DNA sequence line
- Issue: line 263: not a plain DNA sequence line
- Issue: line 441: not a plain DNA sequence line
- Issue: line 546: not a plain DNA sequence line

### `raw/Nova pasta (2)/training_sequences/pseudonomas_aeruginosa.txt`

- Kind: `line_sequence_txt`
- Records read: 2053
- Length range: 1001-1001
- Issue: line 364: not a plain DNA sequence line
- Issue: line 398: not a plain DNA sequence line

### `raw/iPro-MP/repo/Dataset/Train/12_train.txt`

- Kind: `fasta_txt`
- Records read: 4950
- Length range: 81-81
- Issue: Helicobacter pylori strain 26695--676: invalid DNA symbols Y
- Issue: Helicobacter pylori strain 26695--750: invalid DNA symbols N
- Issue: Helicobacter pylori strain 26695--1600: invalid DNA symbols WY
- Issue: Helicobacter pylori strain 26695--1977: invalid DNA symbols N
- Issue: Helicobacter pylori strain 26695--2039: invalid DNA symbols N
- Issue: Helicobacter pylori strain 26695 CDS--1730: invalid DNA symbols R
- Issue: Helicobacter pylori strain 26695 Convergent--61901: invalid DNA symbols K
- Issue: Helicobacter pylori strain 26695 Convergent--61952: invalid DNA symbols K

### `raw/iPro-MP/repo/requirements.txt`

- Kind: `line_sequence_txt`
- Records read: 0
- Issue: line 1: not a plain DNA sequence line
- Issue: line 2: not a plain DNA sequence line
- Issue: line 3: not a plain DNA sequence line
- Issue: line 4: not a plain DNA sequence line
- Issue: line 5: not a plain DNA sequence line
- Issue: line 6: not a plain DNA sequence line
- Issue: line 7: not a plain DNA sequence line

## Manual Review Items

- `raw/Nova pasta (2)/training_sequences.zip` (zip, records/items: 36): archive inventoried but not expanded during validation; first entries: synechocistis.txt, __MACOSX/._synechocistis.txt, anabaena_sp.txt, __MACOSX/._anabaena_sp.txt, bacillus_amyloliquefaciens.txt

## Scope Notes

- Processed CSV files with `sequence,label` were checked for DNA alphabet, 81 bp length, binary labels, and filename count consistency.
- FASTA, FASTA-like TXT, and gzip-compressed sequence files were checked for DNA alphabet. Fixed length was enforced only when an expected length was encoded in the filename.
- Raw TXT files with one DNA sequence per line were checked for DNA alphabet, without fixed-length enforcement because raw sources may contain longer windows before cropping.
- Numeric feature CSVs, TSV physicochemical references, notebooks, scripts, and documentation were classified as not applicable for direct biological sequence validation.
- The `predictions_ecoli` folder was explicitly ignored by request and is outside this validation report.
- ZIP archives were inventoried but not expanded during validation; use extracted, named source directories for experimental inputs.
