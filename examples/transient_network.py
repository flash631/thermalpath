"""Print a synthetic two-node network with a load change at one second."""

import os

for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[variable] = "1"

from thermalpath import Link, Network, Node, solve_transient  # noqa: E402


def main() -> None:
    """Run the documented network and print its temperature history in kelvin."""
    network = Network(
        (Node("a"), Node("b"), Node("sink", fixed_temperature_k=300)),
        (
            Link("ab", "a", "b", 1),
            Link("a0", "a", "sink", 2),
            Link("b0", "b", "sink", 1),
        ),
    )
    result = solve_transient(
        network,
        {"a": 2, "b": 3},
        {"a": 300, "b": 300},
        [0, 1, 3],
        [{"a": 10, "b": 0}, {"a": 0, "b": 6}],
    )
    print("time_s,a_K,b_K,sink_K")
    for time, row in zip(result.times_s, result.temperatures_k, strict=True):
        print(f"{time:g},{row['a']:.12f},{row['b']:.12f},{row['sink']:.12f}")


if __name__ == "__main__":
    main()
