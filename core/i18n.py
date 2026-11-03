"""Offline dictionary-based localization for the JouriEpi interface and reports."""
from __future__ import annotations

from typing import Mapping

LANGUAGES = {"en": "English", "fr": "Français", "de": "Deutsch", "ar": "العربية", "es": "Español", "ru": "Русский", "zh": "中文", "ja": "日本語"}
_MESSAGES: dict[str, dict[str, str]] = {
    "en": {
        "file": "File", "analysis": "Analysis", "diagnostics": "Diagnostics", "reports": "Reports",
        "language": "Language", "theme": "Theme", "help": "Help", "dark_mode": "Clinical dark mode",
        "loading": "Loading JouriEpi Clinical Workstation...", "title": "JouriEpi: Clinical Epidemiological & Causal Inference Suite",
        "offline": "Offline · data never leaves this session", "save_workspace": "Save Workspace (.jepi)",
        "load_workspace": "Load Workspace (.jepi)", "export_code": "Export Reproducibility Code",
        "paired": "Paired 2×2 & McNemar analysis", "dual_roc": "Dual ROC comparison (DeLong)",
        "methods": "Statistical methods & algorithmic provenance", "results": "Formatted results tables",
        "narrative": "Narrative results", "sensitivity": "Causal sensitivity & confounder audit",
        "embedded_figures": "Embedded figures", "not_estimable": "Not estimable", "yes": "Yes", "no": "No",
        "language_help": "Language applies to supported interface labels and generated dossier text. Calculations are unchanged.",
        "report_methods": "1. Statistical methods & algorithmic provenance", "report_tables": "2. Formatted results tables",
        "report_narrative": "3. Narrative results", "report_sensitivity": "4. Causal sensitivity & confounder audit",
        "report_figures": "Embedded figures", "report_integrity": "Audit and regulatory-use note",
        "report_subtitle": "Air-Gapped, Privacy-Preserving Offline Analytical Engine",
        "report_cells": "Cell order: a = exposed cases; b = exposed non-cases; c = unexposed cases; d = unexposed non-cases. Undefined estimates are reported as not estimable rather than silently corrected.",
        "report_forest_caption": "Figure 1. Forest plot generated locally from the current analysis (300 DPI PNG).",
        "report_roc_caption": "Figure 2. ROC curve generated locally from the current diagnostic analysis (300 DPI PNG).",
        "report_fagan_caption": "Figure 3. Fagan nomogram generated locally from the current diagnostic analysis (300 DPI PNG).",
        "report_dca_caption": "Figure 4. Decision curve analysis net benefit plot generated locally (300 DPI PNG).",
        "sensitivity_metric": "Sensitivity", "specificity_metric": "Specificity", "ppv_metric": "Positive predictive value", "npv_metric": "Negative predictive value",
        "auc_metric": "AUC", "estimate_metric": "Estimate", "p_value_metric": "Two-sided p-value", "confidence_interval": "95% confidence interval",
        "calculate": "Calculate", "warning_changed": "Inputs changed. Recalculate before interpreting results.", "strobe_title": "STROBE-style results narrative",
        "nav_analysis": "2×2 Analysis", "nav_line_list": "Line list → 2×2", "nav_dta": "Diagnostic Test Accuracy (DTA)",
        "nav_power": "Sample size & power", "nav_advanced": "Advanced analyses", "nav_publication": "Publication & STROBE",
        "association_analysis": "Association Analysis", "contingency_table": "Contingency table", "sampling_design": "Sampling design",
        "cohort_cross": "Cohort / cross-sectional", "case_control": "Case-control", "exposed": "Exposed", "unexposed": "Unexposed",
        "case_positive": "Case (D+)", "noncase_negative": "Non-case (D−)", "row_total": "Row total", "column_totals": "Column totals",
        "new_session": "New Session", "export_dossier": "Export Dossier (.docx)", "download_workspace": "Download .jepi workspace",
        "load_selected_workspace": "Load selected workspace", "workspace_saved": "Workspace prepared locally. Save the downloaded .jepi file to keep it.",
        "workspace_loaded": "Workspace checksum verified and state loaded.", "institutional_logo": "Institutional logo (optional)",
        "workspace": "Workspace", "workspace_help": "Choose the analysis view to open", "offline_detail": "Uploaded data and report assets are processed locally. No network service is used for analysis.",
        "method_scope_note": "Modern reference calculations; exact parity with historical software is not claimed.",
        "logo_help": "Optional logo included in generated Word dossier headers; stored only in this session.",
        "demo_dataset": "Load Clinical Demo Dataset", "demo_choose": "Choose a synthetic clinical example…",
        "demo_cardiovascular": "Cardiovascular Risk Study (Cohort 2x2)",
        "demo_roc": "Diagnostic Biomarker vs. Gold Standard (Continuous ROC/AUC)",
        "demo_stratified": "Multicenter Trial Stratification (Simpson's / Breslow-Day)",
        "demo_disclaimer": "Synthetic teaching data only — not real patient records or clinical evidence.",
        "demo_loaded": "Clinical demo loaded and its analysis calculated.",
        "help_reference_title": "Clinical methods reference",
        "help_boschloo_title": "Boschloo vs Fisher", "help_woolf_katz_title": "Woolf vs Katz confidence intervals",
        "help_evalue_title": "E-value", "help_fagan_title": "Fagan nomogram",
        "help_boschloo": "Boschloo vs Fisher: Fisher’s exact test conditions on both margins and is a familiar conservative exact option for sparse 2×2 tables. Boschloo’s unconditional exact test can be more powerful for some tables. Choose the method and sided alternative in the analysis plan, not after seeing the result; neither method fixes bias or confounding.",
        "help_woolf_katz": "Woolf vs Katz: Woolf’s log-odds-ratio interval uses the reciprocal-cell variance and is appropriate as a large-sample approximation when cells are positive. Katz’s log-risk-ratio interval uses the risk-ratio-specific variance and requires positive case counts for that formula. Both are asymptotic; sparse or zero cells can make them unavailable or unreliable, and no correction is silently applied.",
        "help_evalue": "E-value: the minimum strength of association, on the risk-ratio scale, that an unmeasured confounder would need with both exposure and outcome (conditional on measured covariates) to explain away an observed association under the E-value framework. It is a sensitivity metric, not proof that confounding exists or does not exist; interpret the confidence-limit E-value alongside the point estimate and study limitations.",
        "help_fagan": "Fagan nomogram: combines a clinically justified pre-test probability with a positive or negative likelihood ratio. Convert pre-test probability to odds, multiply by the likelihood ratio, then convert back to post-test probability. The result depends on the pre-test probability and on transportable test accuracy; the nomogram does not validate the test or establish clinical utility.",
        "help_citations": "Citations for the methods described here. Download both APA and BibTeX formats for reuse.",
        "citation_apa": "APA citations", "citation_bibtex": "BibTeX citations", "download_citations": "Download citation block (.txt)",
        "menu_file_help": "Session and workspace file management", "menu_analysis_help": "Open 2×2 association analysis",
        "menu_diagnostics_help": "Open diagnostic accuracy and ROC tools", "menu_reports_help": "Open publication and dossier tools",
        "menu_language_help": "Choose the interface language", "menu_theme_help": "Switch between light and dark clinical themes",
        "menu_help_help": "Help, accessibility, and offline privacy information", "file_help_fr": "Gestion de session et fichiers",
        "file_help_de": "Sitzungs- und Dateiverwaltung", "analysis_help_fr": "Ouvrir l’analyse d’association 2×2",
        "analysis_help_de": "2×2-Assoziationsanalyse öffnen", "diagnostics_help_fr": "Ouvrir les outils diagnostiques et ROC",
        "diagnostics_help_de": "Diagnostik- und ROC-Werkzeuge öffnen", "reports_help_fr": "Ouvrir les rapports et le dossier clinique",
        "reports_help_de": "Berichte und klinisches Dossier öffnen", "language_help_fr": "Choisir la langue de l’interface",
        "language_help_de": "Sprache der Benutzeroberfläche auswählen", "theme_help_fr": "Basculer entre les thèmes cliniques clair et sombre",
        "theme_help_de": "Zwischen hellem und dunklem klinischem Design wechseln", "help_help_fr": "Aide, accessibilité et confidentialité hors ligne",
        "help_help_de": "Hilfe, Barrierefreiheit und Offline-Datenschutz",
    },
    "fr": {
        "file": "Fichier", "analysis": "Analyse", "diagnostics": "Diagnostics", "reports": "Rapports",
        "language": "Langue", "theme": "Thème", "help": "Aide", "dark_mode": "Mode clinique sombre",
        "loading": "Chargement du poste clinique JouriEpi...", "title": "JouriEpi : suite d’épidémiologie clinique et d’inférence causale",
        "offline": "Hors ligne · les données restent dans cette session", "save_workspace": "Enregistrer l’espace (.jepi)",
        "load_workspace": "Charger un espace (.jepi)", "export_code": "Exporter le code reproductible",
        "paired": "Analyse appariée 2×2 et test de McNemar", "dual_roc": "Comparaison de deux courbes ROC (DeLong)",
        "methods": "Méthodes statistiques et provenance algorithmique", "results": "Tableaux de résultats",
        "narrative": "Résultats narratifs", "sensitivity": "Sensibilité causale et audit des facteurs de confusion",
        "embedded_figures": "Figures intégrées", "not_estimable": "Non estimable", "yes": "Oui", "no": "Non",
        "language_help": "La langue s’applique aux libellés pris en charge et au dossier généré. Les calculs restent inchangés.",
        "report_methods": "1. Méthodes statistiques et provenance algorithmique", "report_tables": "2. Tableaux de résultats", "report_narrative": "3. Résultats narratifs", "report_sensitivity": "4. Sensibilité causale et audit des facteurs de confusion", "report_figures": "Figures intégrées", "report_integrity": "Note d’audit et d’usage réglementaire", "report_subtitle": "Moteur analytique hors ligne, respectueux de la confidentialité", "report_cells": "Ordre des cellules : a = cas exposés ; b = non-cas exposés ; c = cas non exposés ; d = non-cas non exposés. Les estimations indéfinies sont indiquées comme non estimables sans correction silencieuse.", "report_forest_caption": "Figure 1. Diagramme en forêt généré localement à partir de l’analyse (PNG 300 DPI).", "report_roc_caption": "Figure 2. Courbe ROC générée localement à partir de l’analyse diagnostique (PNG 300 DPI).", "report_fagan_caption": "Figure 3. Nomogramme de Fagan généré localement (PNG 300 DPI).", "report_dca_caption": "Figure 4. Courbe de bénéfice net de l’analyse décisionnelle générée localement (PNG 300 DPI).",
        "sensitivity_metric": "Sensibilité", "specificity_metric": "Spécificité", "ppv_metric": "Valeur prédictive positive", "npv_metric": "Valeur prédictive négative", "auc_metric": "AUC", "estimate_metric": "Estimation", "p_value_metric": "Valeur p bilatérale", "confidence_interval": "Intervalle de confiance à 95 %", "calculate": "Calculer", "warning_changed": "Les données ont changé. Recalculez avant d’interpréter les résultats.", "strobe_title": "Récit des résultats selon STROBE",
        "nav_analysis": "Analyse 2×2", "nav_line_list": "Liste brute → 2×2", "nav_dta": "Précision Diagnostique (DTA)",
        "nav_power": "Taille d'échantillon & Puissance", "nav_advanced": "Analyses avancées (McNemar & ROC)", "nav_publication": "Publication & Normes STROBE",
        "association_analysis": "Analyse d'Association", "contingency_table": "Tableau de contingence", "sampling_design": "Plan d'échantillonnage",
        "cohort_cross": "Cohorte / Transversale", "case_control": "Cas-témoins", "exposed": "Exposés", "unexposed": "Non exposés",
        "case_positive": "Cas (M+)", "noncase_negative": "Témoins (M−)", "row_total": "Total de ligne", "column_totals": "Totaux de colonne",
        "new_session": "Nouvelle session", "export_dossier": "Exporter le dossier (.docx)", "download_workspace": "Télécharger l’espace (.jepi)",
        "load_selected_workspace": "Charger l’espace sélectionné", "workspace_saved": "Espace préparé localement. Enregistrez le fichier .jepi téléchargé pour le conserver.",
        "workspace_loaded": "Somme de contrôle vérifiée et espace chargé.", "institutional_logo": "Logo institutionnel (facultatif)",
        "workspace": "Espace de travail", "workspace_help": "Choisir la vue d’analyse à ouvrir", "offline_detail": "Les données importées et les rapports sont traités localement. Aucun service réseau n’est utilisé pour l’analyse.",
        "method_scope_note": "Calculs de référence modernes ; aucune équivalence exacte avec un logiciel historique n’est revendiquée.",
        "logo_help": "Logo facultatif pour l’en-tête du dossier Word ; conservé uniquement dans cette session.",
        "demo_dataset": "Charger un jeu de démonstration clinique", "demo_choose": "Choisir un exemple clinique synthétique…",
        "demo_cardiovascular": "Étude du risque cardiovasculaire (cohorte 2×2)",
        "demo_roc": "Biomarqueur diagnostique vs référence (ROC/AUC continu)",
        "demo_stratified": "Stratification d’un essai multicentrique (paradoxe de Simpson / Breslow-Day)",
        "demo_disclaimer": "Données synthétiques pédagogiques uniquement — ni dossiers patients réels ni preuves cliniques.",
        "demo_loaded": "Démonstration clinique chargée et analyse calculée.",
        "help_reference_title": "Référence des méthodes cliniques",
        "help_boschloo_title": "Boschloo ou Fisher", "help_woolf_katz_title": "Intervalles de confiance de Woolf et Katz",
        "help_evalue_title": "E-value", "help_fagan_title": "Nomogramme de Fagan",
        "help_boschloo": "Boschloo ou Fisher : le test exact de Fisher conditionne sur les deux marges et constitue une option exacte classique, souvent conservatrice, pour les tableaux 2×2 clairsemés. Le test exact inconditionnel de Boschloo peut être plus puissant pour certains tableaux. Choisissez la méthode et le sens du test dans le plan d’analyse, jamais après avoir vu le résultat ; aucun des deux tests ne corrige les biais ou la confusion.",
        "help_woolf_katz": "Woolf ou Katz : l’intervalle de Woolf pour le log-rapport de cotes utilise la variance fondée sur les inverses des cellules et constitue une approximation asymptotique lorsque les cellules sont positives. L’intervalle de Katz pour le log-risque relatif utilise une variance spécifique au risque et nécessite des nombres de cas positifs pour cette formule. Les deux méthodes sont asymptotiques ; les cellules rares ou nulles peuvent rendre les estimations indisponibles ou peu fiables. Aucune correction n’est appliquée silencieusement.",
        "help_evalue": "E-value : force minimale d’association, sur l’échelle du risque relatif, qu’un facteur de confusion non mesuré devrait avoir avec l’exposition et le résultat (conditionnellement aux covariables mesurées) pour expliquer l’association observée dans le cadre de l’E-value. C’est un indicateur de sensibilité, non une preuve de présence ou d’absence de confusion. Interprétez aussi l’E-value de la limite de confiance et les limites de l’étude.",
        "help_fagan": "Nomogramme de Fagan : combine une probabilité pré-test justifiée cliniquement et un rapport de vraisemblance positif ou négatif. Convertissez la probabilité pré-test en cotes, multipliez par le rapport de vraisemblance, puis reconvertissez en probabilité post-test. Le résultat dépend de la probabilité pré-test et de la validité externe des performances du test ; le nomogramme ne valide pas le test et n’établit pas son utilité clinique.",
        "help_citations": "Références des méthodes décrites ici. Téléchargez les formats APA et BibTeX pour les réutiliser.",
        "citation_apa": "Références APA", "citation_bibtex": "Références BibTeX", "download_citations": "Télécharger les références (.txt)",
        "menu_file_help": "Gestion de session et fichiers", "menu_analysis_help": "Ouvrir l’analyse d’association 2×2",
        "menu_diagnostics_help": "Ouvrir les outils diagnostiques et ROC", "menu_reports_help": "Ouvrir les rapports et le dossier clinique",
        "menu_language_help": "Choisir la langue de l’interface", "menu_theme_help": "Basculer entre les thèmes cliniques clair et sombre",
        "menu_help_help": "Aide, accessibilité et confidentialité hors ligne", "file_help_fr": "Gestion de session et fichiers",
        "file_help_de": "Sitzungs- und Dateiverwaltung", "analysis_help_fr": "Ouvrir l’analyse d’association 2×2",
        "analysis_help_de": "2×2-Assoziationsanalyse öffnen", "diagnostics_help_fr": "Ouvrir les outils diagnostiques et ROC",
        "diagnostics_help_de": "Diagnostik- und ROC-Werkzeuge öffnen", "reports_help_fr": "Ouvrir les rapports et le dossier clinique",
        "reports_help_de": "Berichte und klinisches Dossier öffnen", "language_help_fr": "Choisir la langue de l’interface",
        "language_help_de": "Sprache der Benutzeroberfläche auswählen", "theme_help_fr": "Basculer entre les thèmes cliniques clair et sombre",
        "theme_help_de": "Zwischen hellem und dunklem klinischem Design wechseln", "help_help_fr": "Aide, accessibilité et confidentialité hors ligne",
        "help_help_de": "Hilfe, Barrierefreiheit und Offline-Datenschutz",
    },
    "de": {
        "file": "Datei", "analysis": "Analyse", "diagnostics": "Diagnostik", "reports": "Berichte",
        "language": "Sprache", "theme": "Design", "help": "Hilfe", "dark_mode": "Klinischer Dunkelmodus",
        "loading": "JouriEpi Clinical Workstation wird geladen...", "title": "JouriEpi: Klinische Epidemiologie und Kausalinferenz",
        "offline": "Offline · Daten verlassen diese Sitzung nicht", "save_workspace": "Arbeitsbereich speichern (.jepi)",
        "load_workspace": "Arbeitsbereich laden (.jepi)", "export_code": "Reproduzierbaren Code exportieren",
        "paired": "Gepaarte 2×2-Analyse und McNemar-Test", "dual_roc": "Vergleich zweier ROC-Kurven (DeLong)",
        "methods": "Statistische Methoden und algorithmische Herkunft", "results": "Formatierte Ergebnistabellen",
        "narrative": "Ergebnisbeschreibung", "sensitivity": "Kausale Sensitivität und Confounder-Prüfung",
        "embedded_figures": "Eingebettete Abbildungen", "not_estimable": "Nicht schätzbar", "yes": "Ja", "no": "Nein",
        "language_help": "Die Sprache gilt für unterstützte Beschriftungen und den generierten Bericht. Berechnungen bleiben unverändert.",
        "report_methods": "1. Statistische Methoden und algorithmische Herkunft", "report_tables": "2. Formatierte Ergebnistabellen", "report_narrative": "3. Ergebnisbeschreibung", "report_sensitivity": "4. Kausale Sensitivität und Confounder-Prüfung", "report_figures": "Eingebettete Abbildungen", "report_integrity": "Prüf- und regulatorischer Hinweis", "report_subtitle": "Offline-Analyse ohne Weitergabe vertraulicher Daten", "report_cells": "Zellreihenfolge: a = Fälle exponiert; b = Nichtfälle exponiert; c = Fälle nicht exponiert; d = Nichtfälle nicht exponiert. Nicht bestimmbare Schätzungen werden ohne stille Korrektur gekennzeichnet.", "report_forest_caption": "Abbildung 1. Lokal erstellter Forest-Plot der aktuellen Analyse (PNG mit 300 DPI).", "report_roc_caption": "Abbildung 2. Lokal erstellte ROC-Kurve der aktuellen Diagnostik (PNG mit 300 DPI).", "report_fagan_caption": "Abbildung 3. Lokal erstelltes Fagan-Nomogramm (PNG mit 300 DPI).", "report_dca_caption": "Abbildung 4. Lokal erstellter Nettonutzen-Plot der Decision-Curve-Analyse (PNG mit 300 DPI).",
        "sensitivity_metric": "Sensitivität", "specificity_metric": "Spezifität", "ppv_metric": "Positiver Vorhersagewert", "npv_metric": "Negativer Vorhersagewert", "auc_metric": "AUC", "estimate_metric": "Schätzwert", "p_value_metric": "Zweiseitiger p-Wert", "confidence_interval": "95%-Konfidenzintervall", "calculate": "Berechnen", "warning_changed": "Eingaben wurden geändert. Vor der Interpretation erneut berechnen.", "strobe_title": "Ergebnistext nach STROBE",
        "nav_analysis": "2×2-Analyse", "nav_line_list": "Rohdatenliste → 2×2", "nav_dta": "Diagnostische Testgenauigkeit",
        "nav_power": "Stichprobenumfang & Power", "nav_advanced": "Erweiterte Analysen (McNemar & ROC)", "nav_publication": "Publikation & STROBE-Richtlinien",
        "association_analysis": "Assoziationsanalyse", "contingency_table": "Kontingenztafel", "sampling_design": "Studiendesign",
        "cohort_cross": "Kohorte / Querschnitt", "case_control": "Fall-Kontroll", "exposed": "Exponiert", "unexposed": "Nicht exponiert",
        "case_positive": "Fälle (K+)", "noncase_negative": "Kontrollen (K−)", "row_total": "Zeilensumme", "column_totals": "Spaltensummen",
        "new_session": "Neue Sitzung", "export_dossier": "Dossier exportieren (.docx)", "download_workspace": "Arbeitsbereich herunterladen (.jepi)",
        "load_selected_workspace": "Ausgewählten Arbeitsbereich laden", "workspace_saved": "Arbeitsbereich lokal vorbereitet. Speichern Sie die heruntergeladene .jepi-Datei.",
        "workspace_loaded": "Prüfsumme bestätigt und Arbeitsbereich geladen.", "institutional_logo": "Institutionslogo (optional)",
        "workspace": "Arbeitsbereich", "workspace_help": "Analyseansicht auswählen", "offline_detail": "Importierte Daten und Berichte werden lokal verarbeitet. Für Analysen wird kein Netzwerkdienst verwendet.",
        "method_scope_note": "Moderne Referenzberechnungen; eine exakte Übereinstimmung mit historischer Software wird nicht behauptet.",
        "logo_help": "Optionales Logo im Kopf des Word-Dossiers; wird nur in dieser Sitzung gespeichert.",
        "demo_dataset": "Klinischen Demo-Datensatz laden", "demo_choose": "Synthetisches klinisches Beispiel wählen…",
        "demo_cardiovascular": "Studie zum kardiovaskulären Risiko (Kohorte 2×2)",
        "demo_roc": "Diagnostischer Biomarker vs. Referenzstandard (kontinuierliche ROC/AUC)",
        "demo_stratified": "Stratifizierung einer multizentrischen Studie (Simpson-Paradoxon / Breslow-Day)",
        "demo_disclaimer": "Nur synthetische Lehrdaten — keine echten Patientendaten oder klinischen Belege.",
        "demo_loaded": "Klinische Demo geladen und Analyse berechnet.",
        "help_reference_title": "Referenz klinischer Methoden",
        "help_boschloo_title": "Boschloo oder Fisher", "help_woolf_katz_title": "Woolf- und Katz-Konfidenzintervalle",
        "help_evalue_title": "E-Value", "help_fagan_title": "Fagan-Nomogramm",
        "help_boschloo": "Boschloo oder Fisher: Fishers exakter Test konditioniert auf beide Randverteilungen und ist eine verbreitete, oft konservative exakte Option für dünn besetzte 2×2-Tabellen. Boschloos unbedingter exakter Test kann bei bestimmten Tabellen mehr Power haben. Methode und ein-/zweiseitige Alternative sind vor der Ergebnisprüfung im Analyseplan festzulegen; keiner der Tests behebt Verzerrungen oder Confounding.",
        "help_woolf_katz": "Woolf oder Katz: Das Woolf-Intervall für den Log-Odds-Ratio verwendet eine Varianz aus den Zellreziproken und ist bei positiven Zellen eine asymptotische Näherung. Das Katz-Intervall für den Log-Risk-Ratio verwendet eine risikospezifische Varianz und benötigt für diese Formel positive Fallzahlen. Beide Verfahren sind asymptotisch; kleine oder null besetzte Zellen können Schätzungen unzuverlässig oder nicht verfügbar machen. Es erfolgt keine stille Korrektur.",
        "help_evalue": "E-Value: die minimale Stärke eines Zusammenhangs auf der Risk-Ratio-Skala, die ein nicht gemessener Confounder sowohl mit Exposition als auch Ergebnis (bedingt auf gemessene Kovariaten) aufweisen müsste, um den beobachteten Zusammenhang im E-Value-Rahmen zu erklären. Dies ist eine Sensitivitätskennzahl, kein Beweis für oder gegen Confounding. Berücksichtigen Sie den E-Value der Konfidenzgrenze und die Studienlimitationen.",
        "help_fagan": "Fagan-Nomogramm: verbindet eine klinisch begründete Prätestwahrscheinlichkeit mit einem positiven oder negativen Likelihood-Ratio. Prätestwahrscheinlichkeit in Odds umrechnen, mit dem Likelihood-Ratio multiplizieren und anschließend in eine Posttestwahrscheinlichkeit zurückrechnen. Das Ergebnis hängt von der Prätestwahrscheinlichkeit und der Übertragbarkeit der Testgüte ab; das Nomogramm validiert den Test nicht und belegt keinen klinischen Nutzen.",
        "help_citations": "Quellen für die hier beschriebenen Methoden. APA- und BibTeX-Formate können heruntergeladen und wiederverwendet werden.",
        "citation_apa": "APA-Zitate", "citation_bibtex": "BibTeX-Zitate", "download_citations": "Zitate herunterladen (.txt)",
        "menu_file_help": "Sitzungs- und Dateiverwaltung", "menu_analysis_help": "2×2-Assoziationsanalyse öffnen",
        "menu_diagnostics_help": "Diagnostik- und ROC-Werkzeuge öffnen", "menu_reports_help": "Berichte und klinisches Dossier öffnen",
        "menu_language_help": "Sprache der Benutzeroberfläche auswählen", "menu_theme_help": "Zwischen hellem und dunklem klinischem Design wechseln",
        "menu_help_help": "Hilfe, Barrierefreiheit und Offline-Datenschutz", "file_help_fr": "Gestion de session et fichiers",
        "file_help_de": "Sitzungs- und Dateiverwaltung", "analysis_help_fr": "Ouvrir l’analyse d’association 2×2",
        "analysis_help_de": "2×2-Assoziationsanalyse öffnen", "diagnostics_help_fr": "Ouvrir les outils diagnostiques et ROC",
        "diagnostics_help_de": "Diagnostik- und ROC-Werkzeuge öffnen", "reports_help_fr": "Ouvrir les rapports et le dossier clinique",
        "reports_help_de": "Berichte und klinisches Dossier öffnen", "language_help_fr": "Choisir la langue de l’interface",
        "language_help_de": "Sprache der Benutzeroberfläche auswählen", "theme_help_fr": "Basculer entre les thèmes cliniques clair et sombre",
        "theme_help_de": "Zwischen hellem und dunklem klinischem Design wechseln", "help_help_fr": "Aide, accessibilité et confidentialité hors ligne",
        "help_help_de": "Hilfe, Barrierefreiheit und Offline-Datenschutz",
    },
}

# Startup and local-preference labels shared by the UI and first-launch prompt.
_MESSAGES["en"].update({"prefs_title": "Local preferences & institutional defaults", "prefs_author": "Study author / analyst", "prefs_setting": "Default study setting", "prefs_path": "Preferences are saved locally to", "select_language_hint": "Choose the interface language. You can change it later from Language."})
_MESSAGES["fr"].update({"prefs_title": "Préférences locales et paramètres institutionnels", "prefs_author": "Auteur de l’étude / analyste", "prefs_setting": "Cadre d’étude par défaut", "prefs_path": "Les préférences sont enregistrées localement dans", "select_language_hint": "Choisissez la langue de l’interface. Vous pourrez la modifier dans Langue."})
_MESSAGES["de"].update({"prefs_title": "Lokale Einstellungen und institutionelle Vorgaben", "prefs_author": "Studienautor/in / Analyst/in", "prefs_setting": "Standard-Studienumgebung", "prefs_path": "Einstellungen werden lokal gespeichert unter", "select_language_hint": "Wählen Sie die Oberflächensprache. Sie können sie später unter Sprache ändern."})

# Additional offline locale packs. Missing long-form translations intentionally
# remain absent so the translation engine can apply the documented English
# fallback instead of pretending an English string is a verified translation.
_ADDITIONAL_TRANSLATIONS: dict[str, dict[str, str]] = {
    "ar": {
        "file": "ملف", "analysis": "التحليل", "diagnostics": "التشخيص", "reports": "التقارير", "language": "اللغة", "theme": "المظهر", "help": "المساعدة", "dark_mode": "الوضع السريري الداكن", "loading": "جارٍ تحميل محطة JouriEpi السريرية...", "title": "JouriEpi: حزمة الوبائيات السريرية والاستدلال السببي", "offline": "دون اتصال · لا تغادر البيانات هذه الجلسة", "save_workspace": "حفظ مساحة العمل (.jepi)", "load_workspace": "تحميل مساحة العمل (.jepi)", "export_code": "تصدير كود قابل لإعادة الإنتاج", "paired": "تحليل مزدوج 2×2 واختبار McNemar", "dual_roc": "مقارنة منحنيي ROC بطريقة DeLong", "methods": "الطرق الإحصائية ومصدر الخوارزميات", "results": "جداول نتائج منسقة", "narrative": "النتائج السردية", "sensitivity": "حساسية سببية وتدقيق المربكات", "embedded_figures": "الأشكال المضمنة", "not_estimable": "غير قابل للتقدير", "yes": "نعم", "no": "لا", "calculate": "احسب", "confidence_interval": "فاصل الثقة 95%", "nav_analysis": "تحليل 2×2", "nav_line_list": "قائمة السجلات ← 2×2", "nav_dta": "دقة الاختبار التشخيصي", "nav_power": "حجم العينة والقوة", "nav_advanced": "تحليلات متقدمة", "nav_publication": "النشر وإرشادات STROBE", "association_analysis": "تحليل الارتباط", "contingency_table": "جدول التقاطع", "sampling_design": "تصميم المعاينة", "cohort_cross": "أتراب / مقطعي", "case_control": "حالات وشواهد", "exposed": "معرّض", "unexposed": "غير معرّض", "case_positive": "حالة (D+)", "noncase_negative": "غير حالة (D−)", "new_session": "جلسة جديدة", "export_dossier": "تصدير الملف السريري (.docx)", "demo_dataset": "تحميل بيانات سريرية تجريبية", "demo_disclaimer": "بيانات تعليمية اصطناعية فقط، وليست سجلات مرضى أو أدلة سريرية.", "help_reference_title": "مرجع الطرق السريرية", "help_boschloo_title": "Boschloo مقابل Fisher", "help_woolf_katz_title": "فواصل الثقة Woolf وKatz", "help_evalue_title": "قيمة E", "help_fagan_title": "مخطط Fagan", "citation_apa": "مراجع APA", "citation_bibtex": "مراجع BibTeX", "download_citations": "تنزيل المراجع (.txt)"
    },
    "es": {
        "file": "Archivo", "analysis": "Análisis", "diagnostics": "Diagnóstico", "reports": "Informes", "language": "Idioma", "theme": "Tema", "help": "Ayuda", "dark_mode": "Modo clínico oscuro", "loading": "Cargando la estación clínica JouriEpi...", "title": "JouriEpi: suite de epidemiología clínica e inferencia causal", "offline": "Sin conexión · los datos no salen de esta sesión", "save_workspace": "Guardar espacio de trabajo (.jepi)", "load_workspace": "Cargar espacio de trabajo (.jepi)", "export_code": "Exportar código reproducible", "paired": "Análisis pareado 2×2 y prueba de McNemar", "dual_roc": "Comparación de curvas ROC (DeLong)", "methods": "Métodos estadísticos y procedencia algorítmica", "results": "Tablas de resultados", "narrative": "Resultados narrativos", "sensitivity": "Sensibilidad causal y auditoría de confusión", "embedded_figures": "Figuras integradas", "not_estimable": "No estimable", "yes": "Sí", "no": "No", "calculate": "Calcular", "confidence_interval": "Intervalo de confianza del 95 %", "nav_analysis": "Análisis 2×2", "nav_line_list": "Lista de registros → 2×2", "nav_dta": "Exactitud diagnóstica", "nav_power": "Tamaño muestral y potencia", "nav_advanced": "Análisis avanzados", "nav_publication": "Publicación y STROBE", "association_analysis": "Análisis de asociación", "contingency_table": "Tabla de contingencia", "sampling_design": "Diseño de muestreo", "cohort_cross": "Cohorte / transversal", "case_control": "Casos y controles", "exposed": "Expuestos", "unexposed": "No expuestos", "case_positive": "Caso (D+)", "noncase_negative": "No caso (D−)", "new_session": "Nueva sesión", "export_dossier": "Exportar expediente (.docx)", "demo_dataset": "Cargar conjunto clínico de demostración", "demo_disclaimer": "Datos sintéticos educativos; no son historias clínicas ni evidencia clínica.", "help_reference_title": "Referencia de métodos clínicos", "help_boschloo_title": "Boschloo frente a Fisher", "help_woolf_katz_title": "Intervalos de confianza de Woolf y Katz", "help_evalue_title": "Valor E", "help_fagan_title": "Nomograma de Fagan", "citation_apa": "Citas APA", "citation_bibtex": "Citas BibTeX", "download_citations": "Descargar citas (.txt)"
    },
    "ru": {
        "file": "Файл", "analysis": "Анализ", "diagnostics": "Диагностика", "reports": "Отчёты", "language": "Язык", "theme": "Тема", "help": "Справка", "dark_mode": "Тёмная клиническая тема", "loading": "Загрузка клинической станции JouriEpi...", "title": "JouriEpi: клиническая эпидемиология и причинный вывод", "offline": "Офлайн · данные не покидают этот сеанс", "save_workspace": "Сохранить рабочую область (.jepi)", "load_workspace": "Загрузить рабочую область (.jepi)", "export_code": "Экспорт воспроизводимого кода", "paired": "Парный анализ 2×2 и критерий Мак-Немара", "dual_roc": "Сравнение ROC-кривых (DeLong)", "methods": "Статистические методы и происхождение алгоритмов", "results": "Таблицы результатов", "narrative": "Текст результатов", "sensitivity": "Причинная чувствительность и аудит смешения", "embedded_figures": "Встроенные рисунки", "not_estimable": "Не оценивается", "yes": "Да", "no": "Нет", "calculate": "Рассчитать", "confidence_interval": "95%-й доверительный интервал", "nav_analysis": "Анализ 2×2", "nav_line_list": "Список наблюдений → 2×2", "nav_dta": "Диагностическая точность", "nav_power": "Размер выборки и мощность", "nav_advanced": "Расширенный анализ", "nav_publication": "Публикация и STROBE", "association_analysis": "Анализ связи", "contingency_table": "Таблица сопряжённости", "sampling_design": "Дизайн выборки", "cohort_cross": "Когортное / поперечное", "case_control": "Случай–контроль", "exposed": "Подвергшиеся воздействию", "unexposed": "Не подвергшиеся воздействию", "case_positive": "Случай (D+)", "noncase_negative": "Не случай (D−)", "new_session": "Новый сеанс", "export_dossier": "Экспорт клинического отчёта (.docx)", "demo_dataset": "Загрузить клинический пример", "demo_disclaimer": "Только синтетические учебные данные — не реальные записи пациентов и не клинические доказательства.", "help_reference_title": "Справочник клинических методов", "help_boschloo_title": "Бошлоо и Фишер", "help_woolf_katz_title": "Доверительные интервалы Вулфа и Каца", "help_evalue_title": "E-значение", "help_fagan_title": "Номограмма Фагана", "citation_apa": "Ссылки APA", "citation_bibtex": "Ссылки BibTeX", "download_citations": "Скачать ссылки (.txt)"
    },
    "zh": {
        "file": "文件", "analysis": "分析", "diagnostics": "诊断", "reports": "报告", "language": "语言", "theme": "主题", "help": "帮助", "dark_mode": "临床深色模式", "loading": "正在加载 JouriEpi 临床工作站…", "title": "JouriEpi：临床流行病学与因果推断套件", "offline": "离线 · 数据不会离开当前会话", "save_workspace": "保存工作区 (.jepi)", "load_workspace": "加载工作区 (.jepi)", "export_code": "导出可复现代码", "paired": "配对 2×2 与 McNemar 分析", "dual_roc": "DeLong 双 ROC 比较", "methods": "统计方法与算法来源", "results": "格式化结果表", "narrative": "叙述性结果", "sensitivity": "因果敏感性与混杂审查", "embedded_figures": "嵌入图形", "not_estimable": "无法估计", "yes": "是", "no": "否", "calculate": "计算", "confidence_interval": "95% 置信区间", "nav_analysis": "2×2 分析", "nav_line_list": "个体数据列表 → 2×2", "nav_dta": "诊断试验准确性", "nav_power": "样本量与检验效能", "nav_advanced": "高级分析", "nav_publication": "出版与 STROBE", "association_analysis": "关联分析", "contingency_table": "列联表", "sampling_design": "抽样设计", "cohort_cross": "队列 / 横断面", "case_control": "病例对照", "exposed": "暴露组", "unexposed": "未暴露组", "case_positive": "病例 (D+)", "noncase_negative": "非病例 (D−)", "new_session": "新会话", "export_dossier": "导出临床档案 (.docx)", "demo_dataset": "加载临床演示数据", "demo_disclaimer": "仅为合成教学数据，不是真实患者记录或临床证据。", "help_reference_title": "临床方法参考", "help_boschloo_title": "Boschloo 与 Fisher 比较", "help_woolf_katz_title": "Woolf 与 Katz 置信区间", "help_evalue_title": "E 值", "help_fagan_title": "Fagan 列线图", "citation_apa": "APA 引文", "citation_bibtex": "BibTeX 引文", "download_citations": "下载引文 (.txt)"
    },
    "ja": {
        "file": "ファイル", "analysis": "解析", "diagnostics": "診断", "reports": "レポート", "language": "言語", "theme": "テーマ", "help": "ヘルプ", "dark_mode": "臨床ダークモード", "loading": "JouriEpi 臨床ワークステーションを読み込み中…", "title": "JouriEpi：臨床疫学・因果推論スイート", "offline": "オフライン · データはこのセッション外へ送信されません", "save_workspace": "ワークスペースを保存 (.jepi)", "load_workspace": "ワークスペースを読み込む (.jepi)", "export_code": "再現可能なコードをエクスポート", "paired": "対応のある 2×2 と McNemar 検定", "dual_roc": "DeLong ROC 曲線比較", "methods": "統計手法とアルゴリズムの由来", "results": "整形済み結果表", "narrative": "結果の文章", "sensitivity": "因果感度分析と交絡監査", "embedded_figures": "埋め込み図", "not_estimable": "推定不能", "yes": "はい", "no": "いいえ", "calculate": "計算", "confidence_interval": "95% 信頼区間", "nav_analysis": "2×2 解析", "nav_line_list": "個票データ → 2×2", "nav_dta": "診断精度", "nav_power": "サンプルサイズと検出力", "nav_advanced": "高度な解析", "nav_publication": "出版・STROBE", "association_analysis": "関連解析", "contingency_table": "分割表", "sampling_design": "サンプリング設計", "cohort_cross": "コホート／横断研究", "case_control": "症例対照", "exposed": "曝露群", "unexposed": "非曝露群", "case_positive": "症例 (D+)", "noncase_negative": "非症例 (D−)", "new_session": "新しいセッション", "export_dossier": "臨床レポートをエクスポート (.docx)", "demo_dataset": "臨床デモデータを読み込む", "demo_disclaimer": "教育用の合成データです。実患者記録や臨床エビデンスではありません。", "help_reference_title": "臨床手法リファレンス", "help_boschloo_title": "Boschloo と Fisher", "help_woolf_katz_title": "Woolf と Katz の信頼区間", "help_evalue_title": "E 値", "help_fagan_title": "Fagan ノモグラム", "citation_apa": "APA 引用", "citation_bibtex": "BibTeX 引用", "download_citations": "引用をダウンロード (.txt)"
    },
}

_ADDITIONAL_TRANSLATIONS["es"].update({
    "demo_choose": "Elegir un ejemplo clínico sintético…", "demo_cardiovascular": "Estudio de riesgo cardiovascular (cohorte 2×2)",
    "demo_roc": "Biomarcador diagnóstico frente a referencia (ROC/AUC continuo)", "demo_stratified": "Estratificación de ensayo multicéntrico (Simpson/Breslow-Day)",
    "demo_loaded": "Demostración cargada y análisis calculado.", "help_boschloo": "Boschloo frente a Fisher: Fisher condiciona en ambos márgenes; Boschloo es una prueba exacta incondicional que puede ofrecer mayor potencia en algunas tablas. Preespecifique la alternativa.",
    "help_woolf_katz": "Woolf usa la varianza del log-odds basada en los inversos de las celdas; Katz usa una varianza específica para el log-riesgo relativo. Son aproximaciones asintóticas y no se corrigen silenciosamente las celdas cero.",
    "help_evalue": "El valor E resume la fuerza mínima de asociación que un confusor no medido necesitaría con exposición y resultado para explicar la asociación observada bajo el marco E-value. No demuestra causalidad ni ausencia de confusión.",
    "help_fagan": "El nomograma de Fagan combina una probabilidad preprueba clínicamente justificada con una razón de verosimilitud para obtener una probabilidad posprueba. No valida por sí mismo la prueba.",
})
_ADDITIONAL_TRANSLATIONS["ru"].update({
    "demo_choose": "Выберите синтетический клинический пример…", "demo_cardiovascular": "Сердечно-сосудистый риск (когортная таблица 2×2)",
    "demo_roc": "Диагностический биомаркер и эталон (ROC/AUC)", "demo_stratified": "Стратификация многоцентрового исследования (Симпсон / Бреслоу—Дэй)",
    "demo_loaded": "Демонстрационный набор загружен, анализ рассчитан.",
    "help_boschloo": "Бошлоо и Фишер: точный критерий Фишера условный, а критерий Бошлоо — безусловный и иногда более мощный. Альтернативу следует задать заранее.",
    "help_woolf_katz": "Интервал Вулфа использует дисперсию логарифма отношения шансов; интервал Каца — дисперсию логарифма относительного риска. Это асимптотические приближения; нулевые ячейки автоматически не корректируются.",
    "help_evalue": "E-значение характеризует минимальную силу связи неизмеренного смешивающего фактора с экспозицией и исходом, необходимую для объяснения наблюдаемой связи в рамках метода. Оно не доказывает причинность.",
    "help_fagan": "Номограмма Фагана объединяет обоснованную предтестовую вероятность с отношением правдоподобия для получения посттестовой вероятности. Она не подтверждает валидность теста.",
})
_ADDITIONAL_TRANSLATIONS["zh"].update({
    "demo_choose": "选择合成临床示例…", "demo_cardiovascular": "心血管风险研究（队列 2×2）", "demo_roc": "诊断生物标志物与金标准（ROC/AUC）",
    "demo_stratified": "多中心试验分层（Simpson / Breslow–Day）", "demo_loaded": "已加载临床演示数据并完成计算。",
    "help_boschloo": "Boschloo 与 Fisher：Fisher 精确检验对两个边际条件化；Boschloo 无条件精确检验在部分表格中可能更有检验效能。应预先指定单双侧假设。",
    "help_woolf_katz": "Woolf 对数优势比区间使用单元格倒数方差；Katz 对数相对风险区间使用相对风险专属方差。两者均为渐近方法，零单元格不会被静默修正。",
    "help_evalue": "E 值表示在该框架下，未测量混杂因素与暴露及结局所需的最小关联强度。它是敏感性指标，不证明因果关系或不存在混杂。",
    "help_fagan": "Fagan 列线图将有临床依据的验前概率与似然比结合，得到验后概率。列线图本身不能验证诊断试验或证明临床效用。",
})
_ADDITIONAL_TRANSLATIONS["ja"].update({
    "demo_choose": "合成臨床例を選択…", "demo_cardiovascular": "心血管リスク研究（コホート 2×2）", "demo_roc": "診断バイオマーカーと基準検査（ROC/AUC）",
    "demo_stratified": "多施設試験の層別化（Simpson／Breslow–Day）", "demo_loaded": "臨床デモを読み込み、解析を計算しました。",
    "help_boschloo": "Boschloo と Fisher：Fisher の正確検定は周辺度数を条件とし、Boschloo の無条件正確検定は一部の表で検出力が高くなることがあります。対立仮説は事前に指定します。",
    "help_woolf_katz": "Woolf の対数オッズ比区間はセル逆数の分散を、Katz の対数リスク比区間はリスク比固有の分散を用います。いずれも漸近近似で、ゼロセルを自動補正しません。",
    "help_evalue": "E 値は、観察された関連を説明するために未測定交絡因子が曝露とアウトカムに持つ必要がある最小の関連強度を要約します。因果関係の証明ではありません。",
    "help_fagan": "Fagan ノモグラムは、臨床的に妥当な検査前確率と尤度比から検査後確率を求めます。検査自体の妥当性を証明するものではありません。",
})
_ADDITIONAL_TRANSLATIONS["ar"].update({
    "demo_choose": "اختر مثالاً سريرياً اصطناعياً…", "demo_cardiovascular": "دراسة مخاطر القلب والأوعية (أتراب 2×2)", "demo_roc": "مؤشر حيوي تشخيصي مقابل المعيار المرجعي (ROC/AUC)",
    "demo_stratified": "تقسيم تجربة متعددة المراكز (مفارقة سمبسون / Breslow-Day)", "demo_loaded": "تم تحميل المثال وحساب التحليل.",
    "help_boschloo": "Boschloo مقابل Fisher: يكيّف اختبار Fisher الدقيق على الهوامش، بينما اختبار Boschloo الدقيق غير المشروط قد يكون أعلى قدرة لبعض الجداول. حدّد اتجاه الاختبار مسبقاً.",
    "help_woolf_katz": "يستخدم Woolf تباين لوغاريتم نسبة الأرجحية، ويستخدم Katz تبايناً خاصاً بلوغاريتم الخطر النسبي. كلاهما تقريبي asymptotic ولا تُصحح الخلايا الصفرية بصمت.",
    "help_evalue": "تلخص قيمة E الحد الأدنى لقوة ارتباط عامل مربك غير مقاس بالتعرض والنتيجة لتفسير الارتباط المرصود ضمن إطار قيمة E؛ ولا تثبت السببية.",
    "help_fagan": "يجمع مخطط Fagan احتمالاً قبلياً مبرراً سريرياً مع نسبة الترجيح لاشتقاق الاحتمال البعدي. ولا يثبت المخطط صلاحية الاختبار.",
})

_ADDITIONAL_TRANSLATIONS["ar"].update({"language_help": "تُطبّق اللغة على تسميات الواجهة المدعومة والنصوص المُنشأة؛ ولا تتغير الحسابات.", "institutional_logo": "الشعار المؤسسي (اختياري)", "logo_help": "شعار اختياري في ترويسة تقرير Word؛ يُحفظ في هذه الجلسة فقط.", "workspace": "مساحة العمل", "workspace_help": "اختر عرض التحليل لفتحه", "offline_detail": "تُعالج البيانات والتقارير محلياً. لا تُستخدم خدمة شبكة للتحليل.", "method_scope_note": "حسابات مرجعية حديثة؛ لم يُثبت التطابق التام مع البرامج التاريخية.", "prefs_title": "التفضيلات المحلية والإعدادات المؤسسية", "prefs_author": "مؤلف الدراسة / المحلل", "prefs_setting": "بيئة الدراسة الافتراضية", "prefs_path": "تُحفظ التفضيلات محلياً في", "select_language_hint": "اختر لغة الواجهة. يمكنك تغييرها لاحقاً من قائمة اللغة.", "report_subtitle": "محرك تحليلي محلي يحافظ على الخصوصية"})
_ADDITIONAL_TRANSLATIONS["es"].update({"language_help": "El idioma se aplica a las etiquetas compatibles y al texto de los informes; los cálculos no cambian.", "institutional_logo": "Logotipo institucional (opcional)", "logo_help": "Logotipo opcional en el encabezado Word; se conserva solo en esta sesión.", "workspace": "Espacio de trabajo", "workspace_help": "Elegir la vista de análisis que se abrirá", "offline_detail": "Los datos y los informes se procesan localmente. No se usa ningún servicio de red para el análisis.", "method_scope_note": "Cálculos de referencia modernos; no se afirma paridad exacta con software histórico.", "prefs_title": "Preferencias locales y valores institucionales", "prefs_author": "Autor del estudio / analista", "prefs_setting": "Entorno de estudio predeterminado", "prefs_path": "Las preferencias se guardan localmente en", "select_language_hint": "Elija el idioma de la interfaz. Puede cambiarlo después en Idioma.", "report_subtitle": "Motor analítico sin conexión que protege la privacidad"})
_ADDITIONAL_TRANSLATIONS["ru"].update({"language_help": "Язык применяется к поддерживаемым надписям и тексту отчётов; расчёты не меняются.", "institutional_logo": "Логотип учреждения (необязательно)", "logo_help": "Необязательный логотип в заголовке Word; хранится только в этом сеансе.", "workspace": "Рабочая область", "workspace_help": "Выберите представление анализа", "offline_detail": "Данные и отчёты обрабатываются локально; сетевой сервис для анализа не используется.", "method_scope_note": "Современные справочные расчёты; точное совпадение с историческим ПО не заявляется.", "prefs_title": "Локальные настройки и данные учреждения", "prefs_author": "Автор исследования / аналитик", "prefs_setting": "Среда исследования по умолчанию", "prefs_path": "Настройки сохраняются локально в", "select_language_hint": "Выберите язык интерфейса. Его можно изменить позже в меню Язык.", "report_subtitle": "Автономный аналитический механизм с защитой конфиденциальности"})
_ADDITIONAL_TRANSLATIONS["zh"].update({"language_help": "语言应用于受支持的界面标签和报告文本；计算结果不变。", "institutional_logo": "机构标志（可选）", "logo_help": "可选的 Word 报告页眉标志，仅保存在当前会话。", "workspace": "工作区", "workspace_help": "选择要打开的分析视图", "offline_detail": "数据和报告在本地处理；分析不使用网络服务。", "method_scope_note": "现代参考计算；不声称与历史软件完全一致。", "prefs_title": "本地偏好设置与机构默认值", "prefs_author": "研究作者／分析员", "prefs_setting": "默认研究环境", "prefs_path": "偏好设置保存在本地：", "select_language_hint": "请选择界面语言。之后可在“语言”菜单中更改。", "report_subtitle": "离线隐私保护分析引擎"})
_ADDITIONAL_TRANSLATIONS["ja"].update({"language_help": "対応する画面ラベルとレポート文に言語が適用されます。計算結果は変わりません。", "institutional_logo": "機関ロゴ（任意）", "logo_help": "Word レポートのヘッダーに任意で表示するロゴです。このセッション内のみ保持されます。", "workspace": "ワークスペース", "workspace_help": "開く解析画面を選択", "offline_detail": "データとレポートはローカルで処理され、解析にネットワークサービスは使用しません。", "method_scope_note": "現代的な参照計算です。旧ソフトとの完全一致は主張しません。", "prefs_title": "ローカル設定と機関の既定値", "prefs_author": "研究責任者／分析者", "prefs_setting": "既定の研究環境", "prefs_path": "設定のローカル保存先：", "select_language_hint": "インターフェース言語を選択してください。後から「言語」メニューで変更できます。", "report_subtitle": "プライバシーを保護するオフライン分析エンジン"})

# Complete the remaining core report, metric, workspace, and tooltip terms for
# all five additional locales. The dictionary-schema test guards against gaps.
_ADDITIONAL_TRANSLATIONS["ar"].update({
 "analysis_help_de":"فتح تحليل الارتباط 2×2","analysis_help_fr":"فتح تحليل الارتباط 2×2","diagnostics_help_de":"فتح أدوات التشخيص وROC","diagnostics_help_fr":"فتح أدوات التشخيص وROC","file_help_de":"إدارة الجلسة والملفات","file_help_fr":"إدارة الجلسة والملفات","help_help_de":"المساعدة وإمكانية الوصول والخصوصية دون اتصال","help_help_fr":"المساعدة وإمكانية الوصول والخصوصية دون اتصال","language_help_de":"اختيار لغة الواجهة","language_help_fr":"اختيار لغة الواجهة","reports_help_de":"فتح التقارير والملف السريري","reports_help_fr":"فتح التقارير والملف السريري","theme_help_de":"التبديل بين المظهر الفاتح والداكن","theme_help_fr":"التبديل بين المظهر الفاتح والداكن",
 "auc_metric":"المساحة تحت المنحنى","column_totals":"مجاميع الأعمدة","download_workspace":"تنزيل مساحة العمل (.jepi)","estimate_metric":"التقدير","help_citations":"مراجع الطرق الإحصائية الموصوفة؛ نزّل صيغ APA أو BibTeX لإعادة الاستخدام.","load_selected_workspace":"تحميل مساحة العمل المحددة","menu_analysis_help":"فتح تحليل الارتباط 2×2","menu_diagnostics_help":"فتح أدوات الدقة التشخيصية ومنحنيات ROC","menu_file_help":"إدارة الجلسة وملفات مساحة العمل","menu_help_help":"المساعدة وإمكانية الوصول والخصوصية دون اتصال","menu_language_help":"اختيار لغة الواجهة","menu_reports_help":"فتح أدوات النشر والتقارير","menu_theme_help":"التبديل بين المظهر السريري الفاتح والداكن","npv_metric":"القيمة التنبؤية السلبية","p_value_metric":"قيمة p ثنائية الطرف","ppv_metric":"القيمة التنبؤية الإيجابية","report_cells":"ترتيب الخلايا: a حالات معرّضة؛ b غير حالات معرّضة؛ c حالات غير معرّضة؛ d غير حالات غير معرّضة. تُعرض التقديرات غير المحددة على أنها غير قابلة للتقدير دون تصحيح صامت.","report_dca_caption":"الشكل 4. منحنى المنفعة الصافية لتحليل منحنى القرار، مُنشأ محلياً (PNG بدقة 300 DPI).","report_fagan_caption":"الشكل 3. مخطط Fagan مُنشأ محلياً (PNG بدقة 300 DPI).","report_figures":"الأشكال المضمنة","report_forest_caption":"الشكل 1. مخطط الغابة مُنشأ محلياً من التحليل (PNG بدقة 300 DPI).","report_integrity":"ملاحظة التدقيق والاستخدام التنظيمي","report_methods":"1. الطرق الإحصائية ومصدر الخوارزميات","report_narrative":"3. النتائج السردية","report_roc_caption":"الشكل 2. منحنى ROC مُنشأ محلياً من التحليل التشخيصي (PNG بدقة 300 DPI).","report_sensitivity":"4. الحساسية السببية وتدقيق المربكات","report_tables":"2. جداول النتائج المنسقة","row_total":"مجموع الصف","sensitivity_metric":"الحساسية","specificity_metric":"النوعية","strobe_title":"سرد النتائج وفق STROBE","warning_changed":"تغيرت المدخلات. أعد الحساب قبل تفسير النتائج.","workspace_loaded":"تم التحقق من المجموع الاختباري وتحميل مساحة العمل.","workspace_saved":"تم إعداد مساحة العمل محلياً. احفظ ملف .jepi الذي تم تنزيله للاحتفاظ به."
})
_ADDITIONAL_TRANSLATIONS["es"].update({
 "analysis_help_de":"Abrir análisis de asociación 2×2","analysis_help_fr":"Abrir análisis de asociación 2×2","diagnostics_help_de":"Abrir herramientas diagnósticas y ROC","diagnostics_help_fr":"Abrir herramientas diagnósticas y ROC","file_help_de":"Gestión de sesión y archivos","file_help_fr":"Gestión de sesión y archivos","help_help_de":"Ayuda, accesibilidad y privacidad sin conexión","help_help_fr":"Ayuda, accesibilidad y privacidad sin conexión","language_help_de":"Elegir idioma de la interfaz","language_help_fr":"Elegir idioma de la interfaz","reports_help_de":"Abrir informes y expediente clínico","reports_help_fr":"Abrir informes y expediente clínico","theme_help_de":"Cambiar entre temas claro y oscuro","theme_help_fr":"Cambiar entre temas claro y oscuro",
 "auc_metric":"Área bajo la curva","column_totals":"Totales de columna","download_workspace":"Descargar espacio de trabajo (.jepi)","estimate_metric":"Estimación","help_citations":"Referencias de los métodos descritos. Descargue APA o BibTeX para reutilizarlas.","load_selected_workspace":"Cargar espacio de trabajo seleccionado","menu_analysis_help":"Abrir análisis de asociación 2×2","menu_diagnostics_help":"Abrir herramientas diagnósticas y ROC","menu_file_help":"Gestión de sesión y archivos","menu_help_help":"Ayuda, accesibilidad y privacidad sin conexión","menu_language_help":"Elegir idioma de la interfaz","menu_reports_help":"Abrir herramientas de publicación e informes","menu_theme_help":"Cambiar entre temas clínicos claro y oscuro","npv_metric":"Valor predictivo negativo","p_value_metric":"Valor p bilateral","ppv_metric":"Valor predictivo positivo","report_cells":"Orden de celdas: a casos expuestos; b no casos expuestos; c casos no expuestos; d no casos no expuestos. Las estimaciones no definidas se indican como no estimables sin corrección silenciosa.","report_dca_caption":"Figura 4. Curva de beneficio neto del análisis de decisión, generada localmente (PNG 300 DPI).","report_fagan_caption":"Figura 3. Nomograma de Fagan generado localmente (PNG 300 DPI).","report_figures":"Figuras integradas","report_forest_caption":"Figura 1. Diagrama de bosque generado localmente a partir del análisis (PNG 300 DPI).","report_integrity":"Nota de auditoría y uso regulatorio","report_methods":"1. Métodos estadísticos y procedencia algorítmica","report_narrative":"3. Resultados narrativos","report_roc_caption":"Figura 2. Curva ROC generada localmente a partir del análisis diagnóstico (PNG 300 DPI).","report_sensitivity":"4. Sensibilidad causal y auditoría de confusión","report_tables":"2. Tablas de resultados","row_total":"Total de fila","sensitivity_metric":"Sensibilidad","specificity_metric":"Especificidad","strobe_title":"Narrativa de resultados STROBE","warning_changed":"Los datos cambiaron. Recalcule antes de interpretar los resultados.","workspace_loaded":"Suma de comprobación verificada y espacio de trabajo cargado.","workspace_saved":"Espacio preparado localmente. Guarde el archivo .jepi descargado para conservarlo."
})
_ADDITIONAL_TRANSLATIONS["ru"].update({
 "analysis_help_de":"Открыть анализ связи 2×2","analysis_help_fr":"Открыть анализ связи 2×2","diagnostics_help_de":"Открыть инструменты диагностики и ROC","diagnostics_help_fr":"Открыть инструменты диагностики и ROC","file_help_de":"Управление сеансом и файлами","file_help_fr":"Управление сеансом и файлами","help_help_de":"Справка, доступность и офлайн-конфиденциальность","help_help_fr":"Справка, доступность и офлайн-конфиденциальность","language_help_de":"Выбрать язык интерфейса","language_help_fr":"Выбрать язык интерфейса","reports_help_de":"Открыть отчёты и клиническое досье","reports_help_fr":"Открыть отчёты и клиническое досье","theme_help_de":"Переключить светлую или тёмную тему","theme_help_fr":"Переключить светлую или тёмную тему",
 "auc_metric":"Площадь под кривой","column_totals":"Итоги по столбцам","download_workspace":"Скачать рабочую область (.jepi)","estimate_metric":"Оценка","help_citations":"Источники описанных методов. Загрузите форматы APA или BibTeX для повторного использования.","load_selected_workspace":"Загрузить выбранную рабочую область","menu_analysis_help":"Открыть анализ связи 2×2","menu_diagnostics_help":"Открыть инструменты диагностики и ROC","menu_file_help":"Управление сеансом и файлами","menu_help_help":"Справка, доступность и офлайн-конфиденциальность","menu_language_help":"Выбрать язык интерфейса","menu_reports_help":"Открыть публикационные инструменты и отчёты","menu_theme_help":"Переключить светлую или тёмную клиническую тему","npv_metric":"Отрицательная прогностическая ценность","p_value_metric":"Двустороннее значение p","ppv_metric":"Положительная прогностическая ценность","report_cells":"Порядок ячеек: a — случаи с воздействием; b — неслучаи с воздействием; c — случаи без воздействия; d — неслучаи без воздействия. Неопределимые оценки отмечаются без скрытой коррекции.","report_dca_caption":"Рисунок 4. Кривая чистой пользы анализа решений, созданная локально (PNG 300 DPI).","report_fagan_caption":"Рисунок 3. Номограмма Фагана, созданная локально (PNG 300 DPI).","report_figures":"Встроенные рисунки","report_forest_caption":"Рисунок 1. Локально созданный лесной график текущего анализа (PNG 300 DPI).","report_integrity":"Примечание об аудите и нормативном использовании","report_methods":"1. Статистические методы и происхождение алгоритмов","report_narrative":"3. Текст результатов","report_roc_caption":"Рисунок 2. ROC-кривая, созданная локально по диагностическому анализу (PNG 300 DPI).","report_sensitivity":"4. Причинная чувствительность и аудит смешения","report_tables":"2. Форматированные таблицы результатов","row_total":"Итого по строке","sensitivity_metric":"Чувствительность","specificity_metric":"Специфичность","strobe_title":"Описание результатов по STROBE","warning_changed":"Данные изменились. Пересчитайте перед интерпретацией результатов.","workspace_loaded":"Контрольная сумма проверена, рабочая область загружена.","workspace_saved":"Рабочая область подготовлена локально. Сохраните загруженный файл .jepi."
})
_ADDITIONAL_TRANSLATIONS["zh"].update({
 "analysis_help_de":"打开 2×2 关联分析","analysis_help_fr":"打开 2×2 关联分析","diagnostics_help_de":"打开诊断准确性与 ROC 工具","diagnostics_help_fr":"打开诊断准确性与 ROC 工具","file_help_de":"会话与文件管理","file_help_fr":"会话与文件管理","help_help_de":"帮助、无障碍与离线隐私信息","help_help_fr":"帮助、无障碍与离线隐私信息","language_help_de":"选择界面语言","language_help_fr":"选择界面语言","reports_help_de":"打开报告与临床档案","reports_help_fr":"打开报告与临床档案","theme_help_de":"切换浅色或深色主题","theme_help_fr":"切换浅色或深色主题",
 "auc_metric":"曲线下面积","column_totals":"列合计","download_workspace":"下载工作区 (.jepi)","estimate_metric":"估计值","help_citations":"此处方法的参考文献。可下载 APA 或 BibTeX 格式以供引用。","load_selected_workspace":"加载所选工作区","menu_analysis_help":"打开 2×2 关联分析","menu_diagnostics_help":"打开诊断准确性与 ROC 工具","menu_file_help":"会话与工作区文件管理","menu_help_help":"帮助、无障碍与离线隐私信息","menu_language_help":"选择界面语言","menu_reports_help":"打开出版与报告工具","menu_theme_help":"切换浅色或深色临床主题","npv_metric":"阴性预测值","p_value_metric":"双侧 p 值","ppv_metric":"阳性预测值","report_cells":"单元格顺序：a=暴露组病例；b=暴露组非病例；c=未暴露组病例；d=未暴露组非病例。不可定义的估计会明确标记，不进行静默修正。","report_dca_caption":"图 4. 本地生成的决策曲线净获益图（PNG 300 DPI）。","report_fagan_caption":"图 3. 本地生成的 Fagan 列线图（PNG 300 DPI）。","report_figures":"嵌入图形","report_forest_caption":"图 1. 根据分析本地生成的森林图（PNG 300 DPI）。","report_integrity":"审计与监管使用说明","report_methods":"1. 统计方法与算法来源","report_narrative":"3. 叙述性结果","report_roc_caption":"图 2. 根据诊断分析本地生成的 ROC 曲线（PNG 300 DPI）。","report_sensitivity":"4. 因果敏感性与混杂审查","report_tables":"2. 格式化结果表","row_total":"行合计","sensitivity_metric":"敏感度","specificity_metric":"特异度","strobe_title":"STROBE 结果叙述","warning_changed":"输入数据已更改。请重新计算后再解释结果。","workspace_loaded":"校验和已验证，工作区已加载。","workspace_saved":"工作区已在本地准备。请保存下载的 .jepi 文件以保留内容。"
})
_ADDITIONAL_TRANSLATIONS["ja"].update({
 "analysis_help_de":"2×2 関連解析を開く","analysis_help_fr":"2×2 関連解析を開く","diagnostics_help_de":"診断精度と ROC ツールを開く","diagnostics_help_fr":"診断精度と ROC ツールを開く","file_help_de":"セッションとファイルの管理","file_help_fr":"セッションとファイルの管理","help_help_de":"ヘルプ、アクセシビリティ、オフラインのプライバシー情報","help_help_fr":"ヘルプ、アクセシビリティ、オフラインのプライバシー情報","language_help_de":"インターフェース言語を選択","language_help_fr":"インターフェース言語を選択","reports_help_de":"レポートと臨床資料を開く","reports_help_fr":"レポートと臨床資料を開く","theme_help_de":"ライト／ダークテーマを切り替える","theme_help_fr":"ライト／ダークテーマを切り替える",
 "auc_metric":"曲線下面積","column_totals":"列合計","download_workspace":"ワークスペースをダウンロード (.jepi)","estimate_metric":"推定値","help_citations":"ここで説明した手法の参考文献です。再利用用に APA または BibTeX をダウンロードできます。","load_selected_workspace":"選択したワークスペースを読み込む","menu_analysis_help":"2×2 関連解析を開く","menu_diagnostics_help":"診断精度と ROC ツールを開く","menu_file_help":"セッションとワークスペースの管理","menu_help_help":"ヘルプ、アクセシビリティ、オフラインのプライバシー情報","menu_language_help":"インターフェース言語を選択","menu_reports_help":"出版・レポートツールを開く","menu_theme_help":"ライト／ダーク臨床テーマを切り替える","npv_metric":"陰性的中率","p_value_metric":"両側 p 値","ppv_metric":"陽性的中率","report_cells":"セルの順序：a=曝露あり症例、b=曝露あり非症例、c=曝露なし症例、d=曝露なし非症例。定義できない推定値は自動補正せず、その旨を明示します。","report_dca_caption":"図 4. ローカルで生成した意思決定曲線の純便益図（PNG 300 DPI）。","report_fagan_caption":"図 3. ローカルで生成した Fagan ノモグラム（PNG 300 DPI）。","report_figures":"埋め込み図","report_forest_caption":"図 1. 解析からローカルで生成したフォレストプロット（PNG 300 DPI）。","report_integrity":"監査および規制利用に関する注記","report_methods":"1. 統計手法とアルゴリズムの由来","report_narrative":"3. 結果の文章","report_roc_caption":"図 2. 診断解析からローカルで生成した ROC 曲線（PNG 300 DPI）。","report_sensitivity":"4. 因果感度分析と交絡監査","report_tables":"2. 整形済み結果表","row_total":"行合計","sensitivity_metric":"感度","specificity_metric":"特異度","strobe_title":"STROBE に沿った結果記述","warning_changed":"入力が変更されました。結果を解釈する前に再計算してください。","workspace_loaded":"チェックサムを検証し、ワークスペースを読み込みました。","workspace_saved":"ワークスペースをローカルで準備しました。保持するにはダウンロードした .jepi ファイルを保存してください。"
})

for _locale, _translations in _ADDITIONAL_TRANSLATIONS.items():
    _MESSAGES[_locale] = dict(_translations)

def normalize_language(language: str | None) -> str:
    """Return a supported language code, defaulting safely to English."""
    code = (language or "en").lower().split("-")[0]
    return code if code in _MESSAGES else "en"

def translate(key: str, language: str = "en", *, fallback: str | None = None) -> str:
    """Translate a key; missing locale entries use English, unknown keys remain explicit."""
    code = normalize_language(language)
    if key in _MESSAGES[code]:
        return _MESSAGES[code][key]
    if fallback is not None:
        return fallback
    return _MESSAGES["en"].get(key, key)

def translate_mapping(values: Mapping[str, str], language: str = "en") -> dict[str, str]:
    """Translate dictionary values whose keys are localization keys."""
    return {key: translate(key, language, fallback=value) for key, value in values.items()}


_MENU_TOOLTIPS = {
    "en": {"file": "Session and workspace file management", "analysis": "Open 2×2 association analysis",
           "diagnostics": "Open diagnostic accuracy and ROC tools", "reports": "Open publication and dossier tools",
           "language": "Choose the interface language", "theme": "Switch between light and dark clinical themes",
           "help": "Help, accessibility, and offline privacy information"},
    "fr": {"file": "Gestion de session et fichiers", "analysis": "Ouvrir l’analyse d’association 2×2",
           "diagnostics": "Ouvrir les outils diagnostiques et ROC", "reports": "Ouvrir les rapports et le dossier clinique",
           "language": "Choisir la langue de l’interface", "theme": "Basculer entre les thèmes cliniques clair et sombre",
           "help": "Aide, accessibilité et confidentialité hors ligne"},
    "de": {"file": "Sitzungs- und Dateiverwaltung", "analysis": "2×2-Assoziationsanalyse öffnen",
           "diagnostics": "Diagnostik- und ROC-Werkzeuge öffnen", "reports": "Berichte und klinisches Dossier öffnen",
           "language": "Sprache der Benutzeroberfläche auswählen", "theme": "Zwischen hellem und dunklem klinischem Design wechseln",
           "help": "Hilfe, Barrierefreiheit und Offline-Datenschutz"},
}

_MENU_TOOLTIPS.update({
    "ar": {"file": "إدارة الجلسة وملفات مساحة العمل", "analysis": "فتح تحليل الارتباط 2×2", "diagnostics": "فتح أدوات الدقة التشخيصية ومنحنيات ROC", "reports": "فتح أدوات النشر والتقارير", "language": "اختيار لغة الواجهة", "theme": "التبديل بين المظهر السريري الفاتح والداكن", "help": "المساعدة وإمكانية الوصول والخصوصية دون اتصال"},
    "es": {"file": "Gestión de sesión y archivos", "analysis": "Abrir análisis de asociación 2×2", "diagnostics": "Abrir herramientas diagnósticas y ROC", "reports": "Abrir informes y herramientas de publicación", "language": "Elegir idioma de la interfaz", "theme": "Cambiar entre temas clínicos claro y oscuro", "help": "Ayuda, accesibilidad y privacidad sin conexión"},
    "ru": {"file": "Управление сеансом и файлами", "analysis": "Открыть анализ связи 2×2", "diagnostics": "Открыть инструменты диагностики и ROC", "reports": "Открыть отчёты и публикационные инструменты", "language": "Выбрать язык интерфейса", "theme": "Переключить светлую или тёмную тему", "help": "Справка, доступность и офлайн-конфиденциальность"},
    "zh": {"file": "会话与工作区文件管理", "analysis": "打开 2×2 关联分析", "diagnostics": "打开诊断准确性与 ROC 工具", "reports": "打开出版和报告工具", "language": "选择界面语言", "theme": "切换浅色或深色临床主题", "help": "帮助、无障碍与离线隐私信息"},
    "ja": {"file": "セッションとワークスペースの管理", "analysis": "2×2 関連解析を開く", "diagnostics": "診断精度と ROC ツールを開く", "reports": "出版・レポートツールを開く", "language": "インターフェース言語を選択", "theme": "ライト／ダーク臨床テーマを切り替える", "help": "ヘルプ、アクセシビリティ、オフラインのプライバシー情報"},
})


def menu_tooltip(menu: str, language: str = "en") -> str:
    """Localized native hover text for each top-level menu action."""
    code = normalize_language(language)
    return _MENU_TOOLTIPS.get(code, _MENU_TOOLTIPS["en"]).get(menu, menu)
