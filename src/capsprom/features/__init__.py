"""Feature encoding utilities for CapsProm."""

from .physicochemical import PhysicochemicalTable, load_physicochemical_table
from .dna_bert import (
    DEFAULT_DNA_BERT_MODEL,
    DnaBertEncoder,
    TransformersDnaBertBackend,
    dna_bert_kmer_text,
)
from .sequence_derived import GCContentSkewEncoder, PseKNCEncoder
from .encoders import (
    FeatureBlock,
    CombinedFeatures,
    KmerFrequencyEncoder,
    OneHotEncoder,
    PhysicochemicalEncoder,
    FeatureSetBuilder,
    validate_dna_sequence,
)
from .builder import (
    FeatureBlockSpec,
    FeatureEngineeringSpec,
    build_feature_set,
    build_feature_set_from_mapping,
    encode_sequences_as_multi_head,
    encode_sequences_as_vectors,
    feature_spec_from_mapping,
)

__all__ = [
    "PhysicochemicalTable",
    "load_physicochemical_table",
    "FeatureBlock",
    "CombinedFeatures",
    "KmerFrequencyEncoder",
    "OneHotEncoder",
    "PhysicochemicalEncoder",
    "GCContentSkewEncoder",
    "PseKNCEncoder",
    "FeatureSetBuilder",
    "validate_dna_sequence",
    "FeatureBlockSpec",
    "DEFAULT_DNA_BERT_MODEL",
    "DnaBertEncoder",
    "TransformersDnaBertBackend",
    "dna_bert_kmer_text",
    "FeatureEngineeringSpec",
    "build_feature_set",
    "build_feature_set_from_mapping",
    "encode_sequences_as_multi_head",
    "encode_sequences_as_vectors",
    "feature_spec_from_mapping",
]
