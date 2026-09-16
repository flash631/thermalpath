# Applicability limits

D01 models a steady chain with one prescribed power and one fixed sink
temperature. Every resistance represents a distinct thermal connection.
The calculation omits parallel losses, thermal storage, temperature-dependent
material properties, radiation, spreading resistance, and spatial variation.

Inputs are synthetic. No measurements, device datasheets, or experimentally
established uncertainty bounds support this example. A calculated source
temperature cannot establish compliance with a component limit unless the
network, load, environment, and limit are independently justified.

The later plate is depth averaged with prescribed convection. It will not solve
airflow, turbulence, boiling, or thickness gradients. It will not estimate a
convection coefficient from fan speed or enclosure shape.

Finite inputs can still exceed floating-point range. The API rejects a
nonfinite output and a conduction resistance that underflows to zero. Very small
finite temperature rises can round away when added to a much larger ambient;
the API does not promise relative accuracy on such a rise.
