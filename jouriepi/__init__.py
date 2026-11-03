"""Public Python package facade for JouriEpi.

The implementation lives in :mod:`core`; this package provides the stable
top-level import path used by applications and reproducible analysis scripts.
Importing it is headless and does not initialize either desktop UI.
"""
from core import *  # noqa: F401,F403 - re-export the explicitly curated core API
from core import __all__ as _core_all

__version__ = "1.0.0"

__all__ = list(_core_all)
