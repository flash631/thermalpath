# Worksheet UI tests

Run `python -m pytest tests/ui tests/integration/test_app_network.py` from the
repository root. The tests use Streamlit AppTest with synthetic cases and no
external server. The existing full gate includes this directory.

Checks cover the displayed default, valid submissions, independent rational
references, exact agreement with direct library calls, unsubmitted edits,
session separation, error recovery and the fixed three-node workload. Invalid
submitted state is injected to test the server guard independently of widget
sanitization. AppTest resets unsubmitted form edits on a rerun; valid edits are
submitted again when testing the next calculation.

These are simulated UI checks, not browser rendering or load tests. The two
extreme conductance-ratio cases now pass after a bounded correction in the
library solver. Their original errors remain in the D28 devlog. The 2e-10 K/W
absolute screens, zero relative tolerance and all 19 cases are unchanged.
