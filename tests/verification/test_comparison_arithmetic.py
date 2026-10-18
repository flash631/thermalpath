"""Independent rational and high-precision decimal residual/RMSE checks."""

from decimal import Decimal, localcontext
from fractions import Fraction

import pytest

from tests.unit.test_comparison_metrics import NOTE, reference
from thermalpath.comparison import (
    ReferenceSample,
    TemperaturePrediction,
    compare_reference,
)


@pytest.mark.parametrize(
    "reference_values,predicted_values",
    [
        ((300, 300), (303, 296)),
        ((300, 301, 302, 300), (303, 305, 302, 303)),
        ((300.125, 301.5, 302.25), (300.25, 301.25, 303)),
    ],
)
def test_rational_residuals_and_decimal_rmse(reference_values, predicted_values):
    rows = tuple(
        ReferenceSample(str(i), "body", i, t, "synthetic constants")
        for i, t in enumerate(reference_values)
    )
    predictions = tuple(
        TemperaturePrediction("body", i, t) for i, t in enumerate(predicted_values)
    )
    residuals = [
        Fraction(p) - Fraction(r)
        for p, r in zip(predicted_values, reference_values, strict=True)
    ]
    mse = sum(r * r for r in residuals) / len(residuals)
    with localcontext() as context:
        context.prec = 80
        expected = float((Decimal(mse.numerator) / Decimal(mse.denominator)).sqrt())
    result = compare_reference(
        reference(rows, "transient"), predictions, matching_note=NOTE
    )
    assert [r.residual_k for r in result.rows] == [float(r) for r in residuals]
    assert result.rmse_k == pytest.approx(expected, abs=1e-14, rel=0)


@pytest.mark.parametrize(
    "small,large", [(1e-300, 2e-300), (1e307, 1e308), (5e-324, 1e-323)]
)
def test_scaled_rmse_avoids_square_overflow_and_underflow(small, large):
    rows = (
        ReferenceSample("a", "body", 0, small, "row 1"),
        ReferenceSample("b", "body", 1, large, "row 2"),
    )
    predictions = (
        TemperaturePrediction("body", 0, large),
        TemperaturePrediction("body", 1, small),
    )
    with localcontext() as context:
        context.prec = 1100
        exact = abs(Decimal.from_float(large) - Decimal.from_float(small))
    result = compare_reference(
        reference(rows, "transient"), predictions, matching_note=NOTE
    )
    assert result.rmse_k > 0
    assert result.rmse_k == pytest.approx(float(exact), rel=2e-15, abs=0)
