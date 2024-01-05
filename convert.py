import re
from re import DOTALL, MULTILINE, IGNORECASE
from textwrap import indent

ESCAPE_CHARACTERS = "_%&"

def _m2l_sections(text):
    text = re.sub(r"^#{4}\s*(.+)\s*$", r"\\subsection{\1}", text, flags=MULTILINE)
    text = re.sub(r"^#{3}\s*(.+)\s*$", r"\\section{\1}", text, flags=MULTILINE)
    text = re.sub(r"^#{2}\s*(.+)\s*$", r"\\chapter{\1}", text, flags=MULTILINE)
    text = re.sub(r"^#{1}\s*(.+)\s*$", r"", text, flags=MULTILINE)
    return text

def _m2l_code(text):
    # Inline literal code
    text = re.sub(r"(?<![`\\])`([^`]+?)(?<!\\)`(?!`)", r"\\texttt{\1}", text)
    
    # Block literal code
    pattern = r"^```\n(.*?)\n```$"
    replace = "\\begin{{verbatim}}\n{}\n\\end{{verbatim}}\n"
    while True:
        match_ = re.search(pattern, text, flags=DOTALL+MULTILINE)
        if match_ is None:
            break
        start, end = match_.span()
        content = match_.groups()[0]
        text = text[:start] + replace.format(indent(content, " "*4)) + text[end:]
    return text

def _m2l_href(text):
    return re.sub(r"\[(.+?)\]\((.+?)\)", r"\\href{\2}{\1}", text)

def _m2l_enumerate(text):
    pattern = r"\n(-\s*.*?\n)+\n"
    replace = "\n\\begin{{itemize}}\n{}\n\\end{{itemize}}\n"
    while True:
        match_ = re.search(pattern, text, flags=MULTILINE)
        if match_ is None:
            break
        start, end = match_.span()
        content = "\n".join(["\\item " + item.strip("-").strip() for item in match_.group().strip().split("\n")])
        text = text[:start] + replace.format(indent(content, " "*4)) + text[end:]
    return text

def _m2l_emph(text):
    text = re.sub(r"(?<!\*)\*{2}(\w[^\*\n]*?\w)\*{2}(?!\*)", r"\\emph{\1}", text)
    text = re.sub(r"(?<!\*)\*{1}(\w[^\*\n]*?\w)\*{1}(?!\*)", r"\\emph{\1}", text)
    return text
    
def _escape(text):
    # List of spans of verbatims in text
    verbatims = []

    # Positions in text to be escaped
    escape_positions = set()

    # Populate verbatims
    # Ignoring case to also capture environment `Verbatim` from package `fancyvrb`
    for verbatim in re.finditer(r"\\begin{verbatim}.+?\\end{verbatim}", text, flags=DOTALL+IGNORECASE):
        verbatims.append(verbatim.span())

    # Populate escape_positins (for all escape characteres)
    for ch in ESCAPE_CHARACTERS:
        for match_ in re.finditer(ch, text):
            pos = match_.start()
            if any(start <= pos and end > pos for start, end in verbatims):
                # In verbatim, do not escape
                continue
            escape_positions.add(pos)

    # Add escape characters where necessary
    # sorted and reversed so that already added escape characters don't mess
    # with the numbering of the rest
    text = list(text)
    for pos in sorted(escape_positions, reverse=True):
        text.insert(pos, "\\")
    
    return "".join(text)

def markdown_to_latex(text):
    text = _m2l_sections(text)
    text = _m2l_code(text)
    text = _m2l_href(text)
    text = _m2l_enumerate(text)
    text = _m2l_emph(text)
    text = _escape(text)
    return text


if __name__ == "__main__":
    with open("input.md", "r") as f:
        text = f.read()

    with open("output.txt", "w") as f:
        f.write(markdown_to_latex(text))
