"""Independent exact arithmetic for a shipped synthetic reference table."""

from fractions import Fraction
from pathlib import Path

from thermalpath.comparison import loads_reference


def test_synthetic_recipe_matches_every_imported_row():
    root = Path(__file__).resolve().parents[2]
    base = root / "data/reference/synthetic_temperature"
    result = loads_reference(
        base.with_suffix(".csv").read_bytes(), base.with_suffix(".json").read_bytes()
    )
    # Independent rational recipe: T(t) = 300 K + (1/4 K/s) t.
    times = [Fraction(0), Fraction(5, 2), Fraction(10), Fraction(5, 2)]
    assert result.kind == "synthetic"
    assert result.mode == "transient"
    assert len(result.samples) == len(times)
    for i, (sample, time) in enumerate(zip(result.samples, times, strict=True), 1):
        assert sample.sample_id == f"sample-{i}"
        assert Fraction(sample.time_s) == time
        assert Fraction(sample.temperature_k) == 300 + time / 4
        assert sample.source_record == f"recipe evaluation {i}"
