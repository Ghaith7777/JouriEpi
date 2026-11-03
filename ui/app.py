"""Offline clinical-research interface for JouriEpi.

This module contains presentation and interaction only. Statistical functions in
``core`` are deliberately not modified by the UI redesign.
"""

from __future__ import annotations

import html
import hashlib
import json
import csv
from io import StringIO
from pathlib import Path
from zipfile import BadZipFile

import pandas as pd
import streamlit as st

from core.assumptions import audit_expected_counts
from core.engine_2x2 import Table2x2, analyze_2x2
from core.causal_sensitivity import e_value
from core.stratification import analyze_stratified_tables, analyze_stratified_dataframe
from core.diagnostic_accuracy import DiagnosticTestAccuracy, fagan_post_test_probability, compare_roc_curves
from core.i18n import LANGUAGES, menu_tooltip, normalize_language, translate
from core.preferences import has_saved_language, load_preferences, save_preferences, preferences_path
from core.interaction import analyze_additive_interaction
from core.journal_export import export_journal_docx, export_journal_html, export_journal_latex
from core.paired_analysis import mcnemar_test
from core.session_manager import save_workspace, load_workspace
from core.script_exporter import export_python_script, export_r_script
from core.decision_curve import analyze_decision_curve
from core.report_generator import generate_clinical_dossier
from core.audit_certificate import certificate_json
from core.exact_advanced import analyze_boschloo
from core.demo_data import DEMO_DATASETS, get_demo_dataset
from core.io_loader import aggregate_line_list, load_uploaded_table
from core.data_validator import inspect_line_list
from core.strobe_export import comparison_latex, comparison_markdown, strobe_narrative, technical_payload
from core.power_sample import (case_control_sample_size, cohort_sample_size,
                               cross_sectional_sample_size, two_proportion_power)
from ui.components import (metric_card, result_table, table_2x2, expected_counts_grid,
                           forest_plot_svg, forest_plot_png_bytes, power_curve_svg,
                           stratified_forest_plot_svg, roc_plot_svg, roc_plot_png_bytes, dual_roc_plot_svg,
                           fagan_nomogram_svg, decision_curve_svg, figure_export_payloads)
from ui.formatting import fmt_ci, fmt_num, fmt_pct, fmt_p


st.set_page_config(page_title="JouriEpi Clinical Workstation v1.0", page_icon=str(Path(__file__).resolve().parent / "assets" / "jouriepi.png"), layout="wide", initial_sidebar_state="expanded")

# Bundled local theme; no remote fonts, scripts, stylesheets, or network calls.
_STYLE_PATH = Path(__file__).resolve().parent / "assets" / "style.css"
_STYLE_TEXT = _STYLE_PATH.read_text(encoding="utf-8") if _STYLE_PATH.is_file() else ""
_STYLE_TEXT += "\n.stApp [data-testid='stHorizontalBlock'] [data-testid='stButton'] button{padding:.25rem .3rem!important;font-size:.8rem!important}\n"
_INITIAL_LANGUAGE = st.session_state.get("language", load_preferences().get("language", "en"))
if _INITIAL_LANGUAGE == "ar":
    _STYLE_TEXT += "\n.stApp,[data-testid='stSidebar']{direction:rtl;text-align:right}.stApp [data-testid='stHorizontalBlock']{direction:rtl}\n"
st.markdown(f"<style>{_STYLE_TEXT}</style>", unsafe_allow_html=True)
APP_VERSION = "1.0.0"
_BUILD_HASH = hashlib.sha256(Path(__file__).read_bytes() + _STYLE_TEXT.encode("utf-8")).hexdigest()[:10]


NAV_ITEMS = ["2×2 Analysis", "Line list → 2×2", "Diagnostic Test Accuracy (DTA)", "Sample size & power", "Advanced analyses", "Publication & STROBE"]
NAV_TRANSLATION_KEYS = {
    "2×2 Analysis": "nav_analysis", "Line list → 2×2": "nav_line_list",
    "Diagnostic Test Accuracy (DTA)": "nav_dta", "Sample size & power": "nav_power",
    "Advanced analyses": "nav_advanced", "Publication & STROBE": "nav_publication",
}


def _persist_count(key: str) -> None:
    """Preserve count inputs when Streamlit removes hidden-section widgets."""
    st.session_state[f"saved_{key}"] = int(st.session_state[key])


def _set_count(key: str, value: int) -> None:
    st.session_state[key] = int(value)
    st.session_state[f"saved_{key}"] = int(value)


def _persist_value(key: str) -> None:
    """Mirror a section-specific widget value so it survives navigation."""
    st.session_state[f"saved_{key}"] = st.session_state[key]


def _set_persisted_value(key: str, value) -> None:
    st.session_state[key] = value
    st.session_state[f"saved_{key}"] = value


for key, value in {"a": 25, "b": 15, "c": 7, "d": 30, "alpha": 0.05,
                   "use_ha": False, "nav_section": NAV_ITEMS[0], "analysis_result": None,
                   "analysis_counts": None, "line_result": None, "power_result": None,
                   "line_design": "Cohort / cross-sectional", "sampling_design": "Cohort / cross-sectional", "planning_design": "Cohort", "planning_design_widget": "Cohort",
                   "planning_alpha": 0.05, "power_plan": 0.80}.items():
    if key in {"a", "b", "c", "d", "alpha", "use_ha", "line_design", "sampling_design", "planning_design", "planning_design_widget", "planning_alpha", "power_plan"}:
        saved_key = f"saved_{key}"
        if saved_key not in st.session_state:
            st.session_state[saved_key] = value
        if key not in st.session_state:
            st.session_state[key] = st.session_state[saved_key]
    elif key not in st.session_state:
        st.session_state[key] = value

if "language" not in st.session_state:
    st.session_state["language"] = load_preferences().get("language", "en")
if "dark_mode" not in st.session_state:
    st.session_state["dark_mode"] = load_preferences().get("theme", "light") == "dark"
if "institution_study_author" not in st.session_state or "institution_default_setting" not in st.session_state:
    _saved_institution = load_preferences().get("institution", {})
    st.session_state.setdefault("institution_study_author", _saved_institution.get("study_author", ""))
    st.session_state.setdefault("institution_default_setting", _saved_institution.get("default_setting", ""))
    st.session_state.setdefault("dossier_study_author", _saved_institution.get("study_author", ""))
    st.session_state.setdefault("dossier_study_setting", _saved_institution.get("default_setting", ""))
if "show_workspace_panel" not in st.session_state:
    st.session_state["show_workspace_panel"] = False


def _save_local_preferences() -> None:
    """Persist only explicit user settings to the local JSON preferences file."""
    st.session_state["dossier_study_author"] = st.session_state.get("institution_study_author", "")
    st.session_state["dossier_study_setting"] = st.session_state.get("institution_default_setting", "")
    save_preferences({
        "language": normalize_language(st.session_state.get("language", "en")),
        "theme": "dark" if st.session_state.get("dark_mode", False) else "light",
        "institution": {
            "study_author": st.session_state.get("institution_study_author", ""),
            "default_setting": st.session_state.get("institution_default_setting", ""),
        },
    })


def _choose_language(code: str) -> None:
    st.session_state["language"] = normalize_language(code)
    st.session_state["show_language_panel"] = False
    _save_local_preferences()


def _choose_theme() -> None:
    st.session_state["dark_mode"] = not st.session_state.get("dark_mode", False)
    _save_local_preferences()


@st.dialog("Select Workstation Language / Choisissez votre langue / اختر لغة المنظومة")
def _first_launch_language_dialog() -> None:
    st.write(translate("select_language_hint", st.session_state.get("language", "en")))
    columns = st.columns(4)
    for index, (code, endonym) in enumerate(LANGUAGES.items()):
        with columns[index % 4]:
            if st.button(endonym, key=f"startup_language_{code}", width="stretch"):
                _choose_language(code)
                st.session_state["startup_language_prompt_dismissed"] = True
                st.rerun()


if not has_saved_language() and not st.session_state.get("startup_language_prompt_dismissed", False):
    _first_launch_language_dialog()

LANG = st.session_state.get("language", "en")
if st.session_state.get("dark_mode"):
    st.markdown(chr(60) + "style>" + """
    :root{color-scheme:dark;--epi-bg:#0b0f19;--epi-card:#111827;--epi-text:#f8fafc;--epi-navy:#f8fafc;--epi-muted:#cbd5e1;--epi-border:#334155;--epi-accent:#2dd4bf;--epi-focus:#5eead4;--epi-accent-soft:#134e4a;--epi-green:#86efac;--epi-green-bg:#14532d;--epi-amber:#fde68a;--epi-amber-bg:#78350f;--epi-red:#fecaca;--epi-red-bg:#7f1d1d}
    .stApp,[data-testid="stAppViewContainer"],section.main, [data-testid="stSidebar"]{background:#0b0f19!important;color:#f8fafc!important}
    [data-testid="stSidebar"]{border-right:1px solid #334155!important}
    [data-testid="stVerticalBlockBorderWrapper"], [data-testid="stMetric"],.metric-card,.plot-panel,.result-panel,.brand-panel{background:#111827!important;border-color:#334155!important}
    .stApp p,.stApp label,.stApp h1,.stApp h2,.stApp h3,.stApp h4,.stApp span,.stApp li,.stApp small,.stApp [data-testid="stCaptionContainer"],.stApp .stMarkdown,.stApp .stText,.stApp [data-testid="stMetricLabel"],.stApp [data-testid="stMetricValue"],.stApp [data-testid="stMetricDelta"]{color:#f8fafc}
    .stApp .muted-note,.stApp .metric-label,.stApp .metric-detail,.stApp .metric-status,.stApp .brand-meta,.stApp .app-subtitle,.stApp .step-label{color:#cbd5e1!important}
    .stApp [data-baseweb="select"]>div,.stApp [data-baseweb="input"]>div,.stApp input,.stApp textarea,.stApp select,.stApp [data-baseweb="textarea"]>div{background:#1e293b!important;color:#f8fafc!important;border-color:#475569!important}
    .stApp [data-baseweb="select"] *, .stApp [data-baseweb="input"] *, .stApp input::placeholder,.stApp textarea::placeholder{color:#f8fafc!important}
    .stApp [role="listbox"],.stApp [role="option"],.stApp [data-baseweb="popover"]{background:#1e293b!important;color:#f8fafc!important}
    .stApp button{background:#111827!important;color:#f8fafc!important;border-color:#475569!important}
    .stApp button:hover{background:#1e293b!important;color:#ffffff!important;border-color:#5eead4!important}
    .stApp button[kind="primary"],.stApp [data-testid="stBaseButton-primary"]{background:#0f766e!important;color:#ffffff!important;border-color:#2dd4bf!important}
    .stApp [data-testid="stFileUploader"],.stApp [data-testid="stFileUploaderDropzone"],.stApp [data-testid="stFileUploader"] section{background:#111827!important;color:#f8fafc!important;border-color:#475569!important}
    .stApp [data-testid="stFileUploader"] button,.stApp [data-baseweb="select"] button,.stApp [data-testid="stSegmentedControl"] button,.stApp [data-baseweb="button-group"] button{background:#1e293b!important;color:#f8fafc!important;border-color:#475569!important}
    .stApp [data-testid="stSegmentedControl"] button[aria-pressed="true"],.stApp [data-baseweb="button-group"] button[aria-pressed="true"]{background:#134e4a!important;color:#ffffff!important;border-color:#2dd4bf!important}
    .stApp .table-head{background:#1e293b!important;color:#f8fafc!important}.stApp .row-head,.stApp .count-cell{background:#111827!important;color:#f8fafc!important}.stApp .total-cell{background:#1e293b!important;color:#cbd5e1!important}.stApp .grand-total{background:#134e4a!important;color:#f8fafc!important}
    .stApp .offline-badge{background:#134e4a!important;color:#ccfbf1!important;border-color:#2dd4bf!important}
    .stApp [data-testid="stAlert"]{color:#f8fafc!important}
    .stApp [data-testid="stDataFrame"],.stApp [data-testid="stTable"]{color:#f8fafc!important;border-color:#334155!important}
    .stApp [data-testid="stDataFrame"] *{color:#f8fafc!important}
    .stApp button:focus-visible,.stApp input:focus-visible,.stApp textarea:focus-visible{outline:3px solid #5eead4!important;outline-offset:2px!important}
    /* Streamlit/BaseWeb tooltips are sometimes portaled outside .stApp. */
    body [role="tooltip"],body [data-baseweb="tooltip"],body [data-testid="stTooltipContent"],body .stTooltip{background:#1e293b!important;color:#f8fafc!important;border:1px solid #334155!important;box-shadow:0 4px 14px rgba(0,0,0,.6)!important}
    body [role="tooltip"] *,body [data-baseweb="tooltip"] *,body [data-testid="stTooltipContent"] *{color:#f8fafc!important}
    """ + chr(60) + "/style>", unsafe_allow_html=True)
# Simulated native-style workstation menu. All actions remain local.
menu = st.columns([1.0, 1.15, 1.6, 1.0, 1.2, 0.9, 0.8])
for col, label, key in zip(menu[:7], ("File", "Analysis", "Diagnostics", "Reports", "Language", "Theme", "Help"),
                           ("file", "analysis", "diagnostics", "reports", "language", "theme", "help")):
    with col:
        if st.button(translate(key, LANG), key=f"menu_{key}", width="stretch", help=menu_tooltip(key, LANG)):
            if key == "file":
                st.session_state["show_workspace_panel"] = not st.session_state.get("show_workspace_panel", False)
                st.session_state["show_language_panel"] = False
            elif key == "analysis":
                st.session_state["nav_section"] = NAV_ITEMS[0]
                st.session_state["show_workspace_panel"] = False
            elif key == "diagnostics":
                st.session_state["nav_section"] = NAV_ITEMS[2]
                st.session_state["show_workspace_panel"] = False
            elif key == "reports":
                st.session_state["nav_section"] = NAV_ITEMS[5]
                st.session_state["show_workspace_panel"] = False
            elif key == "language":
                st.session_state["show_language_panel"] = not st.session_state.get("show_language_panel", False)
            elif key == "theme":
                _choose_theme()
            elif key == "help":
                st.session_state["show_help_panel"] = not st.session_state.get("show_help_panel", False)
            if key in {"analysis", "diagnostics", "reports", "theme"}:
                st.rerun()
if st.session_state.get("show_language_panel"):
    st.caption(translate("language_help", LANG))
    language_columns = st.columns(4, gap="small")
    for index, (code, endonym) in enumerate(LANGUAGES.items()):
        with language_columns[index % 4]:
            st.button(endonym, key=f"language_{code}", type="primary" if st.session_state.get("language", "en") == code else "secondary",
                      width="stretch", help=translate("language_help", LANG), on_click=_choose_language, args=(code,))
LANG = st.session_state.get("language", "en")
if st.session_state.get("show_help_panel"):
    with st.expander(translate("help_reference_title", LANG), expanded=True):
        st.info(translate("language_help", LANG) + " · Offline-first: no analysis data is sent to a remote service.")
        st.subheader(translate("help_boschloo_title", LANG))
        st.write(translate("help_boschloo", LANG))
        st.subheader(translate("help_woolf_katz_title", LANG))
        st.write(translate("help_woolf_katz", LANG))
        st.subheader(translate("help_evalue_title", LANG))
        st.write(translate("help_evalue", LANG))
        st.subheader(translate("help_fagan_title", LANG))
        st.write(translate("help_fagan", LANG))
        apa = (
            "Boschloo, R. D. (1970). Raised conditional level of significance for the 2×2-table when testing the equality of two probabilities. Statistica Neerlandica, 24(1), 1–9. https://doi.org/10.1111/j.1467-9574.1970.tb00104.x\n"
            "DeLong, E. R., DeLong, D. M., & Clarke-Pearson, D. L. (1988). Comparing the areas under two or more correlated receiver operating characteristic curves: A nonparametric approach. Biometrics, 44(3), 837–845. https://doi.org/10.2307/2531595\n"
            "Fagan, T. J. (1975). Letter: Nomogram for Bayes theorem. The New England Journal of Medicine, 293, 257. https://doi.org/10.1056/NEJM197507312930513\n"
            "Katz, D., Baptista, J., Azen, S. P., & Pike, M. C. (1978). Obtaining confidence intervals for the risk ratio in cohort studies. Biometrics, 34(3), 469–474. https://doi.org/10.2307/2530610\n"
            "Robins, J. M., Breslow, N. E., & Greenland, S. (1986). Estimators of the Mantel-Haenszel variance consistent in both sparse data and large-strata limiting models. Biometrics, 42(2), 311–323. https://doi.org/10.2307/2531058\n"
            "Fisher, R. A. (1922). On the interpretation of χ² from contingency tables, and the calculation of P. Journal of the Royal Statistical Society, 85(1), 87–94. https://doi.org/10.2307/2340521\n"
            "VanderWeele, T. J., & Ding, P. (2017). Sensitivity analysis in observational research: Introducing the E-value. Annals of Internal Medicine, 167(4), 268–274. https://doi.org/10.7326/M16-2607\n"
            "Woolf, B. (1955). On estimating the relation between blood group and disease. Annals of Human Genetics, 19(4), 251–253. https://doi.org/10.1111/j.1469-1809.1955.tb01348.x"
        )
        bibtex = '''@article{Boschloo1970, author={Boschloo, R. D.}, title={Raised conditional level of significance for the 2x2-table when testing the equality of two probabilities}, journal={Statistica Neerlandica}, year={1970}, volume={24}, number={1}, pages={1--9}, doi={10.1111/j.1467-9574.1970.tb00104.x}}
@article{DeLong1988, author={DeLong, E. R. and DeLong, D. M. and Clarke-Pearson, D. L.}, title={Comparing the areas under two or more correlated receiver operating characteristic curves: A nonparametric approach}, journal={Biometrics}, year={1988}, volume={44}, number={3}, pages={837--845}, doi={10.2307/2531595}}
@article{Fagan1975, author={Fagan, T. J.}, title={Letter: Nomogram for Bayes theorem}, journal={The New England Journal of Medicine}, year={1975}, volume={293}, pages={257}, doi={10.1056/NEJM197507312930513}}
@article{Katz1978, author={Katz, D. and Baptista, J. and Azen, S. P. and Pike, M. C.}, title={Obtaining confidence intervals for the risk ratio in cohort studies}, journal={Biometrics}, year={1978}, volume={34}, number={3}, pages={469--474}, doi={10.2307/2530610}}
@article{RobinsBreslowGreenland1986, author={Robins, J. M. and Breslow, N. E. and Greenland, S.}, title={Estimators of the Mantel-Haenszel variance consistent in both sparse data and large-strata limiting models}, journal={Biometrics}, year={1986}, volume={42}, number={2}, pages={311--323}, doi={10.2307/2531058}}
@article{Fisher1922, author={Fisher, R. A.}, title={On the interpretation of chi-square from contingency tables, and the calculation of P}, journal={Journal of the Royal Statistical Society}, year={1922}, volume={85}, number={1}, pages={87--94}, doi={10.2307/2340521}}
@article{VanderWeeleDing2017, author={VanderWeele, Tyler J. and Ding, Peng}, title={Sensitivity Analysis in Observational Research: Introducing the E-Value}, journal={Annals of Internal Medicine}, year={2017}, volume={167}, number={4}, pages={268--274}, doi={10.7326/M16-2607}}
@article{Woolf1955, author={Woolf, B.}, title={On estimating the relation between blood group and disease}, journal={Annals of Human Genetics}, year={1955}, volume={19}, number={4}, pages={251--253}, doi={10.1111/j.1469-1809.1955.tb01348.x}}'''
        st.subheader(translate("citation_apa", LANG))
        st.text(apa)
        st.subheader(translate("citation_bibtex", LANG))
        st.code(bibtex, language="bibtex")
        st.download_button(translate("download_citations", LANG), f"APA\n\n{apa}\n\nBibTeX\n\n{bibtex}",
                           file_name="jouriepi-method-citations.txt", mime="text/plain", key="download_method_citations")
        st.subheader("Methodological Whitepaper · mathematical reference")
        st.markdown(r"""
**Woolf log-odds interval:** \(\widehat{OR}=ad/bc\), \(SE(\log OR)=\sqrt{1/a+1/b+1/c+1/d}\), then exponentiate \(\log(OR)\pm z_{1-\alpha/2}SE\), where all four cells must be positive.

**Katz log-risk-ratio interval:** \(\widehat{RR}=[a/(a+b)]/[c/(c+d)]\); \(SE(\log RR)=\sqrt{1/a-1/(a+b)+1/c-1/(c+d)}\). The log interval is exponentiated; zero cases make this formula unavailable.

**Boschloo exact test:** for independent \(X_1\sim Bin(n_1,\theta)\) and \(X_0\sim Bin(n_0,\theta)\) under the null of equal probabilities, the unconditional p-value is \(p_B=\sup_{\theta\in[0,1]}P_\theta\{p_F(X_1,X_0)\le p_F(x_{1,obs},x_{0,obs})\}\), using the chosen Fisher-p ordering and sided alternative. It may be more powerful than Fisher's conditional test for some tables; pre-specify sidedness.

**DeLong AUC covariance:** a nonparametric correlated-ROC comparison based on placements / generalized U-statistics; for paired tests the variance of the AUC difference is \(Var(A_1)+Var(A_2)-2Cov(A_1,A_2)\). A single AUC standard error is not a paired DeLong comparison.

**Mantel–Haenszel pooled OR:** \(\widehat{OR}_{MH}=\frac{\sum_i a_i d_i/n_i}{\sum_i b_i c_i/n_i}\). The Robins–Breslow–Greenland variance is an asymptotic variance estimator for the log pooled effect; homogeneity and sparse-stratum assumptions still require review.

For the common RBG log-OR variance form, let \(R=\sum_i a_i d_i/n_i\) and \(S=\sum_i b_i c_i/n_i\). Then \(\widehat{Var}(\log OR_{MH})=\frac{\sum_i (a_i+d_i)a_i d_i/n_i^2}{2R^2}+\frac{\sum_i[(a_i+d_i)b_i c_i+(b_i+c_i)a_i d_i]/n_i^2}{2RS}+\frac{\sum_i(b_i+c_i)b_i c_i/n_i^2}{2S^2}\), when the terms are estimable. Implementations can differ in sparse-data handling; check the specific reported variance field and software version.

**E-value:** for an RR ≥ 1, \(E=RR+\sqrt{RR(RR-1)}\); for protective estimates invert the RR first. For a confidence interval excluding the null, apply the same formula to the confidence limit closest to 1 (invert a protective limit); if the interval includes 1, the confidence-limit E-value is 1. This summarizes sensitivity to unmeasured confounding; it does not prove absence of bias.

**Fagan update:** \(PosttestOdds=PretestOdds\times LR\), with \(PretestOdds=p/(1-p)\) and \(PosttestProbability=PosttestOdds/(1+PosttestOdds)\). Select LR+ or LR− according to the test result.
""")
        st.subheader("Vancouver references · DOI links")
        st.markdown("1. Fisher RA. On the interpretation of χ² from contingency tables, and the calculation of P. *J R Stat Soc*. 1922;85(1):87–94. [doi:10.2307/2340521](https://doi.org/10.2307/2340521)\n\n2. Woolf B. On estimating the relation between blood group and disease. *Ann Hum Genet*. 1955;19:251–253. [doi:10.1111/j.1469-1809.1955.tb01348.x](https://doi.org/10.1111/j.1469-1809.1955.tb01348.x)\n\n3. Katz D, Baptista J, Azen SP, Pike MC. Obtaining confidence intervals for the risk ratio in cohort studies. *Biometrics*. 1978;34(3):469–474. [doi:10.2307/2530610](https://doi.org/10.2307/2530610)\n\n4. Boschloo RD. Raised conditional level of significance for the 2×2-table when testing the equality of two probabilities. *Stat Neerl*. 1970;24(1):1–9. [doi:10.1111/j.1467-9574.1970.tb00104.x](https://doi.org/10.1111/j.1467-9574.1970.tb00104.x)\n\n5. Fagan TJ. Letter: Nomogram for Bayes theorem. *N Engl J Med*. 1975;293:257. [doi:10.1056/NEJM197507312930513](https://doi.org/10.1056/NEJM197507312930513)\n\n6. DeLong ER, DeLong DM, Clarke-Pearson DL. Comparing the areas under two or more correlated receiver operating characteristic curves: a nonparametric approach. *Biometrics*. 1988;44(3):837–845. [doi:10.2307/2531595](https://doi.org/10.2307/2531595)\n\n7. Robins JM, Breslow NE, Greenland S. Estimators of the Mantel-Haenszel variance consistent in both sparse data and large-strata limiting models. *Biometrics*. 1986;42(2):311–323. [doi:10.2307/2531058](https://doi.org/10.2307/2531058)\n\n8. VanderWeele TJ, Ding P. Sensitivity analysis in observational research: Introducing the E-value. *Ann Intern Med*. 2017;167(4):268–274. [doi:10.7326/M16-2607](https://doi.org/10.7326/M16-2607)")
        privacy_statement = ("JouriEpi local privacy and IRB/DPO statement\n\n" 
            "Architecture: the application is designed to process imported data and calculations locally. The desktop launcher binds its Streamlit service to 127.0.0.1 and disables Streamlit usage-statistics collection. This statement describes the bundled application configuration; it is not an independent network-traffic audit or proof of operation on an air-gapped host.\n\n"
            "Telemetry: no application analytics or remote analysis endpoint is intentionally implemented. Optional browser/desktop components and the host operating system remain outside this application's control; deployment owners should verify firewall and endpoint policy.\n\n"
            "Integrity: the clinical dossier includes a SHA-256 hash over its canonical analysis payload. This supports change detection for that payload but is not a digital signature, identity attestation, or full session-chain-of-custody certificate.\n\n"
            "Governance: use synthetic or appropriately authorized data; determine legal basis, ethics approval, retention, access controls, and re-identification risks locally. JouriEpi is a research aid, not a validated medical device or substitute for IRB/DPO review.")
        st.text_area("IRB / DPO privacy statement (editable before export)", value=privacy_statement, height=210, key="privacy_statement_text")
        st.download_button("Download IRB / DPO statement (.txt)", st.session_state["privacy_statement_text"], file_name="jouriepi-IRB-DPO-privacy-statement.txt", mime="text/plain", key="download_privacy_statement")
        privacy_html = ("<!doctype html><html lang='en'><head><meta charset='utf-8'><title>JouriEpi IRB / DPO privacy statement</title>"
            "<" + "style>body{font:10pt/1.4 Arial,sans-serif;max-width:800px;margin:1.2cm auto;color:#111}h1{font-size:16pt}pre{white-space:pre-wrap;font:inherit}"
            "@media print{body{margin:1cm;max-width:none}h1{break-after:avoid}pre{orphans:3;widows:3}}</" + "style></head><body><h1>JouriEpi IRB / DPO privacy statement</h1><pre>" +
            html.escape(st.session_state["privacy_statement_text"]) + "</pre><p>Print from the browser using the system print dialog.</p></body></html>")
        st.download_button("Download printable IRB / DPO statement (.html)", privacy_html,
                           file_name="jouriepi-IRB-DPO-privacy-statement.html", mime="text/html", key="download_privacy_statement_html")


def _reset_table() -> None:
    for key, value in {"a": 25, "b": 15, "c": 7, "d": 30, "alpha": 0.05, "use_ha": False,
                       "analysis_result": None, "analysis_counts": None}.items():
        if key in {"a", "b", "c", "d"}:
            _set_count(key, value)
        else:
            st.session_state[key] = value
            if key in {"alpha", "use_ha"}:
                st.session_state[f"saved_{key}"] = value


def _load_example() -> None:
    for key, value in {"a": 25, "b": 15, "c": 7, "d": 30}.items():
        _set_count(key, value)
    st.session_state["analysis_result"] = None


def _load_clinical_demo() -> None:
    """Load a built-in synthetic dataset and calculate its matching analysis."""
    key = st.session_state.get("clinical_demo_selector", "")
    if key not in DEMO_DATASETS:
        return
    demo = get_demo_dataset(key)
    st.session_state["active_demo_dataset"] = key
    st.session_state["show_workspace_panel"] = False
    st.session_state["show_help_panel"] = False
    if key == "cardiovascular":
        counts = (18, 82, 8, 92)
        for name, value in zip(("a", "b", "c", "d"), counts):
            _set_count(name, value)
        table = Table2x2(*counts)
        alpha = float(st.session_state.get("alpha", 0.05))
        st.session_state["analysis_result"] = analyze_2x2(table, alpha, haldane_anscombe=False)
        st.session_state["analysis_counts"] = counts
        st.session_state["analysis_design"] = "Cohort / cross-sectional"
        st.session_state["saved_sampling_design"] = "Cohort / cross-sectional"
        st.session_state["sampling_design"] = "Cohort / cross-sectional"
        st.session_state["nav_section"] = NAV_ITEMS[0]
    elif key == "roc":
        frame = demo.copy()
        scores = frame["biomarker_score"].astype(float).tolist()
        outcomes = frame["gold_standard"].astype(int).tolist()
        signature_hash = hashlib.sha256(frame.to_csv(index=False).encode("utf-8")).hexdigest()
        result = DiagnosticTestAccuracy().from_scores(scores, outcomes)
        st.session_state["demo_roc_frame"] = frame
        st.session_state["dta_input_mode"] = "Continuous score + gold standard"
        st.session_state["dta_score_col"] = "biomarker_score"
        st.session_state["dta_gold_col"] = "gold_standard"
        st.session_state["dta_result"] = result
        st.session_state["dta_scores"] = scores
        st.session_state["dta_outcomes"] = outcomes
        st.session_state["dta_source_signature"] = ("clinical-demo", len(frame), "biomarker_score", "gold_standard", signature_hash)
        st.session_state["dta_input_sha256"] = signature_hash
        st.session_state["dta_input_name"] = "synthetic-diagnostic-biomarker-demo.csv"
        st.session_state["dca_result"] = None
        st.session_state["nav_section"] = NAV_ITEMS[2]
    else:
        text = "\n".join(f"{label},{a},{b},{c},{d}" for label, (a, b, c, d) in demo.items())
        st.session_state["advanced_strata_text"] = text
        st.session_state["stratified_result"] = analyze_stratified_tables(demo)
        st.session_state["stratified_inputs"] = text
        st.session_state["nav_section"] = NAV_ITEMS[4]
    if key != "roc":
        st.session_state["demo_roc_frame"] = None
    st.session_state["clinical_demo_loaded_notice"] = True
    st.rerun()


with st.sidebar:
    st.markdown(
        f"<div class='brand-panel'><div class='brand-title'>JouriEpi</div>"
        f"<div class='brand-meta'>Clinical Workstation | v{APP_VERSION}<br>Build {_BUILD_HASH}</div></div>",
        unsafe_allow_html=True,
    )
    institutional_logo = st.file_uploader(
        translate("institutional_logo", LANG), type=["png", "jpg", "jpeg"],
        key="institutional_logo_upload", help=translate("logo_help", LANG),
    )
    st.selectbox(
        translate("demo_dataset", LANG), options=["", *DEMO_DATASETS.keys()],
        format_func=lambda key: translate("demo_choose", LANG) if not key else translate(
            {"cardiovascular": "demo_cardiovascular", "roc": "demo_roc", "stratified": "demo_stratified"}[key], LANG
        ),
        key="clinical_demo_selector", on_change=_load_clinical_demo,
        help=translate("demo_disclaimer", LANG),
    )
    st.caption(translate("demo_disclaimer", LANG))
    if st.session_state.pop("clinical_demo_loaded_notice", False):
        st.success(translate("demo_loaded", LANG))
    if institutional_logo is not None:
        st.session_state["institutional_logo_bytes"] = institutional_logo.getvalue()
        st.session_state["institutional_logo_name"] = institutional_logo.name
        st.image(st.session_state["institutional_logo_bytes"], caption="Report logo preview", width=150)
    else:
        if st.session_state.pop("_workspace_logo_loaded", False):
            if st.session_state.get("institutional_logo_bytes"):
                st.image(st.session_state["institutional_logo_bytes"], caption="Restored report logo", width=150)
        else:
            st.session_state.pop("institutional_logo_bytes", None)
            st.session_state.pop("institutional_logo_name", None)
    with st.expander(translate("prefs_title", LANG), expanded=False):
        st.caption(f"{translate('prefs_path', LANG)}: {preferences_path()}")
        st.text_input(translate("prefs_author", LANG), key="institution_study_author", max_chars=300,
                      on_change=_save_local_preferences)
        st.text_input(translate("prefs_setting", LANG), key="institution_default_setting", max_chars=300,
                      on_change=_save_local_preferences)
    if st.session_state.get("show_workspace_panel"):
        with st.expander(translate("file", LANG) + " · Workspace", expanded=True):
            file_actions = st.columns(2)
            if file_actions[0].button(translate("new_session", LANG), key="new_jepi_session", width="stretch",
                                      help=translate("new_session", LANG)):
                keep = {"language": st.session_state.get("language", "en"), "dark_mode": st.session_state.get("dark_mode", False)}
                st.session_state.clear()
                st.session_state.update(keep)
                st.rerun()
            if file_actions[1].button(translate("export_dossier", LANG), key="menu_export_dossier", width="stretch",
                                      help=translate("export_dossier", LANG)):
                st.session_state["nav_section"] = NAV_ITEMS[5]
                st.session_state["show_workspace_panel"] = False
                st.rerun()
            workspace_keys = {"nav_section", "a", "b", "c", "d", "alpha", "use_ha",
                              "sampling_design", "planning_design", "planning_design_widget",
                              "planning_alpha", "power_plan", "line_design", "dta_input_mode",
                              "institutional_logo_bytes", "institutional_logo_name", "line_list_dataframe",
                              "line_list_source_name", "line_list_source_bytes", "language", "dark_mode",
                              "dossier_title", "dossier_study_id", "dossier_study_setting", "dossier_study_author"}
            workspace_state = {k: st.session_state[k] for k in workspace_keys if k in st.session_state}
            workspace_state.update({k: v for k, v in st.session_state.items()
                                    if k.startswith("saved_") and isinstance(v, (str, int, float, bool, tuple, list))})
            workspace_state["active_tab"] = st.session_state.get("nav_section", NAV_ITEMS[0])
            if st.button(translate("save_workspace", LANG), key="save_jepi_workspace", width="stretch"):
                try:
                    content = save_workspace(workspace_state, metadata={"application": "JouriEpi", "version": APP_VERSION})
                    st.download_button(translate("download_workspace", LANG), content, file_name="jouriepi-workspace.jepi",
                                       mime="application/zip", key="download_jepi_workspace", width="stretch")
                    st.success(translate("workspace_saved", LANG))
                except (ValueError, TypeError, OSError) as exc:
                    st.error(f"Workspace could not be saved: {exc}")
            workspace_file = st.file_uploader(translate("load_workspace", LANG), type=["jepi"], key="jepi_workspace_upload")
            if workspace_file is not None:
                if st.button(translate("load_selected_workspace", LANG), key="load_jepi_workspace", width="stretch"):
                    try:
                        restored = load_workspace(workspace_file.getvalue())
                        for key, value in restored.items():
                            if key.startswith("_") or key in {"language", "dark_mode", "active_tab"}:
                                continue
                            st.session_state[key] = value
                        if restored.get("institutional_logo_bytes"):
                            st.session_state["_workspace_logo_loaded"] = True
                        if restored.get("active_tab") in NAV_ITEMS:
                            st.session_state["nav_section"] = restored["active_tab"]
                        st.success(translate("workspace_loaded", LANG))
                        st.rerun()
                    except (ValueError, TypeError, KeyError, OSError) as exc:
                        st.error(f"Workspace could not be loaded: {exc}")
    st.markdown(f"**{translate('file', LANG)} · {translate('workspace', LANG)}**")
    st.radio(translate("workspace", LANG), NAV_ITEMS,
             format_func=lambda value: translate(NAV_TRANSLATION_KEYS[value], LANG),
             key="nav_section", label_visibility="collapsed",
             help=translate("workspace_help", LANG))
    st.divider()
    st.markdown(f"<span class='offline-badge'>{html.escape(translate('offline', LANG))}</span>", unsafe_allow_html=True)
    st.caption(translate("offline_detail", LANG))
    st.caption(translate("method_scope_note", LANG))

st.title(translate("title", LANG))
st.markdown(f'<div class="app-subtitle">{html.escape(translate("report_subtitle", LANG))}</div>', unsafe_allow_html=True)
st.markdown(f'<span class="offline-badge">● {html.escape(translate("offline", LANG))}</span>', unsafe_allow_html=True)


def render_analysis() -> None:
    st.markdown(f'<div class="section-kicker">{html.escape(translate("association_analysis", LANG))}</div>', unsafe_allow_html=True)
    st.header(translate("analysis", LANG) + " · 2×2")
    st.session_state["sampling_design"] = st.session_state.get("saved_sampling_design", "Cohort / cross-sectional")
    design = st.segmented_control(translate("sampling_design", LANG), ["Cohort / cross-sectional", "Case-control"],
                                  format_func=lambda value: translate("cohort_cross" if value == "Cohort / cross-sectional" else "case_control", LANG),
                                  key="sampling_design", help="Choose how participants were sampled; this determines which measures are identifiable.",
                                  selection_mode="single", on_change=_persist_value, args=("sampling_design",))
    design = design or "Cohort / cross-sectional"
    st.session_state["saved_sampling_design"] = design
    if design == "Case-control":
        st.caption("Case-control sampling supports the odds ratio. Risk ratios, risk differences and attributable fractions are not identifiable from sampled case/control margins.")
    else:
        st.caption("Cohort/cross-sectional counts support risks and risk differences when the sampled margins represent the target groups.")

    st.subheader(translate("contingency_table", LANG))
    st.caption("Enter counts in the four editable cells. Totals are calculated automatically.")
    with st.container(border=True):
        head = st.columns([1.15, 1, 1, 1])
        for col, label in zip(head, ["", translate("case_positive", LANG), translate("noncase_negative", LANG), translate("row_total", LANG)]):
            col.markdown(f"<div class='muted-note'><b>{label}</b></div>", unsafe_allow_html=True)
        r1 = st.columns([1.15, 1, 1, 1])
        r1[0].markdown(f"**{translate('exposed', LANG)}**")
        r1[1].number_input(f"a · {translate('exposed', LANG)} cases", min_value=0, step=1, key="a", on_change=_persist_count, args=("a",), help="Number exposed with disease/case outcome.", label_visibility="collapsed")
        r1[2].number_input(f"b · {translate('exposed', LANG)} non-cases", min_value=0, step=1, key="b", on_change=_persist_count, args=("b",), help="Number exposed without disease/case outcome.", label_visibility="collapsed")
        r1[3].markdown(f"**{int(st.session_state.a)+int(st.session_state.b):,}**<div class='muted-note'>row total</div>", unsafe_allow_html=True)
        r2 = st.columns([1.15, 1, 1, 1])
        r2[0].markdown(f"**{translate('unexposed', LANG)}**")
        r2[1].number_input(f"c · {translate('unexposed', LANG)} cases", min_value=0, step=1, key="c", on_change=_persist_count, args=("c",), help="Number unexposed with disease/case outcome.", label_visibility="collapsed")
        r2[2].number_input(f"d · {translate('unexposed', LANG)} non-cases", min_value=0, step=1, key="d", on_change=_persist_count, args=("d",), help="Number unexposed without disease/case outcome.", label_visibility="collapsed")
        r2[3].markdown(f"**{int(st.session_state.c)+int(st.session_state.d):,}**<div class='muted-note'>row total</div>", unsafe_allow_html=True)
        totals = st.columns([1.15, 1, 1, 1])
        totals[0].markdown(f"<span class='muted-note'>{html.escape(translate('column_totals', LANG))}</span>", unsafe_allow_html=True)
        totals[1].markdown(f"**{int(st.session_state.a)+int(st.session_state.c):,}**", unsafe_allow_html=True)
        totals[2].markdown(f"**{int(st.session_state.b)+int(st.session_state.d):,}**", unsafe_allow_html=True)
        totals[3].markdown(f"**{int(st.session_state.a)+int(st.session_state.b)+int(st.session_state.c)+int(st.session_state.d):,}**<div class='muted-note'>N</div>", unsafe_allow_html=True)
        alpha_cols = st.columns([1.1, 1.2, 2.2])
        st.session_state["alpha"] = st.session_state.get("saved_alpha", 0.05)
        st.session_state["use_ha"] = st.session_state.get("saved_use_ha", False)
        alpha = alpha_cols[0].segmented_control("Alpha", [0.10, 0.05, 0.01], key="alpha", format_func=lambda x: f"{x:.2f}", help="Two-sided type-I error rate used for confidence intervals.", on_change=_persist_value, args=("alpha",))
        st.session_state["saved_alpha"] = float(alpha or 0.05)
        confidence = int(round((1 - float(alpha or 0.05)) * 100))
        alpha_cols[1].markdown(f"<div style='padding-top:1.7rem'><b>{confidence}% CI</b></div>", unsafe_allow_html=True)
        alpha_cols[2].checkbox("Add 0.5 to every cell (sensitivity analysis)", key="use_ha", help="Haldane–Anscombe correction is reported separately and applies only when at least one observed cell is zero.", on_change=_persist_value, args=("use_ha",))
        st.session_state["saved_use_ha"] = bool(st.session_state.use_ha)
        total = sum(int(st.session_state[k]) for k in ("a", "b", "c", "d"))
        if int(st.session_state.a)+int(st.session_state.b) == 0:
            st.error("The exposed row total is zero. Add at least one exposed participant.")
        if int(st.session_state.c)+int(st.session_state.d) == 0:
            st.error("The unexposed row total is zero. Add at least one unexposed participant.")
        if int(st.session_state.a)+int(st.session_state.c) == 0 and total > 0:
            st.warning("The case (D+) column total is zero. Case risks and some association estimates will be undefined.")
        if int(st.session_state.b)+int(st.session_state.d) == 0 and total > 0:
            st.warning("The non-case (D−) column total is zero. Some association estimates will be undefined.")
        if total == 0:
            st.error("The grand total N must be greater than zero.")
        actions = st.columns([1.2, 1, 1, 3])
        calculate = actions[0].button("Calculate", type="primary", width="stretch")
        actions[1].button("Reset", on_click=_reset_table, width="stretch")
        actions[2].button("Load example", on_click=_load_example, width="stretch")
        actions[3].markdown("<div class='muted-note' style='padding-top:.65rem'>All estimates are recalculated only when you select Calculate.</div>", unsafe_allow_html=True)
        if calculate:
            try:
                table = Table2x2(*(int(st.session_state[k]) for k in ("a", "b", "c", "d")))
                st.session_state.analysis_result = analyze_2x2(table, float(alpha or 0.05), haldane_anscombe=bool(st.session_state.use_ha))
                st.session_state.analysis_counts = (table.a, table.b, table.c, table.d)
                st.session_state.analysis_design = design
            except ValueError as exc:
                st.session_state.analysis_result = None
                st.error(str(exc))

    result = st.session_state.get("analysis_result")
    if not result:
        st.info("Enter your 2×2 counts and select **Calculate** to view estimates, tests, and assumptions.", icon="ℹ️")
        return
    if st.session_state.analysis_counts != tuple(int(st.session_state[k]) for k in ("a", "b", "c", "d")):
        st.info("Counts have changed since the last calculation. Select **Calculate** to refresh the displayed results.")
        return
    design = st.session_state.get("analysis_design", design)
    a,b,c,d = st.session_state.analysis_counts
    confidence = f"{int(round((1-float(result['alpha']))*100))}%"
    st.divider()
    st.markdown('<div class="section-kicker">Results</div>', unsafe_allow_html=True)
    st.subheader("Key estimates")
    if design == "Case-control":
        cards = st.columns(4)
        cards[0].markdown('<div class="metric-card"><div class="metric-label">Risk ratio</div><div class="metric-value">Not shown</div><div class="metric-detail">Invalid for case-control sampling</div><div class="metric-status status-warn">● Not identifiable</div></div>', unsafe_allow_html=True)
    else:
        cards = st.columns(4)
        rr_ci = result.get("risk_ratio_katz_ci")
        rr_status = "good" if rr_ci and (rr_ci[0] > 1 or rr_ci[1] < 1) else ("neutral" if rr_ci else "warn")
        with cards[0]: metric_card("Risk ratio", fmt_num(result.get("risk_ratio")), f"{confidence} CI {fmt_ci(rr_ci)}", rr_status)
    or_ci = result.get("odds_ratio_woolf_ci")
    or_status = "good" if or_ci and (or_ci[0] > 1 or or_ci[1] < 1) else ("neutral" if or_ci else "warn")
    with cards[1]: metric_card("Odds ratio", fmt_num(result.get("odds_ratio")), f"{confidence} CI {fmt_ci(or_ci)}", or_status)
    if design != "Case-control":
        rd_ci = result.get("risk_difference_wald_ci")
        rd_status = "good" if rd_ci and (rd_ci[0] > 0 or rd_ci[1] < 0) else "neutral"
        with cards[2]: metric_card("Risk difference", fmt_pct(result.get("risk_difference")), f"{confidence} CI {fmt_pct(rd_ci[0]) if rd_ci else '—'} – {fmt_pct(rd_ci[1]) if rd_ci else '—'}", rd_status)
    else:
        cards[2].markdown('<div class="metric-card"><div class="metric-label">Risk difference</div><div class="metric-value">Not shown</div><div class="metric-detail">Invalid for case-control sampling</div><div class="metric-status status-warn">● Not identifiable</div></div>', unsafe_allow_html=True)
    pval = result.get("fisher_two_sided_p")
    with cards[3]: metric_card("Fisher exact p", fmt_p(pval), "Two-sided · probability ordering", "good" if pval is not None and pval < float(result["alpha"]) else "neutral", "p < α" if pval is not None and pval < float(result["alpha"]) else "p ≥ α")

    if st.session_state.use_ha:
        ha = result.get("odds_ratio_haldane_anscombe")
        ha_ci = result.get("odds_ratio_haldane_anscombe_woolf_ci")
        if any(x == 0 for x in (a,b,c,d)):
            st.caption(f"Haldane–Anscombe sensitivity estimate: OR {fmt_num(ha)}; {confidence} CI {fmt_ci(ha_ci)}. A 0.5 correction was applied to all four cells because at least one observed cell is zero.")
        else:
            st.caption("No zero cells, so the corrected estimate equals the standard one. No duplicate sensitivity row is shown.")

    st.subheader("Association measures")
    rows = []
    if design != "Case-control":
        rows.extend([
            ("Risk in exposed", fmt_pct(result.get("risk_exposed")), None, "a / (a+b)", "Observed case proportion among exposed participants."),
            ("Risk in unexposed", fmt_pct(result.get("risk_unexposed")), None, "c / (c+d)", "Observed case proportion among unexposed participants."),
            ("Risk ratio", fmt_num(result.get("risk_ratio")), result.get("risk_ratio_katz_ci"), "Katz", "Ratio of exposed to unexposed risks; null value = 1."),
            ("Risk difference", fmt_num(result.get("risk_difference")), result.get("risk_difference_wald_ci"), "Wald", "Absolute difference in risks; null value = 0."),
            ("Attributable fraction among exposed", fmt_pct(result.get("attributable_fraction_exposed")), result.get("attributable_fraction_exposed_katz_ci"), "Katz transform", "Fraction of exposed-group risk above the unexposed baseline; descriptive, not causal."),
            ("Population attributable fraction", fmt_pct(result.get("population_attributable_fraction")), None, "Risk-based definition", "Population risk contrast under the implemented definition; not shown for case-control designs."),
        ])
    rows.append(("Odds ratio", fmt_num(result.get("odds_ratio")), result.get("odds_ratio_woolf_ci"), "Woolf", "Ratio of disease odds; null value = 1."))
    result_table(rows, confidence)

    forest_markup = forest_plot_svg(result, confidence)
    with st.expander("Forest plot · confidence intervals", expanded=True):
        st.markdown(f'<div class="result-panel">{forest_markup}<div class="muted-note">Text alternative: RR {fmt_num(result.get("risk_ratio"))} ({fmt_ci(result.get("risk_ratio_katz_ci"))}); OR {fmt_num(result.get("odds_ratio"))} ({fmt_ci(result.get("odds_ratio_woolf_ci"))}); RD {fmt_num(result.get("risk_difference"))} ({fmt_ci(result.get("risk_difference_wald_ci"))}). Dashed lines indicate null values (1 for ratios, 0 for risk difference).</div></div>', unsafe_allow_html=True)
    try:
        forest_svg, forest_png, forest_pdf = figure_export_payloads(forest_markup)
        export_cols = st.columns(3)
        export_cols[0].download_button("Download forest plot (SVG)", forest_svg, file_name="jouriepi-forest-plot.svg", mime="image/svg+xml", key="export_forest_svg")
        export_cols[1].download_button("Download forest plot (300 DPI PNG)", forest_png, file_name="jouriepi-forest-plot-300dpi.png", mime="image/png", key="export_forest_png")
        export_cols[2].download_button("Download forest plot (vector PDF)", forest_pdf, file_name="jouriepi-forest-plot.pdf", mime="application/pdf", key="export_forest_pdf")
    except (ValueError, RuntimeError, OSError) as exc:
        st.caption(f"Figure exports unavailable: {exc}")

    st.subheader("Statistical tests")
    tests = [
        {"Test": "Pearson χ²", "Statistic": fmt_num(result.get("pearson_chi2")), "p-value": fmt_p(result.get("pearson_p")), "When to use": "Asymptotic test of independence; review expected counts."},
        {"Test": "Yates-corrected χ²", "Statistic": fmt_num(result.get("yates_chi2")), "p-value": fmt_p(result.get("yates_p")), "When to use": "Continuity-corrected asymptotic test for a 2×2 table."},
        {"Test": "Fisher exact · two-sided", "Statistic": "—", "p-value": fmt_p(result.get("fisher_two_sided_p")), "When to use": "Conditional exact test; two-sided p uses probability ordering."},
        {"Test": "Fisher exact · less", "Statistic": "—", "p-value": fmt_p(result.get("fisher_less_p")), "When to use": "One-sided alternative: exposed-case cell a is smaller than expected under the null."},
        {"Test": "Fisher exact · greater", "Statistic": "—", "p-value": fmt_p(result.get("fisher_greater_p")), "When to use": "One-sided alternative: exposed-case cell a is larger than expected under the null."},
    ]
    st.dataframe(tests, hide_index=True, width="stretch", column_config={"Test": st.column_config.TextColumn("Test", help="Pearson/Yates are asymptotic chi-square tests; Fisher is conditional exact."), "p-value": st.column_config.TextColumn("p-value", help="Probability, under the null model, of results at least as extreme as observed under the specified test."), "When to use": st.column_config.TextColumn("When to use", width="large")})

    st.subheader("Assumptions & observed counts")
    audit = audit_expected_counts(Table2x2(a,b,c,d))
    chip = (f'<span class="status-chip chip-warn">⚠ {audit["cells_below_5"]} expected cell(s) below 5 · consider Fisher</span>' if audit["any_expected_below_5"] else '<span class="status-chip chip-good">✓ All expected counts ≥ 5</span>')
    st.markdown(chip, unsafe_allow_html=True)
    expected = audit["expected_counts"]
    st.markdown(expected_counts_grid(expected), unsafe_allow_html=True)
    st.caption(f"Expected-count text alternative: exposed cases {expected[0][0]:.2f}, exposed non-cases {expected[0][1]:.2f}; unexposed cases {expected[1][0]:.2f}, unexposed non-cases {expected[1][1]:.2f}. Amber cells are below 5.")
    if audit["zero_observed_cells"]:
        st.warning(f"{audit['zero_observed_cells']} observed cell(s) are zero. Some ratio intervals are not estimable without a separately requested correction.")
    else:
        st.caption("No zero observed cells.")

    risk1, risk0 = result.get("risk_exposed"), result.get("risk_unexposed")
    if design == "Case-control":
        summary = f"The observed case/control table has an odds ratio of {fmt_num(result.get('odds_ratio'))} ({confidence} CI {fmt_ci(or_ci)}). This is a descriptive association; interpretation depends on the study design and sampling assumptions."
    elif risk1 is not None and risk0 is not None and result.get("risk_ratio") is not None:
        rr = result["risk_ratio"]
        direction = "higher" if rr > 1 else ("lower" if rr < 1 else "the same")
        summary = f"The observed risk among exposed participants was {fmt_num(rr)} times the unexposed risk ({direction} relative risk; RR {fmt_num(rr)}, {confidence} CI {fmt_ci(result.get('risk_ratio_katz_ci'))}). This is a descriptive association, not evidence of causation."
    else:
        summary = f"The risk ratio is not estimable from this table. The observed risk difference was {fmt_pct(result.get('risk_difference'))}; interpret estimates in light of the sampling design and sparse-cell limitations."
    st.markdown(f'<div class="result-panel"><div class="section-kicker">Plain-language summary</div><div class="summary-text">{html.escape(summary)}</div></div>', unsafe_allow_html=True)

    export_text = (f"JouriEpi — {design}\nCounts (a,b,c,d): {a}, {b}, {c}, {d}\n"
                   f"Risk ratio: {fmt_num(result.get('risk_ratio'))}; {confidence} CI {fmt_ci(result.get('risk_ratio_katz_ci'))}\n"
                   f"Odds ratio: {fmt_num(result.get('odds_ratio'))}; {confidence} CI {fmt_ci(or_ci)}\n"
                   f"Risk difference: {fmt_num(result.get('risk_difference'), 3)}; {confidence} CI {fmt_ci(result.get('risk_difference_wald_ci'), 3)}\n"
                   f"Fisher exact two-sided: {fmt_p(pval)}\nPearson chi-square: {fmt_num(result.get('pearson_chi2'))}; {fmt_p(result.get('pearson_p'))}\n"
                   "Methods: modern reference calculations; asymptotic intervals; exact parity with historical software has not been verified.")
    with st.expander("Copy results", expanded=False):
        st.caption("Use the copy control on this text block to copy a report-ready summary.")
        st.code(export_text, language=None)
    c1,c2,c3 = st.columns(3)
    c1.download_button("Download results (.txt)", export_text, file_name="jouriepi-results.txt", mime="text/plain", width="stretch", help="Download a report-ready plain-text summary.")
    csv_rows = [{"Measure": label, "Estimate": value, "CI": ci, "Method": method} for label,value,ci,method,_ in rows]
    c2.download_button("Download CSV", pd.DataFrame(csv_rows).to_csv(index=False).encode("utf-8-sig"), file_name="jouriepi-results.csv", mime="text/csv", width="stretch")
    c3.download_button("Download forest plot (PNG)", forest_plot_png_bytes(result), file_name="jouriepi-forest-plot.png", mime="image/png", width="stretch", help="Download a report-ready PNG generated locally in this session.")
    with st.expander("Methods & caveats"):
        st.markdown("""**Confidence intervals (large-sample methods)**

        - **Odds ratio — Woolf:** log(OR) ± z × √(1/a + 1/b + 1/c + 1/d), exponentiated.
        - **Risk ratio — Katz:** log(RR) ± z × √(1/a − 1/(a+b) + 1/c − 1/(c+d)), exponentiated.
        - **Risk difference — Wald:** RD ± z × √(p₁(1−p₁)/(a+b) + p₀(1−p₀)/(c+d)).
        - **Attributable fraction among exposed:** transformed RR interval where estimable.

        Intervals are asymptotic. Fisher two-sided p uses probability ordering. Expected-count warnings do not automatically switch tests. Exact parity with historical software has **not** been verified. Association measures describe observed data and do not establish causation.""")


def render_line_list() -> None:
    st.markdown('<div class="section-kicker">Data import workflow</div>', unsafe_allow_html=True)
    st.header("Line list → 2×2")
    steps = st.columns(4)
    for col, num, label in zip(steps, ("1", "2", "3", "4"), ("Upload", "Map columns", "Confirm values", "Result")):
        col.markdown(f"<div class='step-label'><span class='step-active'>{num}</span>　{label}</div>", unsafe_allow_html=True)
    st.caption("Choose a local CSV, Excel, or SPSS .sav file. Aggregation is blocked if exposure or outcome values are missing; resolve those rows in the source file and upload it again. This app never silently drops records.")
    uploaded = st.file_uploader("Upload line-list file", type=["csv", "xlsx", "xlsm", "xls", "sav"], key="line_file", help="Supported formats: CSV, Excel, and SPSS .sav. File processing stays within this local app session.")
    if not uploaded:
        st.info("Upload a CSV, Excel, or SPSS .sav line list to preview rows, map the exposure and outcome, and build a 2×2 table.", icon="📄")
        return
    try:
        upload_bytes = uploaded.getvalue()
        upload_fingerprint = hashlib.sha256(upload_bytes).hexdigest()
        upload_md5 = hashlib.md5(upload_bytes, usedforsecurity=False).hexdigest()
        frame = load_uploaded_table(uploaded, uploaded.name)
        st.session_state["line_list_dataframe"] = frame.copy()
        st.session_state["line_list_source_name"] = uploaded.name
        st.session_state["line_list_source_bytes"] = upload_bytes
        if st.session_state.get("line_result") and st.session_state.line_result.get("fingerprint") != upload_fingerprint:
            st.session_state.line_result = None
        if st.session_state.get("line_fingerprint") != upload_fingerprint:
            st.session_state["line_fingerprint"] = upload_fingerprint
            st.session_state["line_result"] = None
            st.session_state["line_stratified_result"] = None
            st.session_state.pop("line_exposed_value", None)
            st.session_state.pop("line_case_value", None)
        if frame.empty:
            st.warning("The uploaded file has headers but no data rows. Add data and upload it again.")
            return
        if not frame.columns.is_unique:
            st.error("Column names are duplicated. Rename duplicate columns in the source file and upload it again.")
            return
        st.subheader("Step 1 ? Data Integrity & Health")
        health = inspect_line_list(frame)
        health_cols = st.columns(4)
        health_cols[0].metric("Rows", f"{health['rows']:,}")
        health_cols[1].metric("Columns", f"{health['columns']:,}")
        health_cols[2].metric("Missing cells", f"{health['missing_count']:,}")
        health_cols[3].metric("Missing values", f"{health['missing_pct']:.1f}%")
        st.dataframe(pd.DataFrame(health["types"]), hide_index=True, width="stretch")
        st.caption("Pre-flight check is diagnostic only. No values are changed and no records are dropped.")
        st.dataframe(frame.head(10), hide_index=True, width="stretch")
        missing = pd.Series({item["Column"]: item["Missing"] for item in health["types"]}, dtype="int64")
        with st.expander("Missing values by column"):
            st.dataframe(pd.DataFrame({"Column": missing.index.astype(str), "Missing values": missing.values, "Missing %": (missing.values / len(frame) * 100).round(1)}), hide_index=True, width="stretch")
        if len(frame.columns) < 2:
            st.error("The file must contain at least two columns to define exposure and outcome.")
            return
        st.subheader("Step 2 · Map columns")
        columns = list(frame.columns)
        lower_names = {str(x).lower(): x for x in columns}
        exposure_guess = next((lower_names[x] for x in ("exposure", "exposed", "treatment", "group") if x in lower_names), columns[0])
        outcome_guess = next((lower_names[x] for x in ("outcome", "case", "disease", "status", "event") if x in lower_names and lower_names[x] != exposure_guess), columns[1])
        exposure_col = st.selectbox("Exposure column", columns, index=columns.index(exposure_guess), key="line_exposure_col", help="Column identifying exposed and unexposed participants.")
        outcome_choices = [x for x in columns if x != exposure_col]
        if not outcome_choices:
            st.error("Choose two different columns.")
            return
        if st.session_state.get("line_outcome_col") not in outcome_choices:
            st.session_state["line_outcome_col"] = outcome_guess if outcome_guess in outcome_choices else outcome_choices[0]
        outcome_col = st.selectbox("Outcome column", outcome_choices, index=outcome_choices.index(st.session_state["line_outcome_col"]), key="line_outcome_col", help="Column identifying case/disease and non-case values.")
        stratification_choices = ["None"] + [x for x in columns if x not in {exposure_col, outcome_col}]
        selected_stratum = st.selectbox(
            "Select Stratification Column (e.g., age group, site, sex)",
            stratification_choices, key="line_stratum_col",
            help="Optional: compare exposure–outcome associations across strata. Missing values in this column block stratified analysis.")
        selected_stratum = None if selected_stratum == "None" else selected_stratum
        binary_health = inspect_line_list(frame, exposure_col, outcome_col)["binary_checks"]
        health_left, health_right = st.columns(2)
        for column, role in ((health_left, "exposure"), (health_right, "outcome")):
            check = binary_health[role]
            if check["valid_binary"]:
                column.markdown(f"<span class='status-chip chip-good'>? {role.title()} is binary</span>", unsafe_allow_html=True)
                column.caption(f"{check['column']}: {', '.join(check['categories'])}")
            else:
                column.markdown(f"<span class='status-chip chip-warn'>? {role.title()} needs review</span>", unsafe_allow_html=True)
                column.warning(f"{check['column']}: " + "; ".join(check["issues"]))
        st.subheader("Step 3 · Confirm values")
        exposure_values = list(frame[exposure_col].dropna().unique())
        outcome_values = list(frame[outcome_col].dropna().unique())
        if frame[exposure_col].isna().any() or frame[outcome_col].isna().any():
            st.warning(f"Missing values: {int(frame[exposure_col].isna().sum())} in exposure and {int(frame[outcome_col].isna().sum())} in outcome. Aggregation is blocked until these rows are handled in the source data; no rows are silently dropped.")
            return
        if len(exposure_values) != 2 or len(outcome_values) != 2:
            st.warning(f"Exposure has {len(exposure_values)} non-missing distinct values; outcome has {len(outcome_values)}. Each must have exactly two categories. Recode/filter the source file first.")
            return
        if st.session_state.get("line_exposed_value") not in exposure_values:
            st.session_state["line_exposed_value"] = exposure_values[0]
        if st.session_state.get("line_case_value") not in outcome_values:
            st.session_state["line_case_value"] = outcome_values[0]
        e1,e2 = st.columns(2)
        exposed_value = e1.selectbox("Which exposure value means exposed?", exposure_values, key="line_exposed_value")
        case_value = e2.selectbox("Which outcome value means case / disease?", outcome_values, key="line_case_value")
        st.session_state["line_design"] = st.session_state.get("saved_line_design", "Cohort / cross-sectional")
        line_design = st.segmented_control("Sampling design", ["Cohort / cross-sectional", "Case-control"], key="line_design", help="Select the design used to sample the records.", on_change=_persist_value, args=("line_design",)) or "Cohort / cross-sectional"
        st.session_state["saved_line_design"] = line_design
        if st.button("Aggregate", type="primary", key="aggregate_line_list"):
            try:
                counts = aggregate_line_list(frame, exposure_col, outcome_col, exposed_value, case_value)
                if sum(counts) <= 0:
                    raise ValueError("No eligible rows were available to aggregate.")
                st.session_state.line_result = {"counts": counts, "design": line_design, "source": uploaded.name,
                                                 "fingerprint": upload_fingerprint, "exposure_col": exposure_col,
                                                 "outcome_col": outcome_col, "exposed_value": exposed_value,
                                                 "case_value": case_value, "stratum_col": selected_stratum,
                                                 "input_md5": upload_md5, "input_sha256": upload_fingerprint}
            except ValueError as exc:
                st.session_state["line_result"] = None
                st.error(str(exc))
        result = st.session_state.get("line_result")
        if result and (result.get("exposure_col") != exposure_col or result.get("outcome_col") != outcome_col
                       or result.get("exposed_value") != exposed_value or result.get("case_value") != case_value
                       or result.get("stratum_col") != selected_stratum
                       or result.get("fingerprint") != upload_fingerprint
                       or result.get("design") != line_design):
            st.session_state["line_result"] = None
            st.session_state["line_stratified_result"] = None
            result = None
            st.info("The mapping or reference categories changed, or the sampling design changed, after aggregation. Select **Aggregate** again to refresh the 2×2 result.")
        if result:
            counts = result["counts"]
            st.subheader("Step 4 · Aggregated result")
            st.markdown(f"**Source:** {html.escape(result['source'])} · **N = {sum(counts):,}**")
            table_2x2(*counts)
            st.dataframe([{"Cell": "a · Exposed cases", "Count": counts[0]}, {"Cell": "b · Exposed non-cases", "Count": counts[1]}, {"Cell": "c · Unexposed cases", "Count": counts[2]}, {"Cell": "d · Unexposed non-cases", "Count": counts[3]}], hide_index=True, width="stretch")
            def send_to_analysis():
                for key, value in zip(("a", "b", "c", "d"), counts):
                    _set_count(key, int(value))
                st.session_state["sampling_design"] = line_design
                st.session_state["saved_sampling_design"] = line_design
                table = Table2x2(*(int(value) for value in counts))
                st.session_state["analysis_result"] = analyze_2x2(
                    table, float(st.session_state.get("alpha", 0.05)),
                    haldane_anscombe=bool(st.session_state.get("use_ha", False)))
                st.session_state["analysis_counts"] = tuple(int(value) for value in counts)
                st.session_state["analysis_design"] = line_design
                st.session_state["nav_section"] = "2×2 Analysis"
            st.button("Send to 2×2 Analysis", on_click=send_to_analysis, type="primary")
            if selected_stratum:
                st.subheader("Multi-strata comparison")
                try:
                    sr = analyze_stratified_dataframe(
                        frame, exposure_col=exposure_col, outcome_col=outcome_col,
                        stratum_col=selected_stratum, exposed_value=exposed_value,
                        case_value=case_value)
                    st.session_state["line_stratified_result"] = sr
                    strata_rows = [{
                        "Stratum": item.label, "a": item.counts[0], "b": item.counts[1],
                        "c": item.counts[2], "d": item.counts[3],
                        "OR": item.odds_ratio, "OR 95% CI": item.odds_ratio_ci,
                        "RR": item.risk_ratio, "RR 95% CI": item.risk_ratio_ci,
                        "OR (Haldane–Anscombe sensitivity)": item.odds_ratio_haldane_anscombe,
                    } for item in sr.strata]
                    st.dataframe(pd.DataFrame(strata_rows), hide_index=True, width="stretch")
                    c1, c2 = st.columns(2)
                    with c1:
                        metric_card("Mantel–Haenszel pooled OR", fmt_num(sr.mantel_haenszel_odds_ratio),
                                    f"RBG 95% CI {fmt_ci(sr.mantel_haenszel_odds_ratio_ci) if sr.mantel_haenszel_odds_ratio_ci else 'not estimable'}", "neutral")
                    with c2:
                        metric_card("Mantel–Haenszel pooled RR", fmt_num(sr.mantel_haenszel_risk_ratio),
                                    "No continuity correction applied", "neutral")
                    st.markdown(stratified_forest_plot_svg(sr.strata, sr.mantel_haenszel_odds_ratio,
                                                           sr.mantel_haenszel_odds_ratio_ci), unsafe_allow_html=True)
                    try:
                        strat_svg, strat_png, strat_pdf = figure_export_payloads(stratified_forest_plot_svg(
                            sr.strata, sr.mantel_haenszel_odds_ratio, sr.mantel_haenszel_odds_ratio_ci))
                        ecols = st.columns(3)
                        ecols[0].download_button("Stratified forest (SVG)", strat_svg, file_name="jouriepi-stratified-forest.svg", mime="image/svg+xml", key="export_strat_svg")
                        ecols[1].download_button("Stratified forest (300 DPI PNG)", strat_png, file_name="jouriepi-stratified-forest.png", mime="image/png", key="export_strat_png")
                        ecols[2].download_button("Stratified forest (vector PDF)", strat_pdf, file_name="jouriepi-stratified-forest.pdf", mime="application/pdf", key="export_strat_pdf")
                    except (ValueError, RuntimeError, OSError) as exc:
                        st.caption(f"Stratified figure exports unavailable: {exc}")
                    if sr.simpsons_paradox_detected:
                        st.warning("Potential Simpson’s paradox reversal detected: crude and stratum-specific OR directions disagree. Interpret in the context of study design and confounding assumptions.")
                    for warning in sr.warnings:
                        st.caption(warning)
                    if sr.effect_measure_modification:
                        st.warning("Effect measure modification flagged: Breslow–Day homogeneity test p < 0.05. Consider stratum-specific estimates rather than interpreting the pooled estimate as a single common effect.")
                except (ValueError, TypeError) as exc:
                    st.session_state["line_stratified_result"] = None
                    st.warning(f"Stratified analysis unavailable: {exc}")
            else:
                st.session_state["line_stratified_result"] = None
    except ValueError as exc:
        st.session_state["line_result"] = None
        st.error(f"Could not use this file: {exc}")
    except (OSError, ImportError, RuntimeError, TypeError, BadZipFile, pd.errors.ParserError, pd.errors.EmptyDataError):
        st.session_state["line_result"] = None
        st.error("Could not read this file. Check that it is a valid, non-empty CSV or Excel workbook with a header row, then try again.")


def render_power() -> None:
    st.markdown('<div class="section-kicker">Study planning</div>', unsafe_allow_html=True)
    st.header("Sample size & power")
    st.session_state["planning_design_widget"] = st.session_state.get("saved_planning_design_widget", "Cohort")
    st.session_state["planning_alpha"] = st.session_state.get("saved_planning_alpha", 0.05)
    st.session_state["power_plan"] = st.session_state.get("saved_power_plan", 0.80)
    design = st.segmented_control("Study design", ["Cohort", "Cross-sectional", "Case-control"], key="planning_design_widget", help="The design determines how group sizes and target effects are parameterized.", on_change=_persist_value, args=("planning_design_widget",)) or "Cohort"
    st.session_state["planning_design"] = design
    st.session_state["saved_planning_design_widget"] = design
    st.session_state["saved_planning_design"] = design
    st.caption("Inputs are planning assumptions, not observed data. Estimates use an independent two-proportion normal approximation.")
    if design == "Case-control":
        col1,col2,col3 = st.columns(3)
        odds_ratio = col1.number_input("Target odds ratio", min_value=0.001, value=1.5, step=0.1, help="Target ratio of disease odds for exposed versus unexposed.")
        p_control = col2.number_input("Exposure prevalence among controls", min_value=0.001, max_value=0.999, value=0.22, step=0.01, help="Proportion exposed among controls.")
        allocation = col3.number_input("Cases per control", min_value=0.1, value=1.0, step=0.5, help="Target ratio of cases to controls.")
        p_case = odds_ratio * p_control / (1 - p_control + odds_ratio * p_control)
        p_exposed = p_case
    else:
        col1,col2,col3 = st.columns(3)
        p_control = col1.number_input("Risk / prevalence in unexposed", min_value=0.001, max_value=0.999, value=0.10, step=0.01, help="Expected outcome proportion in the unexposed group.")
        p_exposed = col2.number_input("Risk / prevalence in exposed", min_value=0.001, max_value=0.999, value=0.20, step=0.01, help="Expected outcome proportion in the exposed group.")
        allocation = col3.number_input("Exposed per unexposed", min_value=0.1, value=1.0, step=0.5, help="Allocation ratio: exposed sample size divided by unexposed sample size.")
    alpha_plan = st.segmented_control("Planning alpha", [0.10, 0.05, 0.01], key="planning_alpha", format_func=lambda x: f"{x:.2f}", help="Two-sided type-I error rate.", on_change=_persist_value, args=("planning_alpha",)) or 0.05
    st.session_state["saved_planning_alpha"] = float(alpha_plan)
    power_cols = st.columns([2, 3])
    power_plan = power_cols[0].slider("Target power", min_value=0.50, max_value=0.99, step=0.01, key="power_plan", help="Probability of rejecting the null under the specified alternative, under this approximation.", on_change=_persist_value, args=("power_plan",))
    st.session_state["saved_power_plan"] = float(power_plan)
    power_cols[1].markdown("<div class='muted-note' style='padding-top:1.8rem'>Range: 0.50–0.99 · Common targets: 0.80 / 0.90 / 0.95</div>", unsafe_allow_html=True)
    quick = st.columns(3)
    for col, value in zip(quick, (0.80, 0.90, 0.95)):
        col.button(f"Power {value:.2f}", key=f"quick_power_{value}", width="stretch", on_click=_set_persisted_value, args=("power_plan", value))
    if st.button("Calculate sample size", type="primary", key="calculate_power"):
        try:
            if design == "Case-control":
                n_control, n_exposed = case_control_sample_size(float(odds_ratio), float(p_control), float(alpha_plan), float(power_plan), float(allocation))
                achieved_power = two_proportion_power(n_control, n_exposed, float(p_control), float(p_exposed), float(alpha_plan))
                group_a, group_b = "Controls", "Cases"
            else:
                fn = cohort_sample_size if design == "Cohort" else cross_sectional_sample_size
                n_control, n_exposed = fn(float(p_control), float(p_exposed), float(alpha_plan), float(power_plan), float(allocation))
                achieved_power = two_proportion_power(n_control, n_exposed, float(p_control), float(p_exposed), float(alpha_plan))
                group_a, group_b = "Unexposed", "Exposed"
            st.session_state.power_result = {"design": design, "n_control": n_control, "n_exposed": n_exposed, "achieved_power": achieved_power, "target_power": power_plan, "alpha": alpha_plan, "p_control": p_control, "p_exposed": p_exposed, "allocation": allocation, "group_a": group_a, "group_b": group_b, "odds_ratio": odds_ratio if design == "Case-control" else None}
        except ValueError as exc:
            st.session_state.power_result = None
            st.error(f"Could not calculate sample size: {exc}")
    result = st.session_state.get("power_result")
    if not result:
        st.info("Set your parameters and click **Calculate sample size** to see group sizes, achieved power, and the power curve.", icon="ℹ️")
        return
    st.subheader("Recommended sample")
    total_n = result["n_control"] + result["n_exposed"]
    m1,m2,m3,m4 = st.columns(4)
    with m1: metric_card(result["group_a"], f"{result['n_control']:,}", "participants", "neutral")
    with m2: metric_card(result["group_b"], f"{result['n_exposed']:,}", "participants", "neutral")
    with m3: metric_card("Total N", f"{total_n:,}", "participants", "neutral")
    with m4: metric_card("Achieved power", fmt_pct(result["achieved_power"]), f"Target {fmt_pct(result['target_power'])}", "good" if result["achieved_power"] >= result["target_power"] else "neutral", "Target met" if result["achieved_power"] >= result["target_power"] else "Below target")
    def calc_power_for_total(n):
        if design == "Case-control":
            control_n = max(2, int(round(n / (1 + result["allocation"]))))
            case_n = max(2, int(round(control_n * result["allocation"])))
        else:
            control_n = max(2, int(round(n / (1 + result["allocation"]))))
            case_n = max(2, int(round(control_n * result["allocation"])))
        return two_proportion_power(control_n, case_n, float(result["p_control"]), float(result["p_exposed"]), float(result["alpha"]))
    st.subheader("Power curve")
    power_markup = power_curve_svg(calc_power_for_total, total_n, result["achieved_power"])
    st.markdown(f'<div class="result-panel">{power_markup}<div class="muted-note">The curve is an approximate sensitivity view around the selected total N. Text alternative: selected N = {total_n:,}; achieved power = {fmt_pct(result["achieved_power"])}.</div></div>', unsafe_allow_html=True)
    try:
        power_svg, power_png, power_pdf = figure_export_payloads(power_markup)
        exports = st.columns(3)
        exports[0].download_button("Power curve (SVG)", power_svg, file_name="jouriepi-power-curve.svg", mime="image/svg+xml", key="export_power_svg")
        exports[1].download_button("Power curve (300 DPI PNG)", power_png, file_name="jouriepi-power-curve.png", mime="image/png", key="export_power_png")
        exports[2].download_button("Power curve (vector PDF)", power_pdf, file_name="jouriepi-power-curve.pdf", mime="application/pdf", key="export_power_pdf")
    except (ValueError, RuntimeError, OSError) as exc:
        st.caption(f"Power curve exports unavailable: {exc}")
    if design == "Case-control":
        assumptions = f"Case-control normal approximation; target OR {fmt_num(result['odds_ratio'])}, control exposure prevalence {fmt_pct(result['p_control'])}, cases per control {fmt_num(result['allocation'])}, two-sided α={result['alpha']:.2f}, target power {fmt_pct(result['target_power'])}."
    else:
        assumptions = f"Independent two-proportion normal approximation; unexposed proportion {fmt_pct(result['p_control'])}, exposed proportion {fmt_pct(result['p_exposed'])}, exposed:unexposed allocation {fmt_num(result['allocation'])}:1, two-sided α={result['alpha']:.2f}, target power {fmt_pct(result['target_power'])}."
    st.caption(assumptions)
    st.caption("Excludes clustering, complex survey design, attrition and survival-time methods. These are modern planning calculations and are not claimed to reproduce historical software.")


def render_dta() -> None:
    st.markdown('<div class="section-kicker">Clinical diagnostics</div>', unsafe_allow_html=True)
    st.header("Diagnostic Test Accuracy (DTA)" if LANG == "en" else ("Précision diagnostique" if LANG == "fr" else "Diagnostische Testgüte"))
    st.caption("Use a reference-standard 2×2 table for a single operating point, or upload patient-level scores and binary reference outcomes to estimate a full ROC curve and AUC. Intervals are asymptotic/reference intervals, not regulatory validation.")
    mode = st.segmented_control("Input method", ["2×2 diagnostic table", "Continuous score + gold standard"], key="dta_input_mode")
    if mode != "Continuous score + gold standard":
        st.subheader("Diagnostic contingency table")
        cols = st.columns(4)
        tp = cols[0].number_input("True positives (TP)", min_value=0, value=45, step=1, key="dta_tp")
        fp = cols[1].number_input("False positives (FP)", min_value=0, value=5, step=1, key="dta_fp")
        fn = cols[2].number_input("False negatives (FN)", min_value=0, value=15, step=1, key="dta_fn")
        tn = cols[3].number_input("True negatives (TN)", min_value=0, value=135, step=1, key="dta_tn")
        if st.button("Calculate diagnostic metrics", type="primary", key="calculate_dta_counts"):
            try:
                st.session_state["dta_result"] = DiagnosticTestAccuracy().from_counts(int(tp), int(fp), int(fn), int(tn))
                st.session_state["dta_source_signature"] = (int(tp), int(fp), int(fn), int(tn))
            except ValueError as exc:
                st.session_state["dta_result"] = None
                st.error(f"DTA analysis unavailable: {exc}")
        result = st.session_state.get("dta_result")
        signature = (int(tp), int(fp), int(fn), int(tn))
        if result and result.mode == "counts" and signature == st.session_state.get("dta_source_signature"):
            _render_dta_result(result)
            _render_fagan_panel(result)
        elif result and result.mode == "counts":
            st.info("Diagnostic counts changed. Recalculate to refresh the results.")
    else:
        demo_mode = st.session_state.get("active_demo_dataset") == "roc" and st.session_state.get("demo_roc_frame") is not None
        uploaded = None
        if demo_mode:
            frame = st.session_state["demo_roc_frame"].copy()
            st.info(translate("demo_disclaimer", LANG))
        else:
            uploaded = st.file_uploader("Upload local CSV/Excel/SPSS file with a score and gold-standard outcome", type=["csv", "xlsx", "xlsm", "xls", "sav"], key="dta_score_file")
            if not uploaded:
                st.info("Choose a local file containing one numeric score column and one binary gold-standard outcome column.")
                return
        try:
            if uploaded is not None:
                frame = load_uploaded_table(uploaded, uploaded.name)
            if frame.empty or len(frame.columns) < 2:
                st.error("The file must contain rows and at least two columns.")
                return
            score_col = st.selectbox("Continuous prediction / score column", list(frame.columns), key="dta_score_col")
            outcome_options = [c for c in frame.columns if c != score_col]
            outcome_col = st.selectbox("Gold-standard binary outcome column (0/1)", outcome_options, key="dta_gold_col")
            st.dataframe(frame.head(8), hide_index=True, width="stretch")
            if st.button("Calculate ROC and AUC", type="primary", key="calculate_dta_scores"):
                scores = pd.to_numeric(frame[score_col], errors="raise").tolist()
                outcomes = pd.to_numeric(frame[outcome_col], errors="raise").tolist()
                result = DiagnosticTestAccuracy().from_scores(scores, outcomes)
                st.session_state["dta_result"] = result
                st.session_state["dta_scores"] = scores
                st.session_state["dta_outcomes"] = outcomes
                st.session_state["dca_result"] = None
                source_bytes = (frame.to_csv(index=False).encode("utf-8") if uploaded is None else uploaded.getvalue())
                source_name = "synthetic-diagnostic-biomarker-demo.csv" if uploaded is None else uploaded.name
                source_hash = hashlib.sha256(source_bytes).hexdigest()
                st.session_state["dta_input_sha256"] = source_hash
                st.session_state["dta_input_md5"] = hashlib.md5(source_bytes, usedforsecurity=False).hexdigest()
                st.session_state["dta_input_name"] = source_name
                st.session_state["dta_source_signature"] = ("clinical-demo" if uploaded is None else uploaded.name, len(frame), score_col, outcome_col, source_hash)
            result = st.session_state.get("dta_result")
            source_bytes = (frame.to_csv(index=False).encode("utf-8") if uploaded is None else uploaded.getvalue())
            source_hash = hashlib.sha256(source_bytes).hexdigest()
            signature = ("clinical-demo" if uploaded is None else uploaded.name, len(frame), score_col, outcome_col, source_hash)
            if result and result.mode == "scores" and signature == st.session_state.get("dta_source_signature"):
                _render_dta_result(result)
                _render_decision_curve_panel(st.session_state.get("dta_scores", []),
                                             st.session_state.get("dta_outcomes", []))
        except (ValueError, TypeError, KeyError, RuntimeError, ImportError, OSError) as exc:
            st.error(f"ROC analysis unavailable: {exc}. Confirm numeric scores and a gold-standard outcome coded exactly 0/1.")
    render_dual_roc_panel()


def render_dual_roc_panel() -> None:
    """Optional paired/independent DeLong comparison, isolated from single-ROC state."""
    with st.container(border=True):
        st.subheader(translate("dual_roc", LANG))
        st.caption("Paired mode requires both model scores on the same subjects and one shared binary outcome. Independent mode requires two separate cohorts.")
        mode = st.radio("Comparison design", ["Paired subjects", "Independent samples"], horizontal=True, key="delong_design")
        if mode == "Paired subjects":
            uploaded = st.file_uploader("Upload paired model scores and outcome", type=["csv", "xlsx", "xls", "xlsm", "sav"], key="delong_paired_file")
            if uploaded is None:
                return
            try:
                frame = load_uploaded_table(uploaded, uploaded.name)
                if len(frame.columns) < 3:
                    st.warning("The paired file must contain two score columns and one binary outcome column.")
                    return
                c1, c2, c3 = st.columns(3)
                score1_col = c1.selectbox("Model 1 score", list(frame.columns), key="delong_paired_score1")
                score2_options = [c for c in frame.columns if c != score1_col]
                score2_col = c2.selectbox("Model 2 score", score2_options, key="delong_paired_score2")
                outcome_options = [c for c in frame.columns if c not in {score1_col, score2_col}]
                outcome_col = c3.selectbox("Reference outcome (0/1)", outcome_options, key="delong_paired_outcome")
                if st.button("Compare paired ROC curves", type="primary", key="calculate_delong_paired"):
                    result = compare_roc_curves(pd.to_numeric(frame[score1_col], errors="raise").tolist(),
                                                pd.to_numeric(frame[score2_col], errors="raise").tolist(),
                                                pd.to_numeric(frame[outcome_col], errors="raise").tolist(), paired=True)
                    st.session_state["delong_result"] = result
                    st.session_state["delong_signature"] = ("paired", hashlib.sha256(uploaded.getvalue()).hexdigest(), score1_col, score2_col, outcome_col)
            except (ValueError, TypeError, KeyError, RuntimeError, ImportError, OSError) as exc:
                st.error(f"Paired DeLong comparison unavailable: {exc}")
        else:
            up1, up2 = st.columns(2)
            file1 = up1.file_uploader("Model 1 cohort file", type=["csv", "xlsx", "xls", "xlsm", "sav"], key="delong_ind_file1")
            file2 = up2.file_uploader("Model 2 cohort file", type=["csv", "xlsx", "xls", "xlsm", "sav"], key="delong_ind_file2")
            if file1 is None or file2 is None:
                return
            try:
                f1 = load_uploaded_table(file1, file1.name); f2 = load_uploaded_table(file2, file2.name)
                s1c = st.selectbox("Model 1 score column", list(f1.columns), key="delong_ind_score1")
                y1c = st.selectbox("Model 1 outcome column (0/1)", [c for c in f1.columns if c != s1c], key="delong_ind_outcome1")
                s2c = st.selectbox("Model 2 score column", list(f2.columns), key="delong_ind_score2")
                y2c = st.selectbox("Model 2 outcome column (0/1)", [c for c in f2.columns if c != s2c], key="delong_ind_outcome2")
                if st.button("Compare independent ROC curves", type="primary", key="calculate_delong_independent"):
                    result = compare_roc_curves(pd.to_numeric(f1[s1c], errors="raise").tolist(),
                                                pd.to_numeric(f2[s2c], errors="raise").tolist(),
                                                pd.to_numeric(f1[y1c], errors="raise").tolist(),
                                                outcomes2=pd.to_numeric(f2[y2c], errors="raise").tolist(), paired=False)
                    st.session_state["delong_result"] = result
                    st.session_state["delong_signature"] = ("independent", hashlib.sha256(file1.getvalue()).hexdigest(), hashlib.sha256(file2.getvalue()).hexdigest(), s1c, y1c, s2c, y2c)
            except (ValueError, TypeError, KeyError, RuntimeError, ImportError, OSError) as exc:
                st.error(f"Independent DeLong comparison unavailable: {exc}")
        result = st.session_state.get("delong_result")
        if result is not None:
            cards = st.columns(4)
            cards[0].metric("AUC 1", f"{result.auc1:.4f}")
            cards[1].metric("AUC 2", f"{result.auc2:.4f}")
            cards[2].metric("Δ AUC (1 − 2)", f"{result.delta_auc:.4f}")
            cards[3].metric("Two-sided p", fmt_p(result.p_value_two_sided))
            st.caption(f"SE difference = {result.standard_error_difference:.5f}; Z = {fmt_num(result.z_statistic, 4)}; covariance = {result.covariance:.6f}; method = {'paired DeLong covariance' if result.paired else 'independent AUC variances'}. AUC difference is Model 1 minus Model 2.")
            markup = dual_roc_plot_svg(result)
            st.markdown(markup, unsafe_allow_html=True)
            try:
                svg, png, pdf = figure_export_payloads(markup)
                ex = st.columns(3)
                ex[0].download_button("Dual ROC (SVG)", svg, file_name="jouriepi-dual-roc.svg", mime="image/svg+xml", key="export_dual_roc_svg")
                ex[1].download_button("Dual ROC (300 DPI PNG)", png, file_name="jouriepi-dual-roc-300dpi.png", mime="image/png", key="export_dual_roc_png")
                ex[2].download_button("Dual ROC (vector PDF)", pdf, file_name="jouriepi-dual-roc.pdf", mime="application/pdf", key="export_dual_roc_pdf")
            except (ValueError, RuntimeError, OSError) as exc:
                st.caption(f"Dual ROC figure export unavailable: {exc}")


def _render_dta_result(result) -> None:
    labels = ((translate("sensitivity_metric", LANG), "sensitivity"), (translate("specificity_metric", LANG), "specificity"),
              (translate("ppv_metric", LANG), "ppv"), (translate("npv_metric", LANG), "npv"), ("LR+", "lr_positive"),
              ("LR−", "lr_negative"), ("Diagnostic OR", "dor"))
    if result.mode == "scores":
        st.metric(translate("auc_metric", LANG), fmt_num(result.auc, 3))
        st.caption(f"DeLong placement-value variance: {fmt_num(result.auc_variance)}; 95% CI {fmt_ci(result.auc_ci, 3) if result.auc_ci else 'not estimable'}.")
        roc_markup = roc_plot_svg(result.roc_points, result.auc)
        st.markdown(roc_markup, unsafe_allow_html=True)
        try:
            roc_svg, roc_png, roc_pdf = figure_export_payloads(roc_markup)
            exports = st.columns(3)
            exports[0].download_button("ROC curve (SVG)", roc_svg, file_name="jouriepi-roc.svg", mime="image/svg+xml", key="export_roc_svg")
            exports[1].download_button("ROC curve (300 DPI PNG)", roc_png, file_name="jouriepi-roc-300dpi.png", mime="image/png", key="export_roc_png")
            exports[2].download_button("ROC curve (vector PDF)", roc_pdf, file_name="jouriepi-roc.pdf", mime="application/pdf", key="export_roc_pdf")
        except (ValueError, RuntimeError, OSError) as exc:
            st.caption(f"ROC exports unavailable: {exc}")
        st.dataframe([{"Metric": "AUC", "Estimate": result.auc,
                       "95% CI (DeLong normal approximation)": result.auc_ci,
                       "Variance": result.auc_variance}], hide_index=True, width="stretch")
        return
    st.subheader("Clinical metrics")
    cards = st.columns(4)
    for i, (label, key) in enumerate(labels[:4]):
        value = result.metrics.get(key)
        ci = result.intervals.get(key, {}).get("wilson")
        with cards[i]:
            metric_card(label, fmt_num(value, 2), f"Wilson 95% CI {fmt_ci(ci, 2) if ci else 'not estimable'}", "neutral")
    rows = []
    for label, key in labels:
        interval = result.intervals.get(key, {})
        rows.append({"Metric": label, "Estimate": result.metrics.get(key),
                     "Wald 95% CI": interval.get("wald"), "Wilson 95% CI": interval.get("wilson")})
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    fpr = result.metrics.get("specificity")
    sens = result.metrics.get("sensitivity")
    point = (1 - fpr, sens) if fpr is not None and sens is not None else None
    roc_markup = roc_plot_svg((), operating_point=point)
    st.markdown(roc_markup, unsafe_allow_html=True)
    try:
        roc_svg, roc_png, roc_pdf = figure_export_payloads(roc_markup)
        exports = st.columns(3)
        exports[0].download_button("ROC operating point (SVG)", roc_svg, file_name="jouriepi-roc-operating-point.svg", mime="image/svg+xml", key="export_roc_point_svg")
        exports[1].download_button("ROC operating point (300 DPI PNG)", roc_png, file_name="jouriepi-roc-operating-point.png", mime="image/png", key="export_roc_point_png")
        exports[2].download_button("ROC operating point (vector PDF)", roc_pdf, file_name="jouriepi-roc-operating-point.pdf", mime="application/pdf", key="export_roc_point_pdf")
    except (ValueError, RuntimeError, OSError) as exc:
        st.caption(f"ROC exports unavailable: {exc}")
    st.caption("For a 2×2 table, the operating point is identifiable but AUC is not; a single threshold cannot define a full ROC curve.")


def _render_fagan_panel(result) -> None:
    st.subheader("Fagan nomogram · Bayesian post-test probability")
    st.caption("Set a clinically justified pre-test probability. Post-test probability is calculated from pre-test odds × likelihood ratio; this does not independently validate the diagnostic test.")
    pretest = st.slider("Pre-test probability", min_value=0.01, max_value=0.99, value=0.20,
                        step=0.01, format="%.2f", key="dta_pretest_probability")
    lr_pos = result.metrics.get("lr_positive")
    lr_neg = result.metrics.get("lr_negative")
    post_pos = fagan_post_test_probability(pretest, lr_pos) if lr_pos is not None else None
    post_neg = fagan_post_test_probability(pretest, lr_neg) if lr_neg is not None else None
    c1, c2 = st.columns(2)
    with c1:
        metric_card("Post-test probability · positive", fmt_pct(post_pos),
                    f"Pre-test {fmt_pct(pretest)} · LR+ {fmt_num(lr_pos)}", "neutral")
    with c2:
        metric_card("Post-test probability · negative", fmt_pct(post_neg),
                    f"Pre-test {fmt_pct(pretest)} · LR− {fmt_num(lr_neg)}", "neutral")
    markup = fagan_nomogram_svg(pretest, lr_pos, lr_neg, post_pos, post_neg)
    st.markdown(markup, unsafe_allow_html=True)
    try:
        svg, png, pdf = figure_export_payloads(markup)
        exports = st.columns(3)
        exports[0].download_button("Fagan nomogram (SVG)", svg, file_name="jouriepi-fagan-nomogram.svg", mime="image/svg+xml", key="export_fagan_svg")
        exports[1].download_button("Fagan nomogram (300 DPI PNG)", png, file_name="jouriepi-fagan-nomogram.png", mime="image/png", key="export_fagan_png")
        exports[2].download_button("Fagan nomogram (vector PDF)", pdf, file_name="jouriepi-fagan-nomogram.pdf", mime="application/pdf", key="export_fagan_pdf")
    except (ValueError, RuntimeError, OSError) as exc:
        st.caption(f"Fagan figure exports unavailable: {exc}")
    if lr_pos is None or lr_neg is None:
        st.warning("One or both likelihood ratios are not estimable from this table; the corresponding nomogram line is omitted.")


def _render_decision_curve_panel(scores, outcomes) -> None:
    st.subheader("Decision curve analysis · net benefit")
    st.caption("DCA requires predicted risks on the 0–1 probability scale. It compares model-guided decisions with treating everyone or no one across threshold probabilities.")
    if not scores or not outcomes:
        st.info("Calculate ROC/AUC from a score file first.")
        return
    if any(not isinstance(s, (int, float)) or not 0 <= float(s) <= 1 for s in scores):
        st.warning("Decision curve analysis is unavailable because the uploaded scores include values outside [0, 1]. Use predicted probabilities, not arbitrary ranking scores.")
        return
    threshold_range = st.slider("Threshold probability range", min_value=0.05, max_value=0.95,
                                value=(0.05, 0.95), step=0.05, key="dca_threshold_range")
    if st.button("Calculate decision curve", type="primary", key="calculate_dca"):
        try:
            thresholds = [i / 100 for i in range(int(round(threshold_range[0] * 100)),
                                                   int(round(threshold_range[1] * 100)) + 1, 5)]
            st.session_state["dca_result"] = analyze_decision_curve(scores, outcomes, thresholds)
            st.session_state["dca_signature"] = (tuple(scores), tuple(outcomes), tuple(threshold_range))
        except (ValueError, TypeError) as exc:
            st.session_state["dca_result"] = None
            st.error(f"Decision curve could not be calculated: {exc}")
    dca = st.session_state.get("dca_result")
    signature = (tuple(scores), tuple(outcomes), tuple(threshold_range))
    if dca is not None and signature == st.session_state.get("dca_signature"):
        st.markdown(decision_curve_svg(dca), unsafe_allow_html=True)
        st.dataframe([{"Threshold probability": p.threshold_probability,
                       "Model net benefit": p.model_net_benefit,
                       "Treat all net benefit": p.treat_all_net_benefit,
                       "Treat none net benefit": p.treat_none_net_benefit,
                       "TP": p.true_positives, "FP": p.false_positives} for p in dca.points],
                     hide_index=True, width="stretch")
        try:
            markup = decision_curve_svg(dca)
            svg, png, pdf = figure_export_payloads(markup)
            exports = st.columns(3)
            exports[0].download_button("Decision curve (SVG)", svg, file_name="jouriepi-decision-curve.svg", mime="image/svg+xml", key="export_dca_svg")
            exports[1].download_button("Decision curve (300 DPI PNG)", png, file_name="jouriepi-decision-curve.png", mime="image/png", key="export_dca_png")
            exports[2].download_button("Decision curve (vector PDF)", pdf, file_name="jouriepi-decision-curve.pdf", mime="application/pdf", key="export_dca_pdf")
        except (ValueError, RuntimeError, OSError) as exc:
            st.caption(f"Decision curve exports unavailable: {exc}")


def render_publication() -> None:
    st.markdown('<div class="section-kicker">Reporting & publication</div>', unsafe_allow_html=True)
    st.header("Publication & STROBE" if LANG == "en" else ("Publication et STROBE" if LANG == "fr" else "Publikation und STROBE"))
    st.caption("Drafts a results paragraph and comparison tables from the last calculated 2×2 analysis. Author-supplied study details are not inferred; this is not a certification of STROBE compliance.")
    result = st.session_state.get("analysis_result")
    counts = st.session_state.get("analysis_counts")
    current_counts = tuple(int(st.session_state[k]) for k in ("a", "b", "c", "d"))
    if not result or not counts:
        st.info("Calculate a 2×2 analysis first, then return here to prepare the publication outputs.")
        return
    if tuple(counts) != current_counts:
        st.warning("The table counts changed after the last calculation. Recalculate in 2×2 Analysis before exporting.")
        return
    with st.container(border=True):
        st.subheader("Export for Publication · ICMJE / APA")
        st.caption("Journal-style table with top, header, and bottom rules and no vertical rules. Review journal-specific instructions before submission.")
        try:
            html_table = export_journal_html(counts, result, title="Clinical epidemiology results")
            docx_table = export_journal_docx(counts, result, title="Clinical epidemiology results")
            latex_table = export_journal_latex(counts, result, title="Clinical epidemiology results")
            ex1, ex2, ex3 = st.columns(3)
            ex1.download_button("Publication table (.docx)", docx_table, file_name="jouriepi-publication-table.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", key="export_publication_docx")
            ex2.download_button("Publication table (.html)", html_table, file_name="jouriepi-publication-table.html",
                                mime="text/html", key="export_publication_html")
            ex3.download_button("LaTeX tabular (.tex)", latex_table, file_name="jouriepi-publication-table.tex",
                                mime="application/x-tex", key="export_publication_latex")
            with st.expander("Preview LaTeX table code", expanded=False):
                st.code(latex_table, language="latex")
        except (ValueError, TypeError, KeyError) as exc:
            st.error(f"Publication table export unavailable: {exc}")
    with st.expander(translate("export_code", LANG), expanded=False):
        st.caption("Standalone scripts recalculate the current 2×2 analysis locally. Python uses SciPy/statsmodels; R uses base R. Review dependencies and the exported assumptions before reuse.")
        try:
            py_script = export_python_script(counts, alpha=float(st.session_state.get("alpha", 0.05)), analysis_name="JouriEpi 2x2 analysis")
            r_script = export_r_script(counts, alpha=float(st.session_state.get("alpha", 0.05)), analysis_name="JouriEpi 2x2 analysis")
            script_cols = st.columns(2)
            script_cols[0].download_button("Download standalone Python (.py)", py_script, file_name="jouriepi-reproducibility.py", mime="text/x-python", key="export_repro_py", width="stretch")
            script_cols[1].download_button("Download standalone R (.R)", r_script, file_name="jouriepi-reproducibility.R", mime="text/plain", key="export_repro_r", width="stretch")
            with st.expander("Preview exported Python script"):
                st.code(py_script, language="python")
            with st.expander("Preview exported R script"):
                st.code(r_script, language="r")
        except (ValueError, TypeError) as exc:
            st.error(f"Reproducibility scripts unavailable: {exc}")
    design = st.session_state.get("analysis_design", "Cohort / cross-sectional")
    st.subheader("Complete clinical dossier")
    dossier_title = st.text_input("Study / dossier title", value="JouriEpi Clinical Epidemiology Analysis", key="dossier_title")
    metadata_cols = st.columns(3)
    study_id = metadata_cols[0].text_input("Study ID / protocol reference", key="dossier_study_id")
    study_setting = metadata_cols[1].text_input("Study setting", key="dossier_study_setting")
    study_author = metadata_cols[2].text_input("Analyst / author", key="dossier_study_author")
    dta_for_report = st.session_state.get("dta_result")
    forest_png = forest_plot_png_bytes(dict(result))
    roc_png = (roc_plot_png_bytes(dta_for_report.roc_points, dta_for_report.auc)
               if dta_for_report is not None and dta_for_report.mode == "scores" else None)
    fagan_png = dca_png = dual_png = None
    try:
        if dta_for_report is not None and dta_for_report.mode == "counts":
            pretest = float(st.session_state.get("dta_pretest_probability", 0.2))
            lr_pos, lr_neg = dta_for_report.metrics.get("lr_positive"), dta_for_report.metrics.get("lr_negative")
            post_pos = fagan_post_test_probability(pretest, lr_pos) if lr_pos is not None else None
            post_neg = fagan_post_test_probability(pretest, lr_neg) if lr_neg is not None else None
            fagan_svg = fagan_nomogram_svg(pretest, lr_pos, lr_neg, post_pos, post_neg)
            fagan_png = figure_export_payloads(fagan_svg)[1]
        dca_for_report = st.session_state.get("dca_result")
        if dca_for_report is not None:
            dca_png = figure_export_payloads(decision_curve_svg(dca_for_report))[1]
        dual_for_report = st.session_state.get("delong_result")
        if dual_for_report is not None:
            dual_png = figure_export_payloads(dual_roc_plot_svg(dual_for_report))[1]
    except (ValueError, TypeError, RuntimeError, OSError, ImportError):
        # Missing optional figures do not prevent the core dossier from exporting.
        pass
    try:
        dossier_bytes = generate_clinical_dossier(
            counts, result, design=design, title=dossier_title,
            metadata_fields={"Dossier title": dossier_title, "Study ID / protocol reference": study_id or "Not supplied",
                             "Study setting": study_setting or "Not supplied", "Analyst / author": study_author or "Not supplied",
                             "Source": "Current in-session 2×2 analysis"},
            stratified_result=(st.session_state.get("line_stratified_result") or
                               st.session_state.get("stratified_result")),
            e_value_result=st.session_state.get("evalue_result"), dta_result=dta_for_report,
            forest_png=forest_png, roc_png=roc_png, fagan_png=fagan_png, dca_png=dca_png,
            dual_roc_png=dual_png, language=LANG,
            logo_bytes=st.session_state.get("institutional_logo_bytes"))
        st.download_button("Download Complete Clinical Dossier (.docx)", dossier_bytes,
                           file_name="jouriepi-clinical-dossier.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                           type="primary", width="stretch")
    except (ValueError, TypeError, ImportError, OSError) as exc:
        st.error(f"Dossier generation unavailable: {exc}")
    line_result_for_audit = st.session_state.get("line_result")
    source_is_raw = bool(line_result_for_audit and tuple(line_result_for_audit.get("counts", ())) == tuple(counts)
                         and line_result_for_audit.get("input_sha256"))
    certificate = certificate_json(
        parameters={"counts_a_b_c_d": list(counts), "sampling_design": design,
                    "alpha": float(st.session_state.get("alpha", 0.05)),
                    "haldane_anscombe_requested": bool(st.session_state.get("use_ha", False)),
                    "stratification": (line_result_for_audit.get("stratum_col") if source_is_raw else None),
                    "dta_input_sha256": st.session_state.get("dta_input_sha256")},
        metrics={"two_by_two": result,
                 "stratified": (st.session_state.get("line_stratified_result") or st.session_state.get("stratified_result")),
                 "e_value": st.session_state.get("evalue_result"), "dta": st.session_state.get("dta_result"),
                 "decision_curve": st.session_state.get("dca_result"),
                 "fagan": {"pretest_probability": st.session_state.get("dta_pretest_probability"),
                           "posttest_positive": (fagan_post_test_probability(
                               st.session_state.get("dta_pretest_probability", 0.2),
                               st.session_state["dta_result"].metrics["lr_positive"])
                               if st.session_state.get("dta_result") is not None and
                               st.session_state["dta_result"].mode == "counts" and
                               st.session_state["dta_result"].metrics.get("lr_positive") is not None else None),
                           "posttest_negative": (fagan_post_test_probability(
                               st.session_state.get("dta_pretest_probability", 0.2),
                               st.session_state["dta_result"].metrics["lr_negative"])
                               if st.session_state.get("dta_result") is not None and
                               st.session_state["dta_result"].mode == "counts" and
                               st.session_state["dta_result"].metrics.get("lr_negative") is not None else None)}},
        source_name=line_result_for_audit.get("source", "canonical-2x2-counts.json") if source_is_raw else "canonical-2x2-counts.json",
        source_md5=line_result_for_audit.get("input_md5") if source_is_raw else None,
        source_sha256=line_result_for_audit.get("input_sha256") if source_is_raw else None,
        metadata_fields={"dossier_title": dossier_title, "study_id": study_id,
                         "study_setting": study_setting, "study_author": study_author,
                         "sampling_design": design},
        additional_inputs=([{"source_name": st.session_state.get("dta_input_name", "DTA-score-file"),
                             "checksum_scope": "exact uploaded DTA input-file bytes",
                             "md5_integrity_compatibility": st.session_state.get("dta_input_md5"),
                             "sha256": st.session_state.get("dta_input_sha256")}]
                           if st.session_state.get("dta_input_sha256") else []))
    st.download_button("Download Reproducibility Certificate (audit_certificate.json)", certificate,
                       file_name="audit_certificate.json", mime="application/json", width="stretch")
    narrative = strobe_narrative(counts, result, design=design, language=LANG)
    markdown_table = comparison_markdown(counts, result, language=LANG)
    latex_table = comparison_latex(counts, result, language=LANG)
    st.subheader(translate("strobe_title", LANG))
    st.markdown(narrative)
    st.caption("Author checklist still required: study design and setting; dates; eligibility and participant flow; missing data; confounder selection/adjustment; sensitivity analyses; ethics; funding; and all applicable STROBE items.")
    st.subheader("Comparison table")
    st.markdown(markdown_table)
    st.download_button("Download Markdown table", markdown_table, file_name="jouriepi-comparison.md", mime="text/markdown", width="stretch")
    st.download_button("Download LaTeX table", latex_table, file_name="jouriepi-comparison.tex", mime="application/x-tex", width="stretch")
    copy_text = narrative + "\n\n" + markdown_table
    escaped_copy = json.dumps(copy_text, ensure_ascii=False)
    st.components.v1.html(f"""<!doctype html><meta charset="utf-8">
<button id="copy-report" type="button" style="font:600 14px system-ui;padding:10px 14px;border-radius:8px;border:1px solid #82939f;background:#f5f8fa;color:#172b3a;cursor:pointer">Copy narrative + Markdown table</button>
<span id="copy-status" role="status" aria-live="polite" style="font:13px system-ui;margin-left:10px"></span>
<script>
const reportText = {escaped_copy};
const button = document.getElementById('copy-report');
const status = document.getElementById('copy-status');
button.addEventListener('click', async () => {{
  try {{
    if (navigator.clipboard && window.isSecureContext) {{
      await navigator.clipboard.writeText(reportText);
      status.textContent = 'Copied.';
    }} else {{
      const area = document.createElement('textarea');
      area.value = reportText; area.setAttribute('readonly', '');
      area.style.position = 'fixed'; area.style.opacity = '0';
      document.body.appendChild(area); area.select();
      const copied = document.execCommand('copy'); area.remove();
      status.textContent = copied ? 'Copied using browser fallback.' : 'Copy blocked; use the downloadable files or select the text above.';
    }}
  }} catch (error) {{
    status.textContent = 'Clipboard permission denied; use the downloadable files or select the text above.';
  }}
}});
</script>""", height=58, scrolling=False)
    with st.expander("Technical JSON Payload", expanded=False):
        st.caption("Machine-readable counts, estimates, table orientation, sampling design, and method-status provenance.")
        payload = technical_payload(counts, result, design=design, language=LANG)
        st.code(payload, language="json")
        st.download_button("Download technical JSON", payload, file_name="jouriepi-analysis.json", mime="application/json")


def render_advanced() -> None:
    st.markdown('<div class="section-kicker">Sensitivity & advanced exact methods</div>', unsafe_allow_html=True)
    st.header("Advanced analyses")
    st.caption("These are optional modern methods. Review assumptions and choose methods before interpreting results; none establishes causality on its own.")

    with st.container(border=True):
        st.subheader(translate("paired", LANG))
        st.caption("Enter a paired 2×2 table: a=both positive, b=pre/reference positive and post/comparison negative, c=pre/reference negative and post/comparison positive, d=both negative. McNemar inference uses only discordant pairs b and c.")
        pcols = st.columns(4)
        pa = pcols[0].number_input("Both positive (a)", min_value=0, value=20, step=1, key="paired_a")
        pb = pcols[1].number_input("Discordant b", min_value=0, value=5, step=1, key="paired_b")
        pc = pcols[2].number_input("Discordant c", min_value=0, value=2, step=1, key="paired_c")
        pd_ = pcols[3].number_input("Both negative (d)", min_value=0, value=30, step=1, key="paired_d")
        if st.button("Calculate McNemar test", type="primary", key="calculate_mcnemar"):
            try:
                st.session_state["mcnemar_result"] = mcnemar_test(int(pa), int(pb), int(pc), int(pd_), alpha=float(st.session_state.get("alpha", 0.05)))
                st.session_state["mcnemar_counts"] = (int(pa), int(pb), int(pc), int(pd_))
            except (ValueError, TypeError, RuntimeError, ImportError) as exc:
                st.session_state["mcnemar_result"] = None
                st.error(f"McNemar analysis unavailable: {exc}")
        mr = st.session_state.get("mcnemar_result")
        if mr is not None:
            if st.session_state.get("mcnemar_counts") != (int(pa), int(pb), int(pc), int(pd_)):
                st.info("Paired counts changed. Recalculate McNemar results before interpretation.")
            else:
                mcols = st.columns(4)
                mcols[0].metric("Discordant pairs (b+c)", str(mr.discordant_total))
                mcols[1].metric("Edwards-corrected χ²", fmt_num(mr.asymptotic_chi_square, 4))
                mcols[2].metric("Asymptotic p", fmt_p(mr.asymptotic_p_value))
                mcols[3].metric("Exact two-sided p", fmt_p(mr.exact_p_value))
                st.write(f"Paired OR (b/c): {fmt_num(mr.paired_odds_ratio)}; exact {100*(1-mr.alpha):.1f}% conditional CI: {mr.exact_or_ci}.")
                st.caption("The exact test conditions on the discordant total. The exact OR interval transforms Clopper–Pearson limits for b/(b+c); infinite limits can occur and are not silently truncated.")

    with st.container(border=True):
        st.subheader("Additive interaction · RERI, AP and synergy index")
        st.caption("Enter cases and non-cases for exposure groups A=0/B=0, A=1/B=0, A=0/B=1, A=1/B=1. These are odds-ratio-scale measures; they approximate risk-ratio interaction only when the outcome is sufficiently rare. All cells must be positive for this log-odds delta method; no continuity correction is applied.")
        labels = [("00", "A=0, B=0 (reference)"), ("10", "A=1, B=0"), ("01", "A=0, B=1"), ("11", "A=1, B=1")]
        interaction_counts = []
        for code, label in labels:
            st.markdown(f"**{label}**")
            cols = st.columns(2)
            cases = cols[0].number_input(f"Cases · {code}", min_value=0, value={"00": 20, "10": 24, "01": 25, "11": 35}[code], step=1, key=f"interaction_cases_{code}")
            noncases = cols[1].number_input(f"Non-cases · {code}", min_value=0, value={"00": 80, "10": 76, "01": 75, "11": 65}[code], step=1, key=f"interaction_noncases_{code}")
            interaction_counts.append((int(cases), int(noncases)))
        if st.button("Calculate additive interaction", type="primary", key="calculate_additive_interaction"):
            try:
                st.session_state["additive_interaction_result"] = analyze_additive_interaction(interaction_counts, alpha=float(st.session_state.get("alpha", 0.05)))
                st.session_state["additive_interaction_counts"] = tuple(interaction_counts)
            except (ValueError, TypeError, OverflowError) as exc:
                st.session_state["additive_interaction_result"] = None
                st.error(f"Additive interaction could not be estimated: {exc}")
        ir = st.session_state.get("additive_interaction_result")
        if ir is not None:
            if tuple(interaction_counts) != st.session_state.get("additive_interaction_counts"):
                st.info("Exposure-group counts changed. Recalculate before interpreting interaction measures.")
            else:
                c1, c2, c3 = st.columns(3)
                with c1: metric_card("RERI", fmt_num(ir.reri), f"95% CI {fmt_ci(ir.reri_ci)}", "neutral")
                with c2: metric_card("Attributable proportion (AP)", fmt_num(ir.attributable_proportion), f"95% CI {fmt_ci(ir.ap_ci)}", "neutral")
                with c3: metric_card("Synergy index (SI)", fmt_num(ir.synergy_index), f"95% CI {fmt_ci(ir.si_ci)}", "neutral")
                st.write(f"OR10 = {fmt_num(ir.odds_ratio_10)}; OR01 = {fmt_num(ir.odds_ratio_01)}; OR11 = {fmt_num(ir.odds_ratio_11)}.")
                if ir.reri_ci[0] > 0 or ir.reri_ci[1] < 0:
                    st.info("The delta-method RERI interval excludes zero. Interpret in light of the study design, outcome frequency, model specification, and residual confounding; this is not by itself evidence of a biological mechanism.")
                else:
                    st.caption("The delta-method RERI interval includes zero. This does not prove absence of interaction.")

    with st.container(border=True):
        st.subheader("E-value · unmeasured-confounding sensitivity")
        st.caption("Enter an RR directly, or an OR and explicitly choose a conversion. Confidence limits are optional and must be on the same scale as the estimate.")
        e1, e2 = st.columns(2)
        scale = e1.selectbox("Effect measure", ["RR", "OR"], key="evalue_scale")
        estimate = e2.number_input("Point estimate", min_value=0.000001, value=2.0, step=0.1, key="evalue_estimate", format="%.6f")
        use_ci = st.checkbox("Include confidence interval", value=True, key="evalue_use_ci")
        ci = None
        if use_ci:
            c1, c2 = st.columns(2)
            low = c1.number_input("CI lower bound", min_value=0.000001, value=1.2, step=0.1, key="evalue_ci_low", format="%.6f")
            high = c2.number_input("CI upper bound", min_value=0.000001, value=3.1, step=0.1, key="evalue_ci_high", format="%.6f")
            ci = (float(low), float(high))
        method = None
        baseline_risk = None
        if scale == "OR":
            method = st.selectbox("Convert OR to RR", ["sqrt_approximation", "baseline_risk"], format_func=lambda v: "Square-root approximation (rough; best for common outcomes)" if v == "sqrt_approximation" else "Baseline-risk conversion", key="evalue_or_method")
            if method == "baseline_risk":
                baseline_risk = st.number_input("Unexposed baseline risk (p₀)", min_value=0.000001, max_value=0.999999, value=0.2, step=0.01, key="evalue_baseline_risk", format="%.6f")
        if st.button("Calculate E-value", type="primary", key="calculate_evalue"):
            try:
                st.session_state["evalue_result"] = e_value(float(estimate), ci, scale=scale, or_method=method, baseline_risk=baseline_risk)
                st.session_state["evalue_inputs"] = (scale, float(estimate), ci, method, baseline_risk)
            except (ValueError, TypeError) as exc:
                st.session_state["evalue_result"] = None
                st.error(f"E-value could not be calculated: {exc}")
        er = st.session_state.get("evalue_result")
        if er:
            current = (scale, float(estimate), ci, method, baseline_risk)
            if current != st.session_state.get("evalue_inputs"):
                st.info("E-value inputs changed. Select **Calculate E-value** to refresh the result.")
            else:
                m1, m2, m3 = st.columns(3)
                with m1: metric_card("Point E-value", fmt_num(er.e_value), "Risk-ratio scale", "neutral")
                with m2: metric_card("Confidence-limit E-value", fmt_num(er.confidence_limit_e_value), "Nearest limit to null" if ci else "No CI supplied", "neutral")
                with m3: metric_card("Converted RR", fmt_num(er.risk_ratio_estimate), f"Input scale: {er.input_scale}", "neutral")
                st.markdown(er.interpretation)
                st.caption(f"Conversion: {er.conversion_method}. Reference: VanderWeele & Ding (2017), doi:10.7326/M16-2607.")

    with st.container(border=True):
        st.subheader("Stratification & Simpson’s paradox check")
        st.caption("Enter one stratum per CSV line: label,a,b,c,d. Counts follow the app convention: exposed cases, exposed non-cases, unexposed cases, unexposed non-cases. No continuity correction is applied.")
        strata_text = st.text_area("Stratum counts", value="Stratum 1,12,8,6,14\nStratum 2,20,10,10,20", height=110, key="advanced_strata_text")
        if st.button("Analyze strata", type="primary", key="analyze_strata"):
            try:
                parsed = {}
                for line_no, row in enumerate(csv.reader(StringIO(strata_text)), start=1):
                    if not row or all(not cell.strip() for cell in row):
                        continue
                    if len(row) != 5:
                        raise ValueError(f"Line {line_no}: expected label plus four counts.")
                    label = row[0].strip()
                    if not label or label in parsed:
                        raise ValueError(f"Line {line_no}: stratum labels must be non-empty and unique.")
                    values = []
                    for cell in row[1:]:
                        value = int(cell.strip())
                        if value < 0:
                            raise ValueError(f"Line {line_no}: counts must be nonnegative integers.")
                        values.append(value)
                    parsed[label] = tuple(values)
                result = analyze_stratified_tables(parsed)
                st.session_state["stratified_result"] = result
                st.session_state["stratified_inputs"] = strata_text
            except (ValueError, TypeError) as exc:
                st.session_state["stratified_result"] = None
                st.error(f"Stratified analysis could not be calculated: {exc}")
        sr = st.session_state.get("stratified_result")
        if sr:
            if strata_text != st.session_state.get("stratified_inputs"):
                st.info("Stratum counts changed. Select **Analyze strata** to refresh results.")
            else:
                st.subheader("Stratum-specific estimates")
                rows = [{"Stratum": x.label, "a": x.counts[0], "b": x.counts[1], "c": x.counts[2], "d": x.counts[3], "Odds ratio": x.odds_ratio, "Risk ratio": x.risk_ratio} for x in sr.strata]
                st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
                m1, m2, m3 = st.columns(3)
                with m1: metric_card("Crude OR", fmt_num(sr.crude_odds_ratio), "Pooled counts", "neutral")
                with m2: metric_card("Mantel–Haenszel OR", fmt_num(sr.mantel_haenszel_odds_ratio), "Common adjusted OR", "neutral")
                with m3: metric_card("Mantel–Haenszel RR", fmt_num(sr.mantel_haenszel_risk_ratio), "Common adjusted RR", "neutral")
                if sr.simpsons_paradox_detected:
                    st.warning("Simpson’s paradox flag: the crude odds ratio is on the opposite side of 1 from every stratum-specific odds ratio. Inspect stratum sizes and the study design before interpreting the reversal.")
                else:
                    st.success("Simpson’s paradox reversal was not flagged by the implemented odds-ratio direction check.")
                if sr.meaningful_confounding:
                    st.warning("The crude and Mantel–Haenszel OR differ by at least 10% (heuristic confounding flag, not a formal causal conclusion).")
                if sr.breslow_day_p_value is not None:
                    st.write(f"Breslow–Day homogeneity test: χ² = {fmt_num(sr.breslow_day_statistic)}, df = {sr.breslow_day_df}, p = {fmt_p(sr.breslow_day_p_value)}.")
                    st.write(f"Tarone-corrected test: χ² = {fmt_num(sr.breslow_day_tarone_statistic)}, p = {fmt_p(sr.tarone_corrected_p_value)}.")
                for warning in sr.warnings:
                    st.caption(warning)
                if sr.effect_measure_modification:
                    st.warning("Effect measure modification flagged: Breslow–Day p < 0.05. Review stratum-specific effects before reporting a common pooled OR.")

    with st.container(border=True):
        st.subheader("Boschloo’s unconditional exact test")
        counts = tuple(int(st.session_state[k]) for k in ("a", "b", "c", "d"))
        st.caption(f"Uses the current 2×2 table counts (a,b,c,d) = {counts}. Update counts in 2×2 Analysis first if needed. No continuity correction is applied.")
        if st.button("Calculate Boschloo test", type="primary", key="calculate_boschloo"):
            try:
                table = Table2x2(*counts)
                st.session_state["boschloo_result"] = analyze_boschloo(table)
                st.session_state["boschloo_counts"] = counts
            except (ValueError, RuntimeError) as exc:
                st.session_state["boschloo_result"] = None
                st.error(f"Boschloo test unavailable: {exc}")
        br = st.session_state.get("boschloo_result")
        if br:
            if counts != st.session_state.get("boschloo_counts"):
                st.info("The 2×2 counts changed after this test. Select **Calculate Boschloo test** to refresh.")
            else:
                st.write(f"SciPy version: {br.scipy_version}. This is an unconditional exact test; Fisher’s exact test remains available in the main analysis for comparison.")
                b1, b2, b3 = st.columns(3)
                with b1: metric_card("Two-sided p", fmt_p(br.p_value_two_sided), "Boschloo exact", "neutral")
                with b2: metric_card("Greater p", fmt_p(br.p_value_greater), "OR direction > 1", "neutral")
                with b3: metric_card("Less p", fmt_p(br.p_value_less), "OR direction < 1", "neutral")
                st.caption("Choose the alternative based on the analysis plan, not after inspecting the observed result.")


try:
    section = st.session_state.nav_section
    if section == "2×2 Analysis":
        render_analysis()
    elif section == "Line list → 2×2":
        render_line_list()
    elif section == "Diagnostic Test Accuracy (DTA)":
        render_dta()
    elif section == "Sample size & power":
        render_power()
    elif section == "Advanced analyses":
        render_advanced()
    else:
        render_publication()
except Exception:  # Never expose a traceback or raw exception in the app interface.
    st.error("Something went wrong while rendering this section. Your input values have been retained. Try again or return to the previous section; diagnostic details are not shown in the interface.")
