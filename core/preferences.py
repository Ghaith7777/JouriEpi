"""Local, opt-in JouriEpi preferences stored as a small JSON document.

No network access is performed. The default path is under the current user's
home directory; tests and portable deployments can supply an explicit path.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

PREFERENCES_FILENAME = "user_preferences.json"
DEFAULT_PREFERENCES_DIR = Path.home() / "JouriEpi"
SUPPORTED_LANGUAGES = {"en", "fr", "de", "ar", "es", "ru", "zh", "ja"}


def preferences_path(workspace_dir: str | Path | None = None) -> Path:
    """Return the preference JSON path without creating the directory."""
    if workspace_dir is not None:
        return Path(workspace_dir) / PREFERENCES_FILENAME
    configured = os.environ.get("JOURIEPI_WORKSPACE")
    return (Path(configured) if configured else DEFAULT_PREFERENCES_DIR) / PREFERENCES_FILENAME


def default_preferences() -> dict[str, Any]:
    return {"language": "en", "theme": "light", "institution": {"study_author": "", "default_setting": ""}}


def load_preferences(workspace_dir: str | Path | None = None) -> dict[str, Any]:
    """Load valid known fields; a missing or malformed file safely uses defaults."""
    result = default_preferences()
    try:
        payload = json.loads(preferences_path(workspace_dir).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return result
    if not isinstance(payload, dict):
        return result
    language = payload.get("language")
    if isinstance(language, str) and language in SUPPORTED_LANGUAGES:
        result["language"] = language
    theme = payload.get("theme")
    if theme in {"light", "dark"}:
        result["theme"] = theme
    institution = payload.get("institution")
    if isinstance(institution, Mapping):
        result["institution"] = {
            "study_author": str(institution.get("study_author", ""))[:300],
            "default_setting": str(institution.get("default_setting", ""))[:300],
        }
    return result


def has_saved_language(workspace_dir: str | Path | None = None) -> bool:
    """Whether a valid explicit language choice exists (theme-only files do not count)."""
    try:
        payload = json.loads(preferences_path(workspace_dir).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return False
    return isinstance(payload, dict) and payload.get("language") in SUPPORTED_LANGUAGES


def save_preferences(preferences: Mapping[str, Any], workspace_dir: str | Path | None = None) -> Path:
    """Validate and atomically save supported preferences as UTF-8 JSON."""
    defaults = default_preferences()
    language = preferences.get("language", defaults["language"])
    theme = preferences.get("theme", defaults["theme"])
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language code: {language!r}")
    if theme not in {"light", "dark"}:
        raise ValueError(f"Unsupported theme: {theme!r}")
    institution = preferences.get("institution", {})
    if not isinstance(institution, Mapping):
        raise ValueError("institution must be a mapping")
    payload = {
        "language": language, "theme": theme,
        "institution": {
            "study_author": str(institution.get("study_author", ""))[:300],
            "default_setting": str(institution.get("default_setting", ""))[:300],
        },
    }
    path = preferences_path(workspace_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)
    return path
