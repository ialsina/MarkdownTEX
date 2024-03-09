from dataclasses import dataclass
from pathlib import Path
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


@dataclass
class Config:
    default_output_dir_as_input_dir: bool
    fallback_input_dir: str

with open(PATH_CONFIG, "r", encoding="utf-8") as f:
    config = Config(**safe_load(f))

with open(PATH_DEFAULTS, "r", encoding="utf-8") as f:
    defaults = safe_load(f)

PATH_IO = PATH_ROOT / config.fallback_input_dir
