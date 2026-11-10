# FAIR_paleomag_data

Code and figures associated with the manuscript "A community standard in FAIR paleomagnetic data publication" which sets out a community standard for publishing paleomagnetic data so that they are findable, accessible, interoperable and reusable (FAIR).

## Repository structure

```text
FAIR_paleomag_data/
├── README.md
├── environment.yml                       conda environment for running the scripts
└── figures/                              one directory per figure
    └── platforms/                        the MagIC database and Paleomagnetism.org
        ├── capture_platform_screenshots.py   step 1: take the screenshots
        ├── make_platforms_figure.py          step 2: compose the figure
        ├── screenshots/                      inputs written by step 1
        │   ├── magic.png
        │   └── pmag_library.png
        ├── platforms.pdf                     figure (for the manuscript)
        └── platforms.png                     figure (600 dpi)
```

## Figures

| Directory | Figure | Scripts | Output |
| --- | --- | --- | --- |
| [`figures/platforms/`](figures/platforms/) | The two data platforms that the standard builds on: (a) the home page of the MagIC database and (b) the data library of Paleomagnetism.org | `capture_platform_screenshots.py`, `make_platforms_figure.py` | [`platforms.pdf`](figures/platforms/platforms.pdf), [`platforms.png`](figures/platforms/platforms.png) |

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

## Environment

The Python environment for running the scripts is specified in [`environment.yml`](environment.yml):

```bash
mamba env create -f environment.yml
mamba activate fair_paleomag_data
```

`capture_platform_screenshots.py` also requires Google Chrome (version 157 was used). The path to Chrome is set by the `CHROME` constant at the top of the script and is that of a macOS installation; change it on other systems.
