# D01 analytical decision: steady series path

The integrated steady one-dimensional Fourier law gives `R = L/(k A)`.
Adding distinct series drops gives `T_source = T_sink + P sum(R)`.
Dimensions are K/W and K; positive heat is from source to the sink.
With prescribed power and sink temperature, the finite algebraic solution is
unique. There is no time discretization or stability question in this increment.

An independent exact-rational calculation gives 0.05 K/W and 363.90 K for
the synthetic example. The tests reconstruct rejected power independently,
check limiting cases, and check geometric scaling. Range checks reject results
that cannot be represented. Mantissa/exponent scaling avoids intermediate
conduction overflows whose final result would otherwise be representable.

The derived reference and limiting-case checks support D01's equations and
tests within their stated scope. They do not validate an electronics device.
