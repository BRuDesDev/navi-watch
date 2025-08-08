from pathlib import Path

# This file lives at: <project_root>/navi/core/paths.py
PACKAGE_ROOT = Path(__file__).resolve().parent.parent      # …/navi
PROJECT_ROOT = PACKAGE_ROOT.parent                         # project root

ASSETS_DIR = PROJECT_ROOT / "assets"
MODELS_DIR = PROJECT_ROOT / "models"

def asset_path(*parts) -> Path:
    return ASSETS_DIR.joinpath(*parts)

def model_path(*parts) -> Path:
    return MODELS_DIR.joinpath(*parts)
