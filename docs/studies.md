# Steady-network parameter sweeps

`thermalpath.studies` evaluates a finite Cartesian product of prescribed network
inputs. It supports nodal power in W, fixed reservoir temperature in K, and link
conductance in W/K. Topology and boundary type remain fixed. Plate sweeps,
derivatives, uncertainty sampling, and candidate selection are outside this API.

```python
from thermalpath import Link, Network, Node
from thermalpath.studies import SweepAxis, replay_network_sweep, sweep_network

base = Network(
    (Node("body"), Node("sink", fixed_temperature_k=300)),
    (Link("path", "body", "sink", 1),),
)
csv_text = sweep_network(
    base,
    (
        SweepAxis("power_w", "body", (0, 10, 20)),
        SweepAxis("conductance_w_k", "path", (1, 2, 0)),
    ),
)
assert replay_network_sweep(csv_text) == csv_text
with open("network-sweep.csv", "x", encoding="utf-8", newline="") as stream:
    stream.write(csv_text)
```

The last axis varies fastest. This example produces nine rows in the supplied
order: six solutions and three rejected zero-conductance cases. Duplicate axis
values produce duplicate cases with distinct zero-based indices. No axes runs
the base case once. The immutable base network is unchanged.

Run `python examples/network_sweep.py network-sweep.csv` to export this study to
a new file. The example checks replay, prints case counts and measured global
heat imbalance, and refuses to overwrite an existing file.

## Bounds and failures

A sweep accepts at most eight distinct axes, 256 combinations, 64 nodes, and
128 links. Each axis has 1 to 256 finite real values. Each complete case JSON is
limited to 32768 characters; CSV replay accepts at most 32 MiB of characters.
These bounds limit a serial dense-solver workload; they are not accuracy bounds.
Examples and tests use one numerical thread. Applications should apply their
own numerical thread limits before importing numerical libraries.

Unknown targets, duplicate targets, invalid axis collections, nonfinite values,
and excessive sweep sizes reject the whole request. Power axes must target
unknown-temperature nodes; temperature axes must target prescribed-temperature
nodes. Finite but physically invalid candidates, such as zero conductance or
negative absolute temperature, remain in the export with `status=failed` and the
reason. A disconnected case, numerical range failure, or nonpositive computed
temperature also produces a failed row. Failed rows have empty result fields.
Subsequent cases still run. Unexpected programming exceptions propagate rather
than being labelled as physical failures. No partial CSV is returned on a
whole-request exception.

## CSV schema and replay

CSV uses a header, comma separators, quoted text fields, and LF line endings.
Save it as UTF-8 with newline translation disabled. Column order is:

| Column | Meaning |
| --- | --- |
| `sweep_schema_version` | Integer 1 |
| `case_index` | Consecutive integer starting at zero |
| `case_json` | Complete version-1 network JSON, including all nodes, links, defaults and SI inputs |
| `status` | `ok` or `failed` |
| `error` | Failure reason, empty on success |
| `temperatures_k_json` | Node ID to absolute temperature [K] |
| `link_powers_w_json` | Link ID to signed power [W], positive from node_a to node_b |
| `linear_residual_w_json` | Unknown node ID to assembled b - A*T [W] |
| `imbalance_w` | Total source power minus net power removed by reservoirs [W] |

The case JSON uses the [existing network schema](cases.md). Field names carry
the units; binary64 inputs round-trip exactly with Python's JSON decoder. Input
array order and identifiers survive CSV quoting, including commas and newlines.
The file carries each expanded case, so replay needs neither the base network
nor the original axes. It does not retain the user's original decimal spelling.

`replay_network_sweep` verifies the CSV header, version, row widths, consecutive
indices, and bounds. It recomputes all cases from `case_json`. It deliberately
ignores every old output column, including status and error. Invalid network
specifications become failed rows. Replay is not an authenticity check: altered
inputs are evaluated as supplied, and changed results are not automatically
classified as regressions. Keep the original file and source revision when
comparing implementations. Same-environment repeatability is tested; numerical
bit identity across library versions and platforms is not promised.

CSV quoting does not prevent spreadsheet formula interpretation. Import text
columns as text when opening a file containing untrusted identifiers or errors.

## Equations and verification

Every admitted case solves the existing steady equation
`L_uu T_u = P_u - L_uf T_f`. Positive conductances and a path from every unknown
node to a fixed reservoir give an anchored positive-definite system. A sweep
does not change that uniqueness condition or improve conditioning. Matrix
residual and physical heat balance are reported separately.

For the example, conservation gives `G (T_body - T_sink) = P`, hence
`T_body = T_sink + P/G`. The six successful temperatures are 300, 300, 310,
305, 320, and 310 K. Heat input and oriented link power agree. Zero-conductance
candidates are rejected by the established model domain even at zero load.

An independent test uses two unknown nodes, powers P and 3 W, and a 2 W/K link
from the second node to the reservoir. Its exact balances give
`T_b = T_sink + (P + 3 W)/(2 W/K)` and `T_a = T_b + P/G_ab`.
Eighteen cases cover negative, zero and positive P, three conductances, and two
reservoir temperatures. Rational reference arithmetic checks every temperature
and signed power, with absolute tolerances of 2e-12 K and 2e-12 W and no relative
tolerance. Replay and fresh-process CSV checks cover ordering, failures and
input preservation. These are numerical and software checks, not physical
validation or a guarantee of accuracy for arbitrary networks.
