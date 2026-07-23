from pathlib import Path
import unittest

from capsprom.eda.feature_exploration import (
    DatasetRecord,
    iter_dataset_files,
    parse_dataset_name,
    stratified_records,
    config_from_yaml,
    summarize_kmer_differences,
)
from capsprom.eda.plots import generate_eda_figures, write_figure_report


class FeatureEDATests(unittest.TestCase):
    def test_parse_dataset_name_preserves_study_domain_dataset_and_split(self):
        descriptor = parse_dataset_name(
            Path("graphpro-prokaryotic-escherichia_coli-p-6045-n-12397-train.csv")
        )

        self.assertEqual(descriptor["study"], "graphpro")
        self.assertEqual(descriptor["domain"], "prokaryotic")
        self.assertEqual(descriptor["dataset"], "escherichia_coli")
        self.assertEqual(descriptor["split"], "train")

    def test_stratified_records_limits_each_label_deterministically(self):
        records = [DatasetRecord("ACGT", index % 2) for index in range(10)]
        sampled = stratified_records(records, per_label=2)

        self.assertEqual(len(sampled), 4)
        self.assertEqual(sum(record.label == 0 for record in sampled), 2)
        self.assertEqual(sum(record.label == 1 for record in sampled), 2)
        self.assertEqual(sampled, records[:4])

    def test_iter_dataset_files_ignores_cleaning_manifest(self):
        paths = [path.name for path in iter_dataset_files(Path("data/processed/assembled_datasets/intra_strict_dna"))]

        self.assertEqual(len(paths), 58)
        self.assertNotIn("cleaning_manifest.csv", paths)

    def test_config_from_yaml_loads_project_eda_shape(self):
        config = config_from_yaml(Path("configs/eda_intra_features.yaml"))

        self.assertEqual(config.input_dir, Path("data/processed/assembled_datasets/intra_strict_dna"))
        self.assertEqual(config.feature_sample_per_label, 1000)
        self.assertEqual(config.kmer_values, (2, 3, 4))
        self.assertIn("Base stacking", config.dinucleotide_properties)

    def test_kmer_differences_rank_class_specific_words(self):
        records = [
            DatasetRecord("AAAA", 1),
            DatasetRecord("AAAA", 1),
            DatasetRecord("CCCC", 0),
            DatasetRecord("CCCC", 0),
        ]
        rows = summarize_kmer_differences(
            {"study": "toy", "domain": "toy", "dataset": "toy", "split": "train", "file": "toy.csv"},
            records,
            k=2,
            top_n=2,
        )
        kmers = {row["kmer"] for row in rows}

        self.assertEqual(kmers, {"AA", "CC"})

    def test_generate_eda_figures_from_existing_outputs(self):
        output_dir = Path("outputs/eda/intra_strict_feature_exploration")
        if not (output_dir / "dataset_summary.csv").exists():
            self.skipTest("EDA outputs are not available")

        figures = generate_eda_figures(output_dir)
        write_figure_report(output_dir, figures)

        self.assertEqual(len(figures), 5)
        for figure in figures:
            self.assertTrue((output_dir / figure["path"]).exists())


if __name__ == "__main__":
    unittest.main()
