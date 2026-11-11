"""The fields of the FAIR paleomagnetic data standard template, by workbook sheet.

One entry per field: the group it is shown in, its readable header, the MagIC
table and column it maps to (empty for fields with no MagIC column, such as the
laboratory data files), its units, its requirement level and a note. SHEETS
lists the fields of each sheet of the template workbook; LAB_FILE_FIELDS lists
the metadata supplied with the laboratory data files so that they can be
converted into the MagIC measurements table.

The definition is shared by the template figure (figures/template_fields/) and the
supplementary tables (tables/template_workbook/ and tables/shaat_dikes_example/).
"""

from collections import OrderedDict, namedtuple

# Requirement levels
MAGIC = "Required by MagIC"
STANDARD = "Required by this standard"
STANDARD_IF_APPLICABLE = "Required by this standard (if applicable)"
RECOMMENDED = "Recommended"
NO_COLUMN = "No MagIC column"


Field = namedtuple("Field", "group header table column unit level note")


def F(group, header, table, column, unit="", level=RECOMMENDED, note=""):
    return Field(group, header, table, column, unit, level, note)


# ---------------------------------------------------------------------------
# The template: one list of fields per readable table
# ---------------------------------------------------------------------------
CONTRIBUTION_FIELDS = [
    F("Contribution", "Reference (paper DOI)", "contribution", "reference", "", MAGIC),
    F("Contribution", "Laboratory", "contribution", "lab_names", "controlled vocabulary", MAGIC),
    F("Contribution", "MagIC contribution ID", "contribution", "id", "", RECOMMENDED,
      "Assigned by MagIC"),
    F("Contribution", "Dataset DOI", "contribution", "", "", STANDARD,
      "Assigned by MagIC on activation (10.7288/V4/MAGIC/<id>)"),
    F("Contribution", "Data model version", "contribution", "data_model_version", ""),
    F("Contribution", "Contributor", "contribution", "contributor", "EarthRef handle"),
]

# Metadata supplied with the laboratory data files, in lieu of a measurements table, so
# that the files can be converted into the MagIC measurements table (following D. van
# Hinsbergen's metadata sheet of 2026-11-08). Shown in panel 1 of the template figure; sheet 1
# of the template workbook has its own layout (tables/template_workbook/).
LAB_FILE_FIELDS = [
    F("Contribution", "Reference", "contribution", "reference", "", MAGIC,
      "Paper DOI, after publication"),
    F("Contribution", "Laboratory", "contribution", "lab_names", "controlled vocabulary", MAGIC),
    F("Files", "Data files", "", "", "", STANDARD, "Laboratory data files for all specimens"),
    F("Files", "Data file DOI", "", "", "", STANDARD, "Repository DOI of the files"),
    F("Files", "File format", "", "", "", STANDARD,
      "A format read by a converter, e.g. PmagPy or Paleomagnetism.org"),
    F("Instrument", "Instrument", "measurements", "instrument_codes", "", RECOMMENDED),
    F("Instrument", "n orientations", "measurements", "meas_n_orient", "", STANDARD),
    F("Orientation", "Core orientation convention", "", "", "", STANDARD,
      "What the reported azimuth and dip refer to, relative to the specimen x-axis"),
    F("Orientation", "Declination correction", "samples", "azimuth_dec_correction", "°",
      STANDARD, "The correction applied to azimuths, or that none was applied"),
]

MEASUREMENT_FIELDS = [
    F("Names", "Specimen", "measurements", "specimen", "", MAGIC),
    F("Names", "Experiment", "measurements", "experiment", "", MAGIC),
    F("Names", "Measurement", "measurements", "measurement", "", MAGIC),
    F("Step", "Step no.", "measurements", "treat_step_num", "", RECOMMENDED),
    F("Step", "Treatment", "measurements", "method_codes", "method codes", MAGIC,
      "e.g. LT-NO:LP-DIR-T"),
    F("Step", "Temperature", "measurements", "treat_temp", "°C (MagIC: K)",
      STANDARD_IF_APPLICABLE, "Thermal demagnetization steps"),
    F("Step", "AF peak field", "measurements", "treat_ac_field", "mT (MagIC: T)",
      STANDARD_IF_APPLICABLE, "Alternating field demagnetization steps"),
    F("Magnetization", "Moment", "measurements", "magn_moment", "Am²", STANDARD,
      "Or magn_volume (A/m) with specimen volume"),
    F("Magnetization", "Dec", "measurements", "dir_dec", "°, specimen coord.", STANDARD),
    F("Magnetization", "Inc", "measurements", "dir_inc", "°, specimen coord.", STANDARD),
    F("Magnetization", "CSD", "measurements", "dir_csd", "°", RECOMMENDED,
      "Circular standard deviation of repeat measurements"),
    F("Quality", "Good / bad data", "measurements", "quality", "g = good, b = bad", MAGIC),
    F("Source", "Citation", "measurements", "citations", "", MAGIC),
]

SPECIMEN_FIELDS = [
    F("Names", "Location", "sites", "location", "", MAGIC, "Via the sample's site"),
    F("Names", "Site", "samples", "site", "", MAGIC),
    F("Names", "Sample", "specimens", "sample", "", MAGIC),
    F("Names", "Specimen", "specimens", "specimen", "", MAGIC),
    F("Position", "Strat. height", "samples", "height", "m", STANDARD_IF_APPLICABLE,
      "Or sites.order for stratigraphic order; sites.core_depth for cores"),
    F("Sample orientation", "Azimuth", "samples", "azimuth", "° of specimen X-axis", STANDARD),
    F("Sample orientation", "Dip", "samples", "dip", "° of X-axis, positive down", STANDARD),
    F("Sample orientation", "Methods", "samples", "method_codes", "SO- codes", MAGIC,
      "Orientation device, e.g. SO-MAG, SO-SUN, SO-SIGHT, SO-GPS-DIFF"),
    F("Bedding", "Dip direction", "samples", "bed_dip_direction", "°", STANDARD_IF_APPLICABLE,
      "Or strike with a stated convention"),
    F("Bedding", "Dip", "samples", "bed_dip", "°", STANDARD_IF_APPLICABLE),
    F("Specimen", "Volume", "specimens", "volume", "cm³ (MagIC: m³)", STANDARD,
      "Or weight (kg)"),
    F("Specimen", "Demag. type", "specimens", "method_codes", "LP-DIR- code", MAGIC,
      "e.g. LP-DIR-T (thermal), LP-DIR-AF (alternating field)"),
    F("Fit", "Component", "specimens", "dir_comp", "", STANDARD),
    F("Fit", "Fit type", "specimens", "method_codes", "DE- code", STANDARD,
      "DE-BFL (free line), DE-BFL-O (line with the origin as a point), DE-BFL-A (line anchored "
      "to the origin), DE-BFP (plane)"),
    F("Fit", "Step min", "specimens", "meas_step_min", "°C or mT (MagIC: K or T)", STANDARD),
    F("Fit", "Step max", "specimens", "meas_step_max", "°C or mT (MagIC: K or T)", STANDARD),
    F("Fit", "n steps", "specimens", "dir_n_measurements", "", STANDARD),
    F("Fit", "MAD", "specimens", "dir_mad_free", "°", STANDARD, "dir_mad_anc if anchored"),
    F("Fit", "DANG", "specimens", "dir_dang", "°", RECOMMENDED),
    F("Specimen coordinates", "Dec", "specimens", "dir_dec", "°", STANDARD,
      "dir_tilt_correction = -1"),
    F("Specimen coordinates", "Inc", "specimens", "dir_inc", "°", STANDARD,
      "dir_tilt_correction = -1"),
    F("Geographic coordinates", "Dec", "specimens", "dir_dec", "°", STANDARD,
      "dir_tilt_correction = 0"),
    F("Geographic coordinates", "Inc", "specimens", "dir_inc", "°", STANDARD,
      "dir_tilt_correction = 0"),
    F("Tilt-corrected coordinates", "Dec", "specimens", "dir_dec", "°", STANDARD,
      "dir_tilt_correction = 100"),
    F("Tilt-corrected coordinates", "Inc", "specimens", "dir_inc", "°", STANDARD,
      "dir_tilt_correction = 100"),
    F("Result", "Used in site mean", "specimens", "result_quality", "g = included, b = excluded",
      STANDARD, "Keep excluded fits, marked b"),
    F("Result", "Reason / note", "specimens", "description", "", STANDARD_IF_APPLICABLE,
      "Reason for exclusion, for excluded specimens"),
    F("Result", "Software", "specimens", "software_packages", "", STANDARD,
      "Fit definitions differ between programs"),
    F("Source", "Citation", "specimens", "citations", "", MAGIC, "Also required in samples"),
]

SITE_FIELDS = [
    F("Names", "Location", "sites", "location", "", MAGIC, "Links the sites to the pole"),
    F("Names", "Site", "sites", "site", "", MAGIC),
    F("Geology", "Geologic class", "sites", "geologic_classes", "controlled vocabulary", MAGIC),
    F("Geology", "Geologic type", "sites", "geologic_types", "controlled vocabulary", MAGIC),
    F("Geology", "Lithology", "sites", "lithologies", "controlled vocabulary", MAGIC),
    F("Position", "Lat", "sites", "lat", "°N", MAGIC),
    F("Position", "Lon", "sites", "lon", "°E (0–360)", MAGIC),
    F("Position", "Strat. height", "sites", "height", "m", STANDARD_IF_APPLICABLE),
    F("Age", "Age", "sites", "age", "", MAGIC, "Or age_low and age_high"),
    F("Age", "Age min", "sites", "age_low", "", MAGIC, "Or age"),
    F("Age", "Age max", "sites", "age_high", "", MAGIC, "Or age"),
    F("Age", "Unit", "sites", "age_unit", "", MAGIC),
    F("Age", "Age methods", "ages", "method_codes", "GM- codes", MAGIC, "In the ages table"),
    F("Bedding", "Dip direction", "sites", "bed_dip_direction", "°", STANDARD_IF_APPLICABLE),
    F("Bedding", "Dip", "sites", "bed_dip", "°", STANDARD_IF_APPLICABLE),
    F("Mean", "Component", "sites", "dir_comp_name", "", STANDARD),
    F("Mean", "n lines", "sites", "dir_n_specimens_lines", "", STANDARD),
    F("Mean", "n planes", "sites", "dir_n_specimens_planes", "", STANDARD),
    F("Geographic coordinates", "Dec", "sites", "dir_dec", "°", STANDARD,
      "dir_tilt_correction = 0"),
    F("Geographic coordinates", "Inc", "sites", "dir_inc", "°", STANDARD,
      "dir_tilt_correction = 0"),
    F("Tilt-corrected coordinates", "Dec", "sites", "dir_dec", "°", STANDARD,
      "dir_tilt_correction = 100"),
    F("Tilt-corrected coordinates", "Inc", "sites", "dir_inc", "°", STANDARD,
      "dir_tilt_correction = 100"),
    F("Statistics", "k", "sites", "dir_k", "", STANDARD),
    F("Statistics", "α95", "sites", "dir_alpha95", "°", STANDARD),
    F("Statistics", "R", "sites", "dir_r", "", RECOMMENDED, "From n and k"),
    F("VGP", "Polarity", "sites", "dir_polarity", "n, r, t, e", STANDARD),
    F("VGP", "VGP lat", "sites", "vgp_lat", "°N", STANDARD),
    F("VGP", "VGP lon", "sites", "vgp_lon", "°E", STANDARD),
    F("VGP", "dp", "sites", "vgp_dp", "°", RECOMMENDED),
    F("VGP", "dm", "sites", "vgp_dm", "°", RECOMMENDED),
    F("Result", "Methods", "sites", "method_codes", "method codes", MAGIC),
    F("Source", "Citation", "sites", "citations", "", MAGIC),
]

LOCATION_FIELDS = [
    F("Names", "Location", "locations", "location", "", MAGIC),
    F("Names", "Result name", "locations", "result_name", "", STANDARD),
    F("Names", "Location type", "locations", "location_type", "controlled vocabulary", MAGIC),
    F("Geology", "Geologic class", "locations", "geologic_classes", "controlled vocabulary",
      MAGIC),
    F("Geology", "Lithology", "locations", "lithologies", "controlled vocabulary", MAGIC),
    F("Study region bounds", "Lat S", "locations", "lat_s", "°N", MAGIC),
    F("Study region bounds", "Lat N", "locations", "lat_n", "°N", MAGIC),
    F("Study region bounds", "Lon W", "locations", "lon_w", "°E", MAGIC),
    F("Study region bounds", "Lon E", "locations", "lon_e", "°E", MAGIC),
    F("Age", "Age", "locations", "age", "", MAGIC, "Or age_low and age_high"),
    F("Age", "Age min", "locations", "age_low", "", MAGIC, "Or age"),
    F("Age", "Age max", "locations", "age_high", "", MAGIC, "Or age"),
    F("Age", "Unit", "locations", "age_unit", "", MAGIC),
    F("Pole", "Component", "locations", "pole_comp_name", "", STANDARD),
    F("Pole", "Sites used", "locations", "sites", "colon-delimited", STANDARD),
    F("Pole", "N", "locations", "pole_n_sites", "", STANDARD),
    F("Pole", "Coord.", "locations", "dir_tilt_correction", "%", STANDARD,
      "Coordinates of the site directions averaged"),
    F("Pole", "Plat", "locations", "pole_lat", "°N", STANDARD),
    F("Pole", "Plon", "locations", "pole_lon", "°E", STANDARD),
    F("Pole", "K", "locations", "pole_k", "", STANDARD),
    F("Pole", "A95", "locations", "pole_alpha95", "°", STANDARD),
    F("Pole", "Ellipse", "locations", "pole_conf", "colon-delimited", STANDARD_IF_APPLICABLE,
      "Non-Fisherian distributions, e.g. a Kent (1982) ellipse; or pole_dp, pole_dm"),
    F("Pole", "North / south", "locations", "dir_polarity", "n = north, r = south", RECOMMENDED,
      "Which pole is reported"),
    F("Pole", "Paleolatitude", "locations", "paleolat", "°N", RECOMMENDED,
      "At the sampling location"),
    F("Directions at sampling location", "Dec", "locations", "dir_dec", "°", STANDARD,
      "Mean direction at the sampling location"),
    F("Directions at sampling location", "ΔDx", "locations", "", "°", STANDARD,
      "Declination uncertainty from A95 (Butler, 1992); no MagIC column"),
    F("Directions at sampling location", "Inc", "locations", "dir_inc", "°", STANDARD),
    F("Directions at sampling location", "ΔIx", "locations", "", "°", STANDARD,
      "Inclination uncertainty from A95 (Butler, 1992); no MagIC column"),
    F("Flattening", "f", "locations", "pole_flattening", "", STANDARD_IF_APPLICABLE,
      "1.0 = no flattening; method as a code, e.g. DA-DIR-FLAT-EI, DA-DIR-FLAT-SVEI"),
    F("Flattening", "f low", "locations", "pole_flat_low", "", STANDARD_IF_APPLICABLE,
      "Confidence level of the bounds as a code, e.g. SM-BOOT-95"),
    F("Flattening", "f high", "locations", "pole_flat_high", "", STANDARD_IF_APPLICABLE),
    F("Flattening", "Inc", "locations", "dir_inc", "°", RECOMMENDED,
      "Mean inclination; required by MagIC with the corrected-inclination bounds"),
    F("Flattening", "Corr. inc low", "locations", "dir_inc_flat_low", "°", RECOMMENDED),
    F("Flattening", "Corr. inc high", "locations", "dir_inc_flat_high", "°", RECOMMENDED),
    F("Field tests", "Reversal", "locations", "reversal_test", "controlled vocabulary",
      RECOMMENDED, "Describe field tests in the text"),
    F("Field tests", "Reversed %", "locations", "pole_reversed_perc", "%", RECOMMENDED),
    F("Field tests", "Fold", "locations", "fold_test", "controlled vocabulary", RECOMMENDED),
    F("Field tests", "Conglomerate", "locations", "conglomerate_test", "controlled vocabulary",
      RECOMMENDED),
    F("Field tests", "Contact", "locations", "contact_test", "controlled vocabulary", RECOMMENDED),
    F("Tectonics", "Plate / block", "locations", "plate_blocks", "controlled vocabulary",
      RECOMMENDED, "Depends on the plate model; determinable from the coordinates"),
    F("Result", "Methods", "locations", "method_codes", "method codes", MAGIC,
      "Required without a sites table"),
    F("Source", "Citation", "locations", "citations", "", MAGIC,
      "Required without a sites table"),
]

AGE_FIELDS = [
    F("Names", "Location", "ages", "location", "", MAGIC, "One of location, site, sample, specimen"),
    F("Names", "Site", "ages", "site", "", MAGIC, "One of location, site, sample, specimen"),
    F("Age", "Age", "ages", "age", "", RECOMMENDED),
    F("Age", "Age ±", "ages", "age_sigma", "", RECOMMENDED, "Uncertainty of age"),
    F("Age", "Age min", "ages", "age_low", ""),
    F("Age", "Age max", "ages", "age_high", ""),
    F("Age", "Unit", "ages", "age_unit", ""),
    F("Age", "Methods", "ages", "method_codes", "GM- codes", MAGIC),
    F("Age", "Timescale", "ages", "timescale_citations", "", STANDARD_IF_APPLICABLE,
      "If a timescale is used"),
    F("Age", "Basis / note", "ages", "description", "", RECOMMENDED,
      "What is dated and how it relates to the site or location"),
    F("Source", "Citation", "ages", "citations", "", MAGIC),
]

SHEETS = OrderedDict([
    ("Contribution", CONTRIBUTION_FIELDS),
    ("1 Measurements", MEASUREMENT_FIELDS),
    ("2 Specimen directions", SPECIMEN_FIELDS),
    ("3 Site means", SITE_FIELDS),
    ("4 Poles", LOCATION_FIELDS),
    ("5 Ages", AGE_FIELDS),
])
