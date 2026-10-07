"""Headless plots of supplied thermal results, without changing their values."""

from collections.abc import Mapping, Sequence
from io import BytesIO
from pathlib import Path

import matplotlib as mpl
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.colors import Normalize
from matplotlib.figure import Figure
from matplotlib.ticker import LogFormatter, NullFormatter

from thermalpath.grid import RectangularGrid
from thermalpath.models import _scalar

_STYLE = {key: value for key, value in mpl.rcParamsDefault.items() if key != "backend"}
_STYLE.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 11,
        "text.color": "#2f3437",
        "axes.labelcolor": "#2f3437",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.formatter.useoffset": False,
        "text.usetex": False,
        "text.parse_math": False,
        "path.simplify": False,
    }
)


def _values(values: Sequence[float], name: str, *, positive: bool) -> np.ndarray:
    """Copy a finite, nonempty flat numeric sequence."""
    if not isinstance(values, (tuple, list, np.ndarray)) or np.ndim(values) != 1:
        raise ValueError(f"{name} must be a flat tuple, list or array")
    if len(values) == 0:
        raise ValueError(f"{name} must not be empty")
    return np.array([_scalar(value, name, positive=positive) for value in values])


def _series(series: Mapping[str, Sequence[float]], count: int) -> dict[str, np.ndarray]:
    """Validate positive data and explicit labels, preserving input order."""
    if not isinstance(series, Mapping) or not series:
        raise ValueError("series must be a nonempty labelled mapping")
    result = {}
    for label, values in series.items():
        if not isinstance(label, str) or not label.strip():
            raise ValueError("series labels must be nonempty strings")
        data = _values(values, label, positive=True)
        if len(data) != count:
            raise ValueError("series length must match its coordinates")
        result[label] = data
    return result


def plot_temperatures(
    grid: RectangularGrid, fields_k: Mapping[str, Sequence[float]]
) -> Figure:
    """Compare cell temperatures using real cell edges and a shared color scale.

    Parameters
    ----------
    grid : RectangularGrid
        Common geometry in metres; unequal cell widths are supported.
    fields_k : mapping of str to sequence of float
        Nonempty labels and positive finite temperatures [K], one per cell in
        x-first flat order. Mapping order determines left-to-right panel order.

    Returns
    -------
    matplotlib.figure.Figure
        Agg-backed figure, with equal x/y scale and one shared colorbar [K].

    Notes
    -----
    Each cell is flat shaded, without interpolation. The common color limits
    include every value. A constant field uses a symmetric 0.5 K or 1 percent
    padding, whichever is larger. This is a display interval, not uncertainty.
    """
    if not isinstance(grid, RectangularGrid):
        raise ValueError("grid must be a RectangularGrid")
    fields = _series(fields_k, grid.cell_count)
    low = min(float(values.min()) for values in fields.values())
    high = max(float(values.max()) for values in fields.values())
    if low == high:
        padding = max(0.5, low * 0.01)
        low, high = low - padding, high + padding
    with mpl.rc_context(_STYLE):
        figure = Figure(figsize=(5 * len(fields) + 1, 4.5), dpi=150)
        FigureCanvasAgg(figure)
        axes = figure.subplots(1, len(fields), squeeze=False)[0]
        norm = Normalize(vmin=low, vmax=high)
        for axis, (label, values) in zip(axes, fields.items(), strict=True):
            mesh = axis.pcolormesh(
                grid.x_edges_m,
                grid.y_edges_m,
                values.reshape(grid.ny, grid.nx),
                shading="flat",
                cmap="cividis",
                norm=norm,
            )
            axis.set(xlabel="x [m]", ylabel="y [m]", title=label, aspect="equal")
            axis.set_xlim(grid.x_edges_m[0], grid.x_edges_m[-1])
            axis.set_ylim(grid.y_edges_m[0], grid.y_edges_m[-1])
        figure.subplots_adjust(
            left=0.09, right=0.86, bottom=0.18, top=0.88, wspace=0.35
        )
        color_axis = figure.add_axes((0.90, 0.22, 0.018, 0.56))
        figure.colorbar(mesh, cax=color_axis, label="Temperature [K]")
    return figure


def _curves(x: np.ndarray, series: dict[str, np.ndarray], *, errors: bool) -> Figure:
    """Draw the unchanged points on common axes, with distinct line styles."""
    colors = ("#0072b2", "#d55e00", "#009e73", "#333333")
    styles = ("-", "--", "-.", ":")
    markers = ("o", "s", "^", "D")
    with mpl.rc_context(_STYLE):
        figure = Figure(figsize=(7, 4.5), dpi=150)
        FigureCanvasAgg(figure)
        axis = figure.subplots()
        lines = []
        for index, (label, values) in enumerate(series.items()):
            style = index % len(colors)
            lines.extend(
                axis.plot(
                    x,
                    values,
                    label=label,
                    color=colors[style],
                    linestyle=styles[style],
                    marker=markers[style],
                    markersize=4,
                )
            )
        if errors:
            axis.set(
                xscale="log",
                yscale="log",
                xlabel="Grid spacing [m]",
                ylabel="Temperature error norm [K]",
            )
            axis.set_xticks(x, labels=[f"{value:g}" for value in x])
            axis.xaxis.set_minor_formatter(NullFormatter())
            axis.yaxis.set_major_formatter(LogFormatter())
            axis.yaxis.set_minor_formatter(NullFormatter())
        else:
            axis.set(xlabel="Time [s]", ylabel="Temperature [K]")
        axis.grid(True, which="major", color="#e0e0e0", linewidth=0.6)
        axis.legend(handles=lines, labels=list(series), frameon=False)
        figure.subplots_adjust(left=0.15, right=0.96, bottom=0.17, top=0.94)
    return figure


def plot_transient(
    times_s: Sequence[float], temperatures_k: Mapping[str, Sequence[float]]
) -> Figure:
    """Plot labelled temperature histories on one common pair of axes.

    Parameters
    ----------
    times_s : sequence of float
        At least two finite nonnegative, strictly increasing times [s].
    temperatures_k : mapping of str to sequence of float
        Positive finite temperatures [K], one per time, for each nonempty label.

    Returns
    -------
    matplotlib.figure.Figure
        Agg-backed figure with markers at supplied points. Connecting lines
        guide the eye; they do not reconstruct the continuous solution.
    """
    times = _values(times_s, "times_s", positive=False)
    if len(times) < 2 or times[0] < 0 or not np.all(times[1:] > times[:-1]):
        raise ValueError("times_s must be nonnegative and strictly increasing")
    return _curves(times, _series(temperatures_k, len(times)), errors=False)


def plot_errors(
    spacings_m: Sequence[float], errors_k: Mapping[str, Sequence[float]]
) -> Figure:
    """Plot positive temperature error norms against spatial grid spacing.

    Parameters
    ----------
    spacings_m : sequence of float
        At least two finite positive spacings [m], strictly increasing or
        strictly decreasing. Input ordering is preserved.
    errors_k : mapping of str to sequence of float
        Positive finite norms [K], one per spacing, for each nonempty label.
        Zero and negative errors are rejected because both axes are logarithmic.

    Returns
    -------
    matplotlib.figure.Figure
        Agg-backed figure on common log axes. No fitted slope, fabricated
        reference line, error floor, or convergence claim is added.
    """
    spacings = _values(spacings_m, "spacings_m", positive=True)
    ordered = np.all(spacings[1:] > spacings[:-1]) or np.all(
        spacings[1:] < spacings[:-1]
    )
    if len(spacings) < 2 or not ordered:
        raise ValueError(
            "spacings_m must be strictly monotone with at least two values"
        )
    return _curves(spacings, _series(errors_k, len(spacings)), errors=True)


def save_png(figure: Figure, path: str | Path) -> None:
    """Export a figure to a new PNG file without opening a display.

    Parameters
    ----------
    figure : matplotlib.figure.Figure
        Figure to export at 150 dpi, with a white background.
    path : str or pathlib.Path
        New .png filename in an existing directory. Existing files raise
        FileExistsError and are never overwritten.

    Notes
    -----
    Fixed render settings and metadata make repeated exports of an unmodified
    ThermalPath figure byte-identical in the same dependency/font environment.
    Bytes need not agree across operating systems or library versions.
    """
    target = Path(path)
    if target.suffix.lower() != ".png":
        raise ValueError("path must have a .png suffix")
    with mpl.rc_context(_STYLE):
        buffer = BytesIO()
        figure.savefig(
            buffer,
            format="png",
            dpi=150,
            facecolor="white",
            edgecolor="white",
            transparent=False,
            bbox_inches=None,
            metadata={"Software": "ThermalPath"},
        )
    with target.open("xb") as output:
        output.write(buffer.getvalue())
