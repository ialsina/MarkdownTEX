#pylint: disable=E0203,E1101

import re
from re import DOTALL, MULTILINE
from functools import partial


from mdtex import _expressions as xpr
from .app import App
from .commands import execute
from .environment import LatexEnvironment, LatexDocument

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
    def quote_environment_factory(self):
        cfg = self.cfg
        return partial(
            LatexEnvironment, name=cfg.env["quote"],
            args=cfg.env_args.get("quote"), indent_content=True
        )

    @property
    def latex(self):
        if self._latex is None:
            self._latex = self.parse()
        return self._latex

    def sections(self, text):
        cfg = self.cfg
        text = re.sub(xpr.headersix, rf"\\{cfg.headersix}{{\1}}", text)
        text = re.sub(xpr.headerfive, rf"\\{cfg.headerfive}{{\1}}", text)
        text = re.sub(xpr.headerfour, rf"\\{cfg.headerfour}{{\1}}", text)
        text = re.sub(xpr.headerthree, rf"\\{cfg.headerthree}{{\1}}", text)
        text = re.sub(xpr.headertwo, rf"\\{cfg.headertwo}{{\1}}", text)
        if cfg.headerone != "title":
            text = re.sub(xpr.headerone, rf"\\{cfg.headerone}{{\1}}", text)
        else:
            title_match = re.search(xpr.headerone, text)
            if title_match is not None:
                cfg.title = title_match.groups()[0] # pylint: disable=W0201
            text = re.sub(xpr.headerone, "", text)
        return text
    
    @staticmethod
    def inline_code(text):
        """Inline literal code"""
        text = re.sub(xpr.inline_code, r"\\texttt{\1}", text)
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
        TexEnv = self.code_environment_factory # pylint: disable=C0103
        
        while True:
            match_ = re.search(xpr.block_code, text)
            if match_ is None:
                break
            arg, content = match_.groups()
            start, end = match_.span()
            texenv = TexEnv(content=content)
            if arg:
                texenv.args.append(_convert_arg(arg))
            text = text[:start] + str(texenv) + text[end:]
        return text

    def block_quotes(self, text):
        """Block quotes"""
        TexEnv = self.quote_environment_factory # pylint: disable=C0103

        while True:
            match_ = re.search(xpr.block_quotes, text)
            if match_ is None:
                break
            content, _ = match_.groups()
            content = "\n".join([line.strip("> ") for line in content.split("\n")])
            start, end = match_.span()
            texenv = TexEnv(content=content)
            text = text[:start] + str(texenv) + text[end:]
        return text
        
    def environments(self, text):
        while True:
            match_ = re.search(xpr.environment, text)
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
        for comment in re.finditer(xpr.comment, text):
            shield.append(comment.span())
        # Populate hrefs (only first argument)
        for href in re.finditer(r"\\href\{.+?\}", text, flags=MULTILINE):
            shield.append(href.span())
        return shield
    
    @staticmethod
    def href(text):
        return re.sub(xpr.href, r"\\href{\2}{\1}", text)
    
    @staticmethod
    def enumerate(text):
        envs_patterns = [
            ("itemize", xpr.list_dash, lambda x: x.lstrip("-")),
            ("itemize", xpr.list_ast, lambda x: x.lstrip("*")),
            ("itemize", xpr.list_plus, lambda x: x.lstrip("+")),
            ("enumerate", xpr.list_num, lambda x: x.split(".", 1)[1])
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
        text = re.sub(xpr.emph_3ast, rf"\\{cmd_double}{{\\{cmd_single}{{\1}}}}", text)
        text = re.sub(xpr.emph_3usc, rf"\\{cmd_double}{{\\{cmd_single}{{\1}}}}", text)
        text = re.sub(xpr.emph_2ast, rf"\\{cmd_double}{{\1}}", text)
        text = re.sub(xpr.emph_2usc, rf"\\{cmd_double}{{\1}}", text)
        text = re.sub(xpr.emph_1ast, rf"\\{cmd_single}{{\1}}", text)
        text = re.sub(xpr.emph_1usc, rf"\\{cmd_single}{{\1}}", text)
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
        for comment in re.finditer(xpr.comment, text):
            content = comment.groups()[0]
            position = comment.start()
            if content[0] == "%":
                command, arg = re.match(xpr.comment_cmd, content).groups()
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
            self.block_quotes,
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
