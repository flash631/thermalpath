# D27: local steady heat-path worksheet

Completed on 2026-10-22.

Added a small Streamlit worksheet with four SI controls and a fixed three-node
network. Inputs go through the existing library models, steady solver and heat
accounting. The interface shows submitted inputs, temperatures, oriented link
powers, signed sink reservoir input, global imbalance and matrix residual.
Model limits and the distinction between residuals and physical accuracy are
visible with the results. No new physics or cloud service was added.

The analytical review used the series reference Ts = Tb + P/Gs and
Th = Ts + P/Gc. Positive conductances and a fixed sink give a unique solution.
Seven focused tests passed: four independent rational reference cases and
three checks that invalid temperature/conductance inputs retain the library's
validation. The frozen absolute tolerance was 2e-10 K or W, with zero relative
tolerance. No numerical library implementation changed.

Browser checks confirmed the 10 W default gives heater/spreader temperatures
307/305 K, with both links carrying 10 W and reservoir input -10 W. Submitting
20 W gives 314/310 K and -20 W reservoir input. Editing the form to zero power
leaves the submitted 20 W result in place until submission; submitting zero
gives 300 K at every node and zero link power. Default displayed imbalance
and matrix residual were both zero. The layout and visible SI labels were
inspected in a browser.

The complete public gate passed 1474 tests with 99.71% package-wide coverage,
including branches. The coverage scope remains the engineering library; the
browser checks above are separate interface evidence. Archive inspection
matched all 216 tracked source files and 22 library modules. The app adapter
from the source archive, using an isolated wheel installation, reproduced the
default case exactly and matched the source-checkout output. Dependency
consistency, lint, formatting and distribution builds passed.

Streamlit 1.66.0 and its runtime dependencies are recorded in the development
lock file. The source archive includes the worksheet; the wheel contains the
engineering library. Broader AppTest flows and resource-limit testing remain
D28 work. These numerical and interface checks do not establish physical
validation, material operating ranges, or device safety.
