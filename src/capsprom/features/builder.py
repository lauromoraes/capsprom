"""Build feature encoders from experiment feature specifications."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .dna_bert import DEFAULT_DNA_BERT_MODEL, DnaBertEncoder
from .encoders import (
    CombinedFeatures,
    FeatureSetBuilder,
    KmerFrequencyEncoder,
    OneHotEncoder,
    PhysicochemicalEncoder,
)
from .sequence_derived import GCContentSkewEncoder, PseKNCEncoder


@dataclass(frozen=True)
class FeatureBlockSpec:
    """Validated configuration for one feature block."""

    name: str
    encoding: str
    k: int
    normalize: bool = True
    reference_tsv: Path | None = None
    properties: tuple[str, ...] | None = None
    window_size: int | None = None
    step: int | None = None
    include_global: bool = True
    include_skew: bool = True
    include_at_skew: bool = False
    lambda_value: int = 1
    weight: float = 0.05
    model_name: str | None = None
    pooling: str = "mean"
    max_length: int | None = None
    device: str | None = None


@dataclass(frozen=True)
class FeatureEngineeringSpec:
    """Feature configuration independent from model implementation details."""

    blocks: tuple[FeatureBlockSpec, ...]
    combination_mode: str = "concatenate"


def feature_spec_from_mapping(config: Mapping[str, Any], base_dir: Path | str = Path(".")) -> FeatureEngineeringSpec:
    """Create a feature-engineering specification from a configuration mapping.

    The expected mapping corresponds to the `features` section of the project
    experiment configuration. This function intentionally receives a plain
    mapping so it does not depend on a specific YAML parser.
    """

    base_path = Path(base_dir)
    blocks_config = config.get("blocks")
    if not isinstance(blocks_config, Sequence) or isinstance(blocks_config, (str, bytes)):
        raise ValueError("features.blocks must be a sequence of feature block mappings")

    blocks = tuple(_block_spec_from_mapping(block, base_path) for block in blocks_config)
    names = [block.name for block in blocks]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise ValueError(f"feature block names must be unique: {duplicates}")

    combination_mode = str(config.get("combination_mode", "concatenate"))
    if combination_mode not in {"concatenate", "multi_head"}:
        raise ValueError("features.combination_mode must be 'concatenate' or 'multi_head'")

    return FeatureEngineeringSpec(blocks=blocks, combination_mode=combination_mode)


def _block_spec_from_mapping(config: Any, base_dir: Path) -> FeatureBlockSpec:
    if not isinstance(config, Mapping):
        raise ValueError("each feature block must be a mapping")

    name = str(config.get("name", "")).strip()
    encoding = str(config.get("encoding", "")).strip()
    if not name:
        raise ValueError("feature block is missing a non-empty name")
    if encoding not in {"kmer_frequency", "one_hot", "physicochemical", "gc_content_skew", "pseknc", "dna_bert"}:
        raise ValueError(f"unsupported feature encoding {encoding!r} for block {name!r}")

    default_k = 6 if encoding == "dna_bert" else 1 if encoding == "gc_content_skew" else None
    try:
        k = int(config.get("k", default_k))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"feature block {name!r} must define integer k") from exc
    if k < 1:
        raise ValueError(f"feature block {name!r} must use k >= 1")

    if encoding == "dna_bert" and k != 6:
        raise ValueError(
            f"DNA-BERT block {name!r} uses model {config.get('model_name', DEFAULT_DNA_BERT_MODEL)!r}; "
            "zhihan1996/DNA_bert_6 expects k=6"
        )

    reference_tsv = None
    if encoding in {"physicochemical", "pseknc"}:
        raw_reference = config.get("reference_tsv")
        if not raw_reference:
            raise ValueError(f"{encoding} block {name!r} must define reference_tsv")
        reference_tsv = Path(raw_reference)
        if not reference_tsv.is_absolute():
            reference_tsv = base_dir / reference_tsv

    properties = config.get("properties")
    if properties is not None:
        if not isinstance(properties, Sequence) or isinstance(properties, (str, bytes)):
            raise ValueError(f"feature block {name!r} properties must be a sequence of names")
        properties = tuple(str(property_name) for property_name in properties)

    pooling = str(config.get("pooling", "mean"))
    if encoding == "dna_bert" and pooling not in {"mean", "cls"}:
        raise ValueError(f"DNA-BERT block {name!r} pooling must be 'mean' or 'cls'")

    window_size = _optional_int(config, "window_size", name)
    step = _optional_int(config, "step", name)
    lambda_value = int(config.get("lambda_value", 1))
    weight = float(config.get("weight", 0.05))

    max_length = config.get("max_length")
    if max_length is not None:
        try:
            max_length = int(max_length)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"feature block {name!r} max_length must be an integer") from exc

    return FeatureBlockSpec(
        name=name,
        encoding=encoding,
        k=k,
        normalize=bool(config.get("normalize", True)),
        reference_tsv=reference_tsv,
        properties=properties,
        window_size=window_size,
        step=step,
        include_global=bool(config.get("include_global", True)),
        include_skew=bool(config.get("include_skew", True)),
        include_at_skew=bool(config.get("include_at_skew", False)),
        lambda_value=lambda_value,
        weight=weight,
        model_name=str(config.get("model_name", DEFAULT_DNA_BERT_MODEL)) if encoding == "dna_bert" else None,
        pooling=pooling,
        max_length=max_length,
        device=str(config["device"]) if "device" in config and config["device"] is not None else None,
    )


def _optional_int(config: Mapping[str, Any], key: str, block_name: str) -> int | None:
    value = config.get(key)
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"feature block {block_name!r} {key} must be an integer") from exc


def build_feature_set(spec: FeatureEngineeringSpec) -> FeatureSetBuilder:
    """Instantiate the encoders declared by a feature-engineering specification."""

    encoders = []
    for block in spec.blocks:
        if block.encoding == "kmer_frequency":
            encoders.append(KmerFrequencyEncoder(k=block.k, normalize=block.normalize, name=block.name))
        elif block.encoding == "one_hot":
            encoders.append(OneHotEncoder(k=block.k, name=block.name))
        elif block.encoding == "physicochemical":
            if block.reference_tsv is None:
                raise ValueError(f"physicochemical block {block.name!r} is missing reference_tsv")
            encoder = PhysicochemicalEncoder.from_tsv(
                block.reference_tsv,
                name=block.name,
                properties=block.properties,
            )
            if encoder.table.k != block.k:
                raise ValueError(
                    f"physicochemical block {block.name!r} declares k={block.k}, "
                    f"but reference table has k={encoder.table.k}"
                )
            encoders.append(encoder)
        elif block.encoding == "gc_content_skew":
            encoders.append(
                GCContentSkewEncoder(
                    name=block.name,
                    window_size=block.window_size,
                    step=block.step,
                    include_global=block.include_global,
                    include_skew=block.include_skew,
                    include_at_skew=block.include_at_skew,
                )
            )
        elif block.encoding == "pseknc":
            if block.reference_tsv is None:
                raise ValueError(f"pseknc block {block.name!r} is missing reference_tsv")
            encoder = PseKNCEncoder.from_tsv(
                block.reference_tsv,
                name=block.name,
                properties=block.properties,
                lambda_value=block.lambda_value,
                weight=block.weight,
            )
            if encoder.table.k != block.k:
                raise ValueError(
                    f"pseknc block {block.name!r} declares k={block.k}, "
                    f"but reference table has k={encoder.table.k}"
                )
            encoders.append(encoder)
        elif block.encoding == "dna_bert":
            encoders.append(
                DnaBertEncoder(
                    model_name=block.model_name or DEFAULT_DNA_BERT_MODEL,
                    k=block.k,
                    pooling=block.pooling,
                    max_length=block.max_length,
                    device=block.device,
                    name=block.name,
                )
            )
        else:  # pragma: no cover - guarded by validation
            raise ValueError(f"unsupported feature encoding {block.encoding!r}")
    return FeatureSetBuilder(encoders)


def build_feature_set_from_mapping(config: Mapping[str, Any], base_dir: Path | str = Path(".")) -> FeatureSetBuilder:
    """Build a feature set directly from a configuration mapping."""

    return build_feature_set(feature_spec_from_mapping(config, base_dir=base_dir))


def encode_sequences_as_vectors(sequences: Sequence[str], feature_set: FeatureSetBuilder) -> list[list[float]]:
    """Encode sequences as flattened vectors for classical classifiers."""

    return [feature_set.encode(sequence).as_flat_vector() for sequence in sequences]


def encode_sequences_as_multi_head(
    sequences: Sequence[str],
    feature_set: FeatureSetBuilder,
) -> dict[str, list[list[list[float]] | list[float]]]:
    """Encode sequences as named feature heads for deep-learning models."""

    heads: dict[str, list[list[list[float]] | list[float]]] = {}
    for sequence in sequences:
        combined: CombinedFeatures = feature_set.encode(sequence)
        for name, values in combined.as_multi_head_inputs().items():
            heads.setdefault(name, []).append(values)
    return heads
