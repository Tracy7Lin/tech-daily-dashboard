from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parent
SRC_ROOT = PACKAGE_ROOT.parent
PROJECT_ROOT = SRC_ROOT.parent

CONFIG_DIR = PROJECT_ROOT / "config"
TEMPLATES_DIR = PROJECT_ROOT / "templates"
BUILD_DIR = PROJECT_ROOT / "build"
SITE_DIR = BUILD_DIR / "site"
DATA_DIR = BUILD_DIR / "data"
