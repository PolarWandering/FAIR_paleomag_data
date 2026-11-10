#!/usr/bin/env python3
"""Build the AGU-formatted reference list as a PDF and a Word document.

The reference list is typeset by LaTeX/BibTeX with the AGU journal class
(apacite style) from ``../FAIR_paleomag_refs.bib``. The same document is then
converted to HTML with tex4ht (``make4ht``) so that the formatting is still
produced by apacite rather than re-implemented, and pandoc turns that HTML
into a .docx with hanging-indent reference paragraphs and linked DOIs.

Usage (from any directory)::

    python build_reference_list.py

Requires a TeX distribution with make4ht and apacite, and pandoc.

Outputs, written beside this script:
    FAIR_paleomag_references.pdf
    FAIR_paleomag_references_AGU.docx

Compilation happens in a private temporary directory that is deleted
afterwards. Building inside the repository was unreliable: an editor with
LaTeX auto-build (e.g. VS Code LaTeX Workshop) reacts to the copied files by
running latexmk in the same folder, overwriting the .aux and .bbl mid-build.
"""

import html
import os
import re
import shutil
import subprocess
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
BIB_DIR = os.path.dirname(HERE)  # references/, which holds FAIR_paleomag_refs.bib
BUILD = None  # set in main() to a temporary directory
STEM = 'FAIR_paleomag_references'
DOCX_NAME = STEM + '_AGU.docx'

# Hanging indent of 0.5 inch (720 twips), Times New Roman 12 pt.
BIBLIOGRAPHY_STYLE = (
    '<w:pPr><w:spacing w:before="0" w:after="120" w:line="240" w:lineRule="auto" />'
    '<w:ind w:left="720" w:hanging="720" /></w:pPr>'
    '<w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" '
    'w:cs="Times New Roman" /><w:sz w:val="24" /><w:szCs w:val="24" /></w:rPr>'
)


def run(cmd, env=None):
    """Run a command in the build directory and fail loudly if it errors.

    Args:
        cmd: Command and arguments as a list.
        env: Optional environment mapping.

    Raises:
        subprocess.CalledProcessError: If the command exits non-zero; the
            captured output is printed first so the TeX error is visible.
    """
    result = subprocess.run(cmd, cwd=BUILD, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout[-3000:])
        print(result.stderr[-3000:])
        result.check_returncode()
    return result


def build_pdf(env):
    """Typeset the AGU reference list to PDF with pdflatex and BibTeX."""
    run(['pdflatex', '-interaction=nonstopmode', STEM], env)
    blg = run(['bibtex', STEM], env).stdout
    if 'Warning' in blg or 'error' in blg.lower():
        print(blg)
    for _ in range(2):
        run(['pdflatex', '-interaction=nonstopmode', STEM], env)
    shutil.copy(os.path.join(BUILD, STEM + '.pdf'), HERE)


def build_html(env):
    """Convert the document to HTML with tex4ht, reusing the BibTeX output."""
    run(['make4ht', '-u', STEM, 'html'], env)
    return open(os.path.join(BUILD, STEM + '.html'), encoding='utf-8').read()


def clean_entries(raw_html):
    """Extract each reference from the tex4ht HTML as a clean HTML fragment.

    tex4ht marks italic text with ``cmti`` font classes, which pandoc would
    discard, so those spans are turned into ``<em>``. DOIs are made into links.

    Args:
        raw_html: HTML produced by make4ht.

    Returns:
        List of HTML strings, one per reference, in bibliography order.

    Raises:
        ValueError: If no bibliography items are found.
    """
    items = re.findall(r"<p class='bibitem'>(.*?)</p>", raw_html, re.S)
    if not items:
        raise ValueError('no bibliography items found in the tex4ht HTML')
    entries = []
    for item in items:
        item = re.sub(r"<span class='biblabel'>.*?</span></span>", '', item, flags=re.S)
        item = re.sub(r"<span class='cmti-[^']*'>(.*?)</span>", r'<em>\1</em>', item, flags=re.S)
        unknown = re.findall(r"<span class='([^']*)'", item)
        if unknown:
            raise ValueError('unhandled tex4ht font classes: %s' % ', '.join(sorted(set(unknown))))
        item = re.sub(r'</em>(\s*)<em>', r'\1', item)  # italics split across lines
        item = re.sub(r'\s+', ' ', item).strip()
        item = re.sub(r'(https://doi\.org/[^\s<]+?)(?=\.?(?:\s|$))',
                      lambda m: '<a href="%s">%s</a>' % (html.escape(m.group(1)), m.group(1)), item)
        entries.append(item)
    return entries


def make_reference_docx(path):
    """Write a pandoc reference .docx whose Bibliography style has a hanging indent."""
    default = os.path.join(BUILD, 'pandoc_default_reference.docx')
    subprocess.run(['pandoc', '-o', default, '--print-default-data-file', 'reference.docx'], check=True)
    with zipfile.ZipFile(default) as zin, zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            data = zin.read(info.filename)
            if info.filename == 'word/styles.xml':
                styles = data.decode('utf-8')
                pattern = (r'(<w:style w:type="paragraph" w:styleId="Bibliography">.*?)'
                           r'<w:pPr />\s*<w:rPr />')
                styles, count = re.subn(pattern, r'\1' + BIBLIOGRAPHY_STYLE, styles, flags=re.S)
                if count != 1:
                    raise ValueError('could not locate the Bibliography style in reference.docx')
                data = styles.encode('utf-8')
            zout.writestr(info, data)


def build_docx(entries):
    """Assemble the references as HTML and convert them to .docx with pandoc."""
    body = ['<h1>References</h1>']
    body += ['<div custom-style="Bibliography"><p>%s</p></div>' % e for e in entries]
    # No <title>: pandoc would otherwise render the heading as a Title paragraph.
    page = ('<!DOCTYPE html><html><head><meta charset="utf-8">'
            '</head><body>\n%s\n</body></html>\n' % '\n'.join(body))
    html_path = os.path.join(BUILD, STEM + '_for_pandoc.html')
    open(html_path, 'w', encoding='utf-8').write(page)
    reference_doc = os.path.join(BUILD, 'reference.docx')
    make_reference_docx(reference_doc)
    subprocess.run(['pandoc', html_path, '-f', 'html', '-o', os.path.join(HERE, DOCX_NAME),
                    '--reference-doc', reference_doc], check=True)


def main():
    global BUILD
    with tempfile.TemporaryDirectory(prefix='fair_paleomag_refs_') as build_dir:
        BUILD = build_dir
        for name in (STEM + '.tex', 'agujournal2019.cls'):
            shutil.copy(os.path.join(HERE, name), BUILD)
        env = dict(os.environ, BIBINPUTS=BIB_DIR + os.pathsep)
        build_pdf(env)
        entries = clean_entries(build_html(env))
        build_docx(entries)
    print('%d references -> %s and %s' % (len(entries), STEM + '.pdf', DOCX_NAME))


if __name__ == '__main__':
    main()
