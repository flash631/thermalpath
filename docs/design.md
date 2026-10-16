# Compare network candidates

`thermalpath.design.compare_network_candidates` checks named link alternatives
against common upper temperature limits. Supply the nodes once: all candidates
have the same node identifiers, applied powers and prescribed temperatures.
Only the links can change. Positive conductances and valid endpoints define
admissible network inputs; they do not establish manufacturability or physical
feasibility. Disconnected alternatives remain in the comparison if solving fails.

```python
from thermalpath import Link, Node
from thermalpath.design import (
    NetworkCandidate,
    TemperatureRequirement,
    compare_network_candidates,
)

comparison = compare_network_candidates(
    (Node("body", power_w=10), Node("sink", fixed_temperature_k=300)),
    (
        NetworkCandidate("path_a", (Link("g", "body", "sink", 2),)),
        NetworkCandidate("path_b", (Link("g", "body", "sink", 4),)),
    ),
    (TemperatureRequirement("body", 305),),
    comparison_tolerance_k=1e-9,
)
assert [item.status for item in comparison.assessments] == ["borderline", "meets"]
assert comparison.assessments[1].minimum_margin_k == 2.5
```

For required node i, the margin is `maximum_k - temperature_k`, in kelvin.
The smallest margin controls the candidate classification. With the explicit
nonnegative band `comparison_tolerance_k = e`:

| Status | Rule |
| --- | --- |
| `exceeds` | At least one margin is less than `-e`. |
| `meets` | Every margin is greater than `e`. |
| `borderline` | Neither rule holds, including equality at either band edge. |
| `failed` | The solve failed; margins are empty and minimum margin is `None`. |

The band specifies decision resolution. It does not estimate numerical error
or provide an uncertainty bound. At zero band, exact equality remains borderline.
Required nodes can include fixed-temperature nodes. A failing requirement takes
precedence over any passing or borderline requirement on another node.

All alternatives stay in input order. Equal alternatives keep equal margins;
there is no automatic winner or tie breaker. The comparison does not rank cost,
mass, manufacturing constraints or cooling performance outside the stated case.
An infeasible temperature requirement is retained as `exceeds`; a failed solve
is a separate outcome and is never interpreted as zero temperature or zero margin.

The result retains every common requirement and the decision band. Each row of
`cases_csv` contains the full SI network inputs, temperatures, signed link powers,
linear residual and separate global power imbalance, or the failure message.
Row i belongs to `assessments[i]`. Save both the assessments/requirements and CSV
to preserve candidate names and classification settings. The existing
`replay_network_sweep(comparison.cases_csv)` recomputes all network solves.

Inputs are bounded to 64 candidates, 64 common nodes, 128 links per candidate,
64 distinct node requirements and 32768 characters per serialized network.
Lists are copied. Duplicate candidate names, duplicate requirement nodes, missing
endpoints and invalid scalar domains are rejected before any solve. Valid input
networks can still produce retained solver failures, such as unanchored nodes or
nonpositive calculated temperatures. Unexpected programming errors propagate.

This is a nominal model comparison: uncertainty is not evaluated. The result
carries this qualification explicitly. The [uncertainty helper](uncertainty.md)
can study separately declared distributions; its finite percentiles are also
conditional model outputs. A nominal pass does not imply a pass under uncertain
loads, model error or other operating conditions, and establishes no safety,
reliability or physical-validation claim.

Run `python examples/network_candidates.py` for five synthetic alternatives.
The exact scalar relation is `T = 300 + 10/G` K, with G in W/K. The example keeps
a failed solve, an exceeded requirement, equality at the limit and two equal
passing alternatives. Independent tests also solve two unknown-node balances
with rational arithmetic at an absolute tolerance of 2e-12 K/W and zero relative
tolerance. Power balance checks and numerical agreement are separate evidence.
