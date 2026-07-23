from pathlib import Path
import unittest

from capsprom.features import (
    DnaBertEncoder,
    GCContentSkewEncoder,
    KmerFrequencyEncoder,
    OneHotEncoder,
    PhysicochemicalEncoder,
    PseKNCEncoder,
    build_feature_set_from_mapping,
    dna_bert_kmer_text,
    encode_sequences_as_multi_head,
    encode_sequences_as_vectors,
    feature_spec_from_mapping,
    validate_dna_sequence,
)


ROOT = Path(__file__).resolve().parents[1]
DINUC = ROOT / "data/raw/references/normalized-dinuc.tsv"
TRINUC = ROOT / "data/raw/references/normalized-trinuc.tsv"


class FakeDnaBertBackend:
    def encode_text(self, text, pooling, max_length):
        tokens = text.split()
        return [float(len(tokens)), float(len(tokens[0])), float(max_length or 0), 1.0 if pooling == "cls" else 0.0]


class FeatureEngineeringTests(unittest.TestCase):
    def test_kmer_frequency_shape_and_normalization(self):
        block = KmerFrequencyEncoder(k=2).encode("ACGT")

        self.assertEqual(block.shape, (16,))
        self.assertAlmostEqual(sum(block.values), 1.0)

    def test_one_hot_shape(self):
        block = OneHotEncoder(k=1).encode("ACGT")

        self.assertEqual(block.shape, (4, 4))
        self.assertEqual(block.values[0], [1.0, 0.0, 0.0, 0.0])

    def test_one_hot_supports_kmer_tokens(self):
        block = OneHotEncoder(k=2).encode("ACGT")

        self.assertEqual(block.shape, (3, 16))
        self.assertEqual(sum(block.values[0]), 1.0)
        self.assertEqual(block.metadata["encoding"], "one_hot")
        self.assertEqual(block.metadata["k"], 2)

    def test_physicochemical_property_subset_preserves_order(self):
        encoder = PhysicochemicalEncoder.from_tsv(
            DINUC,
            name="dinuc_subset",
            properties=["B-DNA twist", "Base stacking"],
        )
        block = encoder.encode("ACGT")

        self.assertEqual(block.shape, (3, 2))
        self.assertEqual(block.metadata["property_names"], "B-DNA twist|Base stacking")

    def test_invalid_property_fails_fast(self):
        with self.assertRaisesRegex(ValueError, "unknown physicochemical properties"):
            PhysicochemicalEncoder.from_tsv(DINUC, properties=["not a property"])

    def test_invalid_sequence_fails_fast(self):
        with self.assertRaisesRegex(ValueError, "invalid DNA symbols"):
            validate_dna_sequence("ACNT")

    def test_build_feature_set_from_mapping_and_encode_vectors(self):
        config = {
            "combination_mode": "concatenate",
            "blocks": [
                {"name": "kmer2", "encoding": "kmer_frequency", "k": 2},
                {"name": "dinuc", "encoding": "physicochemical", "k": 2, "reference_tsv": str(DINUC), "properties": ["Base stacking"]},
            ],
        }
        feature_set = build_feature_set_from_mapping(config, base_dir=ROOT)
        matrix = encode_sequences_as_vectors(["ACGT", "TGCA"], feature_set)

        self.assertEqual(len(matrix), 2)
        self.assertEqual(len(matrix[0]), 16 + 3)

    def test_encode_multi_head_preserves_named_blocks(self):
        config = {
            "combination_mode": "multi_head",
            "blocks": [
                {"name": "one_hot", "encoding": "one_hot", "k": 1},
                {"name": "trinuc", "encoding": "physicochemical", "k": 3, "reference_tsv": str(TRINUC), "properties": ["Trinucleotide GC Content"]},
            ],
        }
        feature_set = build_feature_set_from_mapping(config, base_dir=ROOT)
        heads = encode_sequences_as_multi_head(["ACGT", "TGCA"], feature_set)

        self.assertEqual(set(heads), {"one_hot", "trinuc"})
        self.assertEqual(len(heads["one_hot"]), 2)
        self.assertEqual(len(heads["one_hot"][0]), 4)
        self.assertEqual(len(heads["trinuc"][0]), 2)


    def test_gc_content_skew_global_features(self):
        block = GCContentSkewEncoder().encode("ACGT")

        self.assertEqual(block.shape, (2,))
        self.assertEqual(block.values, [0.5, 0.0])
        self.assertEqual(block.metadata["encoding"], "gc_content_skew")
        self.assertEqual(block.metadata["feature_names"], "global_gc_content|global_gc_skew")

    def test_gc_content_skew_windowed_features(self):
        block = GCContentSkewEncoder(window_size=4, step=4, include_global=False).encode("GGCCATAT")

        self.assertEqual(block.shape, (4,))
        self.assertEqual(block.values, [1.0, 0.0, 0.0, 0.0])

    def test_pseknc_uses_physicochemical_property_subset(self):
        encoder = PseKNCEncoder.from_tsv(
            DINUC,
            name="psednc",
            properties=["Base stacking"],
            lambda_value=2,
            weight=0.1,
        )
        block = encoder.encode("ACGTAC")

        self.assertEqual(block.shape, (18,))
        self.assertEqual(block.metadata["encoding"], "pseknc")
        self.assertEqual(block.metadata["k"], 2)
        self.assertEqual(block.metadata["property_names"], "Base stacking")
        self.assertEqual(block.metadata["composition_count"], 16)
        self.assertEqual(block.metadata["correlation_count"], 2)

    def test_pseknc_rejects_invalid_lambda(self):
        with self.assertRaisesRegex(ValueError, "lambda_value must be >= 1"):
            PseKNCEncoder.from_tsv(DINUC, lambda_value=0)

    def test_build_feature_set_supports_gc_and_pseknc_blocks(self):
        config = {
            "combination_mode": "concatenate",
            "blocks": [
                {"name": "gc", "encoding": "gc_content_skew", "window_size": 4, "step": 4, "include_global": False},
                {
                    "name": "psednc",
                    "encoding": "pseknc",
                    "k": 2,
                    "reference_tsv": str(DINUC),
                    "properties": ["Base stacking"],
                    "lambda_value": 1,
                    "weight": 0.1,
                },
            ],
        }
        feature_set = build_feature_set_from_mapping(config, base_dir=ROOT)
        matrix = encode_sequences_as_vectors(["ACGTACGT"], feature_set)

        self.assertEqual(len(matrix), 1)
        self.assertEqual(len(matrix[0]), 4 + 17)

    def test_dna_bert_kmer_text_uses_overlapping_six_mers(self):
        text = dna_bert_kmer_text("ACGTACGT", k=6)

        self.assertEqual(text, "ACGTAC CGTACG GTACGT")

    def test_dna_bert_encoder_with_injected_backend(self):
        encoder = DnaBertEncoder(
            name="dna_bert_6",
            model_name="zhihan1996/DNA_bert_6",
            k=6,
            pooling="cls",
            max_length=64,
            backend=FakeDnaBertBackend(),
        )
        block = encoder.encode("ACGTACGT")

        self.assertEqual(block.shape, (4,))
        self.assertEqual(block.values, [3.0, 6.0, 64.0, 1.0])
        self.assertEqual(block.metadata["encoding"], "dna_bert")
        self.assertEqual(block.metadata["model_name"], "zhihan1996/DNA_bert_6")

    def test_dna_bert_feature_spec_defaults_to_model_and_k6(self):
        spec = feature_spec_from_mapping({"blocks": [{"name": "bert", "encoding": "dna_bert"}]})

        self.assertEqual(spec.blocks[0].k, 6)
        self.assertEqual(spec.blocks[0].model_name, "zhihan1996/DNA_bert_6")

    def test_dna_bert_rejects_non_six_mer_for_dna_bert_6(self):
        with self.assertRaisesRegex(ValueError, "expects k=6"):
            feature_spec_from_mapping({"blocks": [{"name": "bert", "encoding": "dna_bert", "k": 5}]})


if __name__ == "__main__":
    unittest.main()
