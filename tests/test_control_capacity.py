from capsprom.data.control_capacity import excluded_intervals, free_runs, non_overlapping_slots


def test_exclusion_merges_and_clips():
    assert excluded_intervals([5, 10, 100], radius=3, length=102) == [(2, 14), (97, 102)]
    assert excluded_intervals([0], radius=2, length=10) == [(0, 3)]


def test_free_runs_and_slots():
    runs = free_runs([(2, 14), (97, 102)], length=102)
    assert runs == [(0, 2), (14, 97)]
    assert non_overlapping_slots(runs, window=81) == 1
    assert non_overlapping_slots(free_runs([], 200), window=81) == 2
