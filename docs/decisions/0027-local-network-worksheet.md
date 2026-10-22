# Local network worksheet

Use a fixed three-node topology for the first interface: heater, unloaded
spreader, and prescribed sink. Four numerical controls map directly to the
existing library's validated SI inputs. Streamlit batches edits in one form;
the submitted values remain visible alongside the results.

No solver equations are implemented in the app. With heater power P, contact
conductance Gc and sink conductance Gs, the independent series reference is
Ts = Tb + P/Gs and Th = Ts + P/Gc. Positive conductances and the fixed sink
give a unique anchored steady system. Each link carries P toward the sink;
reservoir input is -P. At zero power all temperatures equal Tb.

Four frozen reference cases use exact rational arithmetic and an absolute
tolerance of 2e-10 K or W with zero relative tolerance. The tolerance allows
binary64 assembly and subtraction roundoff across the selected cases. It is
not a bound on all possible inputs. Existing library domain checks remain
active. No mesh or time step is introduced, so no new refinement claim applies.

The interface shows units, signed reservoir input, physical balance and matrix
residual separately. It makes no acceptance or safety classification. Control
ranges are usability limits, not measured operating ranges. The source app
ships in the source archive; the wheel remains the reusable library.
