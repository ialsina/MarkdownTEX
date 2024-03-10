#pylint: disable=E0203,E1101

import re
from functools import partial


from mdtex import _expressions as xpr
from .app import App
from .commands import execute
from .environment import LatexEnvironment, LatexDocument

_REGEX_ESCAPE_CHARACTERS = "\\$^.+*"

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
    
    @property
    def escape_characters(self):
        chrlst = list(self.cfg.escape_characters)
        if self.cfg.latex_symb:
            chrlst += ["LaTeX"]
        if "\\" in chrlst:
            chrlst.remove("\\")
            chrlst = ["\\"] + chrlst
        return chrlst

    def sections(self, text):
        cfg = self.cfg
        for i in range(6, 1, -1):
            search = xpr.headers[i]
            replace = rf"\\{cfg.headers[i]}{{\1}}"
            text = re.sub(search, replace, text)
        if cfg.headers[1] != "title":
            text = re.sub(xpr.headers[1], rf"\\{cfg.headers[1]}{{\1}}", text)
        else:
            title_match = re.search(xpr.headers[1], text)
            if title_match is not None:
                cfg.title = title_match.groups()[0] # pylint: disable=W0201
            text = re.sub(xpr.headers[1], "", text)
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

    def _get_shielded_positions_href(self, text, character=None):
        shielded_positions = []
        for match_ in re.finditer(xpr.href, text):
            span = match_.span()
            group = match_.group()
            span_text = (
                span[0] + group.index("[") + 1,
                span[1] + group.index("]")
            )
            span_link = (
                span[0] + group.index("(") + 1,
                span[1] + group.index(")")
            )
            # backslash must be escaped also from link
            if character == "\\":
                shielded_positions.append(span_link)
            shielded_positions.append(span_text)
        return shielded_positions

    def _get_shielded_positions(self, text, character=None):
        shielded_positions = []
        shield_patterns = (
            xpr.comment,
            xpr.block_code,
            xpr.headerany,
        )
        for pattern in shield_patterns:
            for match_ in re.finditer(pattern, text):
                shielded_positions.append(match_.span())
        # Extend with positions coming from hrefs
        shielded_positions.extend(
            self._get_shielded_positions_href(text, character=character)
        )
        return sorted(shielded_positions, key=lambda tup: tup[0])
    
    @staticmethod
    def href(text):
        return re.sub(xpr.href, r"\\href{\2}{\1}", text)
    
    @staticmethod
    def enumerate(text):
        envs_patterns = [
            ("itemize", xpr.list_dash, lambda x: x.lstrip(" -")),
            ("itemize", xpr.list_ast, lambda x: x.lstrip(" *")),
            ("itemize", xpr.list_plus, lambda x: x.lstrip(" +")),
            ("enumerate", xpr.list_num, lambda x: x.split(".", 1)[1])
        ]
        for env, pattern, strip_fun in envs_patterns:
            while True:
                match_ = re.search(pattern, text)
                if match_ is None:
                    break
                start, end = match_.span()
                group = match_.group().strip(" \n")
                content = "\n".join([
                    "\\item " + strip_fun(item).strip(" \n")
                    for item in group.split("\n")
                ])
                texenv = LatexEnvironment(name=env, content=content)
                text = text[:start] + f"\n\n{str(texenv)}\n\n" + text[end:]
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

        # Positions in text to be escaped
        escape_positions = set()
        escape_characters = self.escape_characters
        
        # Populate escape_positins (for all escape characteres)
        for ch in escape_characters:
            # List of spans of verbatims and comments in text
            shield = self._get_shielded_positions(text, ch)
            for match_ in re.finditer(_regex_escape(ch), text):
                pos = match_.start()
                if any(start <= pos < end for start, end in shield):
                    # In shielded position, do not escape
                    continue
                escape_positions.add(pos)

        # Add escape characters where necessary
        # sorted and reversed so that already added escape characters don't mess
        # with the numbering of the rest
        text = list(text)
        for pos in sorted(escape_positions, reverse=True):
            text.insert(pos, "\\")
        return "".join(text)
    
    def break_ligatures(self, text):
        def _break(l, t):
            while l in t:
                t = re.sub(l, f"{l[0]}{{}}{l[1]}", t)
            return t
        cfg = self.cfg
        for lig in cfg.break_ligatures:
            text = _break(_regex_escape(lig), text)
        return text
    
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
    
    def quotation_marks(self, text):

        # pylint: disable=W0101
        quotations_patterns = [
            (("``", "''"), xpr.double_quotations),
            (("`", "'"), xpr.single_quotations),
        ]
        shield = self._get_shielded_positions(text)
        for quotations, pattern in quotations_patterns:
            while True:
                match_ = re.search(pattern, text)
                if match_ is None:
                    break
                start, end = match_.span()
                content = match_.groups()[0]
                if any(s <= start < e for s, e in shield):
                    # In shielded position, do not replace
                    continue
                quotation_text = quotations[0] + content + quotations[1]
                text = text[:start] + quotation_text + text[end:]
        return text
            

    def preamble(self, text):
        return str(LatexDocument(text, self.cfg))

    def parse(self):
        text = self.markdown
        for fun in (
            self.escape,
            self.sections,
            self.inline_code,
            self.environments,
            self.href,
            self.enumerate,
            self.emph,
            self.quotation_marks,
            self.comments,
            self.block_code,
            self.block_quotes,
            self.break_ligatures,
            self.preamble,
        ):
            text = fun(text)
        return text

def _regex_escape(s):
    if len(s) > 1:
        return "".join([_regex_escape(c) for c in s])
    if s in _REGEX_ESCAPE_CHARACTERS:
        return "\\" + s
    return s