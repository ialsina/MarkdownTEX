import json
import re
from collections import defaultdict

from mdtex.config import PATH_FONTS, PATH_FONT_USAGE

__all__ = [
    "supported_fonts",
    "is_font",
    "get_font_usage",
]

def _normalize(s: str):
    if isinstance(s, list):
        return [_normalize(element) for element in s]
    if isinstance(s, dict):
        return {_normalize(k): v for k, v in s.items()}
    return s.lower().replace(" ", "_").replace("-", "_")

try:
    with open(PATH_FONTS, "r", encoding="utf-8") as f:
        supported_fonts = f.read().splitlines()
        _fonts = _normalize(supported_fonts)
    with open(PATH_FONT_USAGE, "r", encoding="utf-8") as f:
        _font_usage = json.loads(f.read())
        _font_usage = _normalize(_font_usage)
except FileNotFoundError as exc:
    raise FileNotFoundError(
        f"Files {PATH_FONTS} and {PATH_FONT_USAGE} must exist to use latex fonts."
    ) from exc

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

_font_packages = _get_font_packages()

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
