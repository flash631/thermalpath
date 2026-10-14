# D20: local temperature derivatives

Use a three-point quadratic derivative for one network parameter at a time.
Keep the actual rounded abscissae, all requested steps and complete solver case
records. This fits the existing bounded network studies and avoids changing
the steady solver. A caller must supply at least three distinct steps to make
step-size dependence visible.

For an anchored network with positive conductances, the reduced conductance
matrix is positive definite. Differentiating A(p)T(p)=b(p) gives
A*T'=b'-A'*T. This establishes smooth local dependence in the admitted interior
and supplies independent analytical references. The implemented finite
differences do not solve that differentiated system or claim its exact result.

The unequal-spacing stencil cancels the quadratic Taylor term. Its leading
error is hm*hp*T'''/6. Subtraction, solver conditioning and finite arithmetic
remain limits; a successful calculation is not an accuracy certificate.
Preserve invalid physical stencils and unrepresentable perturbations as failed
estimates. Do not silently switch to a one-sided rule or shrink a user's step.

Report dimensional dT/dp and dimensionless (p0/T0)*dT/dp using absolute kelvin.
Keep signs. Explicitly document the zero-input scaling limitation. Record
linear residuals and physical balance separately from derivative errors.
Independent references use differentiated balances and exact rational
finite-step errors. No material analytical issue remains within this scope.
