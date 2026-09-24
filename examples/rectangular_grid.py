"""Print geometry for a synthetic six-cell plate; no thermal solve."""

import json
import math
import os

for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[variable] = "1"

from thermalpath import RectangularGrid  # noqa: E402


def main() -> None:
    """Report areas and volumes for a 60 mm by 40 mm by 2 mm plate."""
    grid = RectangularGrid((0, 0.01, 0.03, 0.06), (0, 0.01, 0.04), 0.002)
    print(
        json.dumps(
            {
                "cell_count": grid.cell_count,
                "domain_area_m2": grid.area_m2,
                "domain_volume_m3": grid.volume_m3,
                "sum_cell_areas_m2": math.fsum(
                    grid.cell_area_m2(k) for k in range(grid.cell_count)
                ),
                "sum_cell_volumes_m3": math.fsum(
                    grid.cell_volume_m3(k) for k in range(grid.cell_count)
                ),
                "cells": [
                    {
                        "index": k,
                        "indices_xy": grid.indices(k),
                        "center_m": grid.center_m(k),
                        "area_m2": grid.cell_area_m2(k),
                        "volume_m3": grid.cell_volume_m3(k),
                        "face_areas_wesn_m2": grid.face_areas_m2(k),
                        "neighbors_wesn": grid.neighbors(k),
                    }
                    for k in range(grid.cell_count)
                ],
            },
            indent=2,
            allow_nan=False,
        )
    )


if __name__ == "__main__":
    main()
