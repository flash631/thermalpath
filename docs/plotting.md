# Plotting thermal results

`thermalpath.plotting` provides headless Matplotlib figures for supplied data.
It does not solve a model, estimate uncertainty, or change the numerical results.
Import plotting functions from this module; ordinary solver imports do not load
Matplotlib.

```python
from thermalpath import RectangularGrid, solve_plate
from thermalpath.plotting import plot_temperatures, save_png

grid = RectangularGrid((0, 0.01, 0.03), (0, 0.02), 0.002)
result = solve_plate(grid, 10, west_k=300, east_k=330)
figure = plot_temperatures(grid, {"Computed": result.temperatures_k})
save_png(figure, "temperature.png")  # Requires a new filename.
figure.clear()
```

## Temperature maps

`plot_temperatures(grid, fields_k)` accepts a mapping from panel labels to
positive finite kelvin values in x-first cell order. Every field must have
exactly one value per cell of the common grid. Each panel uses the actual cell
edges in metres and equal x/y scale, including for unequal cell widths and
translated origins. Flat shading places each supplied value over its cell;
it does not interpolate a centre value or turn it into a cell average.

All panels share one normalization and colorbar. The minimum and maximum across
all fields set the color limits, so the same color means the same temperature.
A constant field receives symmetric display padding of the larger of 0.5 K
and 1 percent of its value. Padding is not a physical temperature prediction or
an uncertainty interval. Compare only fields on the same physical geometry;
the function cannot verify the origin of caller-supplied values.

## Transients and spatial errors

`plot_transient(times_s, temperatures_k)` accepts a common, strictly increasing,
nonnegative time grid with at least two points. Each labelled series must supply
one positive finite temperature in kelvin per time. Extract a network node with
`[row["body"] for row in result.temperatures_k]`. Markers identify the supplied
points; connecting straight lines guide the eye. They are not a continuous-time
solution between time steps. Compared histories share both axes.

`plot_errors(spacings_m, errors_k)` accepts at least two strictly monotone,
positive spatial spacings and labelled positive temperature-error norms. Both
axes are logarithmic. Increasing and decreasing input order are retained.
Zero, negative, or nonfinite errors are rejected rather than hidden or replaced
with a small artificial value. A zero error needs a separate numerical report.
The plot adds no fitted order or reference slope. In a two-dimensional study,
state which spacing is used and how both axes are refined.

## Reproduce the figures

Run this command with a directory name that does not yet exist:

```text
python examples/thermal_plots.py thermal-plots
```

The example recomputes the existing [manufactured plate refinement](plate_refinement.md)
and [scalar transient benchmark](transient_energy.md). Its outputs are:

- `temperature.png`: the 16 by 12 finite-volume field beside continuum values
  evaluated at the same cell centres, on one common color scale.
- `transient.png`: backward Euler at a 1 s step beside the analytical RC
  temperatures at those same 21 times, from 0 to 20 s.
- `errors.png`: the measured mean absolute, RMS, and maximum errors on the frozen
  4 by 3, 8 by 6, and 16 by 12 grids. The horizontal coordinate is x spacing;
  y spacing halves with it. The lower measured maximum-error slopes remain.
- `inputs.json`: all plotted values and geometry, with units in field names.
- `manifest.json`: SHA-256 hashes of the inputs and PNGs, plus Matplotlib version.

These are synthetic numerical benchmarks. Figures supply no experimental data
or additional physical validation. Small energy imbalance does not establish
small temperature error, and a plot does not establish a convergence theorem.

## Export and limits

`save_png(figure, path)` writes a new PNG at 150 dpi with a white background.
It uses fixed metadata without a timestamp and refuses to overwrite an existing
file. The destination's parent directory must exist. The example also refuses
an existing output directory. A failed export may leave partial example outputs;
keep them for inspection and choose a new directory for a retry.

Figures use Agg without a display or a global backend switch. Scoped defaults
use bundled DejaVu Sans, literal labels, distinct line styles and markers, and
a shared cividis temperature scale. Caller style settings are restored. Repeated
exports of unmodified figures are byte-identical in the same dependency/font
environment; different operating systems or renderer versions may produce
different bytes. Matplotlib rendering is not thread-safe. Use these helpers
serially. Extremely wide coordinate ranges, many panels, or long labels may
need manual layout adjustment; finite input validation is not a guarantee that
every binary64 scale renders well.

The [Matplotlib mesh documentation](https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.pcolormesh.html)
describes flat cell shading. The [Agg backend](https://matplotlib.org/stable/api/backend_agg_api.html)
provides headless raster output. Returned Figure objects remain available for
inspection or manual adjustment; clear or release them when finished.
