import numpy as np
import pytest

from capsprom.data.sequence_logo import sequence_logo_matrices


def test_logo_matrix_has_two_bits_for_a_conserved_column():
    matrices = sequence_logo_matrices(["AC", "AC", "AC", "AC"])

    np.testing.assert_allclose(matrices.frequencies, [[1, 0, 0, 0], [0, 1, 0, 0]])
    np.testing.assert_allclose(
        matrices.information_heights, [[2, 0, 0, 0], [0, 2, 0, 0]]
    )


def test_logo_matrix_has_zero_bits_for_uniform_column():
    matrices = sequence_logo_matrices(["A", "C", "G", "T"])

    np.testing.assert_allclose(matrices.information_heights, [[0, 0, 0, 0]])


def test_logo_matrix_rejects_unaligned_or_invalid_sequences():
    with pytest.raises(ValueError, match="equal length"):
        sequence_logo_matrices(["AA", "A"])
    with pytest.raises(ValueError, match="invalid DNA"):
        sequence_logo_matrices(["AN"])
