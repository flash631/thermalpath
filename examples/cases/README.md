heater.json is a synthetic version-1 steady network case: a 10 W heater,
a 2 W/K strap, and a 300 K reservoir. The exact solution is 305 K at the
heater and +10 W through the strap. Run it with:

```sh
python -m thermalpath.cli run-network examples/cases/heater.json
```

See docs/cases.md for the schema, units, exit codes, and numerical limits.
D01 uses the synthetic series_stack.py example.
