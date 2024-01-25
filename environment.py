from re import finditer, sub
from typing import Optional
from textwrap import indent as indent_, dedent

class LatexDocument:
    def __init__(self, document, cfg):
        self.document = document
        self.cfg = cfg
    
    def __getattr__(self, __value):
        cfg = self.cfg
        if hasattr(cfg, __value):
            return getattr(cfg, __value)
        return super().__getattr__(__value)
    
    def __str__(self):
        preamble = ""
        preamble += f"\\documentclass{{{self.documentclass}}}\n"
        preamble += "\\usepackage[utf8]{inputenc}\n"
        preamble += "\\usepackage[T1]{fontenc}\n"
        preamble += "\\usepackage[a4paper]{geometry}\n"
        preamble += "\\usepackage{enumitem}\n"
        for pkg in self.packages:
            preamble += f"\\usepackage{{{pkg}}}\n"
        preamble += f"\\title{{{self.title}}}\n"
        preamble += f"\\author{{{self.author}}}\n"
        preamble += f"\\date{{{self.date}}}\n\n"

        document = f"{preamble}\n\\begin{{document}}\n\n" +\
                   f"\\maketitle\n{self.document}\n\n\\end{{document}}"

        return document

class LatexEnvironment:
    def __init__(self,
                 name: str,
                 args: Optional[list[str]] = None,
                 content: Optional[str] = "",
                 indent=True,
                 curly=False,
                 newline=True,
                 indent_content=None,
                 indent_arguments=None,
    ):
        self.name = name
        if args is None:
            args = []
        if isinstance(args, str):
            args = [args]
        self.args = args
        self.content = content
        self.indent = self._get_indent(indent, indent_arguments, indent_content)
        self.curly = curly
        self.newline = newline
        self.parse()
    
    @staticmethod
    def _get_indent(default, *args):
        return tuple((arg if arg is not None else default) for arg in args)


    def __str__(self):
        sep = ",\n" if self.newline else ","
        if self.indent[0]:
            sep += " " * (9 + len(self.name))
        args_str = sep.join(list(filter(bool, self.args)))
        if args_str:
            args_str = f"[{args_str}]"
        line_begin = f"\\begin{{{self.name}}}{args_str}"
        line_end = f"\\end{{{self.name}}}"
        content = self.content
        if self.indent[1]:
            content = indent_(content, " "*4)
        return f"{line_begin}\n{content}\n{line_end}\n"
    
    def add_argument(self, argument):
        if isinstance(argument, list):
            self.args.extend(argument)
        else:
            self.args.append(argument)
    
    def parse(self):
        content = self.content
        pattern_texenvarg = r"\[//\]:\s(?:<>|#)\s\(%texenvarg (.*)\)\n"
        for match_ in finditer(pattern_texenvarg, content):
            self.add_argument(match_.groups()[0].split())
        content = sub(pattern_texenvarg, "", content)
        self.content = content.strip()


