# JSON cases and the network command

The version-1 case format stores constant-conductance network inputs. Files use
UTF-8, temperatures in kelvin, powers in watts, and conductances in watts per
kelvin. Units are fixed by the field names; no conversion or inference occurs.

## Input schema

The root must be an object with exactly three required fields:

| Field | JSON type | Meaning |
| --- | --- | --- |
| `schema_version` | integer | Must be `1`; `1.0`, booleans, and strings are rejected. |
| `nodes` | array | Nonempty collection of node objects, in input order. |
| `links` | array | Link objects, in input order; may be empty. |

Each node requires `id`, a nonempty string without outer whitespace. Optional
`power_w` is a finite number, defaulting to zero. Positive power enters the node;
negative power removes heat. Optional `fixed_temperature_k` is either `null`
(the default, leaving temperature unknown) or a finite positive number. A fixed
node must have zero prescribed power: its reservoir provides the required heat.

Each link requires `id`, `node_a`, `node_b`, and `conductance_w_k`. The first
three are identifiers; endpoints must exist and differ. Conductance is finite
and strictly positive. Positive link power flows from `node_a` to `node_b`.
Node IDs must be unique among nodes and link IDs unique among links. Parallel
links are allowed with distinct IDs. Identifiers are case-sensitive.

Unknown fields, duplicate object keys, missing required fields, invalid types,
nonstandard `NaN`/infinity tokens, and invalid model domains produce errors.
Numbers must be JSON numbers, not strings or booleans. Decimal inputs round to
binary64; overflowing numbers and nonzero floating tokens that round to zero
are rejected. Representable subnormal numbers are accepted. An exactly zero
token remains valid even with a very small exponent. There is no migration from
another schema version. See [network inputs](models.md) for model assumptions.

The shipped [heater case](../examples/cases/heater.json) contains:

```json
{
  "schema_version": 1,
  "nodes": [
    {"id": "heater", "power_w": 10.0},
    {"id": "bath", "fixed_temperature_k": 300.0}
  ],
  "links": [
    {"id": "strap", "node_a": "heater", "node_b": "bath", "conductance_w_k": 2.0}
  ]
}
```

## Run a case

After installing the package, run:

```sh
thermalpath run-network examples/cases/heater.json
```

The equivalent module command works with the selected Python environment:

```sh
python -m thermalpath.cli run-network examples/cases/heater.json
```

On Windows, use `.venv\Scripts\thermalpath.exe` or
`.venv\Scripts\python.exe -m thermalpath.cli` from the project root. Reinstall
the package after updating its source to register the console command.

Output goes to standard output as one JSON object. It has `schema_version: 1`,
`kind: "steady_network_result"`, `temperatures_k` and `link_powers_w` objects
keyed by input IDs, and a `heat_balance` object. The result schema is distinct
from the case schema and is not accepted as an input case. Heat-balance fields
are `node_outflow_w`, `node_residual_w`, `boundary_power_w`, `total_input_w`,
`total_output_w`, and `imbalance_w`; their signs and definitions follow the
[diagnostics API](diagnostics.md). All diagnostic values are watts.

For this synthetic case, `T_heater = 300 + 10/2 = 305 K` and strap power is
`+10 W`. Boundary input is `-10 W`, total input/output are each `10 W`, and
the unknown-node residual and global imbalance are zero.

| Exit code | Meaning |
| --- | --- |
| `0` | Solve and output completed, or help was requested. |
| `1` | File/encoding, case, solver, or output error; message goes to standard error. |
| `2` | Invalid command arguments; usage goes to standard error. |

The input file is read without modification. File, case, and solver errors
produce no result on standard output. An output-device failure may leave a
partial output; check the exit code before consuming a redirected result.

## Round-trip through the Python API

```python
from pathlib import Path
from thermalpath import dumps_case, loads_case

network = loads_case(Path("examples/cases/heater.json").read_text(encoding="utf-8"))
text = dumps_case(network)
assert loads_case(text) == network
```

Serialization preserves array order, IDs, and normalized binary64 values.
It writes explicit defaults, indentation, ASCII escapes for non-ASCII text,
and a final newline. It does not preserve original number spelling, whitespace,
or omitted fields. Repeated serialization of the same network is deterministic.

## Numerical limits

Decoding validates structure and domains without solving. The command also
requires every component to reach a fixed-temperature boundary. The existing
[steady solver](networks.md) and its conditioning and range limits apply.
There is no new numerical method, convergence guarantee, or automatic residual
tolerance in this interface. The command is intended for small local cases;
the dense solver is not a large-network service.

A `1e-20 W` load in the example rounds the computed heater temperature to the
bath temperature, so link power is zero. The command still reports a
`1e-20 W` nodal residual and global imbalance. Exit code zero means execution
completed; it does not certify accuracy or an acceptable engineering balance.
These inputs and reference calculations are synthetic, with no physical
validation or device-safety claim.
