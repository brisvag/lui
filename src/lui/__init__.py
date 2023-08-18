"""Lemmy Terminal UI."""
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("lui")
except PackageNotFoundError:
    __version__ = "uninstalled"

__author__ = "Lorenzo Gaifas"
__email__ = "brisvag@gmail.com"
