"""The readable (template) form of MagIC tables, and its Excel styling.

Each build_* function turns MagIC tables (DataFrames of object columns, as read by
fair_template.magic.read_contribution) into rows of the corresponding sheet of the
template, in the order of the fields in fair_template.definition.SHEETS.
"""

import numpy as np
import pandas as pd
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from pmagpy import pmag

from fair_template.definition import (MAGIC, NO_COLUMN, RECOMMENDED, SHEETS, SPECIMEN_FIELDS,
                                      STANDARD, STANDARD_IF_APPLICABLE)
from fair_template.magic import method_code_definitions, num

# Readable labels for the method codes used (definitions are in the MagIC
# method code list, which is written to the "Method codes" sheet)
CODE_LABELS = {
    "LT-NO": "NRM", "LT-T-Z": "Thermal", "LT-LT-Z": "Low-T cycle", "LT-AF-Z": "AF",
    "LP-DIR-T": "Thermal demag.", "LP-DIR-AF": "AF demag.",
    "DE-BFL": "Line, free", "DE-BFL-A": "Line, anchored", "DE-BFL-O": "Line, origin as point",
    "DE-BFP": "Plane", "DE-FM": "Fisher mean", "DE-VM": "Vector mean",
    "DA-DIR": "Specimen coord.", "DA-DIR-GEO": "Geographic coord.",
    "DA-DIR-TILT": "Tilt-corrected coord.", "LP-DC4": "PCA from Zijderveld diagrams",
    "SO-CMD-NORTH": "Declination-corrected to true north", "SO-MAG": "Magnetic compass",
    "SO-SUN": "Sun compass", "GM-INT": "Interpolated between dated units",
    "GM-UPB": "U-Pb", "SP-SAW": "Sawed", "FS-LOC-GPS": "Location by GPS",
}
QUALITY = {"g": "Included", "b": "Excluded"}
POLARITY = {"n": "normal", "r": "reversed", "t": "transitional", "e": "excursional"}
COORDINATES = {-1: "Specimen", 0: "Geographic", 100: "Tilt-corrected"}
POLE_POLARITY = {"n": "north (n)", "r": "south (r)"}


def codes_with(codes, prefix):
    return [c for c in str(codes).split(":") if c.startswith(prefix)] if pd.notna(codes) else []


def label(codes, prefix=""):
    """Readable form of a colon-delimited method code list."""
    return "; ".join(CODE_LABELS.get(c, c) for c in codes_with(codes, prefix))


def step_readable(value, unit):
    """MagIC step (K or T) in °C or mT."""
    x = num(value)
    if x is None:
        return None
    return round(x - 273.15) if unit == "K" else round(x * 1000, 1)


def round_or_none(value, n=1):
    x = num(value)
    return None if x is None else round(x, n)


def angle(d1, d2):
    """Angle (degrees) between two directions given as (dec, inc)."""
    u = pmag.dir2cart([d1[0], d1[1], 1.])
    v = pmag.dir2cart([d2[0], d2[1], 1.])
    return float(np.degrees(np.arccos(np.clip(np.dot(u, v), -1, 1))))


def butler_uncertainties(a95, paleolat):
    """ΔDx and ΔIx (degrees) from A95 at a paleolatitude (Butler, 1992, eqs. 7.26-7.27)."""
    A95, lat = np.radians(a95), np.radians(paleolat)
    ddx = np.degrees(np.arcsin(np.sin(A95) / np.cos(lat)))
    dix = np.degrees(2 * A95 / (1 + 3 * np.sin(lat) ** 2))
    return ddx, dix


# ---------------------------------------------------------------------------
# Readable rows
# ---------------------------------------------------------------------------
def build_measurements(measurements):
    rows = []
    for _, r in measurements.iterrows():
        codes = r["method_codes"]
        treatment = label(codes, "LT-")
        temp = num(r["treat_temp"])
        af = num(r["treat_ac_field"])
        rows.append([r["specimen"], r["experiment"], r["measurement"],
                     int(float(r["treat_step_num"])), f"{treatment} ({codes})",
                     round(temp - 273.15) if temp is not None and "LT-AF-Z" not in codes else None,
                     round(af * 1000, 1) if af else None,
                     num(r["magn_moment"]), round_or_none(r["dir_dec"]),
                     round_or_none(r["dir_inc"]), round_or_none(r.get("dir_csd")),
                     r["quality"], r["citations"]])
    return rows


def build_specimens(specimens, samples, sites):
    """Specimen rows: one per fit, in specimen, geographic and tilt-corrected coordinates.

    samples is indexed by sample; sites gives the location of each site.
    """
    site_location = sites.drop_duplicates("site").set_index("site")["location"]
    rows = []
    interpreted = specimens[specimens["dir_tilt_correction"].notna()].copy()
    interpreted["tc"] = interpreted["dir_tilt_correction"].astype(float).astype(int)
    for (name, comp), g in interpreted.groupby(["specimen", "dir_comp"], sort=False):
        g = g.set_index("tc")
        first = g.iloc[0]
        smp = samples.loc[first["sample"]]
        unit = first["meas_step_unit"]
        mad = first.get("dir_mad_free") if pd.notna(first.get("dir_mad_free")) else \
            first.get("dir_mad_anc")
        rows.append([
            site_location.get(smp["site"]), smp["site"], first["sample"], name,
            num(smp.get("height")),
            num(smp["azimuth"]), num(smp["dip"]), label(smp["method_codes"], "SO-"),
            num(smp["bed_dip_direction"]), num(smp["bed_dip"]),
            None if pd.isna(first.get("volume")) else num(first["volume"]) * 1e6,
            label(first["method_codes"], "LP-DIR"), comp, label(first["method_codes"], "DE-"),
            step_readable(first["meas_step_min"], unit),
            step_readable(first["meas_step_max"], unit),
            int(float(first["dir_n_measurements"])), round_or_none(mad),
            round_or_none(first.get("dir_dang")),
            *[round_or_none(g.loc[tc, c]) if tc in g.index else None
              for tc in (-1, 0, 100) for c in ("dir_dec", "dir_inc")],
            QUALITY.get(first["result_quality"], first["result_quality"]),
            first.get("description") if pd.notna(first.get("description")) else None,
            first.get("software_packages"), first["citations"]])
    # specimens that were measured but not interpreted
    for _, r in specimens[specimens["dir_tilt_correction"].isna()].iterrows():
        smp = samples.loc[r["sample"]]
        rows.append([site_location.get(smp["site"]), smp["site"], r["sample"], r["specimen"],
                     num(smp.get("height")), num(smp["azimuth"]),
                     num(smp["dip"]), label(smp["method_codes"], "SO-"),
                     num(smp["bed_dip_direction"]), num(smp["bed_dip"]), None,
                     label(r["method_codes"], "LP-DIR")] + [None] * 13 +
                    ["Excluded", "Measured; no component interpreted", None, r["citations"]])
    return rows


def site_bedding(samples):
    """Site bedding from the samples table; empty where the samples of a site differ."""
    g = samples.groupby("site")[["bed_dip_direction", "bed_dip"]]
    bedding = g.first()
    bedding.loc[(g.nunique() > 1).any(axis=1)] = None
    return bedding


def build_sites(sites, samples, ages):
    """Site rows: the tilt-corrected mean of each site and component, with its geographic
    direction. ages is {site: ages-table row} for the age methods.
    """
    s = sites.copy()
    s["tc"] = s["dir_tilt_correction"].astype(float).astype(int)
    bedding = site_bedding(samples)
    rows = []
    for (site, comp), g in s.groupby(["site", "dir_comp_name"], sort=False):
        g = g.set_index("tc")
        t = g.loc[100]
        age = ages.get(site, {})
        rows.append([
            t["location"], site, t["geologic_classes"], t["geologic_types"], t["lithologies"],
            num(t["lat"]), num(t["lon"]), num(t.get("height")), num(t.get("age")),
            num(t["age_low"]), num(t["age_high"]), t["age_unit"],
            label(age.get("method_codes"), "GM-"),
            num(bedding.loc[site, "bed_dip_direction"]), num(bedding.loc[site, "bed_dip"]),
            comp, int(float(t["dir_n_specimens_lines"])), int(float(t["dir_n_specimens_planes"])),
            round_or_none(g.loc[0, "dir_dec"]), round_or_none(g.loc[0, "dir_inc"]),
            round_or_none(t["dir_dec"]), round_or_none(t["dir_inc"]),
            round_or_none(t["dir_k"], 0), round_or_none(t["dir_alpha95"]),
            round_or_none(t["dir_r"], 3), POLARITY.get(t["dir_polarity"], t["dir_polarity"]),
            round_or_none(t["vgp_lat"]), round_or_none(t["vgp_lon"]),
            round_or_none(t["vgp_dp"]), round_or_none(t["vgp_dm"]),
            "; ".join(CODE_LABELS.get(c, c) for c in t["method_codes"].split(":")
                      if not c.startswith("DA-DIR")),
            t["citations"]])
    return rows


def build_locations(poles):
    """Pole rows from pole dictionaries (MagIC locations columns, plus dDx, dIx and
    flattening_note, which have no MagIC column; methods may be given as readable text).
    """
    rows = []
    for p in poles:
        methods = p.get("methods_text") or \
            "; ".join(CODE_LABELS.get(c, c) for c in p["method_codes"].split(":"))
        sites = p.get("sites_text") or p["sites"].replace(":", ", ")
        rows.append([p["location"], p["result_name"], p["location_type"], p["geologic_classes"],
                     p["lithologies"], p["lat_s"], p["lat_n"], p["lon_w"], p["lon_e"], p["age"],
                     p["age_low"], p["age_high"], p["age_unit"], p["pole_comp_name"],
                     sites, p["pole_n_sites"],
                     COORDINATES.get(p.get("dir_tilt_correction"), "Tilt-corrected"),
                     p["pole_lat"], p["pole_lon"], p["pole_k"], p["pole_alpha95"],
                     p.get("pole_conf"),
                     POLE_POLARITY.get(p.get("dir_polarity"), p.get("dir_polarity")),
                     p.get("paleolat"),
                     p.get("dir_dec"), p.get("dDx"), p.get("dir_inc"), p.get("dIx"),
                     p.get("flattening_note", p.get("pole_flattening")), p.get("pole_flat_low"),
                     p.get("pole_flat_high"),
                     p.get("dir_inc") if p.get("dir_inc_flat_low") is not None else None,
                     p.get("dir_inc_flat_low"),
                     p.get("dir_inc_flat_high"), p.get("reversal_test"),
                     p.get("pole_reversed_perc"), p.get("fold_test"),
                     p.get("conglomerate_test"), p.get("contact_test"), p["plate_blocks"],
                     methods, p["citations"]])
    return rows


def build_ages(ages):
    rows = []
    for _, r in ages.iterrows():
        rows.append([r.get("location"), r.get("site"), num(r.get("age")),
                     num(r.get("age_sigma")), num(r.get("age_low")), num(r.get("age_high")),
                     r["age_unit"], f"{label(r['method_codes'], 'GM-')} ({r['method_codes']})",
                     r.get("timescale_citations"), r.get("description"), r["citations"]])
    return rows


def check_coordinate_systems(rows):
    """Recompute geographic and tilt-corrected directions from the specimen-frame ones.

    Uses the sample azimuth/dip and bedding on the same row (PmagPy dogeo and
    dotilt): the check that reporting all three coordinate systems makes possible.
    Returns the angular misfits (degrees) in geographic and tilt-corrected coordinates.
    """
    position = {(f.group, f.header): k for k, f in enumerate(SPECIMEN_FIELDS)}
    keys = [("Sample orientation", "Azimuth"), ("Sample orientation", "Dip"),
            ("Bedding", "Dip direction"), ("Bedding", "Dip"),
            ("Specimen coordinates", "Dec"), ("Specimen coordinates", "Inc"),
            ("Geographic coordinates", "Dec"), ("Geographic coordinates", "Inc"),
            ("Tilt-corrected coordinates", "Dec"), ("Tilt-corrected coordinates", "Inc")]
    cols = [position[key] for key in keys]
    geo, tilt = [], []
    for row in rows:
        az, dip, bed_dir, bed_dip, sdec, sinc, gdec, ginc, tdec, tinc = [row[c] for c in cols]
        if any(x is None for x in (az, dip, bed_dir, bed_dip, sdec, sinc, gdec, ginc, tdec,
                                   tinc)):
            continue
        d, i = pmag.dogeo(sdec, sinc, az, dip)
        geo.append(angle((d, i), (gdec, ginc)))
        d, i = pmag.dotilt(gdec, ginc, bed_dir, bed_dip)
        tilt.append(angle((d, i), (tdec, tinc)))
    return np.array(geo), np.array(tilt)


# ---------------------------------------------------------------------------
# Excel styling
# ---------------------------------------------------------------------------
GROUP_FILLS = ["DCE6F1", "E2EFDA", "FFF2CC", "FCE4D6", "EDE7F6", "DDEBF7", "E7F4EA", "FDEBD0"]
LEVEL_STYLE = {MAGIC: ("0D6E4A", "DCF1E6"), STANDARD: ("1F4E79", "DDEBF7"),
               STANDARD_IF_APPLICABLE: ("1F4E79", "DDEBF7"),
               RECOMMENDED: ("595959", "F2F2F2"), NO_COLUMN: ("7F6000", "FFF2CC")}
THIN = Side(style="thin", color="BFBFBF")
NOTE_FONT = Font(italic=True, color="595959")


def fill(colour):
    return PatternFill("solid", fgColor=colour)


def write_level(cell, level):
    colour, background = LEVEL_STYLE[level]
    cell.value = level
    cell.font = Font(size=8, bold=True, color=colour)
    cell.fill = fill(background)


def write_header(ws, fields, row, magic_row=True):
    """The header block of a readable sheet, starting at row: field groups (merged and
    coloured), headers, the MagIC column (if magic_row), units and requirement level.
    Returns the first row after the block.
    """
    groups = []
    for i, f in enumerate(fields, start=1):
        if not groups or groups[-1][0] != f.group:
            groups.append([f.group, i, i])
        else:
            groups[-1][2] = i
    for k, (group, c0, c1) in enumerate(groups):
        ws.cell(row, c0, group)
        if c1 > c0:
            ws.merge_cells(start_row=row, start_column=c0, end_row=row, end_column=c1)
        for c in range(c0, c1 + 1):
            ws.cell(row, c).fill = fill(GROUP_FILLS[k % len(GROUP_FILLS)])
            ws.cell(row + 1, c).fill = fill(GROUP_FILLS[k % len(GROUP_FILLS)])
        ws.cell(row, c0).font = Font(bold=True)
        ws.cell(row, c0).alignment = Alignment(horizontal="center")
    rows = ["header", "magic", "unit", "level"] if magic_row else ["header", "unit", "level"]
    for i, f in enumerate(fields, start=1):
        for k, kind in enumerate(rows, start=row + 1):
            cell = ws.cell(k, i)
            if kind == "header":
                cell.value, cell.font = f.header, Font(bold=True)
            elif kind == "magic":
                cell.value = f"{f.table}.{f.column}" if f.column else "—"
                cell.font = Font(name="Consolas", size=9, color="404040")
            elif kind == "unit":
                cell.value = f.unit or None
                cell.font = Font(size=9, italic=True, color="595959")
            else:
                write_level(cell, f.level)
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            cell.border = Border(bottom=THIN)
    ws.row_dimensions[row + len(rows)].height = 24
    return row + len(rows) + 1


def set_widths(ws, fields, rows):
    """Column widths from the headers, units and values; moments in scientific notation."""
    for i, f in enumerate(fields, start=1):
        values = [str(r[i - 1]) for r in rows[:200] if r[i - 1] is not None]
        width = max([len(f.header), min(len(f.unit), 18)] + [len(v) for v in values])
        ws.column_dimensions[get_column_letter(i)].width = min(max(width + 2, 7), 42)


def write_rows(ws, fields, rows, first):
    for r, row in enumerate(rows, start=first):
        assert len(row) == len(fields), (ws.title, len(row), len(fields))
        for c, (value, f) in enumerate(zip(row, fields), start=1):
            cell = ws.cell(r, c, value)
            if f.column == "magn_moment":
                cell.number_format = "0.00E+00"
    return first + len(rows)


def write_readable_sheet(wb, title, fields, rows, note):
    """A readable sheet: a note, the header block (with MagIC columns) and the rows."""
    ws = wb.create_sheet(title)
    ws["A1"] = note
    ws["A1"].font = NOTE_FONT
    first = write_header(ws, fields, 2)
    write_rows(ws, fields, rows, first)
    ws.freeze_panes = ws.cell(first, 5 if len(fields) > 6 else 1)
    set_widths(ws, fields, rows)
    return ws


def write_readme(wb, lines):
    """The README sheet: one line per row; a (text, url) pair is written as a hyperlink."""
    ws = wb.active
    ws.title = "README"
    for line in lines:
        text, url = (line, None) if isinstance(line, str) else line
        ws.append([text])
        if url:
            cell = ws.cell(ws.max_row, 1)
            cell.hyperlink = url
            cell.style = "Hyperlink"
    ws["A1"].font = Font(bold=True, size=14)
    ws.column_dimensions["A"].width = 130
    for row in ws.iter_rows():
        row[0].alignment = Alignment(wrap_text=True, vertical="top")
    return ws


def write_field_dictionary(wb, index=1):
    ws = wb.create_sheet("Field dictionary", index)
    ws.append(["Table (level)", "Group", "Field", "MagIC column", "Units / convention",
               "Requirement", "Note"])
    for c in range(1, 8):
        ws.cell(1, c).font = Font(bold=True)
        ws.cell(1, c).fill = fill("DCE6F1")
    for sheet, fields in SHEETS.items():
        for f in fields:
            ws.append([sheet, f.group, f.header, f"{f.table}.{f.column}" if f.column else "—",
                       f.unit, f.level, f.note])
            colour, background = LEVEL_STYLE[f.level]
            ws.cell(ws.max_row, 6).font = Font(bold=True, color=colour)
            ws.cell(ws.max_row, 6).fill = fill(background)
    for col, width in zip("ABCDEFG", (22, 24, 22, 32, 26, 24, 50)):
        ws.column_dimensions[col].width = width
    ws.freeze_panes = "A2"


def write_method_codes(wb, used):
    defs = method_code_definitions()
    ws = wb.create_sheet("Method codes")
    ws.append(["Code", "Readable label used in the tables", "MagIC definition"])
    for c in range(1, 4):
        ws.cell(1, c).font = Font(bold=True)
        ws.cell(1, c).fill = fill("DCE6F1")
    for code in sorted(used):
        ws.append([code, CODE_LABELS.get(code, ""), defs.get(code, "")])
    ws.column_dimensions["A"].width = 16
    ws.column_dimensions["B"].width = 36
    ws.column_dimensions["C"].width = 90


def write_magic_sheet(wb, title, df):
    ws = wb.create_sheet(title)
    df = df.dropna(axis=1, how="all")
    ws.append(["tab delimited", title.replace("MagIC ", "")])
    ws.append(list(df.columns))
    for c in range(1, len(df.columns) + 1):
        ws.cell(2, c).font = Font(name="Consolas", bold=True, size=9)
        ws.cell(2, c).fill = fill("DCE6F1")
    for row in df.itertuples(index=False):
        ws.append([None if (isinstance(v, float) and np.isnan(v)) else v for v in row])
    ws.freeze_panes = "B3"
    for i, col in enumerate(df.columns, start=1):
        ws.column_dimensions[get_column_letter(i)].width = min(max(len(col) + 2, 9), 40)
