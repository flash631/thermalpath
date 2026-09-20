Implemented modules are resistance.py (D01 series calculations), models.py
(D02 typed network inputs and SI validation), networks.py (D03 steady solver),
diagnostics.py (D04 connectivity and signed heat accounting), and io.py/cli.py
(D05 versioned JSON inputs and the run-network command).
Later roadmap increments add transient.py, grid.py, plate.py, studies.py, comparison.py,
and plotting.py. No empty solver APIs are exposed.
