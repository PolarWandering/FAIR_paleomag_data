// Table 1 of the FAIR standard paper: the formats of demagnetization data read by
// the Paleomagnetism.org data converter (v2.7.0) and by the convert_2_magic module
// of PmagPy (v4.5.2), grouped by the software or laboratory from which the format
// originates, written as a Word table.
//
// Usage (after `npm install` in this directory):
//     node make_converter_formats_table.js [output.docx]
// The output defaults to converter_formats.docx next to this script.

const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  WidthType, BorderStyle, AlignmentType, ShadingType,
} = require("docx");

const out = process.argv[2] || path.join(__dirname, "converter_formats.docx");
const FONT = "Arial";
const MONO = "Courier New";
const SIZE = 18; // 9 pt
const W = [2900, 2460, 2000, 2000]; // sums to 9360

// [format, laboratories, paleomagnetism.org, pmagpy functions]
const G = (t) => ({ group: t });
const rows = [
  G("Acquisition and analysis software"),
  ["2G Enterprises, binary", "Barcelona (BCN2G), PGL Beijing", "✓", ["_2g_bin"]],
  ["2G Enterprises, ASCII", "", "", ["_2g_asc"]],
  ["2G Enterprises, tab-delimited export", "Oxford, Southampton, USPMag, Cenieh (two variants), Xi'an", "✓", []],
  ["AGICO JR5", "", "✓ (experimental)", []],
  ["AGICO JR6", "", "✓ (experimental)", ["jr6_jr6", "jr6_txt"]],
  ["AGICO Remasoft (.rs3)", "Oslo", "✓", ["rs3"]],
  ["CIT", "Caltech", "✓", ["cit"]],
  ["Ikayaki (.csv)", "Helsinki (core and block samples)", "✓", []],
  ["Molspin Minispin (Yale format)", "", "", ["mini"]],
  ["PMD (Enkin); PaleoMac", "", "✓", ["pmd"]],
  ["Spinner (.csv)", "", "✓", []],
  G("Laboratory formats"),
  ["Berkeley Geochronology Center", "", "", ["bgc"]],
  ["Black Mountain Lab (.xPCA, .dms)", "", "✓", []],
  ["Geological Survey of Finland", "", "✓", []],
  ["Hebrew University of Jerusalem", "", "", ["huji"]],
  ["IODP (archive half, discrete, JR6)", "", "", ["iodp_srm_lore", "iodp_dscr_lore", "iodp_jr6_lore"]],
  ["Lamont-Doherty Earth Observatory", "", "", ["ldeo"]],
  ["Munich, Geological Survey of Norway, East Anglia (related text formats)", "", "✓", []],
  ["Scripps Institution of Oceanography", "", "", ["sio"]],
  ["University of Montpellier", "", "✓", []],
  ["University of Plymouth", "", "✓", []],
  ["University of Rennes", "", "✓", []],
  ["University of Utrecht", "", "✓", ["utrecht"]],
  G("Database and application formats"),
  ["Generic (user-defined delimited file)", "", "", ["generic"]],
  ["MagIC", "", "✓", "native format"],
  ["Paleomagnetism.org (2.0.0 .col)", "", "native format", []],
  ["Paleomagnetism.org (1.0.0 .dir)", "", "✓ (legacy)", []],
];

const none = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const rule = (sz) => ({ style: BorderStyle.SINGLE, size: sz, color: "000000" });
const thin = rule(4);

function para(children, align) {
  return new Paragraph({ alignment: align, spacing: { before: 30, after: 30 }, children });
}
function txt(t, opts = {}) {
  return new TextRun({ text: t, font: opts.mono ? MONO : FONT, size: SIZE, bold: opts.bold });
}
function cell(children, i, borders, span, shade) {
  return new TableCell({
    width: { size: span ? W.reduce((a, b) => a + b, 0) : W[i], type: WidthType.DXA },
    columnSpan: span ? 4 : undefined,
    margins: { top: 30, bottom: 30, left: 80, right: 80 },
    borders: { top: thin, bottom: thin, left: thin, right: thin },
    shading: shade ? { type: ShadingType.CLEAR, fill: "EDEDED", color: "auto" } : undefined,
    children,
  });
}

const header = new TableRow({
  tableHeader: true,
  children: ["Format", "Laboratories named in Paleomagnetism.org", "Paleomagnetism.org", "PmagPy"].map((h, i) =>
    cell([para([txt(h, { bold: true })])], i, {}, false, true)),
});

const body = rows.map((r, n) => {
  const last = n === rows.length - 1;
  const b = last ? { bottom: rule(12) } : {};
  if (r.group) {
    return new TableRow({ children: [cell([para([txt(r.group, { bold: true })])], 0, b, true, true)] });
  }
  const fn = r[3];
  const pmagpy = typeof fn === "string"
    ? [para([txt(fn)])]
    : fn.length ? fn.map((f) => para([txt(f, { mono: true })])) : [para([txt("")])];
  return new TableRow({
    children: [
      cell([para([txt(r[0])])], 0, b),
      cell([para([txt(r[1])])], 1, b),
      cell([para([txt(r[2])])], 2, b),
      cell(pmagpy, 3, b),
    ],
  });
});

const caption =
  "Table 1. Formats of demagnetization data read by the Paleomagnetism.org data converter (v2.7.0) and by the " +
  "convert_2_magic module of PmagPy (v4.5.2), grouped by the software or laboratory from which the format originates. " +
  "Laboratories listed are those named in the Paleomagnetism.org converter; other laboratories using the same " +
  "acquisition software may produce similar formats. For PmagPy, the name of the conversion function is given.";

const doc = new Document({
  styles: { default: { document: { run: { font: FONT, size: 20 } } } },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
    children: [
      new Paragraph({ spacing: { after: 120 }, children: [new TextRun({ text: caption, font: FONT, size: 20 })] }),
      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: W,
        borders: { top: thin, bottom: thin, left: thin, right: thin, insideHorizontal: thin, insideVertical: thin },
        rows: [header, ...body],
      }),
    ],
  }],
});

Packer.toBuffer(doc).then((buf) => fs.writeFileSync(out, buf));
