"""Reading, writing and validating MagIC 3.0 contributions.

The data model, method codes and controlled vocabularies in resources/ were
downloaded on 2026-10-23 from https://earthref.org/MagIC/data-models/3.0.json,
https://www2.earthref.org/MagIC/method-codes.json and the EarthRef controlled
vocabularies.
"""

import json
import re
from collections import OrderedDict
from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd

from fair_template.definition import SHEETS

RESOURCES = Path(__file__).resolve().parent / "resources"
DATA_MODEL_FILE = RESOURCES / "magic_data_model_3.0_2026-10-22.json"
METHOD_CODES_FILE = RESOURCES / "magic_method_codes_2026-10-22.json"
VOCABULARIES_FILE = RESOURCES / "earthref_controlled_vocabularies.json"


def is_blank(value):
    return value is None or (isinstance(value, float) and np.isnan(value)) or \
        str(value).strip() in ("", "N/A", "NA", "n/a", "…", "...")


def filled(value):
    return not is_blank(value)


def num(value):
    """A value as a float, or None if it is not a number."""
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    return None if np.isnan(x) else x


def tilt_codes(df):
    """dir_tilt_correction as '-1', '0', '100' or None."""
    tc = pd.to_numeric(df["dir_tilt_correction"], errors="coerce")
    return tc.map(lambda x: None if np.isnan(x) else str(int(x)))


def read_contribution(path):
    """A MagIC contribution file as {table: DataFrame of object columns}."""
    tables = OrderedDict()
    for block in Path(path).read_text(encoding="utf-8").split(">>>>>>>>>>"):
        lines = block.strip("\r\n").splitlines()
        if len(lines) < 2:
            continue
        name = lines[0].split("\t")[1].strip()
        df = pd.read_csv(StringIO("\n".join(lines[1:])), sep="\t", dtype=object,
                         keep_default_na=False, na_values=[""])
        if "dir_tilt_correction" in df:
            df["dir_tilt_correction"] = tilt_codes(df)
        tables[name] = df
    return tables


def write_magic_text(contribution, tables, path):
    """A MagIC contribution file (tab delimited, one block per table)."""
    blocks = [("contribution", contribution)] + list(tables.items())
    text = "\n>>>>>>>>>>\n".join(
        f"tab delimited\t{name}\n" + df.dropna(axis=1, how="all").to_csv(sep="\t", index=False)
        .rstrip("\n") for name, df in blocks)
    Path(path).write_text(text + "\n")


def load_resources():
    """The MagIC data model, the controlled vocabularies and the set of method codes."""
    dm = json.load(open(DATA_MODEL_FILE, encoding="utf-8-sig"))
    cv_raw = json.load(open(VOCABULARIES_FILE, encoding="utf-8-sig"))
    vocab = {}
    for key, value in cv_raw.items():
        items = value.get("items", value) if isinstance(value, dict) else value
        if isinstance(items, list):
            vocab[key] = {str(i["item"] if isinstance(i, dict) and "item" in i else i)
                          for i in items}
    codes = set()

    def walk(obj):
        if isinstance(obj, dict):
            if isinstance(obj.get("code"), str):
                codes.add(obj["code"])
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)
    walk(json.load(open(METHOD_CODES_FILE, encoding="utf-8-sig")))
    return dm, vocab, codes


def method_code_definitions():
    """{method code: MagIC definition}."""
    defs = {}
    for group in json.load(open(METHOD_CODES_FILE, encoding="utf-8-sig")).values():
        for c in group["codes"]:
            defs[c["code"]] = c.get("definition", "")
    return defs


def validate(tables, dm, vocab, method_codes):
    """Check required fields, vocabularies, ranges, method codes and links."""
    problems = []
    for table, df in tables.items():
        model = dm["tables"][table]["columns"]
        for col in df.columns:
            if col not in model:
                problems.append(f"{table}: column '{col}' is not in the data model.")
        for col, spec in model.items():
            for rule in spec.get("validations") or []:
                name, arg = re.match(r"(\w+)\((.*)\)", rule).groups()
                args = [a.strip().strip('"') for a in arg.split(",")] if arg else []
                for i, row in df.iterrows():
                    label = f"{table} row {i + 1} ({row.iloc[0]})"
                    value = row.get(col)
                    if name == "required" or name.startswith("requiredUnlessSynthetic"):
                        if not filled(value):
                            problems.append(f"{label}: required '{col}' is empty.")
                    elif name == "requiredUnless":
                        if not filled(value) and not all(filled(row.get(a)) for a in args):
                            problems.append(f"{label}: '{col}' is required unless {args} "
                                            "are given.")
                    elif name == "requiredUnlessTable":
                        if not filled(value) and args[0] not in tables:
                            problems.append(f"{label}: '{col}' is required without a "
                                            f"{args[0]} table.")
                    elif name == "requiredIf":
                        if not filled(value) and filled(row.get(args[0])):
                            problems.append(f"{label}: '{col}' is required when "
                                            f"'{args[0]}' is given.")
                    elif not filled(value):
                        continue
                    elif name == "cv" and args[0] in vocab:
                        for item in str(value).split(":"):
                            if item not in vocab[args[0]]:
                                problems.append(f"{label}: '{item}' is not in the '{args[0]}' "
                                                f"vocabulary ({col}).")
                    elif name in ("min", "max"):
                        x = num(value)
                        # limits are numbers or other columns, e.g. max("lat_n")
                        limit = num(args[0]) if num(args[0]) is not None else num(row.get(args[0]))
                        if x is not None and limit is not None and \
                                ((name == "min" and x < limit) or (name == "max" and x > limit)):
                            problems.append(f"{label}: {col} = {value} violates {rule}.")
                    elif name == "in":
                        ref_table, ref_col = args[0].split(".")
                        refs = set(tables[ref_table][ref_col]) if ref_table in tables else set()
                        for item in str(value).split(":"):
                            if item not in refs:
                                problems.append(f"{label}: '{item}' ({col}) not found in "
                                                f"{args[0]}.")
        if "method_codes" in df.columns:
            for i, value in df["method_codes"].items():
                for code in str(value).split(":") if filled(value) else []:
                    if code not in method_codes:
                        problems.append(f"{table} row {i + 1}: unknown method code '{code}'.")
    # links between levels
    links = [("specimens", "sample", "samples", "sample"),
             ("samples", "site", "sites", "site"),
             ("sites", "location", "locations", "location")]
    for child, col, parent, pcol in links:
        if child in tables and parent in tables:
            missing = set(tables[child][col].dropna()) - set(tables[parent][pcol])
            for m in sorted(missing):
                problems.append(f"{child}: {col} '{m}' has no row in {parent}.")
    return list(OrderedDict.fromkeys(problems))


def coverage(dm):
    """MagIC-required columns that the template covers, and those it misses."""
    template = {(f.table, f.column) for fields in SHEETS.values() for f in fields}
    # geology and coordinates, which MagIC also requires in samples and specimens, are
    # entered once at site level (a site is one unit); the MagIC form fills them down
    geology = ("geologic_classes", "geologic_types", "lithologies")
    template |= {("specimens", c) for c in geology}
    template |= {("samples", c) for c in geology + ("lat", "lon", "citations", "sample")}
    missing, covered = [], []
    skip_prefix = ("int_",)   # intensity columns: required only if their sigma is given
    for table in ("contribution", "locations", "sites", "samples", "specimens", "measurements",
                  "ages"):   # criteria: not used by this standard
        columns = dm["tables"][table]["columns"]
        for col, spec in columns.items():
            rules = [v for v in (spec.get("validations") or []) if v.startswith("required")]
            if not rules or col.startswith(skip_prefix) or \
                    rules[0].startswith("requiredUnlessNatural"):
                continue
            if rules[0].startswith("requiredOneInGroup"):
                # e.g. ages: one of location, site, sample or specimen
                group = rules[0].split('"')[1]
                members = [c for c, s in columns.items() if any(
                    v == f'requiredOneInGroup("{group}")' for v in s.get("validations") or [])]
                ok = any((table, c) in template for c in members)
            else:
                ok = (table, col) in template
            (covered if ok else missing).append(f"{table}.{col}")
    return covered, missing
