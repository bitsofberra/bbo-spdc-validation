# BYU Non-Collinear SPDC Digitized Literature Data

Source: <https://physics.byu.edu/docs/thesis/103>

The source is Dustin Shipp, *Numerical Model of Non-Collinear Parametric
Down-Conversion*, BYU senior thesis (2008). It reports Type-I BBO measurements
using a `351 nm` pump and `690 +/- 5 nm` selected daughter photons. These
wavelengths differ from the default `405 nm / 810 nm` package case, so this
dataset is supplementary only.

## Digitization Method

`byu_fig3_3_digitized.csv` records the ten ring-diameter points read from the
upper-left panel of Figure 3.3, including:

- observed CCD data without a lens
- observed CCD data with a `400 mm` lens
- the computational curve published in the thesis

The PDF page was rendered at high resolution and the plot axes were calibrated
from `-0.4 deg` to `1.0 deg` in crystal-face angle and from `0 deg` to `14 deg`
in ring diameter. A conservative reading uncertainty of `+/- 0.05 deg` is
stored for the digitized ring diameter values.

The thesis discusses an approximate `0.2 deg` crystal-axis offset between the
observed and computational curves. The clean thesis output reports both this
literature-offset context and a fitted offset derived from the digitized curve.
The fitted comparison extends the digitized computational curve linearly at
its boundary; for that reason it is reported with RMSE and MAE, not R².
The comparison is paper-internal: it compares digitized experimental points
against Shipp's published computational curve, not against the package's
default `405 nm / 810 nm` model.
