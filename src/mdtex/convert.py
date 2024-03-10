#pylint: disable=E0203,E1101

import sys
import re
from re import DOTALL, MULTILINE
from functools import partial

from mdtex.app import App
from mdtex.commands import execute
from mdtex.environment import LatexEnvironment, LatexDocument


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
            LatexEnvironment, name=cfg.env["verbatim"],
            args=cfg.env_args.get("verbatim"), indent_content=False
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
            if cfg.pkg["fancyvrb"]:
                return f"label={arg}"
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

        env_verbatim = self.cfg.env["verbatim"]

        # Populate verbatims
        # Ignoring case to also capture environment `Verbatim` from package `fancyvrb`
        for verbatim in re.finditer(rf"\\begin{{{env_verbatim}}}.+?\\end{{{env_verbatim}}}", text, flags=DOTALL):
            shield.append(verbatim.span())
        # Populate comments
        for comment in re.finditer(r"\[//\]:\s(?:<>|#)\s\((.*)\)", text):
            shield.append(comment.span())
        # Populate hrefs (only first argument)
        for href in re.finditer(r"\\href\{.+?\}", text, flags=MULTILINE):
            shield.append(href.span())
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
        cmd_double = self.cfg.cmd["double"]
        cmd_single = self.cfg.cmd["single"]
        text = re.sub(r"(?<!\*)\*{3}(\w[^\*\n]*?\w)\*{3}(?!\*)", rf"\\{cmd_double}{{\\{cmd_single}{{\1}}}}", text)
        text = re.sub(r"(?<!_)_{3}(\w[^\_\n]*?\w)_{3}(?!_)",rf"\\{cmd_double}{{\\{cmd_single}{{\1}}}}", text)
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
        if self.cfg.latex_symb:
            escape_characters = list(escape_characters) + ["LaTeX"]

        # Positions in text to be escaped
        escape_positions = set()
        
        # Populate escape_positins (for all escape characteres)
        for ch in escape_characters:
            for match_ in re.finditer(ch, text):
                pos = match_.start()
                if any(start <= pos < end for start, end in shield):
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
    def _to_comment(text):
        return f"% {text}"

    def comments(self, text):
        commands = set()
        for comment in re.finditer(r"\[//\]:\s+(?:<>|#)\s+\((.*)\)", text):
            content = comment.groups()[0]
            position = comment.start()
            if content[0] == "%":
                command, arg = re.match(r"% (\w*)\s*(.*)", content).groups()
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
