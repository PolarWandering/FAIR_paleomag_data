"""Workflow figure of the FAIR standard paper: the levels of a paleomagnetic
dataset, as they are archived in MagIC and in a Paleomagnetism.org collection.

Each row follows one published dataset up the levels of the standard, from the
measurements of one specimen to the pole:
    column 1  the measurements of a specimen (vector component diagram in
              geographic coordinates, north up) with its fits;
    column 2  one fit in specimen, geographic and tilt-corrected coordinates;
    column 3  the fit directions of the site or locality of that specimen;
    column 4  the VGPs and the pole.
Under each panel is the part of the archive that holds that level, with the
calculation that leads from one level to the next between them.

Top row: the Shaat dikes pole of Swanson-Hysell et al. (2025, Geology 53,
909-913, doi:10.1130/G53450.1), read from MagIC contribution 20884
(doi:10.7288/V4/MAGIC/20884). Every value plotted is read from the archive: the
fits and the site means are those of the specimens and sites tables, and the
pole is that of the locations table.

Bottom row: the Sugar Mill limestone (locality CA7) of Sauerbier et al. (2026,
Tectonics 45, e2025TC009223, doi:10.1029/2025TC009223), read from the published
Paleomagnetism.org collection file CA_sugarmill.col (figshare,
doi:10.6084/m9.figshare.28815698). The collection file holds the demagnetization
steps, the orientations and the interpretations. It holds no means, so the VGPs
and the pole are calculated here following section 3.2 of the paper: one VGP
per ChRM direction (one sample per bed, so that each specimen is its own sample
and site) and the Fisher mean of the VGPs after a 45° cutoff.

The paleomagnetic plots and calculations are made with PmagPy: the vector
component diagrams with their fits (pmagplotlib.plot_zij), the equal-area plots
(ipmag.plot_net, plot_di, plot_di_mean), the maps (ipmag.make_orthographic_map,
plot_vgp, plot_pole), the reading of the MagIC contribution
(ipmag.unpack_magic, contribution_builder.Contribution), the rotations to
geographic coordinates (pmag.dogeo, dogeo_V) and the VGPs and their mean
(ipmag.vgp_calc, do_flip, fisher_mean, pmag.angle). What is added here with
matplotlib is the text written on and under the panels, the arrows between the
coordinate systems of column 2, and the boxes and arrows of the archive strips.

Inputs (../../data/):
    magic_20884/magic_contribution_20884.txt
    sauerbier2026_figshare/CA_sugarmill.col

Outputs: workflow_archiving.pdf and workflow_archiving.png, next to this script.

Usage:
    python make_workflow_figure.py

Requires numpy, pandas, matplotlib, cartopy and pmagpy. The plotting options
used here (the ax, frame, axis_labels, step_labels, step_colors, line_color and
fits arguments of pmagplotlib.plot_zij, the ax argument of ipmag.plot_di and
ipmag.plot_di_mean, and the fig and subplot arguments of
ipmag.make_orthographic_map) need a PmagPy release later than 4.5.2.
"""

import contextlib
import io
import json
import tempfile
from pathlib import Path

import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import ConnectionPatch, FancyBboxPatch
from pmagpy import contribution_builder as cb
from pmagpy import ipmag, pmag, pmagplotlib

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE.parents[1] / "data"
MAGIC_FILE = DATA_DIR / "magic_20884" / "magic_contribution_20884.txt"
COL_FILE = DATA_DIR / "sauerbier2026_figshare" / "CA_sugarmill.col"

# Specimens shown in columns 1 and 2. SD68-6: the magnetite component is about
# half of the NRM, and its site has four magnetite and five low-temperature
# fits. CA7-5A: alternating-field demagnetization, with an anchored ChRM fit
# from 15 to 150 mT.
MAGIC_SPECIMEN = "SD68-6"
COL_SPECIMEN = "CA7-5A"
# Steps labelled on the vector component diagrams, by treatment: the first step,
# the bounds of the characteristic fit and one step within each fit. For each,
# the projection that carries the label ("h" horizontal, "v" vertical), the
# offset of the label from the point (points) and its horizontal alignment.
MAGIC_STEP_LABELS = {273: ("h", (4, 0), "left"), 473: ("v", (5, 0), "left"),      # treat_temp (K)
                     613: ("h", (4, 4), "left"), 713: ("v", (5, 0), "left"),
                     833: ("h", (-4, 6), "right")}
COL_STEP_LABELS = {0: ("h", (4, 0), "left"), 15: ("h", (4, 4), "left"),           # step (mT)
                   50: ("h", (5, 0), "left"), 150: ("h", (-4, 6), "right")}
VGP_CUTOFF = 45.0   # degrees (Sauerbier et al., 2026, section 3.2)

# Colours: the overprint, the characteristic component (and the VGPs calculated
# from it), the study location, and text and neutrals
OVERPRINT_COLOR, CHRM_COLOR, LOCATION_COLOR = "#eb6834", "#2a78d6", "#1baf7a"
INK, INK2, MUTED, RULE, FILL = "#0b0b0b", "#52514e", "#8a8984", "#d9d8d4", "#f1f0ed"
# translucent white behind the text on the nets and maps, so that ticks and
# points stay visible
LABEL_BOX = dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.85)

COLUMN_HEADERS = ["Measurements", "Specimen fit", "Site means", "Pole"]
MAGIC_BOXES = [("MagIC measurements", "treat_temp\nmagn_moment\ndir_dec, dir_inc\nquality"),
               ("MagIC specimens, samples", "meas_step_min/max\ndir_n_measurements\n"
                                            "method_codes\nazimuth, dip, bed_dip"),
               ("MagIC sites", "specimens\ndir_dec, dir_inc\ndir_k, dir_alpha95\n"
                               "vgp_lat, vgp_lon"),
               ("MagIC locations", "sites\npole_lat, pole_lon\npole_k, pole_alpha95\n"
                                   "pole_n_sites")]
MAGIC_ARROWS = ["fit", "average", "average"]
COL_BOXES = [(".col steps", "step (°C or mT)\nx, y, z (µA/m)\nerror\nvisible, selected"),
             (".col specimens", "coreAzimuth, coreDip\nbeddingStrike, beddingDip\n"
                                "interpretations: steps,\ntype, anchored, MAD"),
             ("Statistics module", "VGP per interpretation\nFisher mean of VGPs\n"
                                   "cutoff (here 45°)\nnot in the .col file"),
             ("Paper, Table 1", "D ± ΔDx, I ± ΔIx\nK, A95, N\nfield tests\n"
                                "not in the .col file")]
COL_ARROWS = ["fit", "average", "report"]

# Layout, in inches. Each row is a band of four panels above a band of four
# archive boxes; the captions of the panels hang below them.
FIG_WIDTH = 7.1
LEFT, RIGHT, COLUMN_SPACE = 0.1, 0.1, 0.22     # COLUMN_SPACE as a fraction of a column
TOP = 0.32             # column headers
PANEL = 1.5            # height of the panels
CAPTIONS = 0.3         # captions under the panels (three lines of text need 0.29)
STRIP = 0.62           # height of the archive boxes
ROW_GAP = 0.3          # from the boxes of one row to the panels of the next
FIG_HEIGHT = TOP + 2 * (PANEL + CAPTIONS + STRIP) + ROW_GAP + 0.05

# PmagPy draws its plots for full-size figures; scale lines, markers and text
# to the size of these panels
plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 5.5, "text.color": INK, "lines.linewidth": 0.7, "lines.markersize": 3,
    "legend.frameon": False, "pdf.fonttype": 42})


# ---------------------------------------------------------------------------
# Reading the archives
# ---------------------------------------------------------------------------
def read_magic_contribution(path):
    """Read the tables of a MagIC contribution file with PmagPy.

    Args:
        path (Path): a contribution file, as downloaded from MagIC.

    Returns:
        dict: a pandas DataFrame for each table of the contribution, by table name.
    """
    log = io.StringIO()   # PmagPy reports each table that it writes
    with tempfile.TemporaryDirectory() as table_dir:
        with contextlib.redirect_stdout(log):
            unpacked = ipmag.unpack_magic(path.name, dir_path=table_dir,
                                          input_dir_path=str(path.parent), print_progress=False)
            contribution = cb.Contribution(table_dir)
    if not unpacked:
        raise RuntimeError(f"PmagPy could not unpack {path}:\n{log.getvalue()}")
    return {name: table.df for name, table in contribution.tables.items()}


def col_direction(vector):
    """Declination and inclination of a Cartesian vector of a .col file."""
    dec, inc, _ = pmag.cart2dir([vector["x"], vector["y"], vector["z"]])
    return float(dec), float(inc)


def midpoint(lon_1, lat_1, lon_2, lat_2):
    """Longitude and latitude midway between two points, to centre a globe on both."""
    mean = ipmag.fisher_mean(dec=[lon_1, lon_2], inc=[lat_1, lat_2])
    return mean["dec"], mean["inc"]


def zijderveld_panel(specimen_name, datablock, fits, labelled_steps, unit, margin=0.1):
    """Collect what a vector component diagram shows.

    Args:
        specimen_name (str): the specimen.
        datablock (list): [treatment, dec, inc, moment, quality] of each step, in
            geographic coordinates.
        fits (list): the fits, as dictionaries with the keys of pmag.domean
            (specimen_dec, specimen_inc, measurement_step_min,
            measurement_step_max, calculation_type), a color, the name of the
            component and where that name is written (name_at): ("steps", (a, b))
            beside the vertical projection, midway between the steps with
            treatments a and b; ("axis", offset) right-aligned below the right
            end of the horizontal axis, offset in points; or ("axes", (x, y))
            right-aligned at an axes fraction.
        labelled_steps (dict): the steps to label, by treatment, each with the
            projection ("h" or "v"), offset and alignment of its label.
        unit (str): "°C" for treatments in kelvin, or "mT".
        margin (float): space left around the data, as a fraction of their range.

    Returns:
        dict: the arguments of plot_zijderveld.
    """
    treatments = [step[0] for step in datablock]
    step_colors = [MUTED] * len(datablock)
    for fit in fits:
        first = treatments.index(fit["measurement_step_min"])
        last = treatments.index(fit["measurement_step_max"])
        step_colors[first:last + 1] = [fit["color"]] * (last - first + 1)
    step_labels = []
    for index, treatment in enumerate(treatments):
        if treatment in labelled_steps:
            text = ("NRM" if index == 0 else
                    f"{treatment - 273:.0f}°C" if unit == "°C" else f"{treatment:g} mT")
            step_labels.append((index, text, *labelled_steps[treatment]))
    return dict(specimen=specimen_name, datablock=datablock, fits=fits, step_colors=step_colors,
                step_labels=step_labels, margin=margin)


# ---------------------------------------------------------------------------
# Top row: a MagIC contribution
# ---------------------------------------------------------------------------
def magic_row(tables, specimen_name=MAGIC_SPECIMEN):
    """Collect what the four panels of the MagIC row show, read from the archive.

    Args:
        tables (dict): the tables of the contribution (read_magic_contribution).
        specimen_name (str): the specimen of columns 1 and 2.

    Returns:
        dict: the content of the panels and of the archive strip of the row.
    """
    measurements, specimens, samples, sites, locations = (
        tables[name] for name in ("measurements", "specimens", "samples", "sites", "locations"))
    fits = specimens[(specimens["specimen"] == specimen_name) & specimens["dir_comp"].notna()]
    sample = samples.loc[fits["sample"].iloc[0]]
    site_name = sample["site"]

    # column 1: the steps, rotated to geographic coordinates with the sample
    # orientation, and the fits of the specimens table in geographic coordinates
    steps = measurements[(measurements["specimen"] == specimen_name) &
                         (measurements["quality"] == "g")].sort_values("sequence")
    dec_geo, inc_geo = pmag.dogeo_V(np.column_stack([
        steps["dir_dec"], steps["dir_inc"], np.full(len(steps), sample["azimuth"]),
        np.full(len(steps), sample["dip"])]).astype(float))
    datablock = [[treatment, dec, inc, moment, "g"] for treatment, dec, inc, moment in
                 zip(steps["treat_temp"], dec_geo, inc_geo, steps["magn_moment"])]
    zijderveld_fits = []
    # each component is named beside its vertical projection: low-temp between
    # the labels of 200°C and 440°C, magnetite between 440°C and 560°C
    for component, name, name_at, color in (
            ("lt", "low-temp (lt)", ("steps", (473, 713)), OVERPRINT_COLOR),
            ("mag", "magnetite\n(mag)", ("steps", (713, 833)), CHRM_COLOR)):
        fit = fits[(fits["dir_comp"] == component) & (fits["dir_tilt_correction"] == 0)].iloc[0]
        calculation_type = next(code for code in fit["method_codes"].split(":")
                                if code.startswith("DE-"))
        zijderveld_fits.append(dict(
            specimen_dec=fit["dir_dec"], specimen_inc=fit["dir_inc"],
            measurement_step_min=fit["meas_step_min"], measurement_step_max=fit["meas_step_max"],
            calculation_type=calculation_type, color=color, name=name, name_at=name_at))

    # column 2: the magnetite fit in the three coordinate systems of the specimens
    # table. Geographic and tilt-corrected are close: they are labelled on opposite sides.
    magnetite_fit = fits[fits["dir_comp"] == "mag"].set_index("dir_tilt_correction")
    coordinates = [(label, color, magnetite_fit.loc[code, "dir_dec"],
                    magnetite_fit.loc[code, "dir_inc"], placement)
                   for code, label, color, placement in (
                       (-1, "specimen", MUTED, ((0, -9), "center", "top")),
                       (0, "geographic", INK2, ((3, -7), "left", "top")),
                       (100, "tilt-corrected", CHRM_COLOR, ((6, 8), "right", "bottom")))]

    # column 3: the tilt-corrected fits of the site and their archived means
    groups = []
    for component, color, offset, ha in (("lt", OVERPRINT_COLOR, (-3, -4), "right"),
                                         ("mag", CHRM_COLOR, (2, -9), "center")):
        mean = sites[(sites["site"] == site_name) & (sites["dir_comp_name"] == component) &
                     (sites["dir_tilt_correction"] == 100)].iloc[0]
        members = specimens[specimens["specimen"].isin(mean["specimens"].split(":")) &
                            (specimens["dir_comp"] == component) &
                            (specimens["dir_tilt_correction"] == 100)]
        groups.append(dict(
            color=color, decs=members["dir_dec"].tolist(), incs=members["dir_inc"].tolist(),
            mean=(mean["dir_dec"], mean["dir_inc"], mean["dir_alpha95"]),
            text=f"{component}: {mean['dir_dec']:05.1f}/{mean['dir_inc']:.1f}\n"
                 f"α95 {mean['dir_alpha95']:.1f}°, k = {mean['dir_k']:.0f}\nn = {len(members)}",
            offset=offset, ha=ha))

    # column 4: the archived pole and the VGPs of its sites, reversed ones inverted
    location = locations[locations["pole_lat"].notna()].iloc[0]
    pole_sites = sites[sites["site"].isin(location["sites"].split(":")) &
                       (sites["dir_comp_name"] == "mag") & (sites["dir_tilt_correction"] == 100)]
    vgp_lon = pole_sites["vgp_lon"].to_numpy(dtype=float, copy=True)
    vgp_lat = pole_sites["vgp_lat"].to_numpy(dtype=float, copy=True)
    is_reversed = (pole_sites["dir_polarity"] == "r").to_numpy()
    vgp_lon[is_reversed], vgp_lat[is_reversed] = ipmag.do_flip(
        vgp_lon[is_reversed].tolist(), vgp_lat[is_reversed].tolist())
    pole_lon, pole_lat, a95 = (location[c] for c in ("pole_lon", "pole_lat", "pole_alpha95"))
    # study location: the centre of the archived sampling area of the pole
    study_lon = (location["lon_w"] + location["lon_e"]) / 2
    study_lat = (location["lat_s"] + location["lat_n"]) / 2

    return dict(
        zijderveld=zijderveld_panel(specimen_name, datablock, zijderveld_fits,
                                    MAGIC_STEP_LABELS, "°C", margin=0.05),
        coordinates=dict(points=coordinates, caption=f"specimen {specimen_name}, magnetite fit",
                         code="samples.azimuth, dip → geographic\n"
                              "bed_dip_direction, bed_dip → tilt"),
        directions=dict(groups=groups, caption=f"site {site_name}, tilt-corrected",
                        code="sites.specimens: fits averaged"),
        pole=dict(vgp_lon=vgp_lon, vgp_lat=vgp_lat, pole_lon=pole_lon, pole_lat=pole_lat,
                  a95=a95, study_lon=study_lon, study_lat=study_lat,
                  caption=f"pole {pole_lon:.1f}°E, {pole_lat:.1f}°N, A95 {a95:.1f}°\n"
                          f"N = {len(pole_sites)} site VGPs ({is_reversed.sum()} reversed, "
                          "inverted)",
                  code="locations.sites: sites averaged"),
        boxes=MAGIC_BOXES, arrows=MAGIC_ARROWS)


# ---------------------------------------------------------------------------
# Bottom row: a Paleomagnetism.org collection
# ---------------------------------------------------------------------------
def vgp_mean_with_cutoff(vgps, cutoff=VGP_CUTOFF):
    """Fisher mean of VGPs after an iterative cutoff.

    The VGP farthest from the mean is removed and the mean recalculated, until
    all of the VGPs are within the cutoff angle of the mean.

    Args:
        vgps (DataFrame): VGPs, with columns vgp_lon and vgp_lat.
        cutoff (float): the cutoff angle, in degrees.

    Returns:
        tuple: the VGPs kept, and their Fisher mean as returned by
        ipmag.fisher_mean (dec is the pole longitude, inc the pole latitude).
    """
    while True:
        mean = ipmag.fisher_mean(dec=vgps["vgp_lon"].tolist(), inc=vgps["vgp_lat"].tolist())
        distance = pmag.angle(vgps[["vgp_lon", "vgp_lat"]].to_numpy(), [mean["dec"], mean["inc"]])
        if distance.max() <= cutoff:
            return vgps, mean
        vgps = vgps.drop(vgps.index[distance.argmax()])


def col_row(collection, specimen_name=COL_SPECIMEN):
    """Collect what the four panels of the Paleomagnetism.org row show.

    Args:
        collection (dict): the content of a .col file.
        specimen_name (str): the specimen of columns 1 and 2.

    Returns:
        dict: the content of the panels and of the archive strip of the row.
    """
    specimen = next(s for s in collection["specimens"] if s["name"] == specimen_name)
    interpretation = specimen["interpretations"][0]

    # column 1: the steps, rotated to geographic coordinates. coreDip is the dip
    # of the core from the vertical; pmag.dogeo takes the plunge of the X axis.
    datablock = []
    for step in specimen["steps"]:
        dec, inc, moment = pmag.cart2dir([step["x"], step["y"], step["z"]])
        dec_geo, inc_geo = pmag.dogeo(dec, inc, specimen["coreAzimuth"], specimen["coreDip"] - 90)
        datablock.append([float(step["step"]), dec_geo, inc_geo, moment, "g"])
    fit_dec, fit_inc = col_direction(interpretation["geographic"]["coordinates"])
    anchored = interpretation["anchored"]
    zijderveld_fits = [dict(
        specimen_dec=fit_dec, specimen_inc=fit_inc,
        measurement_step_min=float(interpretation["steps"][0]),
        measurement_step_max=float(interpretation["steps"][-1]),
        calculation_type="DE-BFL-A" if anchored else "DE-BFL", color=CHRM_COLOR,
        name="ChRM (anchored)" if anchored else "ChRM", name_at=("axes", (1, 0.45)))]
    unit = "mT" if specimen["demagnetizationType"] == "alternating" else "°C"

    # column 2: the fit in the three coordinate systems of the interpretation
    coordinates = [(label, color, *col_direction(interpretation[frame]["coordinates"]), placement)
                   for frame, label, color, placement in (
                       ("specimen", "specimen", MUTED, ((0, -9), "center", "top")),
                       ("geographic", "geographic", INK2, ((8, 7), "left", "top")),
                       ("tectonic", "tectonic", CHRM_COLOR, ((-8, -3), "right", "top")))]

    # column 3: the ChRM directions (principal component fits) of the locality
    rows = []
    for s in collection["specimens"]:
        for fit in s["interpretations"]:
            if fit["type"] == "TAU1":
                dec_tc, inc_tc = col_direction(fit["tectonic"]["coordinates"])
                rows.append(dict(specimen=s["name"], site_lat=s["latitude"],
                                 site_lon=s["longitude"], dec_tc=dec_tc, inc_tc=inc_tc))
    chrms = pd.DataFrame(rows)
    locality = specimen_name.split("-")[0]

    # column 4: one VGP per ChRM direction, in the northern hemisphere, and their mean
    vgps = ipmag.vgp_calc(chrms)
    southern = vgps["vgp_lat"] < 0
    vgps.loc[southern, "vgp_lat"] = vgps.loc[southern, "vgp_lat_rev"]
    vgps.loc[southern, "vgp_lon"] = vgps.loc[southern, "vgp_lon_rev"]
    kept, mean = vgp_mean_with_cutoff(vgps)
    pole_lon, pole_lat, a95 = mean["dec"], mean["inc"], mean["alpha95"]

    return dict(
        zijderveld=zijderveld_panel(specimen_name, datablock, zijderveld_fits,
                                    COL_STEP_LABELS, unit),
        coordinates=dict(points=coordinates, caption=f"specimen {specimen_name}, ChRM fit",
                         code="coreAzimuth, coreDip → geographic\n"
                              "beddingStrike, beddingDip → tectonic"),
        # one sample per bed: no mean direction; the mean is taken of the VGPs
        directions=dict(groups=[dict(color=CHRM_COLOR, decs=chrms["dec_tc"].tolist(),
                                     incs=chrms["inc_tc"].tolist(), mean=None)],
                        note=f"{len(chrms)} ChRMs, each treated as\nspecimen = sample = site",
                        caption=f"locality {locality}, tectonic coordinates",
                        code="interpretations[].tectonic"),
        pole=dict(vgp_lon=kept["vgp_lon"].to_numpy(), vgp_lat=kept["vgp_lat"].to_numpy(),
                  pole_lon=pole_lon, pole_lat=pole_lat, a95=a95,
                  study_lon=chrms["site_lon"].mean(), study_lat=chrms["site_lat"].mean(),
                  caption=f"pole {pole_lon:.1f}°E, {pole_lat:.1f}°N, A95 {a95:.1f}°\n"
                          f"N = {len(kept)} VGPs",
                  code="computed; not in the .col file"),
        boxes=COL_BOXES, arrows=COL_ARROWS)


# ---------------------------------------------------------------------------
# Drawing
# ---------------------------------------------------------------------------
def caption_below(ax, caption, code=None):
    """Write a caption, and the archive fields involved, centred under a panel.

    Args:
        ax: the axis of the panel.
        caption (str): the caption.
        code (str): names of archive fields, written below the caption in monospace.
    """
    below = dict(xy=(0.5, 0), xytext=(0, -3), textcoords="offset points", ha="center",
                 va="top", color=INK2, annotation_clip=False)
    text = ax.annotate(caption, xycoords="axes fraction", **below)
    if code:
        ax.annotate(code, xycoords=text, family="monospace", fontsize=4.9, **below)


def plot_zijderveld(ax, panel):
    """Vector component diagram of a specimen, north up, with its fits (PmagPy).

    With the diagram rotated by 90°, PmagPy plots east to the right, and north
    (horizontal projection, solid circles) and up (vertical projection, open
    squares) to the top. Each fit is an arrow along its archived direction,
    from its last step toward its first.
    """
    datablock = panel["datablock"]
    pmagplotlib.plot_zij(None, datablock, 90, panel["specimen"], ax=ax, frame=False,
                         axis_labels={"right": "E", "top": "N, Up"}, step_labels=False,
                         step_colors=panel["step_colors"], line_color=RULE, fits=panel["fits"])
    ax.set_title("")
    for axis_label in ax.texts:
        axis_label.set(color=INK2, fontsize=6.5)
    # PmagPy gives both axes the same range; fit the frame to the data instead
    ax.set_aspect("equal", adjustable="datalim")
    ax.margins(panel["margin"])
    ax.autoscale()
    # labels of selected steps, at the points that PmagPy plots: east, and south
    # (horizontal projection) or down (vertical projection), normalized to the NRM
    east, south, down = (pmag.dir2cart([[step[1] - 90, step[2], step[3]] for step in datablock])
                         / datablock[0][3]).T
    for index, text, projection, offset, ha in panel["step_labels"]:
        ax.annotate(text, (east[index], south[index] if projection == "h" else down[index]),
                    xytext=offset, textcoords="offset points", ha=ha, va="center",
                    fontsize=5.3, color=INK2)
    # the names of the components, in their colours
    treatments = [step[0] for step in datablock]
    for fit in panel["fits"]:
        place, where = fit["name_at"]
        name = dict(color=fit["color"], fontsize=5.8, fontweight="bold",
                    textcoords="offset points")
        if place == "steps":
            first, second = (treatments.index(treatment) for treatment in where)
            ax.annotate(fit["name"], (max(east[first], east[second]),
                                      (down[first] + down[second]) / 2),
                        xytext=(5, 0), ha="left", va="center", **name)
        elif place == "axis":
            ax.annotate(fit["name"], (1, 0), xycoords=("axes fraction", "data"),
                        xytext=(0, where), ha="right", va="top", **name)
        else:
            ax.annotate(fit["name"], where, xycoords="axes fraction", xytext=(0, -3),
                        ha="right", va="top", **name)
    ax.text(0, -0.03, f"{panel['specimen']}, geographic\n● horizontal  □ vertical",
            transform=ax.transAxes, va="top", color=INK2)


def plot_net(ax):
    """Equal-area net (PmagPy) with north labelled."""
    ipmag.plot_net(ax=ax)
    ax.text(0, 1.04, "N", ha="center", va="bottom", fontsize=6.5, color=INK2)


def plot_coordinates(ax, panel):
    """One fit in three coordinate systems (PmagPy), with the rotations between them."""
    plot_net(ax)
    positions = []
    for label, color, dec, inc, (offset, ha, va) in panel["points"]:
        ipmag.plot_di(dec, inc, color=color, markersize=22, alpha=0.8, zorder=3, ax=ax)
        positions.append(pmag.dimap(dec, inc))
        ax.annotate(f"{label}\ncoordinates\n{dec:05.1f}/{inc:.1f}", positions[-1], xytext=offset,
                    textcoords="offset points", ha=ha, va=va, bbox=LABEL_BOX, zorder=7,
                    color=INK2 if color == MUTED else color)
    for start, end in zip(positions[:-1], positions[1:]):
        ax.annotate("", end, xytext=start, zorder=2, arrowprops=dict(
            arrowstyle="-|>", mutation_scale=6, color=INK2, lw=0.7, shrinkA=4, shrinkB=4,
            connectionstyle="arc3,rad=-0.3"))
    caption_below(ax, panel["caption"], panel["code"])


def plot_directions(ax, panel):
    """Fit directions and their Fisher means with α95 (PmagPy).

    A group without a mean shows its directions only.
    """
    plot_net(ax)
    for group in panel["groups"]:
        ipmag.plot_di(group["decs"], group["incs"], color=group["color"], markersize=7,
                      alpha=0.7, zorder=5, ax=ax)
        if group["mean"] is None:
            continue
        dec, inc, a95 = group["mean"]
        ipmag.plot_di_mean(dec, inc, a95, color=group["color"], marker="o", markersize=14,
                           zorder=6, ax=ax)
        ax.collections[-1].set_alpha(0.45)   # the directions show through the mean
        ax.annotate(group["text"], pmag.dimap(dec, inc), xytext=group["offset"],
                    textcoords="offset points", ha=group["ha"], va="top", color=group["color"],
                    bbox=LABEL_BOX, zorder=7)
    if panel.get("note"):
        ax.text(0, -0.35, panel["note"], ha="center", va="center", color=INK2, bbox=LABEL_BOX,
                zorder=7)
    caption_below(ax, panel["caption"], panel["code"])


def plot_pole(fig, subplot, panel):
    """VGPs, their mean pole with A95 and the study location on a globe (PmagPy)."""
    centre_lon, centre_lat = midpoint(panel["pole_lon"], panel["pole_lat"],
                                      panel["study_lon"], panel["study_lat"])
    # the coastlines and the grid of ipmag.make_orthographic_map are drawn for a
    # full-size map: thin the coastlines, and draw the same grid with thinner lines
    with plt.rc_context({"patch.linewidth": 0.3}):
        map_axis = ipmag.make_orthographic_map(centre_lon, centre_lat, fig=fig, subplot=subplot,
                                               land_color=FILL, land_edge_color=MUTED,
                                               grid_lines=False)
    map_axis.gridlines(xlocs=np.arange(-180, 181, 30), ylocs=[-80, -60, -30, 0, 30, 60, 80],
                       linewidth=0.4, color=RULE, linestyle="dotted")
    ipmag.plot_vgp(map_axis, vgp_lon=panel["vgp_lon"], vgp_lat=panel["vgp_lat"],
                   color=CHRM_COLOR, edge=None, markersize=6, alpha=0.55)
    # the mean translucent, so that the VGPs show through it
    ipmag.plot_pole(map_axis, panel["pole_lon"], panel["pole_lat"], panel["a95"], color=INK,
                    edgecolor=INK, marker="s", markersize=5, mean_alpha=0.6, zorder=150)
    ipmag.plot_vgp(map_axis, vgp_lon=[panel["study_lon"]], vgp_lat=[panel["study_lat"]],
                   color=LOCATION_COLOR, edge=None, marker="*", markersize=60, zorder=160)
    map_axis.annotate("study\nlocation", (panel["study_lon"], panel["study_lat"]),
                      xycoords=ccrs.PlateCarree()._as_mpl_transform(map_axis), xytext=(0, -8),
                      textcoords="offset points", ha="center", va="top", color=INK2,
                      bbox=LABEL_BOX, zorder=170)
    map_axis.spines["geo"].set_linewidth(0.7)   # the outline weight of the nets
    caption_below(map_axis, panel["caption"], panel["code"])
    return map_axis


def draw_archive_strip(fig, axes, boxes, arrows):
    """Where each level is archived, under its panel, and the steps between the levels.

    Args:
        fig: the figure.
        axes (list): one axis per column, under the panels.
        boxes (list): (title, fields) of the box of each column.
        arrows (list): the label of the arrow from each box to the next.
    """
    width, height = axes[0].get_position().size * fig.get_size_inches()
    for ax, (title, fields) in zip(axes, boxes):
        ax.axis("off")
        ax.add_patch(FancyBboxPatch((0.1, 0.02), 0.8, 0.96, transform=ax.transAxes,
                                    boxstyle="round,pad=0,rounding_size=0.05",
                                    mutation_aspect=width / height, facecolor=FILL,
                                    edgecolor=RULE, lw=0.6, clip_on=False))
        ax.text(0.5, 0.92, title, transform=ax.transAxes, ha="center", va="top", fontsize=6.3,
                fontweight="bold")
        ax.text(0.5, 0.72, fields, transform=ax.transAxes, ha="center", va="top", fontsize=5.2,
                family="monospace", color=INK2, linespacing=1.25)
    for left, right, label in zip(axes[:-1], axes[1:], arrows):
        fig.add_artist(ConnectionPatch((0.93, 0.45), (0.07, 0.45), coordsA=left.transAxes,
                                       coordsB=right.transAxes, arrowstyle="-|>",
                                       mutation_scale=7, color=CHRM_COLOR, lw=0.8))
        box = left.get_position()
        fig.text((box.x1 + right.get_position().x0) / 2, box.y0 + 0.52 * box.height, label,
                 ha="center", va="bottom", fontsize=6.5, color=CHRM_COLOR)


def draw_row(fig, row, top, headers=None):
    """Draw the four panels of a dataset and its archive strip.

    Args:
        fig: the figure.
        row (dict): the content of the row (magic_row or col_row).
        top (float): distance of the top of the panels from the top of the figure (in).
        headers (list): column headers to write above the row.
    """
    def band(band_top, band_height):
        return fig.add_gridspec(1, 4, left=LEFT / FIG_WIDTH, right=1 - RIGHT / FIG_WIDTH,
                                top=1 - band_top / FIG_HEIGHT,
                                bottom=1 - (band_top + band_height) / FIG_HEIGHT,
                                wspace=COLUMN_SPACE)
    panels = band(top, PANEL)
    strip = band(top + PANEL + CAPTIONS, STRIP)

    plot_zijderveld(fig.add_subplot(panels[0, 0]), row["zijderveld"])
    plot_coordinates(fig.add_subplot(panels[0, 1]), row["coordinates"])
    plot_directions(fig.add_subplot(panels[0, 2]), row["directions"])
    plot_pole(fig, panels[0, 3], row["pole"])
    draw_archive_strip(fig, [fig.add_subplot(strip[0, column]) for column in range(4)],
                       row["boxes"], row["arrows"])
    for column, header in enumerate(headers or []):
        cell = panels[0, column].get_position(fig)
        fig.text(cell.x0 + cell.width / 2, 1 - (top - 0.2) / FIG_HEIGHT, header, fontsize=7.5,
                 fontweight="bold", ha="center", va="bottom")


def main():
    magic = magic_row(read_magic_contribution(MAGIC_FILE))
    col = col_row(json.loads(COL_FILE.read_text()))

    fig = plt.figure(figsize=(FIG_WIDTH, FIG_HEIGHT))
    draw_row(fig, magic, TOP, headers=COLUMN_HEADERS)
    draw_row(fig, col, TOP + PANEL + CAPTIONS + STRIP + ROW_GAP)
    for extension in ("pdf", "png"):
        out = HERE / f"workflow_archiving.{extension}"
        fig.savefig(out, dpi=600, bbox_inches="tight", pad_inches=0.03)
        print("wrote", out)


if __name__ == "__main__":
    main()
