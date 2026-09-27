"""Constant convection data for reduced steady plate models."""

from dataclasses import dataclass

from thermalpath.models import _scalar


@dataclass(frozen=True)
class Convection:
    """Define a constant film coefficient and reservoir temperature.

    Parameters
    ----------
    coefficient_w_m2_k : float
        Finite nonnegative coefficient [W/(m2 K)]. For a lateral edge this
        is its film coefficient. For broad-face convection it is the sum
        of both face coefficients per projected cell area; no factor of two
        is added. Zero disables exchange.
    ambient_temperature_k : float
        Finite positive reservoir temperature [K], required even at zero
        coefficient. Broad faces share this ambient temperature.
    """

    coefficient_w_m2_k: float
    ambient_temperature_k: float

    def __post_init__(self) -> None:
        """Normalize immutable scalar inputs and validate their domains."""
        coefficient = _scalar(self.coefficient_w_m2_k, "coefficient_w_m2_k")
        if coefficient < 0:
            raise ValueError("coefficient_w_m2_k must be nonnegative")
        object.__setattr__(self, "coefficient_w_m2_k", coefficient)
        object.__setattr__(
            self,
            "ambient_temperature_k",
            _scalar(self.ambient_temperature_k, "ambient_temperature_k", positive=True),
        )
