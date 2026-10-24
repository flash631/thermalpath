# Local steady heat-path worksheet

From the repository root, install the tested dependencies and package, then run:

```text
python -m pip install -r requirements-dev.lock
python -m pip install --no-deps --no-build-isolation .
python -m streamlit run app/network_app.py --server.address 127.0.0.1 --server.headless true --browser.gatherUsageStats false
```

Open the local URL printed by Streamlit. Stop the server with Ctrl+C.
The app source is included in the source distribution and repository; the wheel
contains the engineering library. The optional `app` extra also installs
Streamlit, but the lock file records the exact versions tested here.
Set `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS` and `MKL_NUM_THREADS` to `1`
before starting the server when one numerical thread is required.

The worksheet connects a heater to an unloaded spreader and then to an ideal
fixed-temperature sink. It calls `Network`, `solve_steady` and `heat_balance`
from the existing library. There are no cloud services or saved user cases.

Enter power in W, absolute sink temperature in K, and both conductances in W/K.
Press **Calculate temperatures** to apply all four inputs together. The submitted
case is printed above the results; edits inside the form do not change results
until submitted. This follows [Streamlit's form behavior](https://docs.streamlit.io/develop/api-reference/execution-flow/st.form).
The initial page calculates the displayed defaults.

At 10 W, 300 K sink temperature, and conductances of 5 and 2 W/K, the heater is
307 K and the spreader is 305 K. Both link powers are 10 W toward the sink;
the sink reservoir input is -10 W. Global imbalance and matrix residual are
reported separately, in watts.

Controls span 0–1000 W, 1–1000 K and 0.1–100 W/K. These are interface ranges,
not material ratings. The network always has three nodes and two links.
There is no spatial grid, random sampling, heat storage, radiation or
temperature-dependent conductance. The ideal sink can remove any required
heat. Results are model predictions, without physical validation or a device
safety verdict. Read the [network assumptions](../docs/networks.md).

Independent arithmetic tests cover the input mapping and solver results.
The server also checks the finite inclusive control ranges before building a
network. Submitted inputs are kept within each session, including across reruns.
An invalid case shows an input-specific message and no result tables; submitting
a valid replacement clears the error.

The fixed workload is one three-node network solve per render: two unknown
temperatures, two links, zero spatial grid cells and zero random samples. The
form provides no size, grid or sample-count inputs. These structural limits do
not promise a wall-clock timeout or bound total memory across many sessions.

AppTest checks exercise submitted cases, error recovery, session separation and
agreement with direct library calls. All 19 reference cases pass the unchanged
2e-10 K and W absolute screens after a bounded correction in the library solver.
The library attempts at most two linear solves per call; the app still calls it
once per render. See the [D28 evidence](../docs/devlog/day28.md), including the
two original failures. Passing these finite cases does not establish an error
bound across the full control range.
