"""Reference import contracts, rejected inputs, and retained provenance."""

import csv
import hashlib
import io
import json
from dataclasses import FrozenInstanceError

import pytest

from thermalpath.comparison import loads_reference

HEADER = "sample_id,location_id,time_s,temperature_k,source_record\n"
CSV = (HEADER + "s1,body,,300,recipe row 1\n").encode()


def metadata(data=CSV, **updates):
    result = {
        "schema_version": 1,
        "kind": "synthetic",
        "mode": "steady",
        "source": "test fixture recipe",
        "license": "MIT",
        "description": "Synthetic constant-temperature fixture",
        "method": "Assign exactly 300 K to the body",
        "locations": {"body": "Lumped body temperature"},
        "units": {"temperature": "K", "time": "s"},
        "csv_sha256": hashlib.sha256(data).hexdigest(),
    }
    result.update(updates)
    return result


def sidecar(data=CSV, **updates):
    return json.dumps(metadata(data, **updates)).encode()


def test_steady_values_provenance_and_immutable_output():
    raw = sidecar()
    result = loads_reference(CSV, raw)
    assert result.kind == "synthetic"
    assert result.mode == "steady"
    assert result.source == "test fixture recipe"
    assert result.license == "MIT"
    assert result.description == "Synthetic constant-temperature fixture"
    assert result.method == "Assign exactly 300 K to the body"
    assert result.locations == (("body", "Lumped body temperature"),)
    row = result.samples[0]
    assert (row.sample_id, row.location_id, row.time_s) == ("s1", "body", None)
    assert row.temperature_k == 300
    assert row.source_record == "recipe row 1"
    assert result.csv_sha256 == hashlib.sha256(CSV).hexdigest()
    assert result.metadata_sha256 == hashlib.sha256(raw).hexdigest()
    assert loads_reference(CSV, raw) == result
    with pytest.raises(FrozenInstanceError):
        row.temperature_k = 1
    with pytest.raises(FrozenInstanceError):
        result.source = "changed"


def test_replicates_order_unicode_bom_crlf_and_quoted_locator():
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(HEADER.strip().split(","))
    writer.writerows(
        [
            ("z", "body", "2.5", "+3.0125e2", 'row 7, channel "Tα"'),
            ("a", "body", "0", ".300e3", "row 2"),
            ("b", "body", "2.5", "301.5", "row 8"),
        ]
    )
    data = output.getvalue().encode("utf-8-sig")
    raw = b"\xef\xbb\xbf" + sidecar(data, mode="transient")
    result = loads_reference(data, raw)
    assert [s.sample_id for s in result.samples] == ["z", "a", "b"]
    assert [s.time_s for s in result.samples] == [2.5, 0, 2.5]
    assert [s.temperature_k for s in result.samples] == [301.25, 300, 301.5]
    assert result.samples[0].source_record == 'row 7, channel "Tα"'
    assert result.csv_sha256 == hashlib.sha256(data).hexdigest()
    assert result.metadata_sha256 == hashlib.sha256(raw).hexdigest()


def test_experimental_label_is_retained_without_claiming_real_measurements():
    # A synthetic parser fixture exercising the experimental metadata branch.
    raw = sidecar(kind="experimental", method="Fictional acquisition contract for test")
    result = loads_reference(CSV, raw)
    assert result.kind == "experimental"
    assert result.method == "Fictional acquisition contract for test"


@pytest.mark.parametrize("field", list(metadata()))
def test_missing_metadata_field(field):
    meta = metadata()
    del meta[field]
    with pytest.raises(ValueError):
        loads_reference(CSV, json.dumps(meta).encode())


@pytest.mark.parametrize(
    "updates",
    [
        {"extra": "ignored?"},
        {"schema_version": True},
        {"schema_version": 1.0},
        {"schema_version": 2},
        {"kind": "measured"},
        {"kind": []},
        {"mode": "mixed"},
        {"mode": None},
        {"units": {"temperature": "degC", "time": "s"}},
        {"units": {"temperature": "K", "time": "ms"}},
        {"units": {"temperature": "K"}},
        {"units": "SI"},
        {"units": {"temperature": "K", "time": "s", "length": "m"}},
        {"locations": {}},
        {"locations": []},
        {"locations": {"": "body"}},
        {"locations": {"body": ""}},
        {"locations": {"body": 2}},
        {"csv_sha256": "0" * 64},
        {"csv_sha256": None},
    ],
)
def test_incompatible_metadata(updates):
    with pytest.raises(ValueError):
        loads_reference(CSV, sidecar(**updates))


@pytest.mark.parametrize("field", ["source", "license", "method", "description"])
@pytest.mark.parametrize(
    "value",
    [
        "",
        " ",
        "unknown",
        "N/A",
        "None",
        "unspecified",
        " leading",
        "trailing ",
        "a\nb",
        "a\x7fb",
        1,
        None,
    ],
)
def test_untraceable_or_malformed_declarations(field, value):
    with pytest.raises(ValueError):
        loads_reference(CSV, sidecar(**{field: value}))


@pytest.mark.parametrize(
    "raw",
    [
        b"{}",
        b"[]",
        b"null",
        b"{",
        b' {"x":1,"x":2}',
        b'{"units":{"time":"s","time":"ms"}}',
    ],
)
def test_invalid_json(raw):
    with pytest.raises(ValueError):
        loads_reference(CSV, raw)


@pytest.mark.parametrize("data", [b"", "text", bytearray(b"x"), b"\xff"])
@pytest.mark.parametrize("which", ["CSV", "metadata"])
def test_bad_bytes_or_encoding(data, which):
    with pytest.raises(ValueError):
        loads_reference(
            data if which == "CSV" else CSV, data if which == "metadata" else sidecar()
        )


def test_size_and_text_limits():
    for csv_data, meta_data in [(b"x" * 1048577, sidecar()), (CSV, b"x" * 65537)]:
        with pytest.raises(ValueError):
            loads_reference(csv_data, meta_data)
    with pytest.raises(ValueError):
        loads_reference(CSV, sidecar(source="x" * 2049))
    assert loads_reference(CSV, sidecar(source="x" * 2048)).source == "x" * 2048
    locations = {str(i): "x" for i in range(10001)}
    # Exceeds the byte bound first; both limits are independent admission caps.
    with pytest.raises(ValueError):
        loads_reference(CSV, sidecar(locations=locations))


@pytest.mark.parametrize(
    "text",
    [
        HEADER,
        "",
        HEADER.replace("temperature_k", "temperature_c") + "s,b,,1,r\n",
        HEADER.replace("sample_id,location_id", "location_id,sample_id") + "s,b,,1,r\n",
        HEADER + "\n",
        HEADER + "s1,body,,300\n",
        HEADER + "s1,body,,300,r,extra\n",
        HEADER + "s1,body,,300,r\ns1,body,,301,r2\n",
        HEADER + "s1,missing,,300,r\n",
        HEADER + ",body,,300,r\n",
        HEADER + "s1,body,,300,\n",
        HEADER + "s1,body,,300,unknown\n",
        HEADER + 's1,body,,300,"unclosed\n',
        HEADER + 's1,body,,300,"x"garbage\n',
        HEADER + 's1,body,,300,"multi\nline"\n',
        HEADER + "s1,body,0,300,r\n",
    ],
)
def test_bad_csv_rows(text):
    data = text.encode()
    with pytest.raises(ValueError):
        loads_reference(data, sidecar(data))


@pytest.mark.parametrize(
    "token",
    [
        "",
        "NaN",
        "inf",
        "-inf",
        "1e999",
        "1e-999",
        "-1",
        "0",
        "-0",
        " 300",
        "300 ",
        "3_00",
        "٣٠٠",
    ],
)
def test_invalid_temperatures(token):
    data = (HEADER + f"s1,body,,{token},r\n").encode()
    with pytest.raises(ValueError):
        loads_reference(data, sidecar(data))


@pytest.mark.parametrize("token", ["", "NaN", "1e999", "1e-999", "-1", "-1e-999"])
def test_invalid_transient_time(token):
    data = (HEADER + f"s1,body,{token},300,r\n").encode()
    with pytest.raises(ValueError):
        loads_reference(data, sidecar(data, mode="transient"))


def test_row_limit_and_small_positive_temperature():
    data = (
        HEADER + "".join(f"s{i},body,,5e-324,r{i}\n" for i in range(10000))
    ).encode()
    result = loads_reference(data, sidecar(data))
    assert len(result.samples) == 10000
    assert result.samples[0].temperature_k > 0
    data += b"s10000,body,,300,r10000\n"
    with pytest.raises(ValueError, match="10000"):
        loads_reference(data, sidecar(data))


def test_hash_detects_changed_value_and_changed_line_endings():
    raw = sidecar()
    for changed in [CSV.replace(b"300", b"301"), CSV.replace(b"\n", b"\r\n")]:
        with pytest.raises(ValueError, match="csv_sha256"):
            loads_reference(changed, raw)


def test_metadata_change_has_distinct_identity():
    left = loads_reference(CSV, sidecar())
    right = loads_reference(CSV, sidecar(source="another declared recipe"))
    assert left.samples == right.samples
    assert left.csv_sha256 == right.csv_sha256
    assert left.metadata_sha256 != right.metadata_sha256


def test_excessive_json_nesting():
    raw = b"[" * 10000 + b"0" + b"]" * 10000
    with pytest.raises(ValueError, match="nesting"):
        loads_reference(CSV, raw)
