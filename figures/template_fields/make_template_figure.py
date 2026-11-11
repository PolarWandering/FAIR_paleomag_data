"""Template figure of the FAIR standard paper: the fields of the template and
how each is required.

Each panel is one sheet of the template workbook (1 measurements, 2 specimen
directions, 3 site means, 4 poles, 5 ages); each chip is one field, coloured by
its requirement level, with its MagIC column. Columns are in the panel's MagIC
table(s) unless prefixed with another table. Sheet 2 holds both sample and
specimen fields and is shown as one panel, as in the workbook. Citations,
required by MagIC in every table, are shown only in the ages panel, where they
give the source of each age constraint. Panel 1 shows the laboratory data files
in two sections: the metadata supplied with the files and the measurement
fields that the conversion must yield.

The fields are those of fair_template/definition.py, at the top of the repository,
which also defines the full Shaat dikes example (tables/shaat_dikes_example/).

The page is written as HTML and printed to PDF with headless Chrome or
Chromium, then cropped to its content; the PNG is rendered from the PDF with
pdftoppm (poppler). The Source Sans 3 and Source Code Pro fonts are loaded from
Google Fonts, so rendering needs a network connection unless they are installed
locally.

Outputs: template_fields.pdf and template_fields.png, next to this script.

Usage:
    python make_template_figure.py

Requires numpy, pillow, poppler (pdftoppm) and Google Chrome or Chromium.
"""

import html
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parents[1]))
from fair_template.definition import (LAB_FILE_FIELDS, MAGIC, RECOMMENDED, SHEETS,  # noqa: E402
                                 STANDARD, STANDARD_IF_APPLICABLE)

OUTPUT_DIR = SCRIPT_DIR
CHROME_CANDIDATES = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                     "google-chrome-stable", "google-chrome", "chromium", "chromium-browser"]
PAGE_WIDTH_MM = 180
PNG_DPI = 600
FONTS_CSS = ("https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700"
             "&family=Source+Code+Pro:wght@400;500&display=block")

# panels: id -> (sheet, title, subtitle, MagIC tables shown bare); titles are the workbook
# sheet numbers
PANELS = {
    "measurements": ("1 Measurements", "1 · Lab data files / measurement files",
                     "laboratory data files for all demagnetization steps, with the metadata "
                     "needed to convert them into the MagIC measurements table (e.g., with "
                     "PmagPy or Paleomagnetism.org)", ("measurements",)),
    "specimens": ("2 Specimen directions", "2 · Specimen directions",
                  "all fits, with sample orientation and bedding", ("specimens", "samples")),
    "sites": ("3 Site means", "3 · Site means", "means calculated from sample/specimen fits",
              ("sites",)),
    "poles": ("4 Poles", "4 · Poles", "paleomagnetic pole from collection of sites",
              ("locations",)),
    "ages": ("5 Ages", "5 · Ages", "age constraints and their basis", ("ages",)),
}
# panels by grid column, in the order of the MagIC tables (measurements, specimens and
# samples, sites, locations, ages), with the legend in the left column to balance the heights
COLUMNS = [["measurements", "specimens", "legend"], ["sites", "poles", "ages"]]
# fields left out of the figure (in the Excel workbook): the citations, required by MagIC in
# every table, are covered by the reference in panel 1, except in the ages table, where
# they give the source of each age constraint; the experiment and measurement names, also
# required by MagIC, are generated in conversion and need context the figure lacks, so panel 1
# shows the specimen name alone
LEFT_OUT = {("measurements", "citations"), ("specimens", "citations"), ("sites", "citations"),
            ("locations", "citations"), ("measurements", "experiment"),
            ("measurements", "measurement")}
# field groups left out of the figure (in the Excel workbook): the mean direction at the
# sampling location and its ΔDx and ΔIx, which are readily derived from the pole
LEFT_OUT_GROUPS = {"Directions at sampling location"}
# notes under a group name where MagIC's requirement is conditional (data model 3.0:
# requiredUnless("age_low","age_high") on age; requiredOneInGroup("Names") in ages)
GROUP_NOTES = {("1 Measurements", "Quality"): "b for steps excluded from fits",
               ("3 Site means", "Age"): "age, or min and max",
               ("4 Poles", "Age"): "age, or min and max",
               ("5 Ages", "Names"): "at least one"}
# panels drawn in sections (heading, fields) rather than from their sheet alone: the lab
# data files panel shows the metadata supplied with the files, then the measurement fields
# that the conversion must yield
SECTIONS = {"measurements": [("Supplied with the files", LAB_FILE_FIELDS),
                             ("Yielded by conversion (MagIC measurements table)",
                              SHEETS["1 Measurements"])]}

LEVEL_CLASS = {MAGIC: "magic", STANDARD: "std", STANDARD_IF_APPLICABLE: "ifapp",
               RECOMMENDED: "rec"}
LEGEND = [(MAGIC, "Required by MagIC and this standard"),
          (STANDARD, "Required by this standard"),
          (STANDARD_IF_APPLICABLE, "Required by this standard, if applicable"),
          (RECOMMENDED, "Recommended")]

# palette of the workflow figure, with tints for the fills
CSS = """
@page { size: %(width)smm %(height)smm; margin: 0; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: #ffffff; }
body { width: %(width)smm; padding: 2mm 2mm 2mm 2mm; color: #0b0b0b;
       font-family: "Source Sans Pro", "Source Sans 3", "Helvetica Neue", Arial, sans-serif;
       font-size: 6.9pt; line-height: 1.18; -webkit-print-color-adjust: exact;
       print-color-adjust: exact; }
.panel.legend { border: 0.3mm solid #52514e; border-radius: 1.2mm; padding: 2mm 2.5mm 1.5mm;
                margin-top: 1mm; }
.legend .item { display: grid; grid-template-columns: max-content 1fr; gap: 0 2.5mm;
                align-items: center; padding: 1.7mm 0; color: #0b0b0b; }
.legend .sub { margin-bottom: 1mm; }
.mono { font-family: "Source Code Pro", Menlo, monospace; font-size: 6.2pt; }
.grid { display: grid; grid-template-columns: 1fr 1.1fr; gap: 0 3.5mm; align-items: start; }
.column { display: flex; flex-direction: column; gap: 3mm; }
.panel { border-top: 0.5mm solid #0b0b0b; padding-top: 1.2mm; }
.panel h2 { font-size: 9.5pt; font-weight: 700; margin: 0; letter-spacing: 0.01em;
            display: flex; justify-content: space-between; align-items: baseline; }
.panel h2 .table { font-family: "Source Code Pro", Menlo, monospace; font-weight: 500;
                   font-size: 6.6pt; color: #52514e; }
.panel .sub { color: #8a8984; font-size: 7pt; margin: 0.2mm 0 0.3mm 0; }
.group { display: grid; grid-template-columns: 14.5mm 1fr; gap: 0 1.2mm;
         padding: 0.75mm 0; border-bottom: 0.2mm solid #e6e5e1; }
.group:last-child { border-bottom: none; }
.section + .section { border-top: 0.2mm solid #c9c8c3; margin-top: 0.6mm; }
.shead { font-size: 6.6pt; font-weight: 600; font-style: italic; color: #52514e;
         padding: 1mm 0 0.2mm 0; }
.gname { color: #52514e; font-weight: 600; font-size: 6.8pt; padding-top: 0.55mm; }
.gname .gnote { display: block; font-weight: 400; color: #8a8984; font-size: 6pt; }
.chips { display: flex; flex-wrap: wrap; gap: 0.7mm; align-items: flex-start;
         align-content: flex-start; }
.chip { border-radius: 0.8mm; padding: 0.3mm 1mm 0.4mm 1mm; white-space: nowrap;
        border: 0.25mm solid transparent; }
.chip .name { font-weight: 600; }
.chip .col { font-family: "Source Code Pro", Menlo, monospace; font-size: 5.6pt;
             margin-left: 0.9mm; opacity: 0.85; }
.magic { background: #dcf1e6; border-color: #1f9a6b; color: #0d4430; }
.std   { background: #d9e7f8; border-color: #2a78d6; color: #10325c; }
.ifapp { background: #ffffff; border: 0.25mm dashed #2a78d6; color: #10325c; }
.rec   { background: #f1f0ed; border-color: #d9d8d4; color: #52514e; }
.rec .name { font-weight: 400; }
"""


def merged_fields(fields):
    """Fields of one group, with an adjacent Dec and Inc pair merged into one chip."""
    out, i = [], 0
    while i < len(fields):
        f = fields[i]
        nxt = fields[i + 1] if i + 1 < len(fields) else None
        if (f.header.startswith("Dec") and nxt is not None and nxt.header.startswith("Inc")
                and f.level == nxt.level and f.table == nxt.table):
            system = f.header[3:]
            column = f"{f.column}, {nxt.column}" + (f" · {f.note}" if system else "")
            out.append((f"Dec, Inc{system}", f.level, f.table, column))
            i += 2
        else:
            out.append((f.header, f.level, f.table, f.column))
            i += 1
    return out


def group_note(fields):
    """A coordinate-system note shared by every field of a group, e.g. tilt = 0."""
    notes = {f.note for f in fields}
    if len(notes) == 1:
        note = notes.pop()
        if note.startswith("dir_tilt_correction"):
            return note.replace("dir_tilt_correction", "tilt")
    return ""


def groups_html(sheet, fields, main_tables):
    """One row per field group: the group name (with any note) and its field chips."""
    fields = [f for f in fields
              if (f.table, f.column) not in LEFT_OUT and f.group not in LEFT_OUT_GROUPS]
    groups = []
    for f in fields:
        if f.group.endswith(" coordinates"):
            # one row for the three coordinate systems, one chip each
            system = f.group.replace(" coordinates", "")
            f = f._replace(group="Direction", header=f"{f.header} {system.lower()}",
                           note=f.note.replace("dir_tilt_correction", "tilt"))
        if groups and groups[-1][0] == f.group:
            groups[-1][1].append(f)
        else:
            groups.append((f.group, [f]))
    rows = []
    for name, group_fields in groups:
        chips = []
        for header, level, table, column in merged_fields(group_fields):
            # fields with no MagIC column (e.g. the data files) are shown by name only
            label = column if table in main_tables else f"{table}.{column}"
            col_html = f'<span class="col">{html.escape(label)}</span>' if column else ""
            chips.append(f'<span class="chip {LEVEL_CLASS[level]}"><span class="name">'
                         f'{html.escape(header)}</span>{col_html}</span>')
        note = group_note(group_fields) if name != "Direction" else ""
        note = GROUP_NOTES.get((sheet, name), note)
        note_html = f'<span class="gnote">{html.escape(note)}</span>' if note else ""
        rows.append(f'<div class="group"><div class="gname">{html.escape(name)}{note_html}'
                    f'</div><div class="chips">{"".join(chips)}</div></div>')
    return "".join(rows)


def panel_html(key):
    """One panel: a workbook sheet, or the sections listed for it in SECTIONS."""
    sheet, title, subtitle, main_tables = PANELS[key]
    sections = SECTIONS.get(key, [(None, SHEETS[sheet])])
    body = "".join(
        f'<div class="section">'
        + (f'<div class="shead">{html.escape(heading)}</div>' if heading else "")
        + groups_html(sheet, fields, main_tables) + "</div>"
        for heading, fields in sections)
    return (f'<section class="panel"><h2><span>{html.escape(title)}</span>'
            f'<span class="table">{" · ".join(main_tables)}</span></h2>'
            f'<div class="sub">{html.escape(subtitle)}</div>{body}</section>')


def legend_html():
    """The colour key, as a panel: an example chip for each requirement level."""
    items = "".join(f'<div class="item"><span><span class="chip {LEVEL_CLASS[lvl]}">'
                    f'<span class="name">Field name</span><span class="col">magic_column</span>'
                    f'</span></span><span>{html.escape(text)}</span></div>'
                    for lvl, text in LEGEND)
    return (f'<section class="panel legend"><h2><span>Data standard fields</span></h2>'
            f'<div class="sub">Each field is shown with the associated MagIC column</div>'
            f'{items}</section>')


def page_html(height_mm):
    panels = "".join('<div class="column">' + "".join(
        legend_html() if k == "legend" else panel_html(k) for k in col)
        + "</div>" for col in COLUMNS)
    return (f'<!doctype html><html><head><meta charset="utf-8">'
            f'<link rel="stylesheet" href="{html.escape(FONTS_CSS)}"><style>'
            f'{CSS % dict(width=PAGE_WIDTH_MM, height=height_mm)}</style></head><body>'
            f'<div class="grid">{panels}</div></body></html>')


def find_chrome():
    """Path of a Chrome or Chromium executable (macOS application or on the PATH)."""
    for candidate in CHROME_CANDIDATES:
        path = candidate if Path(candidate).is_file() else shutil.which(candidate)
        if path:
            return path
    raise FileNotFoundError(f"No Chrome or Chromium found among {CHROME_CANDIDATES}")


def print_pdf(html_path, pdf_path):
    # the virtual time budget gives the web fonts time to load before printing
    subprocess.run([find_chrome(), "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    "--virtual-time-budget=10000", f"--print-to-pdf={pdf_path}",
                    html_path.as_uri()],
                   check=True, capture_output=True)


def content_height_mm(pdf_path, tmp):
    """Height of the drawn content on the first page, from a low-resolution raster."""
    stem = Path(tmp) / "probe"
    subprocess.run(["pdftoppm", "-r", "100", "-png", "-singlefile", str(pdf_path), str(stem)],
                   check=True)
    img = np.asarray(Image.open(f"{stem}.png").convert("L"))
    rows = np.where((img < 250).any(axis=1))[0]
    return (rows.max() + 1) / 100 * 25.4


def main():
    pdf_path = OUTPUT_DIR / "template_fields.pdf"
    with tempfile.TemporaryDirectory() as tmp:
        html_path = Path(tmp) / "template_fields.html"
        # first pass on a tall page to measure the content, then print at that height
        html_path.write_text(page_html(400))
        print_pdf(html_path, pdf_path)
        height = np.ceil(content_height_mm(pdf_path, tmp) + 2.5)
        html_path.write_text(page_html(height))
        print_pdf(html_path, pdf_path)
    subprocess.run(["pdftoppm", "-r", str(PNG_DPI), "-png", "-singlefile", str(pdf_path),
                    str(OUTPUT_DIR / "template_fields")], check=True)
    print(f"Wrote {pdf_path} ({PAGE_WIDTH_MM} x {height:.0f} mm) and template_fields.png")


if __name__ == "__main__":
    main()
