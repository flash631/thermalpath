# Reproduce the installation and demo

Use Python 3.12 and a new environment name that does not already exist. From
the repository root on Windows:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -I -m pip list
.\.venv\Scripts\python.exe -I -m pip install -r requirements-dev.lock
.\.venv\Scripts\python.exe -I -m pip install --no-deps --no-build-isolation .
.\.venv\Scripts\python.exe -I -m pip check
.\.venv\Scripts\python.exe -I examples\series_stack.py
.\.venv\Scripts\python.exe -I examples\demo_runtime.py
```

On other platforms, create the environment with `python3.12 -m venv .venv`
and use `.venv/bin/python` in the remaining commands. These are portable
command equivalents; the D29 fresh-install observation was made on Windows.
The environment must have `include-system-site-packages = false` in
`pyvenv.cfg`. Before dependency installation it should contain only bootstrap
packaging tools. Python's `-I` option excludes the current/script directory,
user site and Python environment-variable overrides from import resolution.
The project is installed normally, without an editable source link.

The pinned requirements include development tools and the optional worksheet.
They record tested package versions, not an offline bundle or hash-locked
software supply chain. Installation needs available package files and can use
the package manager's download cache. Keep the original lock file with the
source snapshot; do not silently upgrade packages during reproduction.

Check that the imported module belongs to this environment:

```powershell
.\.venv\Scripts\python.exe -I -c "import sys, thermalpath; from pathlib import Path; assert Path(thermalpath.__file__).resolve().is_relative_to(Path(sys.prefix).resolve()); print('Installed import passed')"
```

The documented series demo must return these values and units:

| Output | Reference | Unit |
| --- | ---: | --- |
| Interface resistance | 0.05 | K/W |
| Source temperature | 363.90 | K |
| Source temperature for presentation | 90.75 | degC |
| Applied power | 15 | W |

The independent reference is `R = L/(k*A) = 1/20 K/W` and
`T = 318.15 + 15*(1 + 1/20 + 2) = 363.9 K`. The timing example checks
the case label, every unit and each value with absolute tolerance 1e-12 and
zero relative tolerance. A failed child process or reference check prevents
a successful timing report. It launches five serial processes and prints all
elapsed seconds, median, minimum and maximum. Each interval includes Python
startup, imports, calculation, JSON output and exit. It excludes installation,
environment creation and reference checking. Numerical thread pools are set
to one. There is no speed acceptance threshold.

See [the D29 execution record](devlog/day29.md) for the actual versions,
measurements and checks. Fresh process startup does not clear filesystem
caches. Background load, storage and runtime versions can change the timings.
These observations do not estimate solver scaling or application capacity.

## Engineering discussion notes

These notes explain the implementation choices; they are not a record of an
interview or an external evaluation.

- **Start with a series path.** Its independent arithmetic makes signs, units
  and total resistance easy to check. In the demo, even removing all interface
  resistance reduces temperature by only 0.75 K. That conclusion applies to
  the specified path and inputs; parallel losses would change the model.
- **Separate the model from the worksheet.** Immutable network inputs and
  library calculations can be tested without a browser. The worksheet submits
  one bounded three-node case and displays the library result. It does not
  provide a second implementation of the heat equations.
- **Check balance and accuracy separately.** Small heat imbalance does not
  imply small temperature error. The plate refinement example compares against
  an analytical field across three grids; the network tests use independent
  rational references. See [verification](verification.md).
- **Keep a failed reference visible.** Two extreme worksheet cases originally
  failed the fixed temperature screen. A single guarded solver correction
  resolved those cases without changing the tolerance. The original failures,
  correction rationale and limits remain in [D28](devlog/day28.md).
- **Bound the claim to the evidence.** Synthetic cases verify arithmetic and
  numerical behavior. They do not establish measured material properties,
  physical accuracy or device safety. Reference import records provenance,
  but cannot authenticate a measurement by itself.
- **Make reproduction inspectable.** A normal install, pinned dependencies,
  checked module location and preserved timing samples reveal more than a
  successful run in an existing development environment. The
  [release audit](release_audit.md) records the review of claims and distributed evidence.
