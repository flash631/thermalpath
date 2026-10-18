"""Exact matching, denominator accounting and invalid comparison inputs."""

import math
from dataclasses import FrozenInstanceError, replace

import pytest

from thermalpath.comparison import (
    ReferenceData,
    ReferenceSample,
    TemperaturePrediction,
    compare_reference,
)

NOTE = "Same lumped body and temperature quantity; elapsed seconds from load onset."


def reference(samples=None, mode="steady"):
    return ReferenceData(
        "synthetic",
        mode,
        "arithmetic fixture",
        "MIT",
        "Synthetic temperatures",
        "Assign constants in kelvin",
        (("body", "Lumped body"),),
        samples
        if samples is not None
        else (ReferenceSample("a", "body", None, 300, "row 1"),),
        "0" * 64,
        "1" * 64,
    )


def test_order_replicates_missing_excluded_unused_and_immutable():
    samples = tuple(
        ReferenceSample(name, "body", time, temp, f"row {name}")
        for name, time, temp in (
            ("z", 2, 300),
            ("a", 0, 300),
            ("repeat", 2, 301),
            ("missing", 7, 300),
            ("excluded", 9, 300),
            ("excluded_missing", 10, 300),
        )
    )
    data = reference(samples, "transient")
    predictions = [
        TemperaturePrediction("body", 9, 309),
        TemperaturePrediction("body", 2, 303),
        TemperaturePrediction("body", 0, 296),
        TemperaturePrediction("extra", 0, 350),
    ]
    exclusions = {
        "excluded": "Predetermined holdout",
        "excluded_missing": "Sensor not comparable",
    }
    result = compare_reference(
        data, predictions, matching_note=NOTE, exclusions=exclusions
    )
    assert result.reference is data and result.matching_note == NOTE
    assert [r.sample.sample_id for r in result.rows] == [s.sample_id for s in samples]
    assert [r.status for r in result.rows] == ["matched"] * 3 + [
        "missing",
        "excluded",
        "excluded",
    ]
    assert [r.residual_k for r in result.rows] == [3, -4, 2, None, None, None]
    assert result.rows[4].prediction is predictions[0]
    assert result.rows[5].prediction is None
    assert result.rows[4].reason == exclusions["excluded"]
    assert result.rows[3].reason == "No exact location/time prediction"
    assert result.rows[0].reason is None
    assert result.unused_predictions == (predictions[0], predictions[3])
    assert (result.matched_count, result.missing_count, result.excluded_count) == (
        3,
        1,
        2,
    )
    assert result.rmse_k == pytest.approx(math.sqrt(29 / 3), abs=1e-14, rel=0)
    predictions.clear()
    exclusions.clear()
    assert (
        len(result.predictions) == 4
        and result.rows[4].reason == "Predetermined holdout"
    )
    with pytest.raises(FrozenInstanceError):
        result.rmse_k = 0
    with pytest.raises(FrozenInstanceError):
        result.rows[0].residual_k = 0


@pytest.mark.parametrize("excluded", [False, True])
def test_empty_denominator_is_none(excluded):
    result = compare_reference(
        reference(),
        [],
        matching_note=NOTE,
        exclusions={"a": "Different sensor quantity"} if excluded else None,
    )
    assert result.rmse_k is None and result.matched_count == 0
    assert result.excluded_count == int(excluded)
    assert result.missing_count == int(not excluded)


def test_exact_zero_and_single_row_sign():
    for value, residual in ((300, 0), (297, -3), (304, 4)):
        result = compare_reference(
            reference(),
            [TemperaturePrediction("body", None, value)],
            matching_note=NOTE,
        )
        assert result.rows[0].residual_k == residual
        assert result.rmse_k == abs(residual)


def test_times_and_locations_are_exact_without_interpolation():
    data = reference((ReferenceSample("a", "body", 0.3, 300, "row 1"),), "transient")
    predictions = [
        TemperaturePrediction("body", 0.1 + 0.2, 300),
        TemperaturePrediction("Body", 0.3, 300),
    ]
    result = compare_reference(data, predictions, matching_note=NOTE)
    assert result.missing_count == 1 and result.unused_predictions == tuple(predictions)
    assert result.rmse_k is None


@pytest.mark.parametrize(
    "field,value",
    [
        ("location_id", ""),
        ("location_id", " body"),
        ("location_id", 3),
        ("time_s", -1),
        ("time_s", True),
        ("time_s", "1"),
        ("time_s", float("nan")),
        ("time_s", float("inf")),
        ("temperature_k", 0),
        ("temperature_k", -1),
        ("temperature_k", True),
        ("temperature_k", "300"),
        ("temperature_k", float("nan")),
        ("temperature_k", float("inf")),
    ],
)
def test_invalid_predictions(field, value):
    args = {"location_id": "body", "time_s": None, "temperature_k": 300}
    args[field] = value
    with pytest.raises(ValueError):
        TemperaturePrediction(**args)


@pytest.mark.parametrize("mode,time", [("steady", 0), ("transient", None)])
def test_mode_mismatch(mode, time):
    data = reference(mode=mode)
    with pytest.raises(ValueError, match="prediction time"):
        compare_reference(
            data, [TemperaturePrediction("body", time, 300)], matching_note=NOTE
        )


@pytest.mark.parametrize("time", [None, 0.0])
def test_duplicate_prediction_keys_rejected(time):
    prediction = TemperaturePrediction("body", time, 300)
    data = reference(mode="steady" if time is None else "transient")
    duplicate = replace(prediction, time_s=None if time is None else -0.0)
    with pytest.raises(ValueError, match="unique"):
        compare_reference(data, [prediction, duplicate], matching_note=NOTE)


@pytest.mark.parametrize(
    "predictions",
    [
        None,
        "",
        b"",
        {},
        [None],
        [300],
        [TemperaturePrediction("body", None, 300)] * 10001,
    ],
    ids=["none", "text", "bytes", "mapping", "null-row", "number-row", "too-many"],
)
def test_invalid_prediction_collections(predictions):
    with pytest.raises(ValueError):
        compare_reference(reference(), predictions, matching_note=NOTE)


@pytest.mark.parametrize("note", ["", "unknown", " untrimmed", None])
def test_matching_note_required(note):
    with pytest.raises(ValueError):
        compare_reference(reference(), [], matching_note=note)


@pytest.mark.parametrize(
    "exclusions", [[], {"absent": "Reason"}, {"a": ""}, {"a": None}]
)
def test_invalid_exclusions(exclusions):
    with pytest.raises(ValueError):
        compare_reference(reference(), [], matching_note=NOTE, exclusions=exclusions)


@pytest.mark.parametrize(
    "data",
    [
        None,
        reference(mode="invalid"),
        reference(()),
        reference([]),
        reference((None,)),
        reference(reference().samples * 10001),
        reference(reference().samples * 2),
    ],
    ids=["type", "mode", "empty", "mutable", "row-type", "too-many", "duplicate-id"],
)
def test_invalid_reference_collection(data):
    with pytest.raises(ValueError):
        compare_reference(data, [], matching_note=NOTE)


@pytest.mark.parametrize(
    "field,value",
    [
        ("sample_id", ""),
        ("location_id", "missing"),
        ("source_record", ""),
        ("temperature_k", 0),
        ("temperature_k", float("nan")),
        ("time_s", 0),
    ],
)
def test_direct_reference_rows_revalidated_even_when_excluded(field, value):
    sample = replace(reference().samples[0], **{field: value})
    with pytest.raises(ValueError):
        compare_reference(
            reference((sample,)),
            [],
            matching_note=NOTE,
            exclusions={sample.sample_id: "Declared exclusion"},
        )


@pytest.mark.parametrize("time", [None, -1, float("nan"), True])
def test_invalid_transient_reference_time(time):
    data = reference((replace(reference().samples[0], time_s=time),), "transient")
    with pytest.raises(ValueError):
        compare_reference(data, [], matching_note=NOTE)


def test_maximum_rows_and_predictions_are_accepted():
    rows = tuple(
        ReferenceSample(str(i), "body", float(i), 300, "recipe") for i in range(10000)
    )
    predictions = tuple(TemperaturePrediction("body", i, 300) for i in range(10000))
    result = compare_reference(
        reference(rows, "transient"), predictions, matching_note=NOTE
    )
    assert result.matched_count == 10000 and result.rmse_k == 0
    assert result.unused_predictions == ()
