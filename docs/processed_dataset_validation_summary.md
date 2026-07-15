# Processed Dataset Validation Summary

Scope: `data/processed/assembled_datasets/intra/*.csv`.

| Status | Dataset | Rows | Positive | Negative | Invalid alphabet rows | Length errors | Label errors | Invalid symbols | Example lines |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| fail | bhandari-eukaryotic-Human_promoter-p-196851-n-196851-train.csv | 393702 | 196851 | 196851 | 189 | 0 | 0 | N | 2077,2235,5699,8013,10298 |
| fail | bhandari-eukaryotic-Human_promoter-p-49213-n-49213-test.csv | 98426 | 49213 | 49213 | 51 | 0 | 0 | N | 2018,4784,6443,6663,9012 |
| fail | bhandari-eukaryotic-Plant_promoters-p-255636-n-255636-train.csv | 511272 | 255636 | 255636 | 55 | 0 | 0 | N | 10634,18653,25574,27918,37033 |
| fail | bhandari-eukaryotic-Plant_promoters-p-63909-n-63909-test.csv | 127818 | 63909 | 63909 | 17 | 0 | 0 | N | 12622,26397,29742,33421,34498 |
| pass | bhandari-prokaryotic-Yeast_promoter-p-14693-n-14692-train.csv | 29385 | 14693 | 14692 | 0 | 0 | 0 | - | - |
| pass | bhandari-prokaryotic-Yeast_promoter-p-3673-n-3674-test.csv | 7347 | 3673 | 3674 | 0 | 0 | 0 | - | - |
| pass | cdbprom-prokaryotic-anabaena_sp-p-1510-n-2009-test.csv | 3519 | 1510 | 2009 | 0 | 0 | 0 | - | - |
| pass | cdbprom-prokaryotic-anabaena_sp-p-6041-n-8035-train.csv | 14076 | 6041 | 8035 | 0 | 0 | 0 | - | - |
| pass | cdbprom-prokaryotic-bacillus_amyloliquefaciens-p-2541-n-3379-train.csv | 5920 | 2541 | 3379 | 0 | 0 | 0 | - | - |
| pass | cdbprom-prokaryotic-bacillus_amyloliquefaciens-p-636-n-845-test.csv | 1481 | 636 | 845 | 0 | 0 | 0 | - | - |
| pass | cdbprom-prokaryotic-chlamydophila_pneumoniae-p-243-n-323-test.csv | 566 | 243 | 323 | 0 | 0 | 0 | - | - |
| pass | cdbprom-prokaryotic-chlamydophila_pneumoniae-p-969-n-1293-train.csv | 2262 | 969 | 1293 | 0 | 0 | 0 | - | - |
| pass | cdbprom-prokaryotic-corynebacterium_glutamicum-p-1380-n-1830-train.csv | 3210 | 1380 | 1830 | 0 | 0 | 0 | - | - |
| pass | cdbprom-prokaryotic-corynebacterium_glutamicum-p-345-n-458-test.csv | 803 | 345 | 458 | 0 | 0 | 0 | - | - |
| fail | cdbprom-prokaryotic-helicobacter_pylori-p-1713-n-2272-train.csv | 3985 | 1713 | 2272 | 6 | 0 | 0 | Y | 315,1002,2385,2907,2983 |
| pass | cdbprom-prokaryotic-helicobacter_pylori-p-429-n-568-test.csv | 997 | 429 | 568 | 0 | 0 | 0 | - | - |
| pass | cdbprom-prokaryotic-klebisiella_pneumoniae-p-3189-n-4243-train.csv | 7432 | 3189 | 4243 | 0 | 0 | 0 | - | - |
| pass | cdbprom-prokaryotic-klebisiella_pneumoniae-p-798-n-1061-test.csv | 1859 | 798 | 1061 | 0 | 0 | 0 | - | - |
| pass | cdbprom-prokaryotic-mycrobacterium_tuberculosis-p-1063-n-1414-test.csv | 2477 | 1063 | 1414 | 0 | 0 | 0 | - | - |
| pass | cdbprom-prokaryotic-mycrobacterium_tuberculosis-p-4253-n-5654-train.csv | 9907 | 4253 | 5654 | 0 | 0 | 0 | - | - |
| fail | cdbprom-prokaryotic-pseudonomas_aeruginosa-p-1233-n-1640-test.csv | 2873 | 1233 | 1640 | 1 | 0 | 0 | N | 2727 |
| fail | cdbprom-prokaryotic-pseudonomas_aeruginosa-p-4932-n-6556-train.csv | 11488 | 4932 | 6556 | 2 | 0 | 0 | N | 483,660 |
| pass | cdbprom-prokaryotic-salmonella_typhimurium-p-2354-n-3117-train.csv | 5471 | 2354 | 3117 | 0 | 0 | 0 | - | - |
| pass | cdbprom-prokaryotic-salmonella_typhimurium-p-589-n-779-test.csv | 1368 | 589 | 779 | 0 | 0 | 0 | - | - |
| pass | cdbprom-prokaryotic-streptomyces_coelicolor-p-1567-n-2085-test.csv | 3652 | 1567 | 2085 | 0 | 0 | 0 | - | - |
| pass | cdbprom-prokaryotic-streptomyces_coelicolor-p-6266-n-8339-train.csv | 14605 | 6266 | 8339 | 0 | 0 | 0 | - | - |
| pass | cdbprom-prokaryotic-synechocistis-p-3933-n-5216-train.csv | 9149 | 3933 | 5216 | 0 | 0 | 0 | - | - |
| pass | cdbprom-prokaryotic-synechocistis-p-984-n-1304-test.csv | 2288 | 984 | 1304 | 0 | 0 | 0 | - | - |
| fail | cnnprom-eukaryotic-Arabidopsis_non_tata-p-14172-n-36668-train.csv | 50840 | 14172 | 36668 | 3 | 0 | 0 | N | 45800,48070,49544 |
| fail | cnnprom-eukaryotic-Arabidopsis_non_tata-p-3543-n-9168-test.csv | 12711 | 3543 | 9168 | 1 | 0 | 0 | N | 4749 |
| pass | cnnprom-eukaryotic-Arabidopsis_tata-p-3593-n-9212-train.csv | 12805 | 3593 | 9212 | 0 | 0 | 0 | - | - |
| pass | cnnprom-eukaryotic-Arabidopsis_tata-p-898-n-2304-test.csv | 3202 | 898 | 2304 | 0 | 0 | 0 | - | - |
| pass | cnnprom-eukaryotic-Human_non_tata-p-11887-n-22185-test.csv | 34072 | 11887 | 22185 | 0 | 0 | 0 | - | - |
| fail | cnnprom-eukaryotic-Human_non_tata-p-47546-n-88739-train.csv | 136285 | 47546 | 88739 | 3 | 0 | 0 | N | 2210,10422,124678 |
| pass | cnnprom-eukaryotic-Mouse_non_tata-p-39079-n-79430-train.csv | 118509 | 39079 | 79430 | 0 | 0 | 0 | - | - |
| pass | cnnprom-eukaryotic-Mouse_non_tata-p-9770-n-19858-test.csv | 29628 | 9770 | 19858 | 0 | 0 | 0 | - | - |
| pass | cnnprom-eukaryotic-Mouse_tata-p-1566-n-2824-test.csv | 4390 | 1566 | 2824 | 0 | 0 | 0 | - | - |
| pass | cnnprom-eukaryotic-Mouse_tata-p-6261-n-11296-train.csv | 17557 | 6261 | 11296 | 0 | 0 | 0 | - | - |
| pass | cnnprom-prokaryotic-Bacillus-p-224-n-800-test.csv | 1024 | 224 | 800 | 0 | 0 | 0 | - | - |
| pass | cnnprom-prokaryotic-Bacillus-p-895-n-3200-train.csv | 4095 | 895 | 3200 | 0 | 0 | 0 | - | - |
| pass | cnnprom-prokaryotic-Ecoli-p-2013-n-9600-train.csv | 11613 | 2013 | 9600 | 0 | 0 | 0 | - | - |
| pass | cnnprom-prokaryotic-Ecoli-p-504-n-2400-test.csv | 2904 | 504 | 2400 | 0 | 0 | 0 | - | - |
| pass | graphpro-eukaryotic-Human-p-1404-n-1871-test.csv | 3275 | 1404 | 1871 | 0 | 0 | 0 | - | - |
| pass | graphpro-eukaryotic-Human-p-5613-n-7485-train.csv | 13098 | 5613 | 7485 | 0 | 0 | 0 | - | - |
| pass | graphpro-eukaryotic-Mouse-p-1108-n-1477-test.csv | 2585 | 1108 | 1477 | 0 | 0 | 0 | - | - |
| pass | graphpro-eukaryotic-Mouse-p-4430-n-5907-train.csv | 10337 | 4430 | 5907 | 0 | 0 | 0 | - | - |
| pass | graphpro-prokaryotic-bacillus_amyloliquefaciens-p-2227-n-2969-train.csv | 5196 | 2227 | 2969 | 0 | 0 | 0 | - | - |
| pass | graphpro-prokaryotic-bacillus_amyloliquefaciens-p-557-n-743-test.csv | 1300 | 557 | 743 | 0 | 0 | 0 | - | - |
| pass | graphpro-prokaryotic-campylobacter_jejuni-p-3230-n-4307-train.csv | 7537 | 3230 | 4307 | 0 | 0 | 0 | - | - |
| pass | graphpro-prokaryotic-campylobacter_jejuni-p-808-n-1077-test.csv | 1885 | 808 | 1077 | 0 | 0 | 0 | - | - |
| pass | graphpro-prokaryotic-clostridium_phytofermentans-p-1207-n-1379-train.csv | 2586 | 1207 | 1379 | 0 | 0 | 0 | - | - |
| pass | graphpro-prokaryotic-clostridium_phytofermentans-p-302-n-345-test.csv | 647 | 302 | 345 | 0 | 0 | 0 | - | - |
| pass | graphpro-prokaryotic-escherichia_coli-p-1512-n-3099-test.csv | 4611 | 1512 | 3099 | 0 | 0 | 0 | - | - |
| pass | graphpro-prokaryotic-escherichia_coli-p-6045-n-12397-train.csv | 18442 | 6045 | 12397 | 0 | 0 | 0 | - | - |
| fail | graphpro-prokaryotic-leptospira_interrogans-p-1708-n-1693-test.csv | 3401 | 1708 | 1693 | 1 | 0 | 0 | N | 1824 |
| fail | graphpro-prokaryotic-leptospira_interrogans-p-6833-n-6771-train.csv | 13604 | 6833 | 6771 | 9 | 0 | 0 | N | 2813,3702,7285,7387,7715 |
| pass | graphpro-prokaryotic-rhodobacter_capsulatus-p-2164-n-2593-test.csv | 4757 | 2164 | 2593 | 0 | 0 | 0 | - | - |
| pass | graphpro-prokaryotic-rhodobacter_capsulatus-p-8657-n-10371-train.csv | 19028 | 8657 | 10371 | 0 | 0 | 0 | - | - |

## Summary

- Processed CSV files checked: 58
- Passing CSV files: 46
- Failing CSV files: 12
- Total invalid alphabet rows: 338
- Total length errors: 0
- Total label errors: 0

Interpretation: failures are caused by ambiguous IUPAC symbols in otherwise 81 bp, binary-labeled processed datasets.