# References

The reference list of the manuscript, formatted in AGU style.

```text
references/
├── FAIR_paleomag_refs.bib                 the references cited in the manuscript (BibTeX)
└── reference_list/
    ├── build_reference_list.py            builds the PDF and the Word document
    ├── FAIR_paleomag_references.tex       LaTeX document that typesets the list
    ├── agujournal2019.cls                 AGU journal class
    ├── FAIR_paleomag_references.pdf       reference list (PDF)
    └── FAIR_paleomag_references_AGU.docx  reference list (Word)
```

`FAIR_paleomag_refs.bib` holds the entries tagged `cited-by = {FAIR_paleomag}` in `allrefs.bib` of [Swanson-Hysell-Group/references](https://github.com/Swanson-Hysell-Group/references). The citations are in the Word manuscript, so the .tex includes every entry of the .bib file.

```bash
cd references/reference_list
python build_reference_list.py   # writes the PDF and the .docx
```

The list is typeset with pdflatex and BibTeX using the AGU class (apacite style). For the Word document, the same document is converted to HTML with tex4ht (`make4ht`), so that the formatting still comes from apacite, and pandoc converts the HTML to .docx.

Requires a TeX distribution with `make4ht` and `apacite`, and [pandoc](https://pandoc.org). These are not in the conda environment of the repository.
