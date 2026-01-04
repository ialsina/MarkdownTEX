from dataclasses import dataclass
from pathlib import Path
from typing import Sequence, Mapping
from yaml import safe_load
from importlib.resources import files # add files from data dir

__all__ = [
    "config",
    "defaults",
]

# search for files in data dir in mdtk package dir once the package is installed
DATA_DIR = files("mdtk") / "data" 

PATH_CONFIG = DATA_DIR / "config.yaml"
PATH_DEFAULTS = DATA_DIR / "defaults.yaml"
PATH_PACKAGE_CHOICES = DATA_DIR / "packages.yaml"
PATH_DATA = DATA_DIR / "data"
PATH_FONTS = DATA_DIR / "fonts.txt"
PATH_FONT_USAGE = DATA_DIR / "font_usages.json"

@dataclass
class Config:
    default_output_dir_as_input_dir: bool

@dataclass
class Packages:
    on_off: Sequence[str]
    functionality: Mapping[str, Sequence[str]]

    @property
    def allowed(self):
        return sorted(set(
            self.on_off
            + [el for lst in self.functionality.values() for el in lst]
        ))

    @classmethod
    def from_dict(cls, dct: dict):
        dct = dct.copy()
        on_off = dct.pop("ONOFF")
        functionality = dct
        return cls(on_off=on_off, functionality=functionality)

with open(PATH_CONFIG, "r", encoding="utf-8") as f:
    config = Config(**safe_load(f))

with open(PATH_DEFAULTS, "r", encoding="utf-8") as f:
    defaults = safe_load(f)

with open(PATH_PACKAGE_CHOICES, "r", encoding="utf-8") as f:
    packages = Packages.from_dict(safe_load(f))

