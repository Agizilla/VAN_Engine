import sys
from pathlib import Path
from typing import List, Tuple


REQUIRED_TOP_LEVEL = ["daz", "face", "skin"]
REQUIRED_DAZ = ["daz.timeout_seconds"]
REQUIRED_FACE = ["face.target_size", "face.margin_ratio"]
REQUIRED_SKIN = ["skin.sample_regions"]
POSITIVE_NUMBERS = [
    "daz.timeout_seconds",
    "face.target_size",
    "face.margin_ratio",
    "face.min_detection_confidence",
]
PATHS_TO_CHECK = [
    "daz.daz_studio_path",
]


def _get_nested(config: dict, dotted_key: str):
    parts = dotted_key.split(".")
    val = config
    for p in parts:
        if not isinstance(val, dict):
            return None
        val = val.get(p)
        if val is None:
            return None
    return val


def validate_config(config: dict, config_path: Path) -> List[str]:
    errors = []

    for key in REQUIRED_TOP_LEVEL:
        if key not in config:
            errors.append(f"Missing top-level section: '{key}'")

    for key in REQUIRED_DAZ:
        if _get_nested(config, key) is None:
            errors.append(f"Missing required key: '{key}'")

    for key in REQUIRED_FACE:
        if _get_nested(config, key) is None:
            errors.append(f"Missing required key: '{key}'")

    for key in REQUIRED_SKIN:
        if _get_nested(config, key) is None:
            errors.append(f"Missing required key: '{key}'")

    for key in POSITIVE_NUMBERS:
        val = _get_nested(config, key)
        if val is not None and not isinstance(val, (int, float)):
            errors.append(f"'{key}' must be a number, got {type(val).__name__}")
        elif val is not None and val <= 0:
            errors.append(f"'{key}' must be positive, got {val}")

    for key in PATHS_TO_CHECK:
        val = _get_nested(config, key)
        if val is not None and not Path(val).exists():
            errors.append(f"Path '{key}' does not exist: {val}")

    return errors


def print_validation_errors(errors: List[str]):
    print("Configuration validation failed:")
    for e in errors:
        print(f"  - {e}")
    print()
    print("Fix config.json and try again.")


def ensure_validated(config: dict, config_path: Path):
    errors = validate_config(config, config_path)
    if errors:
        print_validation_errors(errors)
        sys.exit(1)
