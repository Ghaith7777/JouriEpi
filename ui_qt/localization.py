"""Qt presentation labels layered over the shared core/i18n catalog."""
from PySide6.QtWidgets import QAbstractButton, QComboBox, QLabel, QTableWidget

LANGUAGES = {
    "en": "English", "fr": "Français", "de": "Deutsch", "ar": "العربية",
    "es": "Español", "ru": "Русский", "zh": "中文", "ja": "日本語",
}


def normalize_language(language: str) -> str:
    return language if language in LANGUAGES else "en"

_UI = {
    "en": {
        "title": "JouriEpi Clinical Workstation", "file": "File", "analysis": "Analysis",
        "diagnostics": "Diagnostics", "reports": "Reports", "language": "Language", "theme": "Theme", "help": "Help",
        "new_session": "New session", "menu_file_help": "Create a clean local analysis session.",
        "menu_analysis_help": "Choose a statistical workspace.", "menu_diagnostics_help": "Diagnostic test analysis.",
        "menu_reports_help": "Publication and reproducibility exports.", "menu_language_help": "Change the interface language.",
        "menu_theme_help": "Change the clinical color theme.", "menu_help_help": "Application information.",
        "nav_analysis": "2×2 Association", "nav_dta": "Diagnostic accuracy & ROC", "nav_line_list": "Line list & outbreak curve", "nav_publication": "Publication & exports",
        "results": "Results", "estimate_metric": "Estimate",
        "nav_association": "2×2 Association", "nav_stratified": "Stratified & Simpson's check",
        "nav_diagnostics": "Diagnostic accuracy & ROC", "nav_paired": "Paired 2×2 / McNemar",
        "nav_interaction": "Additive interaction", "nav_outbreak": "Line list & outbreak curve",
        "nav_reports": "Publication & exports", "dark_theme": "Dark clinical theme",
        "nav_interaction": "Additive interaction",
        "light_theme": "Light clinical theme", "about": "About JouriEpi", "exit": "Exit",
        "collapse": "Collapse navigation", "expand": "Expand navigation",
        "run": "Run analysis", "file_open": "Import CSV / Excel…", "no_result": "Run an analysis before exporting.",
        "offline_notice": "Offline-first · data stays on this computer · no telemetry",
    },
    "fr": {
        "title": "Poste de travail clinique JouriEpi", "file": "Fichier", "analysis": "Analyse",
        "diagnostics": "Diagnostics", "reports": "Rapports", "language": "Langue", "theme": "Thème", "help": "Aide",
        "new_session": "Nouvelle session", "menu_file_help": "Créer une nouvelle session d’analyse locale.",
        "menu_analysis_help": "Choisir un espace d’analyse statistique.", "menu_diagnostics_help": "Analyse des tests diagnostiques.",
        "menu_reports_help": "Exports de publication et de reproductibilité.", "menu_language_help": "Modifier la langue de l’interface.",
        "menu_theme_help": "Modifier le thème clinique.", "menu_help_help": "Informations sur l’application.",
        "nav_analysis": "Association 2×2", "nav_dta": "Précision diagnostique et ROC", "nav_line_list": "Liste de cas et courbe épidémique", "nav_publication": "Publication et exports",
        "results": "Résultats", "estimate_metric": "Estimation",
        "nav_association": "Association 2×2", "nav_stratified": "Stratification et paradoxe de Simpson",
        "nav_diagnostics": "Précision diagnostique et ROC", "nav_paired": "Appariement 2×2 / McNemar",
        "nav_interaction": "Interaction additive", "nav_outbreak": "Liste de cas et courbe épidémique",
        "nav_reports": "Publication et exportations", "dark_theme": "Thème clinique sombre",
        "nav_interaction": "Interaction additive",
        "light_theme": "Thème clinique clair", "about": "À propos de JouriEpi", "exit": "Quitter",
        "collapse": "Réduire la navigation", "expand": "Développer la navigation",
        "run": "Lancer l’analyse", "file_open": "Importer CSV / Excel…", "no_result": "Lancez une analyse avant l’exportation.",
        "offline_notice": "Priorité hors ligne · données conservées sur cet ordinateur · aucune télémétrie",
    },
    "de": {
        "title": "JouriEpi Klinischer Arbeitsplatz", "file": "Datei", "analysis": "Analyse",
        "diagnostics": "Diagnostik", "reports": "Berichte", "language": "Sprache", "theme": "Design", "help": "Hilfe",
        "new_session": "Neue Sitzung", "menu_file_help": "Eine neue lokale Analysesitzung erstellen.",
        "menu_analysis_help": "Statistischen Arbeitsbereich auswählen.", "menu_diagnostics_help": "Diagnostische Testanalyse.",
        "menu_reports_help": "Publikations- und Reproduzierbarkeitsexporte.", "menu_language_help": "Oberflächensprache ändern.",
        "menu_theme_help": "Klinisches Farbdesign ändern.", "menu_help_help": "Informationen zur Anwendung.",
        "nav_analysis": "2×2-Assoziation", "nav_dta": "Diagnostische Genauigkeit und ROC", "nav_line_list": "Fallliste und Epidemiekurve", "nav_publication": "Publikation und Export",
        "results": "Ergebnisse", "estimate_metric": "Schätzwert",
        "nav_association": "2×2-Assoziation", "nav_stratified": "Stratifizierung und Simpson-Paradoxon",
        "nav_diagnostics": "Diagnostische Genauigkeit und ROC", "nav_paired": "Gepaarte 2×2 / McNemar",
        "nav_interaction": "Additive Interaktion", "nav_outbreak": "Fallliste und Epidemiekurve",
        "nav_reports": "Publikation und Export", "dark_theme": "Dunkles klinisches Design",
        "nav_interaction": "Additive Interaktion",
        "light_theme": "Helles klinisches Design", "about": "Über JouriEpi", "exit": "Beenden",
        "collapse": "Navigation einklappen", "expand": "Navigation ausklappen",
        "run": "Analyse ausführen", "file_open": "CSV / Excel importieren…", "no_result": "Vor dem Export bitte eine Analyse ausführen.",
        "offline_notice": "Offline-first · Daten bleiben auf diesem Computer · keine Telemetrie",
    },
    "ar": {
        "title": "محطة العمل السريرية JouriEpi", "file": "ملف", "analysis": "التحليل",
        "diagnostics": "التشخيص", "reports": "التقارير", "language": "اللغة", "theme": "المظهر", "help": "مساعدة",
        "new_session": "جلسة جديدة", "menu_file_help": "إنشاء جلسة تحليل محلية جديدة.",
        "menu_analysis_help": "اختيار مساحة التحليل الإحصائي.", "menu_diagnostics_help": "تحليل الاختبارات التشخيصية.",
        "menu_reports_help": "تصدير النشر وقابلية إعادة الإنتاج.", "menu_language_help": "تغيير لغة الواجهة.",
        "menu_theme_help": "تغيير المظهر السريري.", "menu_help_help": "معلومات التطبيق.",
        "nav_analysis": "تحليل الارتباط 2×2", "nav_dta": "الدقة التشخيصية ومنحنى ROC", "nav_line_list": "قائمة الحالات والمنحنى الوبائي", "nav_publication": "النشر والتصدير",
        "results": "النتائج", "estimate_metric": "التقدير",
        "nav_association": "تحليل الارتباط 2×2", "nav_stratified": "التحليل الطبقي ومفارقة سيمبسون",
        "nav_diagnostics": "الدقة التشخيصية ومنحنى ROC", "nav_paired": "تحليل مزدوج 2×2 / ماكنيمار",
        "nav_interaction": "التفاعل الإضافي", "nav_outbreak": "قائمة الحالات والمنحنى الوبائي",
        "nav_reports": "النشر والتصدير", "dark_theme": "المظهر السريري الداكن",
        "nav_interaction": "التفاعل الإضافي",
        "light_theme": "المظهر السريري الفاتح", "about": "حول JouriEpi", "exit": "خروج",
        "collapse": "طي شريط التنقل", "expand": "توسيع شريط التنقل",
        "run": "تنفيذ التحليل", "file_open": "استيراد CSV / Excel…", "no_result": "نفّذ تحليلاً قبل التصدير.",
        "offline_notice": "يعمل دون اتصال · تبقى البيانات على هذا الحاسوب · لا توجد قياسات استخدام",
    },
    "es": {
        "title": "Estación clínica JouriEpi", "file": "Archivo", "analysis": "Análisis",
        "diagnostics": "Diagnóstico", "reports": "Informes", "language": "Idioma", "theme": "Tema", "help": "Ayuda",
        "new_session": "Nueva sesión", "menu_file_help": "Crear una nueva sesión de análisis local.",
        "menu_analysis_help": "Elegir un espacio de análisis estadístico.", "menu_diagnostics_help": "Análisis de pruebas diagnósticas.",
        "menu_reports_help": "Exportaciones para publicación y reproducibilidad.", "menu_language_help": "Cambiar el idioma de la interfaz.",
        "menu_theme_help": "Cambiar el tema clínico.", "menu_help_help": "Información de la aplicación.",
        "nav_analysis": "Asociación 2×2", "nav_dta": "Precisión diagnóstica y ROC", "nav_line_list": "Lista de casos y curva epidémica", "nav_publication": "Publicación y exportaciones",
        "results": "Resultados", "estimate_metric": "Estimación",
        "nav_association": "Asociación 2×2", "nav_stratified": "Estratificación y paradoja de Simpson",
        "nav_diagnostics": "Precisión diagnóstica y ROC", "nav_paired": "2×2 pareado / McNemar",
        "nav_interaction": "Interacción aditiva", "nav_outbreak": "Lista de casos y curva epidémica",
        "nav_reports": "Publicación y exportaciones", "dark_theme": "Tema clínico oscuro",
        "nav_interaction": "Interacción aditiva",
        "light_theme": "Tema clínico claro", "about": "Acerca de JouriEpi", "exit": "Salir",
        "collapse": "Contraer navegación", "expand": "Expandir navegación",
        "run": "Ejecutar análisis", "file_open": "Importar CSV / Excel…", "no_result": "Ejecute un análisis antes de exportar.",
        "offline_notice": "Primero sin conexión · los datos permanecen en este equipo · sin telemetría",
    },
    "ru": {
        "title": "Клиническая рабочая станция JouriEpi", "file": "Файл", "analysis": "Анализ",
        "diagnostics": "Диагностика", "reports": "Отчёты", "language": "Язык", "theme": "Тема", "help": "Справка",
        "new_session": "Новая сессия", "menu_file_help": "Создать новую локальную сессию анализа.",
        "menu_analysis_help": "Выбрать статистическое рабочее пространство.", "menu_diagnostics_help": "Анализ диагностических тестов.",
        "menu_reports_help": "Экспорт публикаций и воспроизводимости.", "menu_language_help": "Изменить язык интерфейса.",
        "menu_theme_help": "Изменить клиническую цветовую тему.", "menu_help_help": "Сведения о приложении.",
        "nav_analysis": "Анализ связи 2×2", "nav_dta": "Диагностическая точность и ROC", "nav_line_list": "Список случаев и эпидемическая кривая", "nav_publication": "Публикации и экспорт",
        "results": "Результаты", "estimate_metric": "Оценка",
        "nav_association": "Анализ связи 2×2", "nav_stratified": "Стратификация и парадокс Симпсона",
        "nav_diagnostics": "Диагностическая точность и ROC", "nav_paired": "Парный анализ 2×2 / Мак-Немара",
        "nav_interaction": "Аддитивное взаимодействие", "nav_outbreak": "Список случаев и эпидемическая кривая",
        "nav_reports": "Публикации и экспорт", "dark_theme": "Тёмная клиническая тема",
        "nav_interaction": "Аддитивное взаимодействие",
        "light_theme": "Светлая клиническая тема", "about": "О JouriEpi", "exit": "Выход",
        "collapse": "Свернуть навигацию", "expand": "Развернуть навигацию",
        "run": "Выполнить анализ", "file_open": "Импорт CSV / Excel…", "no_result": "Перед экспортом выполните анализ.",
        "offline_notice": "Автономная работа · данные остаются на этом компьютере · телеметрия отключена",
    },
    "zh": {
        "title": "JouriEpi 临床工作站", "file": "文件", "analysis": "分析",
        "diagnostics": "诊断", "reports": "报告", "language": "语言", "theme": "主题", "help": "帮助",
        "new_session": "新建会话", "menu_file_help": "创建新的本地分析会话。",
        "menu_analysis_help": "选择统计分析工作区。", "menu_diagnostics_help": "诊断试验分析。",
        "menu_reports_help": "出版与可重复性导出。", "menu_language_help": "更改界面语言。",
        "menu_theme_help": "更改临床配色主题。", "menu_help_help": "应用程序信息。",
        "nav_analysis": "2×2 关联分析", "nav_dta": "诊断准确性与 ROC", "nav_line_list": "病例清单与流行曲线", "nav_publication": "出版与导出",
        "results": "结果", "estimate_metric": "估计值",
        "nav_association": "2×2 关联分析", "nav_stratified": "分层分析与辛普森悖论",
        "nav_diagnostics": "诊断准确性与 ROC", "nav_paired": "配对 2×2 / McNemar",
        "nav_interaction": "相加交互作用", "nav_outbreak": "病例清单与流行曲线",
        "nav_reports": "出版与导出", "dark_theme": "深色临床主题",
        "nav_interaction": "相加交互作用",
        "light_theme": "浅色临床主题", "about": "关于 JouriEpi", "exit": "退出",
        "collapse": "折叠导航", "expand": "展开导航",
        "run": "运行分析", "file_open": "导入 CSV / Excel…", "no_result": "请先运行分析再导出。",
        "offline_notice": "离线优先 · 数据保留在此电脑 · 无遥测",
    },
    "ja": {
        "title": "JouriEpi 臨床ワークステーション", "file": "ファイル", "analysis": "解析",
        "diagnostics": "診断", "reports": "レポート", "language": "言語", "theme": "テーマ", "help": "ヘルプ",
        "new_session": "新しいセッション", "menu_file_help": "新しいローカル解析セッションを作成します。",
        "menu_analysis_help": "統計解析ワークスペースを選択します。", "menu_diagnostics_help": "診断検査の解析。",
        "menu_reports_help": "論文および再現性エクスポート。", "menu_language_help": "インターフェース言語を変更します。",
        "menu_theme_help": "臨床テーマを変更します。", "menu_help_help": "アプリケーション情報。",
        "nav_analysis": "2×2 関連分析", "nav_dta": "診断精度と ROC", "nav_line_list": "症例リストと流行曲線", "nav_publication": "論文・エクスポート",
        "results": "結果", "estimate_metric": "推定値",
        "nav_association": "2×2 関連分析", "nav_stratified": "層別解析とシンプソンのパラドックス",
        "nav_diagnostics": "診断精度と ROC", "nav_paired": "対応のある 2×2 / McNemar",
        "nav_interaction": "相加的交互作用", "nav_outbreak": "症例リストと流行曲線",
        "nav_reports": "論文・エクスポート", "dark_theme": "ダーク臨床テーマ",
        "nav_interaction": "相加的交互作用",
        "light_theme": "ライト臨床テーマ", "about": "JouriEpi について", "exit": "終了",
        "collapse": "ナビゲーションを折りたたむ", "expand": "ナビゲーションを展開",
        "run": "解析を実行", "file_open": "CSV / Excel を読み込む…", "no_result": "エクスポート前に解析を実行してください。",
        "offline_notice": "オフライン優先 · データはこの PC 内に保持 · テレメトリーなし",
    },
}

_UI_EXTRA = {
    "en": {
        "title_association": "2×2 Association Analysis", "title_stratified": "Stratified Analysis & Simpson's Paradox",
        "title_diagnostics": "Diagnostic Accuracy & ROC", "title_paired": "Paired 2×2 & McNemar Analysis",
        "title_interaction": "Additive Interaction · RERI / AP / SI", "title_outbreak": "Line List & Outbreak Curve",
        "title_reports": "Publication & Reproducibility Exports",
        "instruction_2x2": "Enter exposed/unexposed rows and case/non-case columns. Cell order: a, b, c, d.",
        "instruction_stratified": "One stratum per line: name, a, b, c, d (nonnegative integer counts).",
        "tp": "True positives", "fp": "False positives", "fn": "False negatives", "tn": "True negatives",
        "alpha": "Significance level α", "copy_latex": "Copy LaTeX", "save_word": "Save Word dossier…",
        "save_python": "Save Python script…", "save_r": "Save R script…", "report_note": "Exports use the exact serialized core result; calculations are not repeated in the UI.",
        "date_column": "Date column", "case_column": "Case/status column", "id_column": "ID column (optional)",
        "no_line_list": "No line list loaded.", "mode_counts": "2×2 diagnostic counts (TP, FP, FN, TN)",
        "mode_scores": "Continuous scores and binary reference outcomes", "mode_delong": "Compare two ROC curves (DeLong)",
        "haldane": "Explicit Haldane–Anscombe sensitivity correction", "boschloo": "Include Boschloo exact test",
    },
    "fr": {
        "title_association": "Analyse d’association 2×2", "title_stratified": "Analyse stratifiée et paradoxe de Simpson",
        "title_diagnostics": "Précision diagnostique et ROC", "title_paired": "Analyse appariée 2×2 et test de McNemar",
        "title_interaction": "Interaction additive · RERI / AP / SI", "title_outbreak": "Liste de cas et courbe épidémique",
        "title_reports": "Publication et exports de reproductibilité",
        "instruction_2x2": "Saisir les lignes exposés/non exposés et les colonnes cas/non-cas. Ordre : a, b, c, d.",
        "instruction_stratified": "Une strate par ligne : nom, a, b, c, d (effectifs entiers non négatifs).",
        "tp": "Vrais positifs", "fp": "Faux positifs", "fn": "Faux négatifs", "tn": "Vrais négatifs",
        "alpha": "Seuil de signification α", "copy_latex": "Copier le LaTeX", "save_word": "Enregistrer le dossier Word…",
        "save_python": "Enregistrer le script Python…", "save_r": "Enregistrer le script R…", "report_note": "Les exports utilisent le résultat exact du noyau ; aucun calcul n’est refait dans l’interface.",
        "date_column": "Colonne de date", "case_column": "Colonne cas/statut", "id_column": "Colonne ID (facultative)",
        "no_line_list": "Aucune liste de cas chargée.", "mode_counts": "Comptages diagnostiques 2×2 (VP, FP, FN, VN)",
        "mode_scores": "Scores continus et résultats de référence binaires", "mode_delong": "Comparer deux courbes ROC (DeLong)",
        "haldane": "Correction de sensibilité Haldane–Anscombe explicite", "boschloo": "Inclure le test exact de Boschloo",
    },
    "de": {
        "title_association": "2×2-Assoziationsanalyse", "title_stratified": "Stratifizierte Analyse und Simpson-Paradoxon",
        "title_diagnostics": "Diagnostische Genauigkeit und ROC", "title_paired": "Gepaarte 2×2-Analyse und McNemar-Test",
        "title_interaction": "Additive Interaktion · RERI / AP / SI", "title_outbreak": "Fallliste und Epidemiekurve",
        "title_reports": "Publikation und Reproduzierbarkeitsexporte",
        "instruction_2x2": "Zeilen exponiert/nicht exponiert, Spalten Fälle/Nichtfälle. Zellreihenfolge: a, b, c, d.",
        "instruction_stratified": "Eine Schicht pro Zeile: Name, a, b, c, d (nichtnegative ganzzahlige Häufigkeiten).",
        "tp": "Richtig positiv", "fp": "Falsch positiv", "fn": "Falsch negativ", "tn": "Richtig negativ",
        "alpha": "Signifikanzniveau α", "copy_latex": "LaTeX kopieren", "save_word": "Word-Dossier speichern…",
        "save_python": "Python-Skript speichern…", "save_r": "R-Skript speichern…", "report_note": "Exporte verwenden das unveränderte Kernergebnis; in der Oberfläche wird nicht erneut gerechnet.",
        "date_column": "Datumsspalte", "case_column": "Fall-/Statusspalte", "id_column": "ID-Spalte (optional)",
        "no_line_list": "Keine Fallliste geladen.", "mode_counts": "Diagnostische 2×2-Zählwerte (TP, FP, FN, TN)",
        "mode_scores": "Kontinuierliche Scores und binäre Referenzergebnisse", "mode_delong": "Zwei ROC-Kurven vergleichen (DeLong)",
        "haldane": "Explizite Haldane–Anscombe-Sensitivitätskorrektur", "boschloo": "Exakten Boschloo-Test einschließen",
    },
    "ar": {
        "title_association": "تحليل الارتباط 2×2", "title_stratified": "التحليل الطبقي ومفارقة سيمبسون",
        "title_diagnostics": "الدقة التشخيصية ومنحنى ROC", "title_paired": "التحليل المزدوج 2×2 واختبار ماكنيمار",
        "title_interaction": "التفاعل الإضافي · RERI / AP / SI", "title_outbreak": "قائمة الحالات والمنحنى الوبائي",
        "title_reports": "التقارير وتصدير قابلية إعادة الإنتاج",
        "instruction_2x2": "أدخل صفوف المعرّضين وغير المعرّضين وأعمدة الحالات وغير الحالات. ترتيب الخلايا: a، b، c، d.",
        "instruction_stratified": "طبقة واحدة في كل سطر: الاسم، a، b، c، d (أعداد صحيحة غير سالبة).",
        "tp": "إيجابيات صحيحة", "fp": "إيجابيات كاذبة", "fn": "سلبيات كاذبة", "tn": "سلبيات صحيحة",
        "alpha": "مستوى الدلالة α", "copy_latex": "نسخ LaTeX", "save_word": "حفظ تقرير Word…",
        "save_python": "حفظ سكربت Python…", "save_r": "حفظ سكربت R…", "report_note": "تستخدم الصادرات نتيجة النواة كما هي؛ لا تُعاد الحسابات داخل الواجهة.",
        "date_column": "عمود التاريخ", "case_column": "عمود الحالة/الوضع", "id_column": "عمود المعرّف (اختياري)",
        "no_line_list": "لم يتم تحميل قائمة الحالات.", "mode_counts": "أعداد تشخيصية 2×2 (إيجابي صحيح، إيجابي كاذب، سلبي كاذب، سلبي صحيح)",
        "mode_scores": "درجات مستمرة ونتائج مرجعية ثنائية", "mode_delong": "مقارنة منحنيي ROC (DeLong)",
        "haldane": "تصحيح حساسية Haldane–Anscombe صريح", "boschloo": "تضمين اختبار Boschloo الدقيق",
    },
    "es": {
        "title_association": "Análisis de asociación 2×2", "title_stratified": "Análisis estratificado y paradoja de Simpson",
        "title_diagnostics": "Precisión diagnóstica y ROC", "title_paired": "Análisis pareado 2×2 y prueba de McNemar",
        "title_interaction": "Interacción aditiva · RERI / AP / SI", "title_outbreak": "Lista de casos y curva epidémica",
        "title_reports": "Publicación y exportaciones reproducibles",
        "instruction_2x2": "Filas expuestos/no expuestos y columnas casos/no casos. Orden de celdas: a, b, c, d.",
        "instruction_stratified": "Un estrato por línea: nombre, a, b, c, d (recuentos enteros no negativos).",
        "tp": "Verdaderos positivos", "fp": "Falsos positivos", "fn": "Falsos negativos", "tn": "Verdaderos negativos",
        "alpha": "Nivel de significación α", "copy_latex": "Copiar LaTeX", "save_word": "Guardar informe Word…",
        "save_python": "Guardar script Python…", "save_r": "Guardar script R…", "report_note": "Las exportaciones usan el resultado exacto del núcleo; la interfaz no repite los cálculos.",
        "date_column": "Columna de fecha", "case_column": "Columna caso/estado", "id_column": "Columna ID (opcional)",
        "no_line_list": "No hay ninguna lista de casos cargada.", "mode_counts": "Recuentos diagnósticos 2×2 (VP, FP, FN, VN)",
        "mode_scores": "Puntuaciones continuas y resultados de referencia binarios", "mode_delong": "Comparar dos curvas ROC (DeLong)",
        "haldane": "Corrección de sensibilidad Haldane–Anscombe explícita", "boschloo": "Incluir prueba exacta de Boschloo",
    },
    "ru": {
        "title_association": "Анализ связи 2×2", "title_stratified": "Стратифицированный анализ и парадокс Симпсона",
        "title_diagnostics": "Диагностическая точность и ROC", "title_paired": "Парный анализ 2×2 и критерий Мак-Немара",
        "title_interaction": "Аддитивное взаимодействие · RERI / AP / SI", "title_outbreak": "Список случаев и эпидемическая кривая",
        "title_reports": "Публикации и экспорт воспроизводимости",
        "instruction_2x2": "Строки: подвергшиеся/не подвергшиеся воздействию; столбцы: случаи/не случаи. Порядок: a, b, c, d.",
        "instruction_stratified": "Одна страта на строку: название, a, b, c, d (неотрицательные целые числа).",
        "tp": "Истинно положительные", "fp": "Ложноположительные", "fn": "Ложноотрицательные", "tn": "Истинно отрицательные",
        "alpha": "Уровень значимости α", "copy_latex": "Копировать LaTeX", "save_word": "Сохранить отчёт Word…",
        "save_python": "Сохранить скрипт Python…", "save_r": "Сохранить скрипт R…", "report_note": "Экспорт использует точный результат ядра; интерфейс не выполняет повторные расчёты.",
        "date_column": "Столбец даты", "case_column": "Столбец случая/статуса", "id_column": "Столбец ID (необязательно)",
        "no_line_list": "Список случаев не загружен.", "mode_counts": "Диагностические данные 2×2 (ИП, ЛП, ЛО, ИО)",
        "mode_scores": "Непрерывные оценки и бинарные эталонные исходы", "mode_delong": "Сравнить две ROC-кривые (DeLong)",
        "haldane": "Явная поправка чувствительности Халдейна—Анскомба", "boschloo": "Включить точный тест Бошлу",
    },
    "zh": {
        "title_association": "2×2 关联分析", "title_stratified": "分层分析与辛普森悖论",
        "title_diagnostics": "诊断准确性与 ROC", "title_paired": "配对 2×2 与 McNemar 检验",
        "title_interaction": "相加交互作用 · RERI / AP / SI", "title_outbreak": "病例清单与流行曲线",
        "title_reports": "出版与可重复性导出",
        "instruction_2x2": "行：暴露组/未暴露组；列：病例/非病例。单元格顺序：a、b、c、d。",
        "instruction_stratified": "每行一个分层：名称、a、b、c、d（非负整数计数）。",
        "tp": "真阳性", "fp": "假阳性", "fn": "假阴性", "tn": "真阴性",
        "alpha": "显著性水平 α", "copy_latex": "复制 LaTeX", "save_word": "保存 Word 报告…",
        "save_python": "保存 Python 脚本…", "save_r": "保存 R 脚本…", "report_note": "导出使用核心计算的原始结果；界面不会重复计算。",
        "date_column": "日期列", "case_column": "病例/状态列", "id_column": "ID 列（可选）",
        "no_line_list": "尚未加载病例清单。", "mode_counts": "2×2 诊断计数（真阳性、假阳性、假阴性、真阴性）",
        "mode_scores": "连续评分与二元参考结局", "mode_delong": "比较两条 ROC 曲线（DeLong）",
        "haldane": "明确启用 Haldane–Anscombe 敏感性校正", "boschloo": "包含 Boschloo 精确检验",
    },
    "ja": {
        "title_association": "2×2 関連分析", "title_stratified": "層別解析とシンプソンのパラドックス",
        "title_diagnostics": "診断精度と ROC", "title_paired": "対応のある 2×2 と McNemar 検定",
        "title_interaction": "相加的交互作用 · RERI / AP / SI", "title_outbreak": "症例リストと流行曲線",
        "title_reports": "論文・再現性エクスポート",
        "instruction_2x2": "行は曝露群/非曝露群、列は症例/非症例です。セル順序：a、b、c、d。",
        "instruction_stratified": "1 行に 1 層：名前、a、b、c、d（0 以上の整数カウント）。",
        "tp": "真陽性", "fp": "偽陽性", "fn": "偽陰性", "tn": "真陰性",
        "alpha": "有意水準 α", "copy_latex": "LaTeX をコピー", "save_word": "Word レポートを保存…",
        "save_python": "Python スクリプトを保存…", "save_r": "R スクリプトを保存…", "report_note": "エクスポートはコアの計算結果をそのまま使用し、UI で再計算しません。",
        "date_column": "日付列", "case_column": "症例/状態列", "id_column": "ID 列（任意）",
        "no_line_list": "症例リストは読み込まれていません。", "mode_counts": "2×2 診断カウント（真陽性、偽陽性、偽陰性、真陰性）",
        "mode_scores": "連続スコアと二値参照アウトカム", "mode_delong": "2 つの ROC 曲線を比較（DeLong）",
        "haldane": "Haldane–Anscombe 感度補正を明示的に適用", "boschloo": "Boschloo の正確検定を含める",
    },
}
for _code, _values in _UI_EXTRA.items():
    _UI[_code].update(_values)

_WIDGET_KEYS = {
    "2×2 Association Analysis": "association_analysis",
    "Stratified Analysis & Simpson's Paradox": "nav_advanced",
    "Diagnostic Accuracy & ROC": "nav_dta",
    "Paired 2×2 & McNemar Analysis": "paired",
    "Additive Interaction · RERI / AP / SI": "nav_interaction",
    "Line List & Outbreak Curve": "nav_line_list",
    "Publication & Reproducibility Exports": "nav_publication",
    "Run analysis": "calculate",
    "Exposed": "exposed",
    "Unexposed": "unexposed",
    "Case / disease +": "case_positive",
    "Cases / disease +": "case_positive",
    "Non-cases / disease −": "noncase_negative",
    "Import CSV / Excel…": "file_open",
    "2×2 Association Analysis": "title_association",
    "Stratified Analysis & Simpson's Paradox": "title_stratified",
    "Diagnostic Accuracy & ROC": "title_diagnostics",
    "Paired 2×2 & McNemar Analysis": "title_paired",
    "Additive Interaction · RERI / AP / SI": "title_interaction",
    "Line List & Outbreak Curve": "title_outbreak",
    "Publication & Reproducibility Exports": "title_reports",
    "Enter exposed/unexposed rows and case/non-case columns. Cell order: a, b, c, d.": "instruction_2x2",
    "One stratum per line: name, a, b, c, d (nonnegative integer counts).": "instruction_stratified",
    "True positives": "tp", "False positives": "fp", "False negatives": "fn", "True negatives": "tn",
    "Significance level α": "alpha", "Copy LaTeX": "copy_latex", "Save Word dossier…": "save_word",
    "Save Python script…": "save_python", "Save R script…": "save_r",
    "Exports are generated from the exact serialized core result; calculations are not repeated in the UI.": "report_note",
    "Date column": "date_column", "Case/status column": "case_column", "ID column (optional)": "id_column",
    "No line list loaded.": "no_line_list",
    "Explicit Haldane–Anscombe sensitivity correction": "haldane", "Include Boschloo exact test": "boschloo",
    "2×2 diagnostic counts (TP, FP, FN, TN)": "mode_counts",
    "Continuous scores and binary reference outcomes": "mode_scores",
    "Compare two ROC curves (DeLong)": "mode_delong",
}


def retranslate_widget_tree(root, language: str) -> None:
    """Refresh known authored labels in-place while preserving user-entered data."""
    for widget in root.findChildren(QLabel) + root.findChildren(QAbstractButton):
        source = widget.property("jouriepi_source_text")
        if source is None:
            source = widget.text()
            widget.setProperty("jouriepi_source_text", source)
        key = _WIDGET_KEYS.get(source)
        if key:
            widget.setText(text(key, language))
    for combo in root.findChildren(QComboBox):
        for index in range(combo.count()):
            source = combo.itemData(index, 0x0101)
            if source is None:
                source = combo.itemText(index)
                combo.setItemData(index, source, 0x0101)
            key = _WIDGET_KEYS.get(source)
            if key:
                combo.setItemText(index, text(key, language))
    for table in root.findChildren(QTableWidget):
        if table.columnCount() == 2:
            table.setHorizontalHeaderLabels([text("results", language), text("estimate_metric", language)])


def text(key: str, language: str = "en") -> str:
    code = normalize_language(language)
    english = _UI["en"].get(key, key)
    if key in _UI.get(code, {}):
        return _UI[code][key]
    # Keep the first native window independent from the scientific core.
    try:
        from core.i18n import translate as core_translate
        return core_translate(key, code, fallback=english)
    except Exception:
        return english


def languages():
    return LANGUAGES
