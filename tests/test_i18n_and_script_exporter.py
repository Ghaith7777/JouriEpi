import ast

import pytest

from core.i18n import LANGUAGES, menu_tooltip, translate, normalize_language, _MESSAGES
from core.script_exporter import export_python_script, export_r_script, export_reproducibility_bundle


def test_language_engine_has_eight_supported_locales_and_safe_fallback():
    assert set(LANGUAGES) == {"en", "fr", "de", "ar", "es", "ru", "zh", "ja"}
    assert translate("save_workspace", "fr") == "Enregistrer l’espace (.jepi)"
    assert translate("save_workspace", "de") == "Arbeitsbereich speichern (.jepi)"
    assert normalize_language("fr-CA") == "fr"
    assert translate("missing_key", "unknown") == "missing_key"


def test_locale_lookups_use_translations_or_explicit_english_fallback():
    keys = set(_MESSAGES["en"])
    assert set(LANGUAGES.values()) == {"English", "Français", "Deutsch", "العربية", "Español", "Русский", "中文", "日本語"}
    for language in LANGUAGES:
        assert set(_MESSAGES[language]) == keys
        assert all(translate(key, language).strip() for key in keys)
        assert all(value.strip() for value in _MESSAGES[language].values())
    assert translate("missing_key", "ja", fallback="Fallback text") == "Fallback text"
    assert all(menu_tooltip("language", language) for language in LANGUAGES)


def test_required_navigation_translations_and_localized_file_tooltips():
    expected = {
        "nav_analysis": ("2×2 Analysis", "Analyse 2×2", "2×2-Analyse"),
        "nav_line_list": ("Line list → 2×2", "Liste brute → 2×2", "Rohdatenliste → 2×2"),
        "nav_dta": ("Diagnostic Test Accuracy (DTA)", "Précision Diagnostique (DTA)", "Diagnostische Testgenauigkeit"),
        "nav_power": ("Sample size & power", "Taille d'échantillon & Puissance", "Stichprobenumfang & Power"),
        "nav_advanced": ("Advanced analyses", "Analyses avancées (McNemar & ROC)", "Erweiterte Analysen (McNemar & ROC)"),
        "nav_publication": ("Publication & STROBE", "Publication & Normes STROBE", "Publikation & STROBE-Richtlinien"),
        "association_analysis": ("Association Analysis", "Analyse d'Association", "Assoziationsanalyse"),
        "contingency_table": ("Contingency table", "Tableau de contingence", "Kontingenztafel"),
        "sampling_design": ("Sampling design", "Plan d'échantillonnage", "Studiendesign"),
        "cohort_cross": ("Cohort / cross-sectional", "Cohorte / Transversale", "Kohorte / Querschnitt"),
        "case_control": ("Case-control", "Cas-témoins", "Fall-Kontroll"),
        "exposed": ("Exposed", "Exposés", "Exponiert"),
        "unexposed": ("Unexposed", "Non exposés", "Nicht exponiert"),
        "case_positive": ("Case (D+)", "Cas (M+)", "Fälle (K+)"),
        "noncase_negative": ("Non-case (D−)", "Témoins (M−)", "Kontrollen (K−)"),
    }
    for key, values in expected.items():
        assert tuple(translate(key, language) for language in ("en", "fr", "de")) == values
    assert menu_tooltip("file", "fr") == "Gestion de session et fichiers"
    assert menu_tooltip("file", "de") == "Sitzungs- und Dateiverwaltung"


def test_all_eight_locales_have_native_language_labels_and_clinical_core_terms():
    expected = {"ar": ("ملف", "حالات وشواهد"), "es": ("Archivo", "Casos y controles"),
                "ru": ("Файл", "Случай–контроль"), "zh": ("文件", "病例对照"),
                "ja": ("ファイル", "症例対照")}
    for language, (file_label, design_label) in expected.items():
        assert translate("file", language) == file_label
        assert translate("case_control", language) == design_label
        assert translate("nav_analysis", language)


def test_reproducibility_scripts_are_standalone_and_valid_python():
    python = export_python_script([25, 15, 7, 30], alpha=0.05)
    ast.parse(python)
    assert "scipy.stats" in python and "statsmodels" in python
    assert "COUNTS = [25, 15, 7, 30]" in python
    r = export_r_script([25, 15, 7, 30])
    assert "chisq.test" in r and "fisher.test" in r and "install.packages" not in r
    bundle = export_reproducibility_bundle([1, 2, 3, 4])
    assert set(bundle) == {"analysis.py", "analysis.R", "manifest.json"}


@pytest.mark.parametrize("counts", [[1, -1, 0, 2], [1.1, 2, 3, 4], [1, 2, 3]])
def test_script_exporter_rejects_invalid_counts(counts):
    with pytest.raises(ValueError):
        export_python_script(counts)
