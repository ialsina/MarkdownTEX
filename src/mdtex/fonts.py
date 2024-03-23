import json
import re
from functools import partial
from collections import defaultdict
from collections.abc import Sequence, Mapping
from typing import Callable

from mdtex.config import PATH_FONTS, PATH_FONT_USAGE
from mdtex._exceptions import NoFontFilesError

__all__ = [
    "supported_fonts",
    "is_font",
    "get_font_usage",
]

class LazyFactory:
    def __init__(self, get_data: Callable):
        self._get_items = get_data
        self._data = None
    @property
    def data(self):
        if self._data is None:
            self._data = self._get_items()
        return self._data
    def __getitem__(self, i):
        return self.data[i]
    def __iter__(self):
        return iter(self.data)
    def __len__(self):
        return len(self.data)

class LazyList(LazyFactory, Sequence): ... # pylint: disable=C0115,C0321
class LazyDict(LazyFactory, Mapping): ... # pylint: disable=C0115,C0321


def _normalize(obj: str | Sequence | Mapping):
    if isinstance(obj, str):
        return obj.lower().replace(" ", "_").replace("-", "_")
    if isinstance(obj, Sequence):
        return [_normalize(element) for element in obj]
    if isinstance(obj, Mapping):
        return {_normalize(k): v for k, v in obj.items()}
    raise TypeError(
        f"Unknown type: {type(obj)}"
    )

def _read_lines(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().splitlines()
    except FileNotFoundError as exc:
        raise NoFontFilesError() from exc
  
def _read_json_normalize(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return _normalize(json.loads(f.read()))
    except FileNotFoundError as exc:
        raise NoFontFilesError() from exc
   
def _get_font_packages():
    pattern = re.compile(r"^\\usepackage(?:\[.*\])?\{(.+)\}", re.MULTILINE)
    font_package_lists = defaultdict(list)
    for font, usage in _font_usage.items():
        for match_ in re.finditer(pattern, usage):
            package = match_.groups()[0]
            font_package_lists[font].append(package)
    # Unfold font packages
    font_packages_ = []
    for font, pkgs in font_package_lists.items():
        font_packages_.extend(pkgs)
    # Select unique font packages
    unique_packages = [package
                       for package
                       in font_packages_
                       if font_packages_.count(package) == 1    
                       ]
    package_font = {}
    for font, pkgs in font_package_lists.items():
        for pkg in pkgs:
            if pkg in unique_packages:
                package_font[_normalize(pkg)] = font
    return package_font

supported_fonts = LazyList(partial(_read_lines, PATH_FONTS))
_fonts = LazyList(partial(_normalize, supported_fonts))
_font_usage = LazyDict(partial(_read_json_normalize, PATH_FONT_USAGE))
_font_packages = LazyDict(_get_font_packages)

def is_font(s: str):
    """Return True if it the passed value is a supported font,
    or a the LaTeX font package name of a supported font.
    Otherwise, return False.
    """
    s = _normalize(s)
    if s in _fonts:
        return True
    if s in _font_packages:
        return True
    return False

def get_font_usage(s: str):
    """Return the LaTeX preamble instructions for the passed font.
    Raise ValueError if the passed value is not a valid font.
    """
    if not is_font(s):
        raise ValueError(
            f"{s} is not a valid font name."
        )
    s = _normalize(s)
    if s in _font_usage:
        return _font_usage[s]
    return _font_usage[_font_packages[s]]
