"""Check geometric and data fidelity rather than renderer-specific golden pixels."""

import copy

import matplotlib as mpl
import numpy as np
import pytest
from matplotlib.backends.backend_agg import FigureCanvasAgg
from PIL import Image

from thermalpath import RectangularGrid, solve_plate
from thermalpath.plotting import (
    plot_errors,
    plot_temperatures,
    plot_transient,
    save_png,
)


def test_unequal_cells_linear_solution_and_shared_scale():
    grid = RectangularGrid((-0.03, -0.02, 0.01, 0.03), (0.02, 0.03, 0.06), 0.002)
    solved = solve_plate(grid, 10, west_k=300, east_k=360)
    # Linear continuum solution: 1000 K/m from the west edge; repeat for each y.
    reference = [305, 325, 350, 305, 325, 350]
    fields = {"Computed": solved.temperatures_k, "Analytical": reference}
    before = copy.deepcopy(fields)
    figure = plot_temperatures(grid, fields)
    figure.canvas.draw()
    assert isinstance(figure.canvas, FigureCanvasAgg)
    left, right, colorbar = figure.axes
    for axis in (left, right):
        mesh = axis.collections[0]
        np.testing.assert_allclose(
            mesh.get_array(), [[305, 325, 350]] * 2, atol=1e-10, rtol=0
        )
        coordinates = mesh.get_coordinates()
        np.testing.assert_array_equal(coordinates[0, :, 0], grid.x_edges_m)
        np.testing.assert_array_equal(coordinates[:, 0, 1], grid.y_edges_m)
        assert axis.get_xlim() == (-0.03, 0.03)
        assert axis.get_ylim() == (0.02, 0.06)
        origin, x_step, y_step = axis.transData.transform(
            [(0, 0.02), (0.01, 0.02), (0, 0.03)]
        )
        assert x_step[0] - origin[0] == pytest.approx(y_step[1] - origin[1])
        assert axis.get_xlabel() == "x [m]"
        assert axis.get_ylabel() == "y [m]"
    assert left.collections[0].norm is right.collections[0].norm
    assert left.collections[0].get_clim() == pytest.approx((305, 350))
    assert colorbar.get_ylabel() == "Temperature [K]"
    assert fields == before


def test_transposed_or_flipped_fields_would_fail():
    grid = RectangularGrid((0, 1, 3), (-2, -1, 2), 1)
    figure = plot_temperatures(grid, {"A": [301, 302, 310, 320], "B": [400] * 4})
    np.testing.assert_array_equal(
        figure.axes[0].collections[0].get_array(), [[301, 302], [310, 320]]
    )
    assert figure.axes[0].collections[0].get_clim() == (301, 400)


def test_constant_field_is_visible():
    figure = plot_temperatures(RectangularGrid((0, 1), (0, 1), 1), {"Constant": [300]})
    assert figure.axes[0].collections[0].get_clim() == (297, 303)
    assert figure.axes[0].collections[0].get_array().item() == 300


def test_transient_points_labels_and_inputs_are_preserved():
    times = [0, 0.5, 2]
    values = {"Body": [300, 301, 304], "Bath": [295, 295, 295]}
    figure = plot_transient(times, values)
    times[1] = 99
    values["Body"][1] = 999
    axis = figure.axes[0]
    for line in axis.lines:
        np.testing.assert_array_equal(line.get_xdata(), [0, 0.5, 2])
    np.testing.assert_array_equal(axis.lines[0].get_ydata(), [300, 301, 304])
    np.testing.assert_array_equal(axis.lines[1].get_ydata(), [295] * 3)
    assert [t.get_text() for t in axis.get_legend().get_texts()] == ["Body", "Bath"]
    assert axis.get_xlabel() == "Time [s]"
    assert axis.get_ylabel() == "Temperature [K]"
    assert axis.get_xscale() == axis.get_yscale() == "linear"


@pytest.mark.parametrize("spacings", [[0.04, 0.02, 0.01], [0.01, 0.02, 0.04]])
def test_error_plot_preserves_norms_and_order(spacings):
    norms = [0.4, 0.1, 0.025]
    figure = plot_errors(spacings, {"Maximum": norms})
    axis = figure.axes[0]
    assert len(axis.lines) == 1
    np.testing.assert_array_equal(axis.lines[0].get_xdata(), spacings)
    np.testing.assert_array_equal(axis.lines[0].get_ydata(), norms)
    assert axis.get_xscale() == axis.get_yscale() == "log"
    assert axis.get_xlabel() == "Grid spacing [m]"
    assert axis.get_ylabel() == "Temperature error norm [K]"
    figure.canvas.draw()
    assert [tick.get_text() for tick in axis.get_xticklabels()] == [
        f"{value:g}" for value in spacings
    ]
    for tick in axis.get_yticklabels():
        assert "$" not in tick.get_text() and "\\" not in tick.get_text()


@pytest.mark.parametrize(
    "bad",
    [
        [],
        {},
        {"": [300, 301]},
        {2: [300, 301]},
        {"T": [300]},
        {"T": [0, 300]},
        {"T": [-1, 300]},
        {"T": [float("nan"), 300]},
        {"T": [float("inf"), 300]},
        {"T": [True, 300]},
        {"T": [[300], [301]]},
        {"T": []},
        {"T": "300"},
        {"T": ["300", 301]},
    ],
)
def test_invalid_series(bad):
    with pytest.raises(ValueError):
        plot_transient([0, 1], bad)


@pytest.mark.parametrize(
    "times",
    [[], [0], [-1, 0], [0, 0], [1, 0], [0, float("inf")], [0, float("nan")], "01"],
)
def test_invalid_times(times):
    with pytest.raises(ValueError):
        plot_transient(times, {"T": [300, 301]})


@pytest.mark.parametrize("spacings", [[1], [1, 1], [1, 3, 2], [0, 1], [-1, 1]])
def test_invalid_spacings(spacings):
    with pytest.raises(ValueError):
        plot_errors(spacings, {"Error": [1] * len(spacings)})


@pytest.mark.parametrize("errors", [[0, 1], [-1, 1], [1, float("nan")]])
def test_log_plot_never_silently_drops_invalid_errors(errors):
    with pytest.raises(ValueError):
        plot_errors([1, 2], {"Error": errors})


def test_invalid_geometry_and_field_length():
    with pytest.raises(ValueError, match="RectangularGrid"):
        plot_temperatures(None, {"T": [300]})
    with pytest.raises(ValueError, match="length"):
        plot_temperatures(RectangularGrid((0, 1), (0, 1), 1), {"T": [300, 301]})


@pytest.mark.parametrize("kind", ["temperature", "transient", "error"])
def test_repeatable_png_ignores_ambient_style_and_never_overwrites(tmp_path, kind):
    def make_figure():
        if kind == "temperature":
            return plot_temperatures(RectangularGrid((0, 1), (0, 1), 1), {"T": [300]})
        if kind == "transient":
            return plot_transient(np.array([0, 1]), {"T": np.array([300, 301])})
        return plot_errors([1, 0.5], {"Error": [0.1, 0.03]})

    paths = [tmp_path / f"plot{i}.png" for i in range(3)]
    figure = make_figure()
    save_png(figure, paths[0])
    save_png(figure, paths[1])
    with mpl.rc_context(
        {
            "font.size": 27,
            "text.usetex": True,
            "savefig.bbox": "tight",
            "axes.facecolor": "red",
        }
    ):
        save_png(make_figure(), paths[2])
        assert mpl.rcParams["text.usetex"] is True
        assert mpl.rcParams["font.size"] == 27
    assert paths[0].read_bytes() == paths[1].read_bytes() == paths[2].read_bytes()
    with Image.open(paths[0]) as image:
        assert image.format == "PNG"
        assert image.width >= 900 and image.height == 675
        assert image.info["Software"] == "ThermalPath"
        assert "Creation Time" not in image.info
    with pytest.raises(FileExistsError):
        save_png(figure, paths[0])
    assert paths[0].read_bytes() == paths[1].read_bytes()
    with pytest.raises(ValueError, match="suffix"):
        save_png(figure, tmp_path / "plot.pdf")
