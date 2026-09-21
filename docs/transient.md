# One-node thermal RC response

`rc_step` evaluates a uniform-temperature body with heat capacity `C` [J/K],
connected through resistance `R` [K/W] to a fixed reservoir `Tb` [K]. A constant
power `P` [W] starts at time zero. Positive power enters the body; negative power
extracts heat. The initial temperature is `T0` [K]. All properties are constant.

The energy balance, equilibrium and time constant are

```text
C dT/dt = P - (T - Tb)/R
Tinf = Tb + P R
tau = R C                     [s]
T(t) = Tinf + (T0 - Tinf) exp(-t/tau).
```

Substitution verifies the equation and `T(0)=T0`. The scalar linear initial-value
problem has a unique solution. Since `R,C>0`, deviations from equilibrium decay
exponentially. For `t>=0`, temperature is a weighted average of `T0` and `Tinf`,
so positive endpoints keep the whole trajectory positive and prevent overshoot.
The API requires positive equilibrium even if the requested time is short.

## Energy and power

The result separates three quantities with different meanings:

| Field | Definition | Sign and unit |
| --- | --- | --- |
| `stored_energy_change_j` | `C (T(t)-T0)` | Positive for warming, J |
| `boundary_power_w` | `(T(t)-Tb)/R` | Positive from body to reservoir, W |
| `storage_power_w` | `C dT/dt` | Positive for warming, W |

Instantaneous conservation is `P = boundary_power_w + storage_power_w`.
Stored energy starts at zero, including when the initial boundary power is
nonzero. With `a=Tinf-T0` and `f=1-exp(-t/tau)`, integrated boundary heat is
`E_boundary = P t - C a f` [J]. Thus `P t = DeltaE + E_boundary`.
Boundary heat can be negative when the reservoir warms the body.

For the synthetic case `T0=Tb=300 K`, `R=2 K/W`, `C=10 J/K`, and `P=5 W`,
the time constant is 20 s and the equilibrium is 310 K. At 20 s:

| Quantity | Approximate value |
| --- | ---: |
| Temperature | 306.321205588286 K |
| Stored energy change | 63.2120558828558 J |
| Boundary power | 3.16060279414279 W |
| Storage rate | 1.83939720585721 W |
| Integrated boundary heat | 36.7879441171442 J |

The applied energy is 100 J. Instantaneous boundary power times elapsed time
is not the integrated boundary heat, because the boundary power changes.

```python
from thermalpath import rc_step

result = rc_step(
    time_s=20.0,
    initial_temperature_k=300.0,
    boundary_temperature_k=300.0,
    resistance_k_w=2.0,
    heat_capacity_j_k=10.0,
    power_w=5.0,
)
print(result.temperature_k)
print(result.stored_energy_change_j)
print(result.boundary_power_w + result.storage_power_w)
```

Run `python examples/rc_step.py` for the same case with unit-labelled JSON.
This API is separate from the version-1 steady-network JSON format and command.

## Numerical scope

This is a closed-form evaluation, so there is no time-step truncation error or
time-step stability restriction. Tests compare to independent 70-digit decimal
references; [verification](verification.md#d06-rc-response) defines the tolerances.

The implementation computes `f` with `-expm1(-t/tau)` to retain small steps.
It stores the amplitude and energy change separately from absolute temperature,
and evaluates temperature from the nearer initial or final endpoint. Boundary
power interpolates between its initial value and `P`; storage rate decays from
its initial value. These choices reduce cancellation but do not certify all
binary64 inputs. A temperature reported as 300 K can coexist with nonzero stored
energy when the temperature rise rounds away. Reconstructing power or energy
from that rounded temperature can therefore lose information.

The API rejects nonfinite inputs, nonpositive resistance/capacity/temperatures,
negative time, nonpositive equilibrium, and unrepresentable time constants or
nonfinite intermediates. It requires the full step's energy scale `C*(Tinf-T0)`
and initial power scales to fit, even for a short observation time. This can
reject a mathematically finite requested result. Very small ratios, products
and exponential tails can underflow to zero; large time ratios can overflow
to infinity and yield the equilibrium limit. No universal relative-error bound
is claimed. These arithmetic limits are distinct from physical applicability.

A single uniform body is an assumption that needs engineering justification.
The calculation does not model internal gradients, variable properties,
radiation, multiple capacitances, or piecewise loads. Inputs and references are
synthetic; they provide numerical verification and no physical validation.
