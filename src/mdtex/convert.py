#pylint: disable=E0203,E1101

import sys
import argparse
from pathlib import Path
import re
from re import DOTALL, MULTILINE
from functools import partial

from mdtex.commands import execute
from mdtex.config import config, defaults, PATH_IO
from mdtex.environment import LatexEnvironment, LatexDocument

class App:

    def __init__(self, args=None):
        if args is None:
            args = []
        self.args = self._parse_arguments(args)
        for arg, value in self.args.items():
            setattr(self, arg, value)
        self._postprocess()
    
    def __iter__(self):
        return iter({k: v for k, v in vars(self).items() if k != "args"}.items())

    @classmethod
    def _get_parser(cls):
        # pylint: disable=C0103
        _ON_OFF = ["ON", "OFF"]

        parser = argparse.ArgumentParser()
        parser.add_argument("input", action="store", nargs="?")
        parser.add_argument("-o", "--output", action="store", default=None)
        parser.add_argument("-d", "--documentclass", action="store")
        parser.add_argument("-T", "--title", action="store", default="")
        parser.add_argument("-A", "--author", action="store", default="")
        parser.add_argument("-D", "--date", action="store", default="")
        parser.add_argument("-1", "--header-one-is-title", action="store", choices=_ON_OFF)
        parser.add_argument("-e", "--escape", action="store", dest="escape_characters")
        parser.add_argument("-v", "--verbose", action="store_true")
        parser.add_argument("--use-emph", action="store", nargs='*', choices=["single", "double"], dest="use_emph")
        parser.add_argument("--pkg-fancyvrb", action="store", choices=_ON_OFF)
        parser.add_argument("--pkg-fancyvrb-args", action="store", nargs="*")
        parser.set_defaults(**defaults)
        return parser

    @staticmethod
    def _parse_arguments(args):
        parser = App._get_parser()
        namespace, unknown_args = parser.parse_known_args(args)

        if not namespace.input.lower().endswith(".md"):
            raise ValueError(
                f'Input file "{namespace.input}" must end in ".md"'
            )

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
    def _get_input_path(input_: str):
        path_in = Path(input_)
        if path_in.is_absolute():
            if path_in.exists():
                return path_in
        else:
            if (PATH_IO / path_in).exists:
                return PATH_IO / path_in
        raise FileNotFoundError(
            f"File {input_} not found."
        )

    @staticmethod
    def _get_output_path(output: str, input_path: Path):
        path_in = input_path
        dir_default = (
            path_in.parent
            if config.default_output_dir_as_input_dir
            else Path(".").absolute()
        )
        path_out = (
            Path(output)
            if output is not None
            else None
        )
        if path_out is None:
            name_out = path_in.name
            name_out = name_out.rstrip(path_in.suffix) + ".tex"
            return dir_default / name_out
        if not path_out.is_absolute():
            return dir_default / path_out
        return path_out

    def _postprocess(self):
        self.input = self._get_input_path(self.input)
        self.output = self._get_output_path(self.output, self.input)

        packages = set()
        for k, v in vars(self).items():
            match_ = re.match(r"^pkg_(.+)(?!_args)$", k)
            if match_ is not None and v is True:
                packages.add(match_.groups()[0])
        self.packages = sorted(packages)
    
    def update(self, *args, **kwargs):
        args = tuple(filter(lambda x: x is not None, args))
        if all(isinstance(arg, dict) for arg in args):
            for arg in args:
                kwargs.update(arg)
        else:
            raise TypeError(
                f"Wrong argument type: {[type(el) for el in args]}"
            )
        for key, value in kwargs.items():
            setattr(self, key, value)



class MarkdownParser:

    def __init__(self, markdown, cfg=None, **kwargs):
        self.markdown = markdown
        self._latex = None
        self.cfg = cfg or App()
        for key, value in kwargs.items():
            setattr(cfg, key, value)
    
    @property
    def code_environment_factory(self):
        cfg = self.cfg
        return partial(
            LatexEnvironment, name=cfg.env_verbatim,
            args=cfg.arg_verbatim, indent_content=False
        )

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
        if cfg.headerone != "title":
            text = re.sub(r"^#{1}\s*(.+)\s*$", rf"\\{cfg.headerone}{{\1}}", text, flags=MULTILINE)
        else:
            title_match = re.search(r"^#{1}\s*(.+)\s*$", text, flags=MULTILINE)
            if title_match is not None:
                cfg.title = title_match.groups()[0] # pylint: disable=W0201
            text = re.sub(r"^#{1}\s*(.+)\s*$", "", text, flags=MULTILINE)
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
        pattern_enclosing = r"^```(.*?)\n(.*?)\n```$"
        TexEnv = self.code_environment_factory # pylint: disable=C0103
        
        while True:
            match_ = re.search(pattern_enclosing, text, flags=DOTALL+MULTILINE)
            if match_ is None:
                break
            arg, content = match_.groups()
            start, end = match_.span()
            texenv = TexEnv(content=content)
            if arg:
                texenv.args.append(_convert_arg(arg))
            text = text[:start] + str(texenv) + text[end:]
        return text

    def environments(self, text):
        pattern_enclosing = r"\[//\]:\s(?:<>|#)\s\(%texenv begin (.*)\)(.+?)\[//\]:\s(?:<>|#)\s\(%texenv end \1\)"
        while True:
            match_ = re.search(pattern_enclosing, text, flags=DOTALL+MULTILINE)
            if match_ is None:
                break
            name, content = match_.groups()
            start, end = match_.span()
            texenv = LatexEnvironment(name=name, content=content)
            text = text[:start] + str(texenv) + text[end:]
        return text


    def _get_shielded_positions(self, text):
        shield = []

        env_verbatim = self.cfg.env_verbatim

        # Populate verbatims
        # Ignoring case to also capture environment `Verbatim` from package `fancyvrb`
        for verbatim in re.finditer(rf"\\begin{{{env_verbatim}}}.+?\\end{{{env_verbatim}}}", text, flags=DOTALL):
            shield.append(verbatim.span())
        for comment in re.finditer(r"\[//\]:\s(?:<>|#)\s\((.*)\)", text):
            shield.append(comment.span())
        return shield
        
    
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

        # List of spans of verbatims and comments in text
        shield = self._get_shielded_positions(text)

        escape_characters = self.cfg.escape_characters

        # Positions in text to be escaped
        escape_positions = set()
        
        # Populate escape_positins (for all escape characteres)
        for ch in escape_characters:
            for match_ in re.finditer(ch, text):
                pos = match_.start()
                if any(start <= pos and end > pos for start, end in shield):
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

    @staticmethod
    def _to_comment(text):
        return f"% {text}"

    def comments(self, text):
        commands = set()
        for comment in re.finditer(r"\[//\]:\s(?:<>|#)\s\((.*)\)", text):
            content = comment.groups()[0]
            position = comment.start()
            if content[0] == "%":
                command, arg = re.match(r"%(\w*)\s*(.*)", content).groups()
                args = arg.split()
                commands.add(command)
                new_text, cfg = execute(command=command, args=args, text=text, position=position)
                text = re.sub(comment.re, new_text, text)
                self.cfg.update(cfg)
            else:
                text = re.sub(comment.re, MarkdownParser._to_comment(content), text)
        return text
    
    def preamble(self, text):
        return str(LatexDocument(text, self.cfg))

    def parse(self):
        text = self.markdown
        for fun in (
            self.sections,
            self.inline_code,
            self.block_code,
            self.environments,
            self.href,
            self.enumerate,
            self.emph,
            self.escape,
            self.comments,
            self.latex_symb,
            self.preamble,
        ):
            text = fun(text)
        return text


if __name__ == "__main__":

    app = App(sys.argv[1:])

    with open(app.input, "r", encoding="utf-8") as f:
        md_parser = MarkdownParser(f.read(), cfg=app)

    with open(app.output, "w", encoding="utf-8") as f:
        f.write(md_parser.latex)
