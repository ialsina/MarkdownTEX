#pylint: disable=E0203,E1101

import re
from functools import partial
from uuid import uuid4
from warnings import warn
from typing import Sequence, Mapping, Any

from mdtk import _expressions as xpr
from ._exceptions import CommandError
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

    @classmethod
    def _get_shielded_positions_href(cls, text, mask_href_name=False):
        shielded_positions = []
        for match_ in re.finditer(xpr.href, text):
            start, _ = match_.span()
            group = match_.group()
            span_text = (
                start + group.index("[") + 1,
                start + group.index("]")
            )
            span_link = (
                start + group.index("(") + 1,
                start + group.index(")")
            )
            # backslash must be escaped also from link
            if mask_href_name:
                shielded_positions.append(span_link)
            shielded_positions.append(span_text)
        return shielded_positions

    @classmethod
    def _get_shielded_positions(cls, text, mask_href_name=None):
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
            cls._get_shielded_positions_href(text, mask_href_name=mask_href_name)
        )
        return _filter_and_validate_positions(shielded_positions)
    
    @classmethod
    def _shield(cls, text):
        positions = cls._get_shielded_positions(text)
        masked_text = ""
        placeholders = {}
        end_p = 0
        for start, end in positions:
            placeholder = f"<{uuid4()}>"
            shielded_text = text[start:end]
            placeholders[placeholder] = shielded_text
            masked_text += text[end_p:start] + placeholder
            end_p = end
        masked_text += text[end_p:]
        return masked_text, placeholders
    
    @classmethod
    def _unshield(cls, text, placeholders):
        for placeholder, shielded_text in placeholders.items():
            text = re.sub(_regex_escape(placeholder), shielded_text, text)
        return text

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

    @staticmethod
    def _escape(text: str, escape_characters: Sequence[str]):
        escape_positions = set()
        # Populate escape_positins (for all escape characteres)
        for ch in escape_characters:
            # List of spans of verbatims and comments in text
            for match_ in re.finditer(_regex_escape(ch), text):
                pos = match_.start()
                escape_positions.add(pos)
        # Add escape characters where necessary
        # sorted and reversed so that already added escape characters don't mess
        # with the numbering of the rest
        text = list(text)
        for pos in sorted(escape_positions, reverse=True):
            text.insert(pos, "\\")
        return "".join(text)

    @classmethod
    def _escape_placeholders(cls, placeholders: Mapping[Any, str], escape_characters: Sequence[str]):
        for placeholder, value in placeholders.items():
            # Escape characters in titles
            match_ = re.match(xpr.headerany, value)
            if match_ is not None:
                title = match_.groups()[0]
                title_e = cls._escape(title, escape_characters=escape_characters)
                placeholders[placeholder] = re.sub(title, title_e, value)
                continue
            # Escape characters in hrefs
            match_ = re.match(xpr.href, value)
            if match_ is not None:
                name, a = match_.groups()
                name_e = cls._escape(name, escape_characters=escape_characters)
                a_e = cls._escape(a, escape_characters=set(escape_characters).intersection(["\\"]))
                placeholders[placeholder] = re.sub(name, name_e, re.sub(a, a_e, value))
                continue
        return placeholders
    
    def escape(self, text):
        """Escape characters"""
        # Positions in text to be escaped
        escape_characters = self.escape_characters
        text, placeholders = MarkdownParser._shield(text)
        text = self._escape(text, escape_characters=escape_characters)
        placeholders = self._escape_placeholders(placeholders, escape_characters=escape_characters)
        return self._unshield(text, placeholders)
    
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
                match_ = re.match(xpr.comment_cmd, content)
                if match_ is None:
                    raise CommandError(content)
                command, arg = match_.groups()
                args = arg.split()
                commands.add(command)
                try:
                    new_text, cfg = execute(command=command, args=args, text=text, position=position)
                except NotImplementedError:
                    warn(f"Not implemented: '{command}'.")
                text = re.sub(comment.re, new_text, text)
                self.cfg.update(cfg)
            else:
                text = re.sub(comment.re, self._to_comment(content), text)
        return text
    
    def quotation_marks(self, text):
        # pylint: disable=W0101
        quotations_patterns = [
            (("``", "''"), xpr.double_quotations),
            (("`", "'"), xpr.single_quotations),
        ]
        text, key = self._shield(text)
        for quotations, pattern in quotations_patterns:
            while True:
                match_ = re.search(pattern, text)
                if match_ is None:
                    break
                start, end = match_.span()
                content = match_.groups()[0]
                quotation_text = quotations[0] + content + quotations[1]
                text = text[:start] + quotation_text + text[end:]
        return self._unshield(text, key)
            

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

def _filter_and_validate_positions(positions: Sequence[tuple[int, int]]):
    filtered_positions = []
    for start1, end1 in sorted(positions):
        if any(start2 <= start1 <= end1 <= end2 for (start2, end2) in filtered_positions):
            continue
        if any(start2 <= start1 <= end2 <= end1 for (start2, end2) in filtered_positions):
            raise ValueError(
                "One position range partially contains another: "
                "(start1 < start2 < end1 < end2)"
            )
        filtered_positions.append((start1, end1))
    return filtered_positions
