# D05 decision: strict versioned network cases

Use the standard-library JSON decoder and the existing immutable network
constructors. Version 1 uses the same SI field names as the Python API. Reject
unknown and duplicate fields so a misspelled load cannot silently become zero.
Keep parsing separate from solving: an unanchored network can round-trip as
input, but the command must report the solver's anchoring error.

Serialization operates on normalized binary64 inputs. Round-trip equality is
exact for those values; it does not recover the original decimal quantities.
Check numeric token range before a nonzero load can underflow to zero. Ordinary
representable decimal rounding remains part of the existing numerical model.

The command calls the existing solver and balance diagnostic, then prints JSON
with explicit SI field names. No separate physics implementation is introduced.
For each unknown node, sum G_ij(T_i-T_j)=P_i [W]; q_ab=G_ab(T_a-T_b) [W].
Every connected positive-conductance component needs a fixed temperature for
unique absolute temperatures. JSON conversion changes neither these equations
nor their stability and conditioning limits. There is no time or spatial
discretization to refine in this increment.

An independent single-link reference gives 305 K and 10 W. The two-boundary
reference eliminates 3*Ta-Tb=610 and -Ta+4*Tb=930 to obtain Ta=3370/11 K and
Tb=3400/11 K. Signed powers are 140/11, -30/11, and -360/11 W. CLI tolerances
use the previously derived D03/D04 budgets. The tiny-load case retains its
nonzero residual even when the temperature rise rounds away. A successful
process exit indicates execution, without an accuracy or physical-validation
certificate. No material analytical issue remains for this bounded interface.
