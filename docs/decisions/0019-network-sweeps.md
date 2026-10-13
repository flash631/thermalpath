# D19: bounded network sweeps with complete CSV cases

The first sweep API uses the existing steady-network solver and case schema.
Three axis fields cover prescribed loads, reservoir temperatures and link
conductances while preserving topology and node boundary type. Full expanded
case inputs in every row make failed candidates and replay independently
inspectable. The original axes are unnecessary for reproduction.

The product has deterministic order with the last axis fastest. Duplicate
values remain present. Finite invalid physical candidates produce failed rows;
invalid sweep structure rejects the request. Only expected ValueError failures
are recorded, so unexpected implementation errors remain visible.

Positive link conductances and anchored components retain the existing steady
system's uniqueness. No new discretization, interpolation or physical model is
introduced. Case, axis and network limits bound serial work. Global physical
imbalance remains separate from the assembled matrix residual. Exact scalar
and two-node balances provide independent reference values and signs.

Replay uses the full input specification and computes fresh outputs, ignoring
old results. It is a reproduction tool, not automatic regression acceptance.
Plate sweeps, sensitivities and uncertainty are outside D19. No unresolved
analytical issue requires changing the established network equations.
