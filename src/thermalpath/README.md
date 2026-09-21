Implemented modules are resistance.py (D01 series calculations), models.py
(D02 typed network inputs and SI validation), networks.py (D03 steady solver),
diagnostics.py (D04 connectivity and signed heat accounting), and io.py/cli.py
(D05 versioned JSON inputs and the run-network command), plus transient.py
(D06 closed-form one-node RC response).
Later roadmap increments extend transient.py and add grid.py, plate.py, studies.py, comparison.py,
and plotting.py. No empty solver APIs are exposed.
