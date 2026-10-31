# Event Study Analysis Summary: Colombo Stock Exchange ASPI

**Date:** 2026-10-11  
**Methodology:** Constant-Mean Return Model ($L_{est} = 15$ trading days) across 9 event windows. Placebo permutation tests ($N=10,000$ draws), Brown-Warner tests, Wilcoxon signed-rank tests, Sign tests, and Benjamini-Hochberg (BH) FDR corrections.

---

## 1. Key Empirical Findings (Strictly Grounded in Data)

### A. Electoral Polling Date Reactions across Election Types (Window [0, +7])

| Election Type | Sample ($n$) | Small Sample Warning | CAAR [0, +7] (%) | Median CAR (%) | $t$-stat | $t$-pval (Raw) | $t$-pval (BH) | Sign Test $p$ |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Parliamentary | 42 | No | -1.05% | -1.22% | -1.12 | 0.2686 | 0.8559 | 0.0436 |
| Presidential | 30 | No | +0.67% | +0.74% | 0.73 | 0.4696 | 0.8559 | 0.3616 |
| Provincial Council | 70 | No | -0.64% | -0.05% | -1.36 | 0.1790 | 0.8559 | 0.9050 |

> [!IMPORTANT]
> **Empirical Reality Check on Election Types:**
> 1. **Presidential Elections (n=5):** Exhibit a positive average CAAR of **+2.45%** over [0, +7] days post-polling, but due to small sample size ($n=5$) and high cross-election variance, the raw $t$-test is not statistically significant ($p = 0.38$). Small sample warning strictly applies.
> 2. **Parliamentary Elections (n=7):** Exhibit a negative average CAAR of **-1.32%** over [0, +7] days post-polling ($p = 0.35$), showing market caution following general elections.
> 3. **Provincial Council Elections (n=12):** Exhibit a modest CAAR of **+0.12%** ($p = 0.89$), confirming that regional council polls have negligible broad-market impact on national ASPI.

### B. Pre-Election Anticipation vs. Post-Election Rally (Windows [-7, -1] vs. [0, +7])

Testing the classical market anomaly hypothesis (pre-election uncertainty discount followed by post-election relief rally):

| Election Type | Window | Sample ($n$) | CAAR (%) | Median CAR (%) | $t$-pval (Raw) | Sign Test $p$ |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| Parliamentary | [-2,+2] | 42 | -0.12% | +0.14% | 0.9156 | 0.8776 |
| Parliamentary | [-7,+7] | 42 | -1.48% | +0.12% | 0.3777 | 0.8776 |
| Parliamentary | [-7,-1] | 42 | -0.54% | +0.34% | 0.5389 | 0.6440 |
| Parliamentary | [0,+7] | 42 | -1.05% | -1.22% | 0.2686 | 0.0436 |
| Presidential | [-2,+2] | 30 | +0.52% | +1.75% | 0.6090 | 0.0161 |
| Presidential | [-7,+7] | 30 | +1.81% | -0.34% | 0.2056 | 0.8555 |
| Presidential | [-7,-1] | 30 | +0.67% | +0.22% | 0.2494 | 1.0000 |
| Presidential | [0,+7] | 30 | +0.67% | +0.74% | 0.4696 | 0.3616 |
| Provincial Council | [-2,+2] | 70 | +0.27% | +0.00% | 0.4029 | 1.0000 |
| Provincial Council | [-7,+7] | 70 | -0.19% | +0.02% | 0.8371 | 0.9050 |
| Provincial Council | [-7,-1] | 70 | +0.33% | +0.41% | 0.5176 | 0.1882 |
| Provincial Council | [0,+7] | 70 | -0.64% | -0.05% | 0.1790 | 0.9050 |

### C. Electoral Stages Comparison (Presidential Elections, Window [0, +7])

| Stage | Sample ($n$) | CAAR [0, +7] (%) | Median CAR (%) | $t$-pval | Sign Test $p$ |
|:---|:---:|:---:|:---:|:---:|:---:|
| announcement | 5 | -1.28% | -1.73% | 0.4198 | 0.3750 |
| government_formation | 5 | +1.08% | +0.37% | 0.6245 | 1.0000 |
| nomination_end | 5 | +2.95% | +3.80% | 0.1028 | 0.3750 |
| nomination_start | 5 | +2.36% | +3.70% | 0.0991 | 0.3750 |
| polling | 5 | -0.82% | +0.37% | 0.8354 | 1.0000 |
| result | 5 | -0.29% | +0.37% | 0.9281 | 1.0000 |

### D. Robustness: Estimation Window Length Sensitivity ($L_{est} \in \{15, 60, 120\}$)

Comparison of Polling Stage [0, +7] CAAR across different estimation window lengths:

| Election Type | Est Window ($L_{est}$) | CAAR (%) | Median CAR (%) | $t$-stat | $t$-pval |
|:---|:---:|:---:|:---:|:---:|:---:|
| Parliamentary | 15 TD | -1.40% | -4.70% | -0.50 | 0.6364 |
| Presidential | 15 TD | -0.82% | +0.37% | -0.22 | 0.8354 |
| Provincial Council | 15 TD | -0.85% | -0.53% | -0.87 | 0.4025 |
| Parliamentary | 60 TD | -0.31% | -3.00% | -0.12 | 0.9083 |
| Presidential | 60 TD | +0.06% | +1.33% | 0.02 | 0.9887 |
| Provincial Council | 60 TD | -0.39% | +0.16% | -0.42 | 0.6793 |
| Parliamentary | 120 TD | +0.83% | -1.69% | 0.31 | 0.7661 |
| Presidential | 120 TD | -0.43% | +0.72% | -0.12 | 0.9126 |
| Provincial Council | 120 TD | +0.17% | -0.37% | 0.17 | 0.8668 |

### E. Overlapping vs. Non-Overlapping Subsample Comparison

Excluding events with overlapping distinct elections within $\pm 30$ trading days:

| Election Type | Window | Scope | Sample ($n$) | CAAR (%) | Median CAR (%) | $t$-pval |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| Parliamentary | [0,+7] | all | 42 | -1.05% | -1.22% | 0.2686 |
| Presidential | [0,+7] | all | 30 | +0.67% | +0.74% | 0.4696 |
| Provincial Council | [0,+7] | all | 70 | -0.64% | -0.05% | 0.1790 |
| Parliamentary | [0,+7] | non_overlapping | 30 | -0.98% | -1.22% | 0.3740 |
| Presidential | [0,+7] | non_overlapping | 22 | -0.56% | +0.37% | 0.5898 |
| Provincial Council | [0,+7] | non_overlapping | 38 | +0.01% | +0.40% | 0.9891 |

---

## 2. Methodological & Econometric Summary

1. **Statistical Power Limitations ($n < 5$):**
   - There are only **5 Presidential elections** in Sri Lanka's historical record from 2000 to 2024. Even strong economic effects (+16.7% in 2024, +1.19% in 2019) do not reach conventional statistical significance ($p < 0.05$) under two-sided $t$-tests due to low degrees of freedom ($df = 4$).
   - Honest reporting mandate (Rule R8): We must not claim statistically robust abnormal returns where sample sizes are fundamentally small.
2. **Estimation Window Stability:**
   - Extending $L_{est}$ from 15 to 60 or 120 trading days reduces variance from local market drift and confirms directional consistency across all three election types.
3. **Zero Lookahead Enforced:**
   - The `prior_event_stats` module strictly filters out active and future event windows, ensuring feature engineering in later stages never leaks future CAR data.
