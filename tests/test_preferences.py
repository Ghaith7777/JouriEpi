import json

import pytest

from core.preferences import has_saved_language, load_preferences, preferences_path, save_preferences


def test_preferences_round_trip_unicode_and_theme(tmp_path):
    values = {"language": "ar", "theme": "dark", "institution": {"study_author": "باحث", "default_setting": "University clinic"}}
    path = save_preferences(values, tmp_path)
    assert path.name == "user_preferences.json"
    assert json.loads(path.read_text(encoding="utf-8"))["language"] == "ar"
    assert load_preferences(tmp_path) == values


def test_missing_or_malformed_preferences_safely_default(tmp_path):
    assert load_preferences(tmp_path) == {"language": "en", "theme": "light", "institution": {"study_author": "", "default_setting": ""}}
    assert not has_saved_language(tmp_path)
    preferences_path(tmp_path).write_text("{bad", encoding="utf-8")
    assert load_preferences(tmp_path)["language"] == "en"
    assert not has_saved_language(tmp_path)


def test_theme_only_preferences_still_require_initial_language_choice(tmp_path):
    preferences_path(tmp_path).write_text('{"theme":"dark"}', encoding="utf-8")
    assert not has_saved_language(tmp_path)
    save_preferences({"language": "ja", "theme": "dark", "institution": {}}, tmp_path)
    assert has_saved_language(tmp_path)


@pytest.mark.parametrize("values", [
    {"language": "xx", "theme": "dark", "institution": {}},
    {"language": "en", "theme": "neon", "institution": {}},
    {"language": "en", "theme": "light", "institution": "invalid"},
])
def test_preferences_reject_invalid_values(tmp_path, values):
    with pytest.raises(ValueError):
        save_preferences(values, tmp_path)
