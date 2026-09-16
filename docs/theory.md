# Model equations and physical scope

## D01: one steady heat path

Fourier's law in a uniform layer is `P = -k A dT/dx`. Define positive `x` from
source to sink and positive `P` in that direction. With no volumetric source,
no lateral loss, and constant conductivity, integrating over thickness `L` gives
`T_hot - T_cold = P L/(k A)`. Thus `R = L/(k A)`, measured in K/W.

For a series chain, every element carries the same steady power. Adding its
temperature drops gives `T_source = T_ambient + P sum(R_i)`. A prescribed sink
temperature, finite resistances, and prescribed power give one source
temperature. Zero resistance is an ideal connection with zero drop. Zero power
gives the sink temperature. Negative power (active cooling) is outside this API.

Positive `L`, `k`, and `A` make layer resistance positive. The source temperature
increases with each resistance and with nonnegative power. Increasing `k` or
`A` decreases layer resistance. The conduction calculation rescales operands
using binary mantissas and exponents to avoid intermediate overflow. A strictly
positive resistance that rounds to zero is rejected as unrepresentable.
The series sum uses `math.fsum`; an overflowing nonzero-power total is rejected.
Zero-power inputs are validated without calculating an unnecessary total.

No spatial or temporal mesh exists in D01. Splitting a layer provides an
algebraic invariance check, not a measured convergence order.

## Planned plate formulation

The later uniform-thickness, depth-averaged plate uses

```text
-div(k t grad(T)) + h_face (T - T_ambient) = q_area
```

Here `k` is isotropic conductivity [W/(m K)], `t` is thickness [m],
`h_face` is the prescribed distributed face coefficient [W/(m² K)], and
`q_area` is heat input per planform area [W/m²]. Every equation term has units
W/m². If both faces exchange heat with the same ambient, `h_face` may be their
sum; different ambients require separate source terms. This convention must be
stated in each case.

Temperature is assumed nearly uniform through thickness. This requires a small
through-thickness temperature drop relative to the differences of interest;
a thin plate alone does not prove it for intense localized heating or low
conductivity. The model cannot resolve thickness gradients, spreading through
package layers, airflow, or convection coefficients.

An edge of in-plane length `s` has heat-transfer area `t s`. Its convection
conductance is `h_edge t s`, not `h_edge s`. For adjacent cells separated by
two half-distances `d_1`, `d_2`, a resistance-consistent conductive connection
has conductance `G = A_face / (d_1/k_1 + d_2/k_2)`. Implementation and independent
verification of this expression belong to D11.

Connections from packages or contacts to the plate must define the receiving
area/nodes and the temperature represented at each end. Do not append a package
or contact temperature drop if it duplicates resistance already resolved by the
plate or its boundary condition. These future equations do not imply that a
plate solver exists in D01.
