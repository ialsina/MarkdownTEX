from pathlib import Path
from yaml import safe_load

PATH_ROOT = Path(__file__).absolute().parent
PATH_DEFAULTS = PATH_ROOT.parent.parent / "defaults.yaml"

with open(PATH_DEFAULTS, "r", encoding="utf-8") as f:
    defaults = safe_load(f)
