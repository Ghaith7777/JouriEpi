# EpiTable 6.04 reverse-engineering notes

## Evidence inventory and method

The supplied Epi Info 6.04 distribution consists of three DOS-era installer parts under `C:\Users\Ghaith\Downloads\EPI604`. Read-only archive inspection and extraction identified the nested `FILES01.EXE` through `FILES16.EXE` packages. Analysis copies in the ignored `legacy_payload/` directory include:

| File | Bytes | Evidence role |
|---|---:|---|
| `EPITABLE.EXE` | 473,305 | Legacy executable; not executed on the Windows host |
| `EPITENG.HLP` | 118,257 | English help; method names, definitions, examples and citations |
| `EPITFRA.HLP` | 123,062 | French help; corroborates tests, thresholds and sample-size methods |
| `EPITABLE.CFG` | 402 | Configuration resource |
| `EPI6.MNU` | 21,363 | Launcher menu source; separates EpiTable from CSAMPLE and STATCALC |
| `ANALYSIS.HLP` | 77,408 | Related analysis help |
| `STATCALC.HLP` | 20,800 | Related sample-size/statistics help |

The HLP files use a Borland-style help format with a binary header, so a plain `strings` dump is incomplete. The findings below come from printable-string extraction decoded as code page 437, checked against both language files where possible. This is direct textual evidence from the shipped help, but not a complete decoding of the help topic structure or proof that every documented option is used by every EPITABLE.EXE path. Section labels below are the visible help topic titles, not page numbers; the legacy file does not expose stable page numbers in this extraction.

The executable was also inspected as data without loading or executing it: it is 473,305 bytes, begins with the DOS `MZ` signature, and has SHA-256 shown below. A read-only printable-ASCII scan found 221 runs of at least five printable bytes; it found references to `EPITENG` but no plain-text occurrences of `FISHER`, `YATES`, `RELATIVE RISK`, `CHI SQUARE`, `CONFIDENCE`, or `XXEXACT`. This negative string result is not evidence that those algorithms are absent: compiled code, overlays, packed resources, and non-ASCII encodings may not expose source-level labels. No disassembler was used to infer undocumented algorithms from machine code.

The launcher menu source `EPI6.MNU` has an `EPI&TABLE calculator` item that invokes `EPITABLE` and separate items for `CSAMPLE` (survey analysis) and `STATCALC` (calculator). This is useful product-boundary evidence: features documented in related applications should not automatically be attributed to EPITABLE. The local `EPITABLE.CFG` contains a default Z value of `1.9600`, a `95%` confidence-interval range, alpha risk `0.050000`, and the default resource `EPITENG.RES`. These are configuration defaults, not proof of the internal formula used by each interval. `CONFIG.EPI` contains printer/page settings and is not evidence for statistical behavior.

SHA-256 hashes of the inspected extracted files (to bind these notes to specific bytes):

| File | SHA-256 |
|---|---|
| `EPITABLE.EXE` | `57561015F97AA80103D895562364C7F4F43672993AB2BF84B10C00DBC5EBFF42` |
| `EPITENG.HLP` | `13159E04EB369B86423862D3F241824C6EE961FF5F012CD6DC2C51FD3FFA85D5` |
| `EPITFRA.HLP` | `064CB22DC20395821584D815072F67D984653108D1DD31D98C0F78C49225D21B` |
| `EPITABLE.CFG` | `159832A014194AE3232610D6FB6AA4512F42686333EC7B9B1754EFB6C1F441BE` |
| `EPI6.MNU` | `81585DAA7BB44BAF3659F6A6DCE37D4B8C9A933DFBA755C82C7CDD310B4A6F87` |
| `ANALYSIS.HLP` | `90F03781841433E423C505AC8D38ECCADB29B763841432A92E2E3E977B2EFB39` |
| `STATCALC.HLP` | `BB4C7620F8AB987FF7BDD8DCE984C321E77B0CFA0C5D9548B3535E4D600C0501` |

## Source-supported historical definitions

### 2×2 table convention

The engine uses the epidemiological orientation specified for this modernization: `a` = exposed cases, `b` = exposed non-cases, `c` = unexposed cases, and `d` = unexposed non-cases. This is an explicit project convention. The extracted English help's topic **“Measure of association and 95% confidence interval”** describes risk in exposed and unexposed groups and gives the following definitions in text:

- Exposed risk: \(R_e = a/(a+b)\).
- Relative risk: \(RR = R_e/R_u\), where \(R_u=c/(c+d)\).
- Risk difference: \(RD = R_e-R_u\).
- Attributable fraction in exposed: \(AF_e = RD/R_e\), expressed as a percentage. The help says this is the proportion of disease among exposed individuals attributable to exposure and cautions that attributable fractions are meaningless without a causal association.
- The extracted help describes a population risk difference using exposed and overall-population risk, but the string-only extraction does not preserve enough surrounding topic structure to settle its sign convention with confidence. For clarity, the modern PAF calculation below explicitly uses population risk minus the counterfactual risk at the unexposed rate.
- Population attributable fraction: population risk difference divided by population disease risk.
- For cohort-style crude 2×2 data, this implementation calculates \(PAF=(R_{pop}-R_u)/R_{pop}\), where \(R_{pop}=(a+c)/N\) and \(R_u=c/(c+d)\). When RR is finite, this equals \(P_e(RR-1)/(1+P_e(RR-1))\), where \(P_e=(a+b)/N\). The often-quoted expression \(P_c(RR-1)/RR\) instead uses the fraction of cases exposed \(P_c\), not population exposure prevalence. The direct risk definition also handles RR=0 and the limit where unexposed risk is zero, unless population risk itself is zero. The extracted help does not show these exact algebraic forms.
- For case-control data, the help defines the odds ratio as the ratio of exposure odds among cases to exposure odds among controls, algebraically \(OR=ad/(bc)\). It notes that incidence risks and the ordinary risk difference generally cannot be calculated from case-control sampling alone; an attributable fraction may be estimated using OR as a relative-risk approximation under suitable assumptions.

These definitions are help-file evidence. The exact handling of zero denominators and display conventions is not specified by the extracted text and is handled explicitly by the modern code below.

### Hypothesis tests and the expected-count threshold

The English topic index lists **“Fisher's exact test”** and **“Chi square for l x c data table.”** Its examples show one-tailed and two-tailed Fisher p-values, Pearson chi-square, and Yates-corrected chi-square. The French help contains the explicit rule: *“Si une table 2 x 2 est entrée et qu'une valeur attendue est <5, le Chi² corrigé de Yates est utilisé”* (if a 2×2 table is entered and an expected value is below 5, Yates-corrected chi-square is used). This establishes a documented threshold for that help-described workflow. It does not establish whether every menu or release path automatically switches tests, so the modern app reports the threshold audit and presents both tests separately.

Modern formulas used here:

- Pearson statistic: \(X^2=\sum_{i,j}(O_{ij}-E_{ij})^2/E_{ij}\), with one degree of freedom for a nondegenerate 2×2 table.
- Yates correction: replace each absolute difference by \(\max(|O_{ij}-E_{ij}|-0.5,0)\) before squaring and dividing by expected count.
- Fisher exact test conditions on the margins and sums hypergeometric probabilities. The modern API returns lower-tail (`x <= observed a`), upper-tail (`x >= observed a`), and two-sided probability-ordering values (tables with probability no greater than the observed table). The help confirms one- and two-tailed Fisher tests, but the extracted strings do not settle the precise two-sided convention. Therefore exact p-value parity is unverified. Probability-ordering two-sided p-values are not generally bounded by either one-sided tail in a simple direction; the convention is explicitly named.

The project flags any expected count below 5 as an audit message. This is a transparent diagnostic and does not silently alter the selected statistic.

### Confidence intervals documented by the legacy help

The English and French help explicitly name these methods:

- **Proportions:** Fleiss quadratic approximation, exact binomial, and exact mid-p. The help says the Fleiss approximation remains valid when a proportion is near zero or one, and describes its cluster-sampling adaptation by replacing `n` with effective sample size `Ne = n / DE`, where `DE` is the design effect. It cites Joseph L. Fleiss, *Statistical Methods for Rates and Proportions*, 2nd edition (1981), pp. 14–15 for the Fleiss interval. It explains that exact mid-p uses half the probability of the observed count and is less conservative than the exact binomial interval.
- **Case-control odds ratio:** the help states that exact and mid-p confidence intervals are calculated and attributes the conditional maximum-likelihood estimate and Fisher/mid-p limits to David Martin's Pascal library `XXEXACT.PAS`.
- **Other association measures:** examples display 95% confidence intervals for relative risk, risk difference, attributable fraction and odds ratio. The extracted material references Fleiss (1981), pp. 115–116, pp. 143–146 and pp. 150–156 in related interval/test topics. The exact equation text for all these association intervals was not fully recoverable from the simple string extraction.

Current implementation and limits:

- Woolf log-odds-ratio interval: \(\exp[\log(OR)\pm z_{1-\alpha/2}\sqrt{1/a+1/b+1/c+1/d}]\), only when all cells are positive.
- Katz log-risk-ratio interval: \(\exp[\log(RR)\pm z_{1-\alpha/2}\sqrt{1/a-1/(a+b)+1/c-1/(c+d)}]\), when both case counts are positive.
- Wald risk-difference interval: \(RD\pm z_{1-\alpha/2}\sqrt{R_e(1-R_e)/(a+b)+R_u(1-R_u)/(c+d)}\).
- `core/proportions.py` provides a Wilson score interval and a two-sided equal-tailed Clopper–Pearson exact interval for a single binomial proportion. The exact interval inverts the regularized incomplete beta function using a standard continued-fraction evaluation and bisection; it is not an exact confidence interval for RR, RD, OR, or attributable fractions.
- These are standard modern large-sample approximations. They are not asserted to reproduce EpiTable's exact, mid-p, Cornfield, or other interval procedures. Exact odds-ratio limits are not implemented.

### Stratification and sample size

The English and French help mention stratum-specific relative risks and Mantel–Haenszel summary relative risk/chi-square. The French help's sample-size topics describe cohort and case-control designs, cite Fleiss (1981), pp. 44–45, and show examples specifying 95% confidence and 80% power. These topic references establish that such methods are documented in the distribution; they do not provide enough extracted formula detail to claim that the present sample-size helper or unimplemented stratified estimates match EpiTable.

The current `two_proportion_sample_size` is a modern normal-approximation calculation for two independent proportions with a user-specified allocation ratio `r = n_exposed/n_control`. It requires target power of at least 0.5, and rejects alpha values so small that the requested two-sided tail probability cannot be represented in double precision. Its control-group size uses

\[n_0 = \frac{\left[z_{1-\alpha/2}\sqrt{\bar p(1-\bar p)(1+1/r)} + z_{1-\beta}\sqrt{p_0(1-p_0)+p_1(1-p_1)/r}\right]^2}{(p_1-p_0)^2},\quad \bar p=\frac{p_0+r p_1}{1+r}.\]

The pooled-null variance factor is `(1 + 1/r)`; it must not be multiplied by an additional 2 because equal allocation already gives the factor 2. A review found and corrected that previous extra factor, which had materially inflated sample sizes. `cohort_sample_size` and `cross_sectional_sample_size` are explicitly named wrappers around this same method; they do not add survival-time, clustered, complex-survey, or loss-to-follow-up adjustments. `case_control_sample_size` derives exposure prevalence among cases from a target odds ratio and the exposure prevalence among controls, then uses the same two-proportion approximation. `two_proportion_power` estimates achieved power for specified group sizes using pooled null variance for the rejection threshold and unpooled alternative variance. These methods do not implement the full set of legacy cohort, cross-sectional and case-control menus. No Mantel–Haenszel stratified engine is currently implemented.

## Modern implementation behavior and edge cases

- Counts must be nonnegative integers (booleans are rejected); each exposure row must have a positive total.
- Undefined ratios return `None` instead of infinity or an arbitrary continuity correction. Odds ratio is undefined when its denominator `b*c` is zero; the uncorrected point estimate is zero when `a*d=0` and `b*c>0`.
- No zero-cell correction is applied automatically. An opt-in Haldane–Anscombe sensitivity estimate is available for the odds ratio only; when enabled and any cell is zero, 0.5 is added to all four cells for that separate estimate and its Woolf-form interval. The primary OR, RR, RD and attributable fractions remain uncorrected. This is a modern option and not evidence of legacy behavior.
- Fisher probabilities are evaluated in log space using `lgamma` to reduce intermediate overflow for large counts; the hypergeometric support is finite and determined by the fixed margins.
- Diagnostic metrics use TP, FP, FN and TN and return `None` when a metric's denominator is zero. The API includes sensitivity, specificity, predictive values, false-positive/false-negative rates, accuracy, balanced accuracy, F1, and positive/negative likelihood ratios. Likelihood ratios can be undefined when their denominators are zero.
- Line-list ingestion requires unique raw header names, two distinct selected columns with exactly two nonmissing categories each, explicit values for “exposed” and “case,” and no missing exposure/outcome rows. The CSV/Excel loader inspects the header before pandas can silently mangle duplicate names. Reversing either selected reference value can reverse interpretation; the UI names both selections explicitly. Result order is always `(a,b,c,d)` as defined above.
- `population_attributable_fraction` uses the direct risk definition `(population risk - unexposed risk) / population risk`, avoiding a division by RR. It is not a causal claim; interpretation depends on causal assumptions and suitable study design.

## Legacy execution status and benchmark provenance

No DOSBox, DOSBox-X, vDos, 86Box or QEMU executable was found on PATH, and no corresponding installation directory or app package was found in the checked standard Windows program locations. `wsl.exe` exists, but `wsl --list --quiet` returned no installed distribution; no emulator is available through WSL either. The three original installer parts are present at `C:\Users\Ghaith\Downloads\EPI604` (`epi604_1.exe`, `epi604_2.exe`, `epi604_3.exe`), but the project rules prohibit executing the legacy binary directly on the Windows host. An isolated DOS environment was therefore not available in this session and no legacy matrix outputs were captured.

`tests/golden_benchmarks.json` remains marked `theoretical_reference_only_not_legacy_output`, has a null `legacy_capture`, and includes per-case and per-value arithmetic provenance. `tests/golden_benchmarks.schema.json` requires the complete five-measure key set and matching per-value provenance for each case; tests verify required matrices and compare values against the implementation without adding a runtime schema dependency. Its standard, sparse and zero-cell expected values are independently calculated formula references tested against the modern implementation, not EpiTable output. The full JSON Schema was separately validated against the fixture during final verification. Do not change this status or label these data as legacy goldens until output provenance records the emulator/version, executable identity/hash, exact input matrix, and captured result.

### How to obtain genuine legacy captures

No DOSBox, DOSBox-X, vDos, 86Box or QEMU executable was found on PATH or in the checked standard Windows program directories. No emulator was installed as part of this task, and no DOS executable was launched on the Windows host. The next legitimate route is for a maintainer to install a trusted DOS emulator, pin and record its version, run it in a disposable isolated VM or sandbox with networking disabled and a read-only copy of the extracted distribution plus a separate writable output directory, and manually enter the three required matrices `(25,15,10,30)`, `(3,1,2,4)`, and `(0,12,8,15)`. Capture the complete displayed reports/screenshots, locale and menu selections, and executable SHA-256; transcribe values into a separate legacy-capture fixture with provenance and independently review the transcription. The zero-cell case must be observed rather than presumed to use a continuity correction. If the program will not start or cannot represent a case, record the exact error and leave that case uncaptured. Do not enable network access or run the DOS executable directly on the host to bypass the blocker.

## References and provenance

10. VanderWeele TJ, Ding P. Sensitivity Analysis in Observational Research: Introducing the E-Value. *Annals of Internal Medicine*. 2017;167(4):268-274. https://doi.org/10.7326/M16-2607. Supports the modern risk-ratio E-value formula; the causal-sensitivity helper is a new feature and is not attributed to EpiTable 6.04.

1. Epi Info 6.04 distribution supplied by the user: `EPITENG.HLP`, `EPITFRA.HLP`, `EPITABLE.EXE`, and associated files. Direct local source files; extracted copies are ignored by version control. Relevant visible help topics are named above.
2. Fleiss JL. *Statistical Methods for Rates and Proportions*. 2nd ed. John Wiley & Sons; 1981. The supplied help explicitly cites pp. 14–15 for the Fleiss quadratic proportion interval, pp. 24–26 for Fisher exact test material, pp. 44–45 for sample-size methods, and pp. 143–146 / pp. 150–156 for association and interval topics.
3. David Martin, `XXEXACT.PAS`, cited by the supplied help as the library used for conditional maximum-likelihood odds-ratio estimation and exact/mid-p confidence limits. The original Pascal source has not been located separately in the extracted materials.
4. Clopper CJ, Pearson ES. The use of confidence or fiducial limits illustrated in the case of the binomial. *Biometrika*. 1934;26(4):404–413. https://doi.org/10.1093/biomet/26.4.404. This is the classical equal-tailed exact binomial interval, not an exact interval for a 2×2 odds ratio. [Publisher record](https://doi.org/10.1093/biomet/26.4.404).
5. Woolf B. On estimating the relation between blood group and disease. *Annals of Human Genetics*. 1955;19(4):251–253. https://doi.org/10.1111/j.1469-1809.1955.tb01348.x. The modern log-OR interval implemented here is the Woolf large-sample method. [PubMed record](https://pubmed.ncbi.nlm.nih.gov/14388528/).
6. Katz D, Baptista J, Azen SP, Pike MC. Obtaining confidence intervals for the risk ratio in cohort studies. *Biometrics*. 1978;34(3):469–474. https://doi.org/10.2307/2530610. The implemented Katz interval is an asymptotic log-risk-ratio interval. [Journal record](https://doi.org/10.2307/2530610).
7. Fisher RA. On the interpretation of χ² from contingency tables, and the calculation of P. *Journal of the Royal Statistical Society*. 1922;85(1):87–94. https://doi.org/10.1111/j.2397-2335.1922.tb00768.x. [Publisher record](https://doi.org/10.1111/j.2397-2335.1922.tb00768.x).
8. Yates F. Contingency tables involving small numbers and the χ² test. *Supplement to the Journal of the Royal Statistical Society*. 1934;1(2):217–235. https://doi.org/10.2307/2983604. [Publisher record](https://doi.org/10.2307/2983604).
9. Haldane JBS. The estimation and significance of the logarithm of a ratio of frequencies. *Annals of Human Genetics*. 1956;20(4):309–311. https://doi.org/10.1111/j.1469-1809.1955.tb01285.x. This historical reference supports log-ratio estimation; the app's explicit 0.5 correction is a separately named modern sensitivity option, not a claimed reproduction of any legacy algorithm. [PubMed record](https://pubmed.ncbi.nlm.nih.gov/13314400/).

No external source was used to fill gaps in the legacy source. Where the extracted help does not provide the complete algorithm, the uncertainty is stated rather than inferred as historical behavior.
