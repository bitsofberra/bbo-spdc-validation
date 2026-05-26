# Karan BBO Phase-Matching Digitized Literature Data

Source: <https://arxiv.org/abs/1810.01184>

`type1_theta_emccd_digitized.csv` records the three Type-I BBO crystal-angle
values associated with Figure 8. In that figure, panels `(a)-(c)` are
experimental EMCCD images and panels `(d)-(f)` are the corresponding numerical
images presented in the paper.

## Digitization Method

Source image used for measurement:

<https://ar5iv.org/html/1810.01184/assets/x8.png>

The native source PNG is `332 x 243` pixels and does not provide a physical
length scale. Consequently, radii are stored in `figure_px`, not in
millimetres. Each annular panel was cropped from the native PNG, its white
panel label was masked, and the ring radius was read as the peak of the
radially averaged intensity profile. A conservative `+/- 1.0 figure_px`
reading uncertainty is assigned.

At `theta_p = 28.64 deg`, both relevant panels show a central blob rather than
an annulus, so no ring radius is assigned. The two annular pairs provide a
paper-internal experiment-versus-numerical comparison:

| Theta (deg) | Experimental panel | Numerical panel | Radius exp. (px) | Radius numerical (px) |
| --- | --- | --- | --- | --- |
| 28.74 | Fig. 8(b) | Fig. 8(e) | 20.3 +/- 1.0 | 21.3 |
| 28.95 | Fig. 8(c) | Fig. 8(f) | 38.3 +/- 1.0 | 39.3 |

These values quantify the paper-internal experimental-versus-numerical trend
shown by Karan et al. in figure-pixel units. They are not a calibrated
millimetre-scale measurement of this package's detector-plane model.
