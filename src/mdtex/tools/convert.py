#pylint: disable=E0203,E1101

import sys
import subprocess

from mdtk import App, MarkdownParser

def md2tex(app: App):
    with open(app.input, "r", encoding="utf-8") as f:
        md_parser = MarkdownParser(f.read(), cfg=app)
    with open(app.output, "w", encoding="utf-8") as f:
        f.write(md_parser.latex)
    return 0

def md2pdf(app: App):
    md2tex(app)
    output = app.output
    subprocess.run(["pdflatex", app.output], check=False)
    files_to_clean = [output.parent / (output.stem + ext)
                      for ext
                      in (".aux", ".log", ".out", ".toc")
                      ]
    subprocess.run(["rm"] + files_to_clean, check=False)
    subprocess.run(["evince", output.parent / (output.stem + ".pdf")], check=False)
    return 0
    
def mdtk():
    app = App(sys.argv[1:])
    if app.type == "tex":
        return md2tex(app)
    if app.type == "pdf":
        return md2pdf(app)
    return 1
