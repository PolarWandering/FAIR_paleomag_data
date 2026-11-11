# Shaat dikes pole example: build report

Source: Swanson-Hysell et al. (2025), Oman was on the northern margin of a wide late Tonian Mozambique Ocean, Geology, doi:10.1130/G53450.1. Data: MagIC contribution 20884 (data/magic_20884/magic_contribution_20884.txt).

## Contents

- Sites: 51 (the sites of the pole row of the locations table), magnetite means in geographic and tilt-corrected coordinates
- Specimens: 119; fits: mag for all, lt for 39; 474 rows (three coordinate systems)
- Samples: 119; measurements: 2,596 (119 experiments)

## Measurements -> specimen fits

Fits re-made from the measurements (Demag GUI step selection: first step at the lower bound to first step at the upper bound) and rotated with the sample orientation and bedding. Maximum misfits (degrees):

| Component | Fit | n | Steps agree | Specimen frame | Geographic | Tilt-corrected |
| --- | --- | --- | --- | --- | --- | --- |
| lt | DE-BFL | 39 | 39 | 0.053 | 0.057 | 0.066 |
| mag | DE-BFL | 88 | 88 | 0.059 | 0.056 | 0.058 |
| mag | DE-VM | 31 | 31 | 0.062 | 0.047 | 0.051 |

Three specimens (SD58-2, SD58-3, SD96-1) have a repeat measurement at the last temperature step; Demag GUI used the first occurrence, which dir_n_measurements confirms.

## Specimen fits -> site means -> VGPs -> pole

- Site means recalculated from the listed specimens (tilt-corrected): n agrees for 51 of 51; direction misfit max 0.06°. 16 sites have one specimen (no k or α95).
- Pole from the VGPs: 110.1°E, 17.8°N, A95 = 2.5°, K = 65.1, N = 51; paleolatitude 37.5°N at 17.1°N, 54.9°E; 44 reversed and 7 normal sites. Pole in the contribution: 0.02° away.
- Mean direction at the reference location: D = 80.5° ± ΔDx 3.1°, I = 56.5° ± ΔIx 2.4° (Butler, 1992).
- Published: 110.1°E, 17.8°N, A95 = 2.5°, K = 65.1, N = 51; paleolatitude 37.5 ± 2.5°N.

## Template coverage and validation

60 MagIC-required columns covered; missing: none.
Validation: no problems found.
Coordinate systems recomputed from each row of the readable specimen table: geographic max 0.11°, tilt-corrected max 0.10° (0.1° rounding).
