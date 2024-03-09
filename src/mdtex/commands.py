
import re
from textwrap import dedent

__all__ = [
    "time", "texenv", "texenvarg", "textag", "execute", "lstcommands"
]

def time(*args, **kwargs):
    return "", {}, None

def texenv(text, position, args):
    raise RuntimeError

def texenvarg(text, position, args):
    raise RuntimeError

def textag(text, position, args):
    raise NotImplementedError(
        dedent("""
            Please, instead of:
            
            ```
            [//] <> (%textag title)
            # MYTITLE
            ```

            use the alternative syntax:
            
            ```
            # MYTITLE
            ```
            with `header_one_is_title` set to `True`.
            """
        )
    )

def _find_line_from_position(text: str, position: int):
    line_breaks = [0] + [i for i, c in enumerate(text) if c == "\n"]
    for line, (start, end) in enumerate(
        zip(line_breaks[:-1], line_breaks[1:]), start=1
    ):
        if position >= start and position < end:
            return line
    raise ValueError(f"Wrong position: {position}")

def _find_line_from_occurence(text: str, occurrence: str):
    for line_num, line_str in enumerate(text.split("\n"), start=1):
        if occurrence in line_str:
            return line_num
    raise ValueError(f"Occurrence not found: {occurrence}")

def _isolate_block(text: str, position: int):
    block_breaks = [0] + [match_.start() for match_ in re.finditer(r"\n\n", text)]
    for start, end in zip(block_breaks[:-1], block_breaks[1:]):
        if position >= start and position < end:
            return text[start:end].strip()
    raise ValueError(f"Wrong position: {position}")

def execute(command, args, text, position=None):
    error_msg = (
        "'%{command}' (line {line}) is not a valid command. Commands include: {lst}."
    )
    if position is not None:
        line = _find_line_from_position(text, position)
    else:
        line = _find_line_from_occurence(text, command)
    if command not in globals():
        raise ValueError(error_msg.format(command=command, line=line, lst=lstcommands()))
        # return MarkdownParser._to_comment(f"{command} {' '.join(args)}"), None
    cmd = globals()[command]
    if not callable(cmd):
        raise TypeError(error_msg.format(command=command, line=line, lst=lstcommands()))
    new_text, new_cfg, text_action = cmd(text=text, position=position, args=args)
    if text_action is not None:
        raise NotImplementedError
    return new_text, new_cfg

def lstcommands(as_string=False, sep=", "):
    lst = sorted([value for value in __all__
                  if not value in ["execute", "lstcommands"]
                  and not value.startswith("_")])
    if as_string:
        return sep.join(lst)
    return lst