#pylint: disable=E0203,E1101

import sys

from mdtex import App, MarkdownParser

def md2tex():
    app = App(sys.argv[1:])

    with open(app.input, "r", encoding="utf-8") as f:
        md_parser = MarkdownParser(f.read(), cfg=app)

    with open(app.output, "w", encoding="utf-8") as f:
        f.write(md_parser.latex)
