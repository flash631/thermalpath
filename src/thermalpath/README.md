Implemented modules are resistance.py (D01 series calculations), models.py
(D02 typed network inputs and SI validation), networks.py (D03 steady solver),
diagnostics.py (D04 connectivity and signed heat accounting), and io.py/cli.py
(D05 versioned JSON inputs and the run-network command), plus transient.py
(D06 closed-form one-node RC response), and transient_networks.py
(D07 backward-Euler networks with interval loads), and transient_energy.py
(D08 per-step energy accounting, with temporal refinement examples and tests),
and grid.py (D09 rectangular cell geometry), plate.py (D10-D12 steady plates),
boundaries.py (D12 convection inputs), sources.py (D13 rectangular heaters),
and plate_diagnostics.py (D14 physical balance and separate matrix residuals).
plotting.py (D18 result figures) and studies.py (D19 bounded network sweeps and
CSV replay) are also implemented. comparison.py (D23) imports temperature
reference CSVs with hash-bound provenance metadata. Later roadmap increments
add reference error metrics. No empty solver APIs are exposed.
