"""Feature encoding utilities for CapsProm."""

from .physicochemical import PhysicochemicalTable, load_physicochemical_table
from .encoders import (
    FeatureBlock,
    CombinedFeatures,
    KmerFrequencyEncoder,
    OneHotEncoder,
    PhysicochemicalEncoder,
    FeatureSetBuilder,
)

__all__ = [
    "PhysicochemicalTable",
    "load_physicochemical_table",
    "FeatureBlock",
    "CombinedFeatures",
    "KmerFrequencyEncoder",
    "OneHotEncoder",
    "PhysicochemicalEncoder",
    "FeatureSetBuilder",
]
