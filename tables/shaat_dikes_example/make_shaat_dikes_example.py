"""Supplementary Table 2 of the FAIR standard paper: the full Shaat dikes example.

The Shaat dikes pole of Swanson-Hysell et al. (2025, Geology 53, 909-913,
doi:10.1130/G53450.1) in the layout of the template and in MagIC form, taken from
MagIC contribution 20884 (doi:10.7288/V4/MAGIC/20884), reduced to what the pole needs:

    sites          the 51 sites of the pole (the sites column of the pole row of the
                   locations table): magnetite ('mag') site means, geographic and
                   tilt-corrected
    specimens      the 119 specimens averaged into those site means, with their
                   magnetite and low-temperature ('lt') fits in specimen, geographic
                   and tilt-corrected coordinates
    samples        the samples of those specimens
    measurements   their thermal demagnetization steps
    locations      the pole; ages: the age constraints

The low-temperature site means are not included: some of their specimens are not
among the 119. Each level is checked against the one below it: specimen fits
re-made from the measurements and rotated, site means recalculated from the
specimen fits, and the pole recalculated from the site VGPs.

Inputs (../../data/): magic_20884/magic_contribution_20884.txt

Outputs, next to this script:
    FAIR_template_example_Oman2025.xlsx     the spreadsheet: readable sheets, field
                                            dictionary, method codes and MagIC sheets
    magic_contribution_Shaat_pole.txt       the MagIC tables, validated
    build_report.md, specimen_fit_checks.csv, site_mean_checks.csv

Usage:
    python make_shaat_dikes_example.py

Requires numpy, pandas, openpyxl and pmagpy.
"""

import sys
from collections import OrderedDict
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import Workbook
from pmagpy import pmag

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_DIR = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(REPO_DIR))
from fair_template.definition import SHEETS  # noqa: E402
from fair_template.magic import (coverage, load_resources, read_contribution,  # noqa: E402
                                 validate, write_magic_text)
from fair_template.readable import (angle, build_ages, build_locations,  # noqa: E402
                                    build_measurements, build_sites, build_specimens,
                                    butler_uncertainties, check_coordinate_systems,
                                    site_bedding, write_field_dictionary, write_magic_sheet,
                                    write_method_codes, write_readable_sheet, write_readme)

MAGIC_FILE = REPO_DIR / "data" / "magic_20884" / "magic_contribution_20884.txt"
OUTPUT_DIR = SCRIPT_DIR
# the MagIC upload file of the example in the repository, linked from the README sheet
MAGIC_TEXT_URL = ("https://github.com/PolarWandering/FAIR_paleomag_data/blob/main/tables/"
                  "shaat_dikes_example/magic_contribution_Shaat_pole.txt")

PAPER = ("Swanson-Hysell et al. (2025), Oman was on the northern margin of a wide late Tonian "
         "Mozambique Ocean, Geology, doi:10.1130/G53450.1")
REFERENCE = "10.1130/G53450.1"
LOCATION = "Zalawt plain"
COMPONENT = "mag"
COMPONENTS = (COMPONENT, "lt")
PLATE = "Arabian Plate"
# Reference location for the paleolatitude (Shaat_location in dike_paleomagnetism.ipynb of
# the 2025_Oman_Paleogeography repository)
REFERENCE_LAT, REFERENCE_LON = 17.1, 54.9
# Published pole (Swanson-Hysell et al., 2025)
PUBLISHED = dict(pole_lon=110.1, pole_lat=17.8, pole_alpha95=2.5, pole_k=65.1, n=51,
                 paleolat=37.5)
# Field tests reported in the paper. The reversal test is class B of McFadden and
# McElhinny (1990): 3.7° between the normal and reversed means, critical angle 5.4°. The
# conglomerate test is on 16 clasts of the Ayn Formation diamictite (Watson, 1956:
# R = 3.9 < Ro95 = 6.4).
FIELD_TESTS = dict(reversal_test="Rb", conglomerate_test="+")
# Ages (Swanson-Hysell et al., 2025): LA-ICPMS U-Pb zircon dates of two dated felsic dikes
# in the pole, and the Leger Granite ID-TIMS date of Bowring et al. (2007,
# doi:10.2475/10.2007.01) with which dike emplacement was broadly comagmatic.
AGES = [
    dict(location=LOCATION, site=None, age=726.1, age_sigma=0.4, age_unit="Ma",
         method_codes="GM-UPB", citations="10.2475/10.2007.01",
         description="Leger Granite, U-Pb zircon ID-TIMS (Bowring et al., 2007); the Shaat dikes "
                     "and Leger Granite were broadly comagmatic (Swanson-Hysell et al., 2025)"),
    dict(location=LOCATION, site="SD39", age=725, age_sigma=9, age_unit="Ma",
         method_codes="GM-UPB", citations="This study",
         description="Felsic dike, U-Pb zircon LA-ICPMS"),
    dict(location=LOCATION, site="SD50", age=727, age_sigma=16, age_unit="Ma",
         method_codes="GM-UPB", citations="This study",
         description="Felsic dike, U-Pb zircon LA-ICPMS"),
]
# pole dictionary entries that are not MagIC locations columns
NOT_LOCATION_COLUMNS = ("dDx", "dIx", "flattening_note")


# ---------------------------------------------------------------------------
# The part of the contribution that the pole needs
# ---------------------------------------------------------------------------
def pole_sites(magic):
    """The sites of the pole, from the pole row of the locations table."""
    locations = magic["locations"]
    return locations.loc[locations["pole_lat"].notna(), "sites"].iloc[0].split(":")


def pole_subset(magic):
    """The tables of the contribution, reduced to what the pole needs."""
    names = pole_sites(magic)
    sites = magic["sites"]
    sites = sites[sites["site"].isin(names) & (sites["dir_comp_name"] == COMPONENT)].copy()
    tilt = sites[sites["dir_tilt_correction"] == "100"]
    assert len(tilt) == len(names), "a pole site has no tilt-corrected mean"
    used = {spec for v in tilt["specimens"] for spec in v.split(":")}
    specimens = magic["specimens"]
    specimens = specimens[specimens["specimen"].isin(used) &
                          specimens["dir_comp"].isin(COMPONENTS)].copy()
    # the DE-VM rows carry a note on how Demag GUI labelled them; not needed in the example
    relabel_note = specimens["description"].str.startswith("Vector mean of the selected steps",
                                                            na=False)
    specimens.loc[relabel_note, "description"] = np.nan
    samples = magic["samples"][magic["samples"]["sample"].isin(specimens["sample"])].copy()
    measurements = magic["measurements"][
        magic["measurements"]["experiment"].isin(set(specimens["experiments"]))].copy()
    locations = magic["locations"][magic["locations"]["pole_lat"].notna()].copy()
    return sites, specimens, samples, measurements, locations


# ---------------------------------------------------------------------------
# Checks: measurements -> specimen fits -> site means -> pole
# ---------------------------------------------------------------------------
def selected_steps(meas, step_min, step_max):
    """Steps of a fit, as Demag GUI selects them: from the first step at the lower
    bound to the first step at the upper bound, in measurement order, good steps only.
    """
    meas = meas.sort_values("sequence", key=lambda s: s.astype(float))
    meas = meas[meas["quality"] == "g"]
    temps = meas["treat_temp"].astype(float).round(1).tolist()
    start, end = temps.index(round(step_min, 1)), temps.index(round(step_max, 1))
    return meas.iloc[start:end + 1]


def refit(steps, fit_code):
    """Specimen-frame direction and MAD of a fit: a free line (DE-BFL) or a vector mean
    (DE-VM).
    """
    block = [[i, float(d), float(n), float(m), "g"] for i, (d, n, m) in
             enumerate(zip(steps["dir_dec"], steps["dir_inc"], steps["magn_moment"]))]
    if fit_code == "DE-VM":
        return pmag.vector_mean([b[1:4] for b in block])[0][:2], None
    if fit_code != "DE-BFL":
        raise ValueError(f"no re-fit implemented for {fit_code}")
    mpars = pmag.domean(block, 0, len(block) - 1, "DE-BFL")
    return (mpars["specimen_dec"], mpars["specimen_inc"]), mpars["specimen_mad"]


def check_specimen_fits(specimens, samples, measurements):
    """Re-fit every specimen component from its measurements and rotate it with the
    sample orientation (pmag.dogeo) and bedding (pmag.dotilt). One row per fit.
    """
    sample_rows = samples.set_index("sample")
    meas_by_experiment = dict(tuple(measurements.groupby("experiment")))
    checks = []
    fits = specimens[specimens["dir_tilt_correction"].notna()]
    for (name, comp), rows in fits.groupby(["specimen", "dir_comp"], sort=False):
        rows = rows.set_index("dir_tilt_correction")
        spec = rows.loc["-1"]
        code = "DE-VM" if "DE-VM" in spec["method_codes"] else "DE-BFL"
        steps = selected_steps(meas_by_experiment[spec["experiments"]],
                               float(spec["meas_step_min"]), float(spec["meas_step_max"]))
        fit, mad = refit(steps, code)
        sample = sample_rows.loc[spec["sample"]]
        gdec, ginc = pmag.dogeo(fit[0], fit[1], float(sample["azimuth"]), float(sample["dip"]))
        rec = dict(specimen=name, component=comp, fit=code, n_steps=len(steps),
                   n_stored=int(float(spec["dir_n_measurements"])),
                   spec_misfit=angle(fit, (float(spec["dir_dec"]), float(spec["dir_inc"]))),
                   geo_misfit=angle((gdec, ginc), (float(rows.loc["0", "dir_dec"]),
                                                   float(rows.loc["0", "dir_inc"]))),
                   mad_refit=mad,
                   mad_stored=None if code == "DE-VM" else float(spec["dir_mad_free"]))
        if "100" in rows.index:
            tdec, tinc = pmag.dotilt(gdec, ginc, float(sample["bed_dip_direction"]),
                                     float(sample["bed_dip"]))
            rec["tilt_misfit"] = angle((tdec, tinc), (float(rows.loc["100", "dir_dec"]),
                                                      float(rows.loc["100", "dir_inc"])))
        checks.append(rec)
    return pd.DataFrame(checks)


def check_site_means(sites, specimens):
    """Fisher means of the listed specimens, compared with the stored site means."""
    checks = []
    fits = specimens[specimens["dir_tilt_correction"].notna()]
    for _, s in sites[sites["dir_dec"].notna()].iterrows():
        listed = s["specimens"].split(":")
        rows = fits[fits["specimen"].isin(listed) & (fits["dir_comp"] == s["dir_comp_name"]) &
                    (fits["dir_tilt_correction"] == s["dir_tilt_correction"])]
        mean = pmag.fisher_mean([[float(d), float(i)] for d, i in
                                 zip(rows["dir_dec"], rows["dir_inc"])])
        # single-specimen sites: the site direction is the specimen direction, no k or α95
        checks.append(dict(site=s["site"], component=s["dir_comp_name"],
                           tc=s["dir_tilt_correction"], n=len(rows),
                           n_stored=int(float(s["dir_n_specimens"])),
                           misfit=angle((mean["dec"], mean["inc"]),
                                        (float(s["dir_dec"]), float(s["dir_inc"]))),
                           a95=mean.get("alpha95"), a95_stored=pd.to_numeric(
                               s["dir_alpha95"], errors="coerce")))
    return pd.DataFrame(checks)


def calculate_pole(tilt_means):
    """Fisher mean of the VGPs of the tilt-corrected site means (reversed ones flipped),
    with the mean direction and its ΔDx and ΔIx at the reference location.
    """
    vgps = [(float(lo), float(la)) if p == "n" else ((float(lo) + 180) % 360, -float(la))
            for lo, la, p in zip(tilt_means["vgp_lon"], tilt_means["vgp_lat"],
                                 tilt_means["dir_polarity"])]
    pole = pmag.fisher_mean([[lo, la] for lo, la in vgps])
    dirs = pmag.flip([[float(d), float(i)] for d, i in zip(tilt_means["dir_dec"],
                                                           tilt_means["dir_inc"])],
                     combine=True)
    d = pmag.fisher_mean(dirs)
    lats, lons = tilt_means["lat"].astype(float), tilt_means["lon"].astype(float)
    # paleolatitude of the study's reference location predicted by the pole
    paleolat = 90 - angle((pole["dec"], pole["inc"]), (REFERENCE_LON, REFERENCE_LAT))
    dDx, dIx = butler_uncertainties(pole["alpha95"], paleolat)
    n_reversed = int((tilt_means["dir_polarity"] == "r").sum())
    return OrderedDict(
        location=LOCATION,
        result_name="Shaat dikes pole (Leger panel, magnetite component)",
        location_type="Region", geologic_classes="Igneous",
        lithologies=":".join(sorted(set(tilt_means["lithologies"]))),
        lat_s=round(lats.min(), 4), lat_n=round(lats.max(), 4),
        lon_w=round(lons.min(), 4), lon_e=round(lons.max(), 4),
        age=726, age_low=float(tilt_means["age_low"].astype(float).min()),
        age_high=float(tilt_means["age_high"].astype(float).max()), age_unit="Ma",
        pole_comp_name=COMPONENT, sites=":".join(tilt_means["site"]),
        pole_n_sites=len(tilt_means), dir_dec=round(d["dec"], 1), dir_inc=round(d["inc"], 1),
        dir_tilt_correction=100, dir_alpha95=round(d["alpha95"], 1), dir_k=round(d["k"], 1),
        dir_n_sites=len(tilt_means), pole_lat=round(pole["inc"], 1),
        pole_lon=round(pole["dec"], 1), pole_k=round(pole["k"], 1),
        pole_alpha95=round(pole["alpha95"], 1), dir_polarity="n", paleolat=round(paleolat, 1),
        paleolat_sigma=round(pole["alpha95"], 1),
        pole_reversed_perc=round(100 * n_reversed / len(tilt_means), 1), **FIELD_TESTS,
        dDx=round(dDx, 1), dIx=round(dIx, 1), pole_flattening=None,
        flattening_note="n/a (dikes)", plate_blocks=PLATE,
        method_codes="DE-FM:DA-DIR-TILT", citations="This study",
        description=(f"Fisher mean of the VGPs of the tilt-corrected site means of the Leger "
                     f"panel, reversed VGPs flipped (Swanson-Hysell et al., 2025). Paleolatitude "
                     f"at {REFERENCE_LAT}°N, {REFERENCE_LON}°E ± A95. The mean direction is at "
                     f"the same location: ΔDx = {dDx:.1f}°, ΔIx = {dIx:.1f}° (Butler, 1992)."))


# ---------------------------------------------------------------------------
# MagIC form
# ---------------------------------------------------------------------------
def inherit_from_sites(samples, sites):
    """Fill the sample columns MagIC requires from the sample's site, where empty."""
    samples = samples.copy()
    site_rows = sites.drop_duplicates("site").set_index("site")
    for col in ("geologic_classes", "geologic_types", "lithologies", "lat", "lon"):
        values = samples["site"].map(site_rows[col])
        samples[col] = samples[col].fillna(values) if col in samples else values
    return samples


def magic_form(sites, samples, specimens, measurements, ages, poles):
    """The example's MagIC tables, with site bedding and geology filled down."""
    tables = OrderedDict()
    tables["locations"] = pd.DataFrame([{k: v for k, v in p.items()
                                         if k not in NOT_LOCATION_COLUMNS} for p in poles])
    sites = sites.copy()
    bedding = site_bedding(samples)
    sites["bed_dip_direction"] = sites["site"].map(bedding["bed_dip_direction"])
    sites["bed_dip"] = sites["site"].map(bedding["bed_dip"])
    tables["sites"] = sites
    tables["samples"] = inherit_from_sites(samples, sites)
    spec = specimens.copy()
    sample_rows = tables["samples"].set_index("sample")
    for col in ("geologic_classes", "geologic_types", "lithologies"):
        spec[col] = spec["sample"].map(sample_rows[col])
    tables["specimens"] = spec
    tables["measurements"] = measurements
    tables["ages"] = ages
    return tables


def write_workbook(path, readme, data, notes, tables, contribution):
    """Readable sheets, field dictionary, method codes and the MagIC-form sheets."""
    used_codes = set()
    for df in tables.values():
        if "method_codes" in df:
            for v in df["method_codes"].dropna():
                used_codes.update(v.split(":"))
    wb = Workbook()
    write_readme(wb, readme)
    for sheet, rows in data.items():
        write_readable_sheet(wb, sheet, SHEETS[sheet], rows, notes[sheet])
    write_field_dictionary(wb)
    write_method_codes(wb, used_codes)
    for name, df in tables.items():
        write_magic_sheet(wb, f"MagIC {name}", df)
    write_magic_sheet(wb, "MagIC contribution", contribution)
    wb.save(path)


def main():
    magic = read_contribution(MAGIC_FILE)
    contribution = magic["contribution"][
        ["id", "data_model_version", "reference", "lab_names", "contributor"]]
    magic_id = str(contribution.iloc[0]["id"])
    sites, specimens, samples, measurements, locations = pole_subset(magic)

    fit_checks = check_specimen_fits(specimens, samples, measurements)
    site_checks = check_site_means(sites, specimens)
    tilt = sites[sites["dir_tilt_correction"] == "100"]
    pole = calculate_pole(tilt)
    stored = locations.iloc[0]
    pole_misfit = angle((pole["pole_lon"], pole["pole_lat"]),
                        (float(stored["pole_lon"]), float(stored["pole_lat"])))

    ages = pd.DataFrame(AGES).astype(object)
    tables = magic_form(sites, samples, specimens, measurements, ages, [pole])
    sample_rows = tables["samples"].set_index("sample")
    age_rows = {a["site"]: a for a in AGES if a["site"]}
    data = OrderedDict([
        ("Contribution", [[REFERENCE, contribution.iloc[0]["lab_names"], magic_id,
                           f"10.7288/V4/MAGIC/{magic_id}",
                           "3.0", contribution.iloc[0].get("contributor")]]),
        ("1 Measurements", build_measurements(measurements)),
        ("2 Specimen directions", build_specimens(specimens, sample_rows, tables["sites"])),
        ("3 Site means", build_sites(tables["sites"], sample_rows, age_rows)),
        ("4 Poles", build_locations([pole])),
        ("5 Ages", build_ages(ages)),
    ])

    dm, vocab, codes = load_resources()
    problems = validate(tables, dm, vocab, codes)
    write_magic_text(contribution, tables, OUTPUT_DIR / "magic_contribution_Shaat_pole.txt")
    covered, missing = coverage(dm)
    geo, tilt_misfit = check_coordinate_systems(data["2 Specimen directions"])

    n_spec = specimens["specimen"].nunique()
    n_lt = specimens.loc[specimens["dir_comp"] == "lt", "specimen"].nunique()
    notes = {
        "Contribution": "Contribution metadata (MagIC contribution table).",
        "1 Measurements": f"Level 1: every demagnetization step of the {n_spec} specimens in "
                          "the pole (directions in specimen coordinates).",
        "2 Specimen directions": f"Level 2: the magnetite (mag) component of the {n_spec} "
                                 f"specimens in the pole and the low-temperature (lt) component "
                                 f"of {n_lt} of them, in specimen, geographic and tilt-corrected "
                                 "coordinates.",
        "3 Site means": f"Level 3: the {len(tilt)} magnetite site means in the pole, in "
                        "geographic and tilt-corrected coordinates, with VGPs.",
        "4 Poles": f"Level 3: the Shaat dikes pole, the Fisher mean of the {len(tilt)} site VGPs.",
        "5 Ages": "Age constraints on the pole (MagIC ages table).",
    }
    readme = [
        "FAIR paleomagnetic data standard: template tables for one paleomagnetic pole",
        f"Example: the Shaat dikes pole of {PAPER}.",
        f"Data: MagIC contribution {magic_id}, dataset DOI 10.7288/V4/MAGIC/{magic_id}:",
        (f"https://earthref.org/MagIC/{magic_id}", f"https://earthref.org/MagIC/{magic_id}"),
        "",
        f"These tables hold everything needed to regenerate the pole: the {len(tilt)} sites "
        f"averaged into the pole, the {n_spec} specimens averaged into those sites, their "
        f"samples and their {len(measurements):,} thermal demagnetization steps. Specimen "
        "directions are given for the magnetite component used in the pole and for the "
        "low-temperature overprint. Each level can be recalculated from the one below it (see "
        "build_report.md).",
        "",
        "How to read the tables. Sheets 1–5 are the template in readable form. Under each column "
        "header are the MagIC data model 3.0 column (table.column), units and conventions, and "
        "whether MagIC requires it, this standard requires it, or it is recommended. The sheets "
        "named 'MagIC …' hold the same data in MagIC form, one table per sheet. The same tables "
        "as one MagIC upload file (tab-delimited text, magic_contribution_Shaat_pole.txt):",
        (MAGIC_TEXT_URL, MAGIC_TEXT_URL),
        "",
        f"MagIC-required columns covered by the template: {len(covered)}; missing: "
        f"{len(missing)}. Validation of the MagIC form: "
        f"{'no problems' if not problems else f'{len(problems)} problems (see build_report.md)'}.",
        "",
        "Built by tables/shaat_dikes_example/make_shaat_dikes_example.py in "
        "github.com/PolarWandering/FAIR_paleomag_data.",
    ]
    write_workbook(OUTPUT_DIR / "FAIR_template_example_Oman2025.xlsx", readme, data, notes,
                   tables, contribution)

    by_fit = fit_checks.groupby(["component", "fit"]).agg(
        n=("specimen", "size"),
        steps_agree=("n_steps", lambda s: int((s == fit_checks.loc[s.index, "n_stored"]).sum())),
        specimen_frame=("spec_misfit", "max"), geographic=("geo_misfit", "max"),
        tilt_corrected=("tilt_misfit", "max")).round(3).astype({"n": int, "steps_agree": int})
    tc = site_checks[site_checks["tc"] == "100"]
    report = [
        "# Shaat dikes pole example: build report", "",
        f"Source: {PAPER}. Data: MagIC contribution {magic_id} "
        f"(data/magic_20884/{MAGIC_FILE.name}).", "",
        "## Contents", "",
        f"- Sites: {len(tilt)} (the sites of the pole row of the locations table), magnetite "
        "means in geographic and tilt-corrected coordinates",
        f"- Specimens: {n_spec}; fits: {COMPONENT} for all, lt for {n_lt}; "
        f"{len(specimens)} rows (three coordinate systems)",
        f"- Samples: {len(samples)}; measurements: {len(measurements):,} "
        f"({measurements['experiment'].nunique()} experiments)", "",
        "## Measurements -> specimen fits", "",
        "Fits re-made from the measurements (Demag GUI step selection: first step at the lower "
        "bound to first step at the upper bound) and rotated with the sample orientation and "
        "bedding. Maximum misfits (degrees):", "",
        "| Component | Fit | n | Steps agree | Specimen frame | Geographic | Tilt-corrected |",
        "| --- | --- | --- | --- | --- | --- | --- |",
        *[f"| {r.Index[0]} | {r.Index[1]} | {r.n} | {r.steps_agree} | {r.specimen_frame} | "
          f"{r.geographic} | {r.tilt_corrected} |" for r in by_fit.itertuples()], "",
        "Three specimens (SD58-2, SD58-3, SD96-1) have a repeat measurement at the last "
        "temperature step; Demag GUI used the first occurrence, which dir_n_measurements "
        "confirms.", "",
        "## Specimen fits -> site means -> VGPs -> pole", "",
        f"- Site means recalculated from the listed specimens (tilt-corrected): n agrees for "
        f"{(tc.n == tc.n_stored).sum()} of {len(tc)}; direction misfit max {tc.misfit.max():.2f}°. "
        f"{(tc.n == 1).sum()} sites have one specimen (no k or α95).",
        f"- Pole from the VGPs: {pole['pole_lon']}°E, {pole['pole_lat']}°N, A95 = "
        f"{pole['pole_alpha95']}°, K = {pole['pole_k']}, N = {pole['pole_n_sites']}; "
        f"paleolatitude {pole['paleolat']}°N at {REFERENCE_LAT}°N, {REFERENCE_LON}°E; "
        f"{(tilt['dir_polarity'] == 'r').sum()} reversed and {(tilt['dir_polarity'] == 'n').sum()} "
        f"normal sites. Pole in the contribution: {pole_misfit:.2f}° away.",
        f"- Mean direction at the reference location: D = {pole['dir_dec']}° ± ΔDx "
        f"{pole['dDx']}°, I = {pole['dir_inc']}° ± ΔIx {pole['dIx']}° (Butler, 1992).",
        f"- Published: {PUBLISHED['pole_lon']}°E, {PUBLISHED['pole_lat']}°N, A95 = "
        f"{PUBLISHED['pole_alpha95']}°, K = {PUBLISHED['pole_k']}, N = {PUBLISHED['n']}; "
        f"paleolatitude {PUBLISHED['paleolat']} ± 2.5°N.", "",
        "## Template coverage and validation", "",
        f"{len(covered)} MagIC-required columns covered; missing: {missing or 'none'}.",
        ("Validation: no problems found." if not problems else
         "Validation problems:\n" + "\n".join(f"- {p}" for p in problems[:40])),
        f"Coordinate systems recomputed from each row of the readable specimen table: geographic "
        f"max {geo.max():.2f}°, tilt-corrected max {tilt_misfit.max():.2f}° (0.1° rounding).", "",
    ]
    (OUTPUT_DIR / "build_report.md").write_text("\n".join(report))
    fit_checks.round(4).to_csv(OUTPUT_DIR / "specimen_fit_checks.csv", index=False)
    site_checks.round(3).to_csv(OUTPUT_DIR / "site_mean_checks.csv", index=False)
    print("\n".join(report))


if __name__ == "__main__":
    main()
