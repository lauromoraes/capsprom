"""DNA-BERT feature encoding utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .encoders import FeatureBlock, sliding_kmers

DEFAULT_DNA_BERT_MODEL = "zhihan1996/DNA_bert_6"


class DnaBertBackend(Protocol):
    """Minimal backend interface used by :class:`DnaBertEncoder`."""

    def encode_text(self, text: str, pooling: str, max_length: int | None) -> list[float]:
        """Return one embedding vector for a space-separated k-mer sentence."""


@dataclass(frozen=True)
class TransformersDnaBertBackend:
    """Hugging Face Transformers backend for DNA-BERT embeddings."""

    model_name: str = DEFAULT_DNA_BERT_MODEL
    device: str | None = None

    def __post_init__(self) -> None:
        try:
            import torch  # noqa: F401
            from transformers import AutoModel, AutoTokenizer
        except ImportError as exc:  # pragma: no cover - depends on optional packages
            raise ImportError(
                "DNA-BERT features require optional dependencies `torch` and `transformers`. "
                "Install them in the project environment before using encoding='dna_bert'."
            ) from exc

        object.__setattr__(self, "_torch", __import__("torch"))
        tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        model = AutoModel.from_pretrained(self.model_name)
        if self.device is not None:
            model = model.to(self.device)
        model.eval()
        object.__setattr__(self, "_tokenizer", tokenizer)
        object.__setattr__(self, "_model", model)

    def encode_text(self, text: str, pooling: str, max_length: int | None) -> list[float]:
        tokenizer = getattr(self, "_tokenizer")
        model = getattr(self, "_model")
        torch = getattr(self, "_torch")
        encoded = tokenizer(
            text,
            return_tensors="pt",
            truncation=max_length is not None,
            max_length=max_length,
        )
        if self.device is not None:
            encoded = {key: value.to(self.device) for key, value in encoded.items()}
        with torch.no_grad():
            output = model(**encoded)
        hidden = output.last_hidden_state[0]
        if pooling == "cls":
            vector = hidden[0]
        elif pooling == "mean":
            attention_mask = encoded.get("attention_mask")
            if attention_mask is None:
                vector = hidden.mean(dim=0)
            else:
                mask = attention_mask[0].to(hidden.device).unsqueeze(-1).float()
                vector = (hidden * mask).sum(dim=0) / mask.sum(dim=0).clamp(min=1.0)
        else:
            raise ValueError("DNA-BERT pooling must be 'mean' or 'cls'")
        return [float(value) for value in vector.detach().cpu().tolist()]


def dna_bert_kmer_text(sequence: str, k: int = 6) -> str:
    """Return the space-separated k-mer sentence expected by DNABERT-style models."""

    if k < 1:
        raise ValueError("k must be >= 1")
    kmers = sliding_kmers(sequence, k)
    if not kmers:
        raise ValueError(f"sequence length must be at least k={k} for DNA-BERT encoding")
    return " ".join(kmers)


class DnaBertEncoder:
    """Encode DNA sequences with a DNABERT-style Hugging Face model."""

    def __init__(
        self,
        model_name: str = DEFAULT_DNA_BERT_MODEL,
        k: int = 6,
        pooling: str = "mean",
        max_length: int | None = None,
        device: str | None = None,
        name: str | None = None,
        backend: DnaBertBackend | None = None,
    ) -> None:
        if pooling not in {"mean", "cls"}:
            raise ValueError("DNA-BERT pooling must be 'mean' or 'cls'")
        self.model_name = model_name
        self.k = k
        self.pooling = pooling
        self.max_length = max_length
        self.device = device
        self.name = name or f"dna_bert_k{self.k}"
        self._backend = backend

    @property
    def backend(self) -> DnaBertBackend:
        if self._backend is None:
            self._backend = TransformersDnaBertBackend(model_name=self.model_name, device=self.device)
        return self._backend

    def encode(self, sequence: str) -> FeatureBlock:
        text = dna_bert_kmer_text(sequence, self.k)
        vector = self.backend.encode_text(text, pooling=self.pooling, max_length=self.max_length)
        return FeatureBlock(
            name=self.name,
            values=vector,
            shape=(len(vector),),
            metadata={
                "encoding": "dna_bert",
                "model_name": self.model_name,
                "k": self.k,
                "pooling": self.pooling,
                "max_length": self.max_length or 0,
            },
        )
