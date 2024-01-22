#pylint: disable=E0203,E1101

import sys
import argparse
import re
from re import DOTALL, MULTILINE, IGNORECASE
from textwrap import indent, dedent
import yaml
from typing import Optional

class App:

    def __init__(self, args=None):
        if args is None:
            args = []
        self.args = self._parse_arguments(args)
        for arg, value in self.args.items():
            setattr(self, arg, value)
    
    @classmethod
    def _get_parser(cls):
        # pylint: disable=C0103
        _ON_OFF = ["ON", "OFF"]

        parser = argparse.ArgumentParser()
        parser.add_argument("input", action="store", nargs="?")
        parser.add_argument("-o", "--output", action="store", default=None)
        parser.add_argument("-d", "--documentclass", action="store")
        parser.add_argument("-t", "--header-one-is-title", action="store", choices=_ON_OFF)
        parser.add_argument("-e", "--escape", action="store", dest="escape_characters")
        parser.add_argument("-v", "--verbose", action="store_true")
        parser.add_argument("--use-emph", action="store", nargs='*', choices=["single", "double"], dest="use_emph")
        parser.add_argument("--pkg-fancyvrb", action="store", choices=_ON_OFF)
        parser.add_argument("--pkg-fancyvrb-args", action="store", nargs="*")
        parser.set_defaults(**cls._read_defaults())
        return parser

    @staticmethod
    def _parse_arguments(args):
        parser = App._get_parser()
        namespace, unknown_args = parser.parse_known_args(args)

        if not namespace.input.lower().endswith(".md"):
            raise ValueError(
                f'Input file "{namespace.input}" must end in ".md"'
            )
        if namespace.output is None:
            namespace.output = namespace.input[:-3] + '.tex'

        for key, value in vars(namespace).items():
            if value == "ON":
                setattr(namespace, key, True)
            elif value == "OFF":
                setattr(namespace, key, False)
        
        namespace.cmd_single = ("emph" if "single" in namespace.use_emph else "textit")
        namespace.cmd_double = ("emph" if "double" in namespace.use_emph else "textbf")
        namespace.env_verbatim = ("Verbatim" if namespace.pkg_fancyvrb else "verbatim")
        namespace.arg_verbatim = (namespace.pkg_fancyvrb_args if namespace.pkg_fancyvrb else [])

        # TODO Confuses, e.g. --headerthree with "input"...
        headers_args, _ = App._parse_headers(namespace.documentclass,
                                             namespace.header_one_is_title,
                                             unknown_args,
        )

        args = vars(namespace)
        args.update(vars(headers_args))

        return args
    
    @staticmethod
    def _parse_headers(document_class, header_one_is_title, args):
        numbers = ("zero", "one", "two", "three", "four", "five", "six")
        default_headers = (
            "part",
            "chapter",
            "section",
            "subsection",
            "subsubsection",
            "paragraph",
            "subparagraph",
            "subparagraph",
        )
        offset = 0
        if header_one_is_title:
            offset -= 1
        if document_class == "book":
            offset += -1
        elif document_class == "report":
            offset += 0
        elif document_class == "article":
            offset += 1
        else:
            raise ValueError(
                f"Wrong value for document class: {document_class}."
            )
        parser = argparse.ArgumentParser()
        parser.add_argument("--headerone",
                            action="store",
                            nargs=1,
                            default=("title"
                                     if header_one_is_title
                                     else default_headers[1 + offset]
                            ),
        )

        for i in range(2, 7):
            parser.add_argument(f"--header{numbers[i]}",
                                action="store",
                                nargs=1,
                                default=default_headers[i + offset]
            )
        return parser.parse_known_args(args)


    
        
    @staticmethod
    def _read_defaults():
        with open("defaults.yaml", "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

class LatexEnvironment:
    def __init__(self,
                 name: str,
                 args: Optional[list[str]] = None,
                 content: Optional[str] = "",
                 indent=True,
                 curly=False,
                 newline=True):
        self.name = name
        if args is None:
            args = []
        if isinstance(args, str):
            args = [args]
        self.args = args
        self.content = content
        self.indent = indent
        self.curly = curly
        self.newline = newline

    def __str__(self):
        sep = ",\n" if self.newline else ","
        if self.indent:
            sep += " " * (9 + len(self.name))
        args_str = sep.join(list(filter(bool, self.args)))
        if args_str:
            args_str = f"[{args_str}]"
        line_begin = f"\\begin{{{self.name}}}{args_str}"
        line_end = f"\\end{{{self.name}}}"
        content = self.content if not self.indent else indent(self.content, " "*4)
        return f"{line_begin}\n{content}\n{line_end}\n"


class MarkdownParser:

    def __init__(self, markdown, cfg=None):
        self.markdown = markdown
        self.cfg = cfg or App()
        self._latex = None
    
    @property
    def latex(self):
        if self._latex is None:
            self._latex = self.parse()
        return self._latex

    def sections(self, text):
        cfg = self.cfg
        text = re.sub(r"^#{6}\s*(.+)\s*$", rf"\\{cfg.headersix}{{\1}}", text, flags=MULTILINE)
        text = re.sub(r"^#{5}\s*(.+)\s*$", rf"\\{cfg.headerfive}{{\1}}", text, flags=MULTILINE)
        text = re.sub(r"^#{4}\s*(.+)\s*$", rf"\\{cfg.headerfour}{{\1}}", text, flags=MULTILINE)
        text = re.sub(r"^#{3}\s*(.+)\s*$", rf"\\{cfg.headerthree}{{\1}}", text, flags=MULTILINE)
        text = re.sub(r"^#{2}\s*(.+)\s*$", rf"\\{cfg.headertwo}{{\1}}", text, flags=MULTILINE)
        text = re.sub(r"^#{1}\s*(.+)\s*$", rf"\\{cfg.headerone}{{\1}}", text, flags=MULTILINE)
        return text
    
    @staticmethod
    def inline_code(text):
        """Inline literal code"""
        text = re.sub(r"(?<![`\\])`([^`]+?)(?<!\\)`(?!`)", r"\\texttt{\1}", text)
        return text
    
    def block_code(self, text):
        """Block literal code"""
        def _convert_arg(arg):
            if arg == "":
                return arg
            if cfg.pkg_fancyvrb:
                return f"label={arg}"
            else:
                return ""

        cfg = self.cfg
        pattern = r"^```(.*?)\n(.*?)\n```$"
        texenv = LatexEnvironment(cfg.env_verbatim, args=cfg.arg_verbatim)
        while True:
            match_ = re.search(pattern, text, flags=DOTALL+MULTILINE)
            if match_ is None:
                break
            start, end = match_.span()
            arg, content = match_.groups()
            texenv.args.append(_convert_arg(arg))
            texenv.content = content
            text = text[:start] + str(texenv) + text[end:]
        return text
    
    @staticmethod
    def href(text):
        return re.sub(r"\[(.+?)\]\((.+?)\)", r"\\href{\2}{\1}", text)
    
    @staticmethod
    def enumerate(text):
        envs_patterns = [
            ("itemize", r"\n(-\s*.*?\n)+\n", lambda x: x.lstrip("-")),
            ("itemize", r"\n(\*\s*.*?\n)+\n", lambda x: x.lstrip("*")),
            ("itemize", r"\n(\+\s*.*?\n)+\n", lambda x: x.lstrip("+")),
            ("enumerate", r"\n(\d+\.\s*.*?\n)+\n", lambda x: x.split(".", 1)[1])
        ]
        for env, pattern, strip_fun in envs_patterns:
            while True:
                match_ = re.search(pattern, text, flags=MULTILINE)
                if match_ is None:
                    break
                start, end = match_.span()
                content = "\n".join([
                    "\\item " + strip_fun(item).strip()
                    for item in match_.group().strip().split("\n")
                ])
                texenv = LatexEnvironment(name=env, content=content)
                text = text[:start] + f"\n{str(texenv)}\n" + text[end:]
        return text
    
    def emph(self, text):
        cmd_double = self.cfg.cmd_double
        cmd_single = self.cfg.cmd_single
        text = re.sub(r"(?<!\*)\*{2}(\w[^\*\n]*?\w)\*{2}(?!\*)", rf"\\{cmd_double}{{\1}}", text)
        text = re.sub(r"(?<!_)_{2}(\w[^\_\n]*?\w)_{2}(?!_)", rf"\\{cmd_double}{{\1}}", text)
        text = re.sub(r"(?<!\*)\*{1}(\w[^\*\n]*?\w)\*{1}(?!\*)", rf"\\{cmd_single}{{\1}}", text)
        text = re.sub(r"(?<!_)_{1}(\w[^\*\n]*?\w)_{1}(?!_)", rf"\\{cmd_single}{{\1}}", text)
        return text
    
    def escape(self, text):
        """Escape characters"""

        # List of spans of verbatims in text
        verbatims = []

        env_verbatim = self.cfg.env_verbatim
        escape_characters = self.cfg.escape_characters

        # Positions in text to be escaped
        escape_positions = set()

        # Populate verbatims
        # Ignoring case to also capture environment `Verbatim` from package `fancyvrb`
        for verbatim in re.finditer(rf"\\begin{env_verbatim}.+?\\end{env_verbatim}", text, flags=DOTALL+IGNORECASE):
            verbatims.append(verbatim.span())

        # Populate escape_positins (for all escape characteres)
        for ch in escape_characters:
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
    
    @staticmethod
    def latex_symb(text):
        """LaTeX command"""

        return re.sub(r"(?<!\\)LaTeX", r"\\LaTeX", text)

    def parse(self):
        text = self.markdown
        for fun in (
            self.sections,
            self.inline_code,
            self.block_code,
            self.href,
            self.enumerate,
            self.emph,
            self.escape,
            self.latex_symb,
        ):
            text = fun(text)
        return text


if __name__ == "__main__":

    app = App(sys.argv[1:])

    with open(app.input, "r") as f:
        md_parser = MarkdownParser(f.read(), cfg=app)

    md_parser.parse()

    with open(app.output, "w") as f:
        f.write(md_parser.latex)
