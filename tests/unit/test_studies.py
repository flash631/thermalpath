"""Sweep admission, ordering, failures and self-contained replay contracts."""

import csv
import io
import json

import pytest

from thermalpath import Link, Network, Node
from thermalpath.studies import SweepAxis, replay_network_sweep, sweep_network


def network():
    return Network(
        (Node("hot", power_w=10), Node("sink", fixed_temperature_k=300)),
        (Link("path", "hot", "sink", 2),),
    )


def rows(text):
    return list(csv.DictReader(io.StringIO(text)))


def rewrite(text, change):
    table = list(csv.reader(io.StringIO(text)))
    change(table)
    output = io.StringIO(newline="")
    csv.writer(output, lineterminator="\n").writerows(table)
    return output.getvalue()


def test_order_duplicates_failures_and_exact_replay():
    base = network()
    axes = [
        SweepAxis("power_w", "hot", [0, 12, 12]),
        SweepAxis("conductance_w_k", "path", [2, 0, 4]),
    ]
    text = sweep_network(base, axes)
    data = rows(text)
    assert len(data) == 9
    assert [row["case_index"] for row in data] == list(map(str, range(9)))
    for i, row in enumerate(data):
        case = json.loads(row["case_json"])
        assert case["nodes"][0]["power_w"] == [0, 12, 12][i // 3]
        assert case["links"][0]["conductance_w_k"] == [2, 0, 4][i % 3]
        assert case["nodes"][1]["fixed_temperature_k"] == 300
        assert case["nodes"][1]["power_w"] == 0
        assert case["nodes"][0]["fixed_temperature_k"] is None
        assert row["status"] == ("failed" if i % 3 == 1 else "ok")
        if row["status"] == "failed":
            assert "positive" in row["error"]
            assert all(row[key] == "" for key in list(row)[5:])
    assert base == network()
    assert replay_network_sweep(text) == text
    assert sweep_network(base, axes) == text


def test_fixed_temperature_axis_and_failed_solution():
    text = sweep_network(
        network(),
        (SweepAxis("fixed_temperature_k", "sink", (300, -1)),),
    )
    assert [row["status"] for row in rows(text)] == ["ok", "failed"]
    text = sweep_network(network(), (SweepAxis("power_w", "hot", (-1000, 2)),))
    assert [row["status"] for row in rows(text)] == ["failed", "ok"]
    assert replay_network_sweep(text) == text


def test_zero_axes_and_unanchored_cases():
    assert len(rows(sweep_network(network(), ()))) == 1
    row = rows(sweep_network(Network((Node("unanchored"),)), ()))[0]
    assert row["status"] == "failed"
    assert row["error"]


def test_arbitrary_identifiers_and_binary64_round_trip():
    name = 'node, "quoted"\nline \u03b1'
    base = Network(
        (
            Node(name, power_w=0.12345678901234567),
            Node("sink", fixed_temperature_k=300),
        ),
        (Link("=link", name, "sink", 0.31),),
    )
    text = sweep_network(base, ())
    row = rows(text)[0]
    assert json.loads(row["case_json"])["nodes"][0]["id"] == name
    assert json.loads(row["case_json"])["nodes"][0]["power_w"] == base.nodes[0].power_w
    assert replay_network_sweep(text) == text


def test_replay_recomputes_and_does_not_trust_stale_outputs():
    text = sweep_network(network(), ())
    changed = rewrite(text, lambda t: t[1].__setitem__(slice(3, None), ["old"] * 6))
    assert replay_network_sweep(changed) == text
    invalid = rewrite(text, lambda t: t[1].__setitem__(2, '{"schema_version":99}'))
    row = rows(replay_network_sweep(invalid))[0]
    assert row["status"] == "failed"
    assert row["case_json"] == '{"schema_version":99}'


@pytest.mark.parametrize("field", ["bad", None, []])
def test_invalid_axis_field(field):
    with pytest.raises(ValueError, match="field"):
        SweepAxis(field, "hot", (1,))


@pytest.mark.parametrize("target", ["", None, 1])
def test_invalid_axis_target(target):
    with pytest.raises(ValueError, match="target_id"):
        SweepAxis("power_w", target, (1,))


@pytest.mark.parametrize("values", [(), [], (1,) * 257, "123", iter([1]), None])
def test_invalid_axis_values(values):
    with pytest.raises(ValueError, match="entries"):
        SweepAxis("power_w", "hot", values)


@pytest.mark.parametrize("value", [True, None, "1", float("nan"), float("inf")])
def test_invalid_scalar(value):
    with pytest.raises(ValueError):
        SweepAxis("power_w", "hot", (value,))


@pytest.mark.parametrize(
    "axes", [None, {}, "axis", [None], [SweepAxis("power_w", "hot", (1,))] * 9]
)
def test_invalid_axes(axes):
    with pytest.raises(ValueError, match="axes|SweepAxis"):
        sweep_network(network(), axes)


@pytest.mark.parametrize(
    "axes,match",
    [
        ((SweepAxis("power_w", "missing", (1,)),), "exist"),
        ((SweepAxis("power_w", "sink", (1,)),), "boundary"),
        ((SweepAxis("fixed_temperature_k", "hot", (1,)),), "boundary"),
        ((SweepAxis("power_w", "hot", (1,)),) * 2, "duplicate"),
        (
            (
                SweepAxis("power_w", "hot", tuple(range(17))),
                SweepAxis("conductance_w_k", "path", tuple(range(16))),
            ),
            "256",
        ),
    ],
)
def test_invalid_targets_and_product_size(axes, match):
    with pytest.raises(ValueError, match=match):
        sweep_network(network(), axes)


def test_network_size_and_type_limits():
    with pytest.raises(ValueError, match="Network"):
        sweep_network(None, ())
    with pytest.raises(ValueError, match="64 nodes"):
        sweep_network(Network(tuple(Node(str(i)) for i in range(65))), ())
    base = network()
    with pytest.raises(ValueError, match="128 links"):
        sweep_network(
            Network(
                base.nodes, tuple(Link(str(i), "hot", "sink", 1) for i in range(129))
            ),
            (),
        )
    with pytest.raises(ValueError, match="32768"):
        sweep_network(Network((Node("x" * 32768, fixed_temperature_k=300),)), ())


def test_case_bound_is_inclusive():
    text = sweep_network(network(), (SweepAxis("power_w", "hot", tuple(range(256))),))
    assert len(rows(text)) == 256
    assert replay_network_sweep(text) == text
    extra = rewrite(text, lambda t: t.append(t[-1]))
    with pytest.raises(ValueError, match="256"):
        replay_network_sweep(extra)


@pytest.mark.parametrize(
    "text",
    [None, "x" * (32 * 1024 * 1024 + 1), "", "wrong\n"],
    ids=["none", "oversize", "empty", "header"],
)
def test_invalid_csv_text(text):
    with pytest.raises(ValueError):
        replay_network_sweep(text)


@pytest.mark.parametrize("column,value", [(0, "2"), (1, "1"), (1, "00")])
def test_csv_envelope(column, value):
    text = rewrite(
        sweep_network(network(), ()), lambda t: t[1].__setitem__(column, value)
    )
    with pytest.raises(ValueError, match="version, index"):
        replay_network_sweep(text)


def test_empty_bad_width_syntax_and_oversize_case_csv():
    text = sweep_network(network(), ())
    for changed, match in [
        (rewrite(text, lambda t: t.pop()), "no cases"),
        (rewrite(text, lambda t: t[1].pop()), "row width"),
        (text.splitlines()[0] + '\n"unterminated', "syntax"),
        (rewrite(text, lambda t: t[1].__setitem__(2, "x" * 32769)), "32768"),
    ]:
        with pytest.raises(ValueError, match=match):
            replay_network_sweep(changed)


def test_unexpected_errors_propagate(monkeypatch):
    def bug(network):
        raise RuntimeError("unexpected")

    monkeypatch.setattr("thermalpath.studies.solve_steady", bug)
    with pytest.raises(RuntimeError, match="unexpected"):
        sweep_network(network(), ())
