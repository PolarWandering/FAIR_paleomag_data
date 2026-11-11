# FAIR_paleomag_data

Code and figures associated with the manuscript "A community standard in FAIR paleomagnetic data publication" which sets out a community standard for publishing paleomagnetic data so that they are findable, accessible, interoperable and reusable (FAIR).

## Repository structure

```text
FAIR_paleomag_data/
├── README.md
├── environment.yml                       conda environment for running the scripts
├── fair_template/                        code shared by the template figure and tables
│   ├── definition.py                         the fields of the template, by workbook sheet
│   ├── magic.py                              reading, writing and validating MagIC files
│   ├── readable.py                           the readable (template) form of MagIC tables
│   └── resources/                            MagIC data model, method codes, vocabularies
├── data/                                 published datasets that the scripts read
│   ├── magic_20884/
│   │   └── magic_contribution_20884.txt      MagIC contribution 20884
│   └── sauerbier2026_figshare/
│       └── CA_sugarmill.col                  Paleomagnetism.org collection
├── figures/                              one directory per figure
│   ├── data_gap/                         the gap between measured and published data
│   │   ├── data_gap.ipynb                    makes the figure from data/
│   │   ├── data/                             MagIC, Scopus and GPMDB inputs (CSV)
│   │   ├── data_gap.pdf                      figure (for the manuscript)
│   │   └── data_gap.png                      figure (600 dpi)
│   ├── platforms/                        the MagIC database and Paleomagnetism.org
│   │   ├── capture_platform_screenshots.py   step 1: take the screenshots
│   │   ├── make_platforms_figure.py          step 2: compose the figure
│   │   ├── screenshots/                      inputs written by step 1
│   │   │   ├── magic.png
│   │   │   └── pmag_library.png
│   │   ├── platforms.pdf                     figure (for the manuscript)
│   │   └── platforms.png                     figure (600 dpi)
│   ├── template_fields/                  the fields of the template and how each is required
│   │   ├── make_template_figure.py           makes the figure from fair_template/definition.py
│   │   ├── template_fields.pdf               figure (for the manuscript)
│   │   └── template_fields.png               figure (600 dpi)
│   └── workflow_archiving/               the levels of a dataset, as archived
│       ├── make_workflow_figure.py           makes the figure from data/
│       ├── workflow_archiving.pdf            figure (for the manuscript)
│       └── workflow_archiving.png            figure (600 dpi)
└── tables/                               one directory per table
    └── shaat_dikes_example/              Supplementary Table 2: the full Shaat dikes example
        ├── make_shaat_dikes_example.py       makes the tables from data/
        ├── FAIR_template_example_Oman2025.xlsx   the example in the template layout and in MagIC form
        ├── magic_contribution_Shaat_pole.txt     the MagIC tables (MagIC upload format)
        ├── build_report.md                   checks of each level against the one below
        ├── specimen_fit_checks.csv
        └── site_mean_checks.csv
```

## Data

| Directory | Dataset | Source | License |
| --- | --- | --- | --- |
| [`data/magic_20884/`](data/magic_20884/) | MagIC contribution 20884 (version 2 of the contribution of Swanson-Hysell et al., 2025): the measurements, specimens, samples, sites and locations tables of the Shaat dikes of Oman | [doi:10.7288/V4/MAGIC/20884](https://doi.org/10.7288/V4/MAGIC/20884) | CC BY 4.0 |
| [`data/sauerbier2026_figshare/`](data/sauerbier2026_figshare/) | `CA_sugarmill.col`, the Paleomagnetism.org collection of the Sugar Mill limestone of Carriacou (locality CA7), one of the collection files published with Sauerbier et al. (2026) | [doi:10.6084/m9.figshare.28815698](https://doi.org/10.6084/m9.figshare.28815698) | CC BY 4.0 |

The files are unmodified copies of the published files. The studies are:

- Swanson-Hysell, N. L., Zhang, Y., Macdonald, F. A., Koran, I., Tasistro-Hart, A. R., and Jay, A. F. (2025). Oman was on the northern margin of a wide late Tonian Mozambique Ocean. *Geology*, 53(11), 909–913. [doi:10.1130/G53450.1](https://doi.org/10.1130/G53450.1)
- Sauerbier, J. D. C., Philippon, M., Dekkers, M. J., Cornée, J.-J., BouDagher-Fadel, M. K., and van Hinsbergen, D. J. J. (2026). Rotation in the southeastern Caribbean arc (Grenadines) accommodated by back-arc basin inversion. *Tectonics*, 45(4), e2025TC009223. [doi:10.1029/2025TC009223](https://doi.org/10.1029/2025TC009223)

## Figures

| Directory | Figure | Scripts | Output |
| --- | --- | --- | --- |
| [`figures/data_gap/`](figures/data_gap/) | The gap between measured and published paleomagnetic data: (a) papers using reconstructions vs. papers reporting poles, (b) the data behind a pole in MagIC studies and (c) the share of published poles with data in MagIC | `data_gap.ipynb` | [`data_gap.pdf`](figures/data_gap/data_gap.pdf), [`data_gap.png`](figures/data_gap/data_gap.png) |
| [`figures/platforms/`](figures/platforms/) | The two data platforms that the standard builds on: (a) the home page of the MagIC database and (b) the data library of Paleomagnetism.org | `capture_platform_screenshots.py`, `make_platforms_figure.py` | [`platforms.pdf`](figures/platforms/platforms.pdf), [`platforms.png`](figures/platforms/platforms.png) |
| [`figures/template_fields/`](figures/template_fields/) | The fields of the template, one panel per sheet of the template workbook (measurements, specimen directions, site means, poles and ages), each field coloured by its requirement level and shown with its MagIC column | `make_template_figure.py` | [`template_fields.pdf`](figures/template_fields/template_fields.pdf), [`template_fields.png`](figures/template_fields/template_fields.png) |
| [`figures/workflow_archiving/`](figures/workflow_archiving/) | The levels of a paleomagnetic dataset, from the measurements of a specimen to the pole, and where each level is archived: in a MagIC contribution (top row) and in a Paleomagnetism.org collection (bottom row) | `make_workflow_figure.py` | [`workflow_archiving.pdf`](figures/workflow_archiving/workflow_archiving.pdf), [`workflow_archiving.png`](figures/workflow_archiving/workflow_archiving.png) |

### `figures/data_gap/`

The notebook `data_gap.ipynb` combines three sources:

- **MagIC**: the deepest data level that each public study archives (measurements, specimen directions, site means or poles only) and, for studies with measurements, the number of demagnetization steps, specimens, samples, sites and locations (`magic_scan.csv`, `magic_level_counts.csv`);
- **Scopus**: papers per year that use plate or paleogeographic reconstructions (`scopus_reconstruction_papers.csv`, counted 29 October 2026);
- **GPMDB** (Pisarevsky et al., 2022): the papers that report poles (`gpmdb_papers.csv`, built from `gpmdb_search_results.csv`, an export of [gpmdb.net](http://www.gpmdb.net) made 27 October 2026). The papers are matched to MagIC studies by DOI or bibliographic details, with the publication details of the MagIC DOIs taken from OpenAlex (`magic_references.csv`).

All inputs are cached as CSV files in `data/`, so the notebook runs offline in seconds. Deleting a file (or setting `RESCAN = True` for the MagIC scan, about 20 minutes) rebuilds it from its source; rebuilding the Scopus counts needs an Elsevier API key and `pybliometrics`.

### `figures/platforms/`

The figure shows two browser windows side by side: (a) the MagIC home page ([earthref.org/MagIC](https://earthref.org/MagIC)) down to its two latest contributions and (b) the Paleomagnetism.org 2 data library ([paleomagnetism.org/library](https://www.paleomagnetism.org/library/)) with its map of publications and the two latest publications in its table.

It is made in two steps:

```bash
cd figures/platforms
python capture_platform_screenshots.py   # writes screenshots/magic.png and screenshots/pmag_library.png
python make_platforms_figure.py          # writes platforms.pdf and platforms.png
```

1. `capture_platform_screenshots.py` drives headless Google Chrome to load each page, waits until the page has finished loading (the plot thumbnails of the MagIC contributions; the markers and map tiles of the library), and saves a screenshot clipped to the region that the figure shows. Both pages are loaded in narrow windows (1000 px for MagIC, 800 px for the library) so that the two panels fit side by side; these are the narrowest widths at which each site keeps its desktop layout. The library map is reset to show one world width.
2. `make_platforms_figure.py` frames each screenshot as a browser window with its URL and places the two windows side by side at equal height, at the full page width of 174 mm.

The committed screenshots were taken on 10 November 2026. Both websites change with time (the "Recent Contributions" list of MagIC, and the publications and map markers of the library), so running the capture script again gives screenshots of the sites as they are then, and not the committed ones. Running `make_platforms_figure.py` alone rebuilds the figure from the committed screenshots.

The content of EarthRef.org, including the MagIC home page, is licensed under CC BY 4.0 unless otherwise noted on the site. The basemap of the library panel is drawn from OpenStreetMap tiles (© OpenStreetMap contributors).

### `figures/template_fields/`

The fields are defined in `fair_template/definition.py`, which also defines the full Shaat dikes example (Supplementary Table 2): for each field its group, readable header, MagIC table and column, units, requirement level and a note. Panel 1 shows the laboratory data files in two sections: the metadata supplied with the files and the measurement fields that the conversion must yield. The figure leaves out the citations (except in the ages panel), the experiment and measurement names, and the mean direction at the sampling location of the poles sheet, which are in the workbook.

```bash
cd figures/template_fields
python make_template_figure.py   # writes template_fields.pdf and template_fields.png
```

The script writes the figure as an HTML page, prints it to PDF with headless Google Chrome or Chromium, crops the page to its content and renders the PNG from the PDF with `pdftoppm` (poppler). The Source Sans 3 and Source Code Pro fonts are loaded from Google Fonts, so the script needs a network connection unless the fonts are installed locally.

### `figures/workflow_archiving/`

Each row of the figure follows one published dataset up the levels of the standard: the measurements of one specimen with its fits (vector component diagram), one fit in specimen, geographic and tilt-corrected coordinates, the fit directions of the site or locality of that specimen, and the VGPs with the pole. Under each panel is the part of the archive that holds that level.

```bash
cd figures/workflow_archiving
python make_workflow_figure.py   # writes workflow_archiving.pdf and workflow_archiving.png
```

The top row is read from MagIC contribution 20884. Every value plotted is read from the archive: the fits and the site means are those of the specimens and sites tables, and the pole is that of the locations table. The bottom row is read from the Paleomagnetism.org collection file `CA_sugarmill.col`, which holds the demagnetization steps, the orientations and the interpretations, and holds no means. The VGPs and the pole of the bottom row are therefore calculated by the script, following section 3.2 of Sauerbier et al. (2026): one VGP per ChRM direction and the Fisher mean of the VGPs after a 45° cutoff.

The paleomagnetic plots and calculations are made with [PmagPy](https://github.com/PmagPy/PmagPy): the vector component diagrams with their fits (`pmagplotlib.plot_zij`), the equal-area plots (`ipmag.plot_net`, `plot_di`, `plot_di_mean`), the maps (`ipmag.make_orthographic_map`, `plot_vgp`, `plot_pole`), the reading of the MagIC contribution, the rotations to geographic coordinates, and the VGPs and their mean. The script adds the text written on and under the panels, the arrows between the coordinate systems of the second column, and the boxes and arrows of the archive strips. The plotting options that it uses to place PmagPy plots as panels of one figure, and to draw the vector component diagrams without a frame and with the fits as arrows, are in PmagPy releases later than 4.5.2.

## Tables

| Directory | Table | Script | Output |
| --- | --- | --- | --- |
| [`tables/shaat_dikes_example/`](tables/shaat_dikes_example/) | Supplementary Table 2: the full Shaat dikes example in the layout of the template and in MagIC form | `make_shaat_dikes_example.py` | [`FAIR_template_example_Oman2025.xlsx`](tables/shaat_dikes_example/FAIR_template_example_Oman2025.xlsx), [`magic_contribution_Shaat_pole.txt`](tables/shaat_dikes_example/magic_contribution_Shaat_pole.txt) |

The tables follow the field definitions in `fair_template/definition.py`.

### `tables/shaat_dikes_example/`

```bash
cd tables/shaat_dikes_example
python make_shaat_dikes_example.py   # writes the spreadsheet, the MagIC file and the checks
```

The example is the part of MagIC contribution 20884 that the Shaat dikes pole needs: the 51 sites of the pole (listed in the pole row of the locations table), the 119 specimens averaged into them, their samples, their 2,596 demagnetization steps, the pole and the ages. The spreadsheet holds the readable sheets of the template, a field dictionary, the method codes used and the MagIC tables; the MagIC tables are also written as `magic_contribution_Shaat_pole.txt` and validated against the MagIC data model (`fair_template/resources/`). Each level is checked against the one below it (`build_report.md`): the specimen fits are re-made from the measurements with PmagPy and rotated, the site means are recalculated from the specimen fits, and the pole from the site VGPs.

## Environment

The Python environment for running the scripts is specified in [`environment.yml`](environment.yml):

```bash
mamba env create -f environment.yml
mamba activate fair_paleomag_data
```

`capture_platform_screenshots.py` also requires Google Chrome (version 157 was used). The path to Chrome is set by the `CHROME` constant at the top of the script and is that of a macOS installation; change it on other systems. `make_template_figure.py` also requires Google Chrome or Chromium, which it looks for at the macOS installation path and then on the `PATH`.
