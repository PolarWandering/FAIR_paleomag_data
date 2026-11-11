// Table 1 of the FAIR standard paper: the formats of demagnetization data read by
// the Paleomagnetism.org data converter (v2.7.0) and by the convert_2_magic module
// of PmagPy (v4.5.2), grouped by the software or laboratory from which the format
// originates.
//
// The table is written both as a Word table (with its caption) and as a graphic of
// the table alone (PDF and PNG), in the style of the version inserted into the
// manuscript: heavy rules above and below the header and at the foot, light rules
// between rows, shaded group rows, blue check marks and PmagPy function names in a
// gray monospaced font. The graphic is written as HTML and printed to PDF with
// headless Chrome or Chromium, at the height of the table; the PNG is rendered from
// the PDF with pdftoppm (poppler). Fonts are local (Arial and Menlo, or their
// metric equivalents Liberation Sans and DejaVu Sans Mono on Linux).
//
// Usage (after `npm install` in this directory):
//     node make_converter_formats_table.js
// Outputs, next to this script: converter_formats.docx, converter_formats.pdf and
// converter_formats.png.
//
// Requires Node.js, the docx package, Google Chrome or Chromium, and poppler.

const fs = require("fs");
const os = require("os");
const path = require("path");
const { execFileSync } = require("child_process");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  WidthType, BorderStyle, ShadingType, VerticalAlign,
} = require("docx");

const OUT_DIR = __dirname;
const STEM = "converter_formats";

// style, after the version of the table in the manuscript
const STYLE = {
  font: "Arial",
  mono: "Menlo",
  text: "111111",
  rule: "111111",     // heavy rules: top, below the header, foot
  divider: "D8D8D4",  // light rules between rows
  group: "F0F0EC",    // fill of the group rows
  check: "2878D4",
  fn: "505050",       // PmagPy function names
};
const CHECK = "✓";
const W = [3000, 2810, 1880, 1670]; // column widths (dxa), sum to 9360 (6.5 in)
const PNG_DPI = 600;
const CHROME_CANDIDATES = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "google-chrome-stable", "google-chrome", "chromium", "chromium-browser"];

const HEADER = ["Format", "Laboratories named in Paleomagnetism.org", "Paleomagnetism.org", "PmagPy"];

// [format, laboratories, paleomagnetism.org, pmagpy functions]; a string in place of
// the PmagPy functions is written as text, not as function names
const G = (t) => ({ group: t });
const rows = [
  G("Acquisition and analysis software"),
  ["2G Enterprises, binary", "Barcelona (BCN2G), PGL Beijing", "✓", ["_2g_bin"]],
  ["2G Enterprises, ASCII", "", "", ["_2g_asc"]],
  ["2G Enterprises, tab-delimited export", "Oxford, Southampton, USPMag, Cenieh (two variants), Xi’an", "✓", []],
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

const caption =
  "Table 1. Formats of demagnetization data read by the Paleomagnetism.org data converter (v2.7.0) and by the " +
  "convert_2_magic module of PmagPy (v4.5.2), grouped by the software or laboratory from which the format originates. " +
  "Laboratories listed are those named in the Paleomagnetism.org converter; other laboratories using the same " +
  "acquisition software may produce similar formats. For PmagPy, the name of the conversion function is given.";

// a Paleomagnetism.org entry split into its check mark (if any) and the text after it
function splitCheck(s) {
  return s.startsWith(CHECK) ? [CHECK, s.slice(CHECK.length)] : ["", s];
}

// ---------------------------------------------------------------- Word table

const SIZE = 17; // 8.5 pt
const none = { style: BorderStyle.NONE, size: 0, color: "auto" };
const heavy = { style: BorderStyle.SINGLE, size: 8, color: STYLE.rule };   // 1 pt
const light = { style: BorderStyle.SINGLE, size: 4, color: STYLE.divider }; // 0.5 pt

function txt(t, opts = {}) {
  return new TextRun({
    text: t, font: opts.mono ? STYLE.mono : STYLE.font, size: opts.mono ? SIZE - 2 : SIZE,
    bold: opts.bold, color: opts.color || STYLE.text,
  });
}
function para(runs) {
  return new Paragraph({ spacing: { before: 0, after: 0, line: 264 }, children: runs });
}
function cell(paras, i, { top = light, bottom = light, span = false, fill, valign } = {}) {
  return new TableCell({
    width: { size: span ? W.reduce((a, b) => a + b, 0) : W[i], type: WidthType.DXA },
    columnSpan: span ? W.length : undefined,
    margins: { top: 62, bottom: 62, left: 92, right: 92 },
    borders: { top, bottom, left: none, right: none },
    shading: fill ? { type: ShadingType.CLEAR, fill, color: "auto" } : undefined,
    verticalAlign: valign,
    children: paras,
  });
}

function docxTable() {
  const header = new TableRow({
    tableHeader: true,
    children: HEADER.map((h, i) => cell([para([txt(h, { bold: true })])], i,
      { top: heavy, bottom: heavy, valign: VerticalAlign.BOTTOM })),
  });
  const body = rows.map((r, n) => {
    const top = n === 0 ? heavy : light;
    const bottom = n === rows.length - 1 ? heavy : light;
    if (r.group) {
      return new TableRow({
        cantSplit: true,
        children: [cell([para([txt(r.group, { bold: true })])], 0, { top, bottom, span: true, fill: STYLE.group })],
      });
    }
    const [check, rest] = splitCheck(r[2]);
    const pmag = r[2] ? [para([...(check ? [txt(check, { color: STYLE.check })] : []), ...(rest ? [txt(rest)] : [])])]
      : [para([])];
    const fn = r[3];
    const pmagpy = typeof fn === "string" ? [para([txt(fn)])]
      : fn.length ? fn.map((f) => para([txt(f, { mono: true, color: STYLE.fn })])) : [para([])];
    return new TableRow({
      cantSplit: true,
      children: [
        cell([para([txt(r[0])])], 0, { top, bottom }),
        cell([para([txt(r[1])])], 1, { top, bottom }),
        cell(pmag, 2, { top, bottom }),
        cell(pmagpy, 3, { top, bottom }),
      ],
    });
  });
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: W,
    borders: { top: none, bottom: none, left: none, right: none, insideHorizontal: none, insideVertical: none },
    rows: [header, ...body],
  });
}

function writeDocx(file) {
  const doc = new Document({
    styles: { default: { document: { run: { font: STYLE.font, size: 20 } } } },
    sections: [{
      properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
      children: [
        new Paragraph({ spacing: { after: 120 }, children: [new TextRun({ text: caption, font: STYLE.font, size: 20 })] }),
        docxTable(),
      ],
    }],
  });
  return Packer.toBuffer(doc).then((buf) => fs.writeFileSync(file, buf));
}

// ---------------------------------------------------------------- graphic

const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

const CSS = `
@page { size: 6.5in %HEIGHT%in; margin: 0; }
html, body { margin: 0; padding: 0; background: #fff; }
body { width: 6.5in; font: 8.4pt/10.75pt ${STYLE.font}, "Liberation Sans", Helvetica, sans-serif; color: #${STYLE.text};
  -webkit-print-color-adjust: exact; print-color-adjust: exact; }
table { width: calc(6.5in - 0.26in); margin: 0.13in; border-collapse: collapse; table-layout: fixed;
  border-top: 0.75pt solid #${STYLE.rule}; border-bottom: 0.75pt solid #${STYLE.rule}; }
th { text-align: left; vertical-align: bottom; font-weight: bold; padding: 3.2pt 4.6pt;
  border-bottom: 0.75pt solid #${STYLE.rule}; }
td { vertical-align: top; padding: 3.1pt 4.6pt; border-top: 0.6pt solid #${STYLE.divider}; }
tr.first td { border-top: none; }
tr.group td { background: #${STYLE.group}; font-weight: bold; padding: 3.8pt 4.6pt; }
.check { color: #${STYLE.check}; }
.fn { display: block; font-family: ${STYLE.mono}, "DejaVu Sans Mono", monospace; font-size: 7.5pt; color: #${STYLE.fn}; }
`;

function tableHtml() {
  const total = W.reduce((a, b) => a + b, 0);
  const cols = W.map((w) => `<col style="width:${(100 * w / total).toFixed(2)}%">`).join("");
  const head = "<tr>" + HEADER.map((h) => `<th>${esc(h)}</th>`).join("") + "</tr>";
  const body = rows.map((r, n) => {
    const cls = n === 0 ? ' class="first' + (r.group ? ' group"' : '"') : (r.group ? ' class="group"' : "");
    if (r.group) return `<tr${cls}><td colspan="${W.length}">${esc(r.group)}</td></tr>`;
    const [check, rest] = splitCheck(r[2]);
    const pmag = (check ? `<span class="check">${check}</span>` : "") + esc(rest);
    const fn = r[3];
    const pmagpy = typeof fn === "string" ? esc(fn) : fn.map((f) => `<span class="fn">${esc(f)}</span>`).join("");
    return `<tr${cls}><td>${esc(r[0])}</td><td>${esc(r[1])}</td><td>${pmag}</td><td>${pmagpy}</td></tr>`;
  }).join("\n");
  return `<table><colgroup>${cols}</colgroup><thead>${head}</thead><tbody>\n${body}\n</tbody></table>`;
}

function pageHtml(heightIn) {
  // the script records the height of the page content (in inches) for the first pass
  return `<!doctype html><html><head><meta charset="utf-8"><style>${CSS.replace("%HEIGHT%", heightIn)}</style>
</head><body>${tableHtml()}
<script>document.body.dataset.height = (document.querySelector("table").getBoundingClientRect().bottom / 96 + 0.13).toFixed(4);</script>
</body></html>`;
}

function findChrome() {
  for (const c of CHROME_CANDIDATES) {
    if (c.startsWith("/") && fs.existsSync(c)) return c;
    try {
      return execFileSync("which", [c], { encoding: "utf8" }).trim();
    } catch (e) { /* not on the PATH */ }
  }
  throw new Error(`No Chrome or Chromium found among ${CHROME_CANDIDATES}`);
}

function writeGraphic(pdfFile, pngStem) {
  const chrome = findChrome();
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "converter_formats-"));
  const html = path.join(tmp, `${STEM}.html`);
  const uri = "file://" + html;
  const run = (args) => execFileSync(chrome, ["--headless", "--disable-gpu", "--no-pdf-header-footer",
    "--virtual-time-budget=2000", ...args, uri], { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] });
  // first pass: lay out the table and read its height; second pass: print at that height
  fs.writeFileSync(html, pageHtml(20));
  const height = Math.ceil(Number(/data-height="([\d.]+)"/.exec(run(["--dump-dom"]))[1]) * 100) / 100;
  fs.writeFileSync(html, pageHtml(height));
  run([`--print-to-pdf=${pdfFile}`]);
  execFileSync("pdftoppm", ["-r", String(PNG_DPI), "-png", "-singlefile", pdfFile, pngStem]);
  fs.rmSync(tmp, { recursive: true, force: true });
  return height;
}

async function main() {
  const docx = path.join(OUT_DIR, `${STEM}.docx`);
  const pdf = path.join(OUT_DIR, `${STEM}.pdf`);
  await writeDocx(docx);
  const height = writeGraphic(pdf, path.join(OUT_DIR, STEM));
  console.log(`Wrote ${docx}, ${pdf} (6.5 x ${height} in) and ${STEM}.png (${PNG_DPI} dpi)`);
}

main();
