from dataclasses import dataclass
from pathlib import Path
from typing import Sequence, Mapping
from yaml import safe_load

__all__ = [
    "config",
    "defaults",
    "PATH_IO",
]


PATH_SRC = Path(__file__).absolute().parent.parent
PATH_ROOT = PATH_SRC.parent
PATH_CONFIG = PATH_ROOT / "config.yaml"
PATH_DEFAULTS = PATH_ROOT / "defaults.yaml"
PATH_PACKAGE_CHOICES = PATH_ROOT / "packages.yaml"


@dataclass
class Config:
    default_output_dir_as_input_dir: bool
    fallback_input_dir: str

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

PATH_IO = PATH_ROOT / config.fallback_input_dir
