"""Minimal random-access reader for UCSC twoBit genome files."""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from pathlib import Path
import struct
from typing import BinaryIO


_SIGNATURE = 0x1A412743
_BASES = "TCAG"
_COMPLEMENT = str.maketrans("ACGTNacgtn", "TGCANtgcan")


@dataclass(frozen=True)
class _SequenceMetadata:
    dna_size: int
    n_blocks: tuple[tuple[int, int], ...]
    mask_blocks: tuple[tuple[int, int], ...]
    packed_offset: int


class TwoBitGenome:
    """Read slices without loading a complete genome into memory."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self._handle = self.path.open("rb")
        self._endian, self._index = self._read_header(self._handle)
        self._metadata: dict[str, _SequenceMetadata] = {}

    def close(self) -> None:
        self._handle.close()

    def __enter__(self) -> "TwoBitGenome":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    @property
    def sequence_names(self) -> tuple[str, ...]:
        return tuple(self._index)

    def sequence_size(self, name: str) -> int:
        """Return the unpacked length of one indexed sequence."""

        return self._metadata_for(name).dna_size

    def fetch(self, name: str, start: int, end: int, *, reverse_complement: bool = False) -> str:
        metadata = self._metadata_for(name)
        if start < 0 or end < start or end > metadata.dna_size:
            raise ValueError(
                f"invalid interval {name}:{start}-{end} for length {metadata.dna_size}"
            )
        if start == end:
            return ""
        first_byte = start // 4
        last_byte = (end + 3) // 4
        self._handle.seek(metadata.packed_offset + first_byte)
        packed = self._handle.read(last_byte - first_byte)
        if len(packed) != last_byte - first_byte:
            raise ValueError(f"truncated packed DNA for {name}")
        sequence = "".join(
            _BASES[(packed[position // 4 - first_byte] >> (6 - 2 * (position % 4))) & 3]
            for position in range(start, end)
        )
        characters = list(sequence)
        _apply_blocks(characters, start, metadata.n_blocks, "N")
        _apply_blocks(characters, start, metadata.mask_blocks, None)
        result = "".join(characters)
        if reverse_complement:
            result = result.translate(_COMPLEMENT)[::-1]
        return result

    def _metadata_for(self, name: str) -> _SequenceMetadata:
        if name not in self._index:
            raise KeyError(f"sequence {name!r} not found in {self.path}")
        if name in self._metadata:
            return self._metadata[name]
        self._handle.seek(self._index[name])
        dna_size = self._uint32()
        n_starts = self._uint32_array(self._uint32())
        n_sizes = self._uint32_array(len(n_starts))
        mask_starts = self._uint32_array(self._uint32())
        mask_sizes = self._uint32_array(len(mask_starts))
        self._uint32()  # reserved
        metadata = _SequenceMetadata(
            dna_size=dna_size,
            n_blocks=tuple(zip(n_starts, n_sizes, strict=True)),
            mask_blocks=tuple(zip(mask_starts, mask_sizes, strict=True)),
            packed_offset=self._handle.tell(),
        )
        self._metadata[name] = metadata
        return metadata

    def _uint32(self) -> int:
        data = self._handle.read(4)
        if len(data) != 4:
            raise ValueError(f"truncated twoBit file: {self.path}")
        return struct.unpack(f"{self._endian}I", data)[0]

    def _uint32_array(self, count: int) -> tuple[int, ...]:
        if count == 0:
            return ()
        data = self._handle.read(4 * count)
        if len(data) != 4 * count:
            raise ValueError(f"truncated twoBit array: {self.path}")
        return struct.unpack(f"{self._endian}{count}I", data)

    @staticmethod
    def _read_header(handle: BinaryIO) -> tuple[str, dict[str, int]]:
        signature = handle.read(4)
        if len(signature) != 4:
            raise ValueError("truncated twoBit header")
        if struct.unpack(">I", signature)[0] == _SIGNATURE:
            endian = ">"
        elif struct.unpack("<I", signature)[0] == _SIGNATURE:
            endian = "<"
        else:
            raise ValueError("invalid twoBit signature")
        version, sequence_count, reserved = struct.unpack(f"{endian}III", handle.read(12))
        if version != 0 or reserved != 0:
            raise ValueError(f"unsupported twoBit header version={version} reserved={reserved}")
        index = {}
        for _ in range(sequence_count):
            name_size_data = handle.read(1)
            if not name_size_data:
                raise ValueError("truncated twoBit index")
            name = handle.read(name_size_data[0]).decode("ascii")
            offset_data = handle.read(4)
            if len(offset_data) != 4:
                raise ValueError("truncated twoBit index offset")
            offset = struct.unpack(f"{endian}I", offset_data)[0]
            if name in index:
                raise ValueError(f"duplicate twoBit sequence name: {name}")
            index[name] = offset
        return endian, index


def _apply_blocks(
    characters: list[str], interval_start: int, blocks: tuple[tuple[int, int], ...], value: str | None
) -> None:
    if not blocks:
        return
    interval_end = interval_start + len(characters)
    first = max(0, bisect_right(blocks, (interval_start, 2**32)) - 1)
    for block_start, block_size in blocks[first:]:
        if block_start >= interval_end:
            break
        overlap_start = max(interval_start, block_start)
        overlap_end = min(interval_end, block_start + block_size)
        for position in range(overlap_start, overlap_end):
            index = position - interval_start
            characters[index] = value if value is not None else characters[index].lower()
