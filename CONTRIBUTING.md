# Contributing

Use Python 3.12 and the versions in `requirements-dev.lock` to reproduce the
tested development environment. Read the relevant equations, limitations, and
ROADMAP acceptance criteria before changing a numerical method or public API.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock
.\.venv\Scripts\python.exe -m pip install --no-deps --no-build-isolation -e .
.\.venv\Scripts\python.exe scripts\check.py
```

On other platforms, use `python3.12` and `.venv/bin/python` instead. Editable
installation is useful during development. The README's normal installation
installs a package copy for use outside the source tree.

Keep public functions typed and modules small. Use NumPy-style docstrings,
explicit SI units, kelvin for absolute temperatures, and clear sign conventions.
Reject nonfinite inputs and invalid physical domains with useful errors.

For physics changes, derive an analytical or manufactured reference independently
of the implementation. Check dimensions, assumptions, existence or stability
where relevant, limiting cases, conservation, and discretization error. Add
invalid-input and regression tests. Justify numerical tolerances. Do not label
agreement with another numerical model as validation against measurements.

Run the complete quality gate: Ruff lint and formatting, pytest with line and
branch coverage across the entire package, and source/wheel builds. The combined
coverage minimum is 90%; coverage does not replace scientific verification.
Keep tests and examples small and deterministic, with numerical thread pools
limited to one. Use synthetic fixtures unless licensed reference data with
traceable provenance is needed.

Keep changes focused and preserve adverse results. Explain the engineering
problem, the resulting behavior, tests actually run, and remaining limitations.
Use Conventional Commits, such as `fix(core): reject nonfinite temperatures`.
Update documentation and the relevant roadmap acceptance evidence when a feature
is complete. Include new public source/test files in `MANIFEST.in` and inspect
the resulting distributions so source releases remain reproducible.

Do not include credentials, personal contact details, or machine-specific paths
in contributions. Preserve contributor attribution and the MIT license; document
the source, license, units, and synthetic or experimental status of reference
data. Do not invent measurements, accuracy claims, citations, or certification.
