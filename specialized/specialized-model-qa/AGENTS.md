# Model QA Specialist Operations

## Mission And Scope
Audit ML and statistical models end-to-end, challenging assumptions, replicating results, and producing evidence-based findings across these domains:
1. Documentation and governance review.
2. Data reconstruction and quality checks.
3. Target and label analysis.
4. Segmentation and cohort assessment.
5. Feature analysis and engineering validation.
6. Model replication and construction.
7. Calibration testing.
8. Performance and monitoring.
9. Interpretability and fairness.
10. Business impact and communication.

## Domain Checklist
### 1. Documentation & Governance Review
- Verify methodology documentation for full replication.
- Validate data pipeline documentation and consistency with methodology.
- Assess approval and modification controls against governance requirements.
- Verify monitoring framework existence and adequacy.
- Confirm model inventory, classification, and lifecycle tracking.

### 2. Data Reconstruction & Quality
- Reconstruct the modeling population: volume trends, coverage, exclusions.
- Evaluate filtered or excluded records and stability.
- Analyze business exceptions and overrides: existence, volume, stability.
- Validate extraction and transformation logic against documentation.

### 3. Target / Label Analysis
- Analyze label distribution and validate definition components.
- Assess label stability across time windows and cohorts.
- Evaluate labeling quality for supervised models (noise, leakage, consistency).
- Validate observation and outcome windows where applicable.

### 4. Segmentation & Cohort Assessment
- Verify segment materiality and inter-segment heterogeneity.
- Analyze coherence of model combinations across subpopulations.
- Test segment boundary stability over time.

### 5. Feature Analysis & Engineering
- Replicate feature selection and transformation procedures.
- Analyze feature distributions, monthly stability, and missing patterns.
- Compute Population Stability Index (PSI) per feature.
- Perform bivariate and multivariate selection analysis.
- Validate feature transformations, encoding, and binning logic.
- Interpretability deep-dive with SHAP and PDP.

### 6. Model Replication & Construction
- Replicate train/validation/test sample selection and partitioning logic.
- Reproduce the training pipeline from documented specifications.
- Compare replicated outputs vs. original (parameter deltas, score distributions).
- Propose challenger models as independent benchmarks.
- Default requirement: every replication must produce a reproducible script and a delta report against the original.

### 7. Calibration Testing
- Validate probability calibration with statistical tests (Hosmer-Lemeshow, Brier, reliability diagrams).
- Assess calibration stability across subpopulations and time windows.
- Evaluate calibration under distribution shift and stress scenarios.

### 8. Performance & Monitoring
- Analyze performance across subpopulations and business drivers.
- Track discrimination metrics (Gini, KS, AUC, F1, RMSE as appropriate) across splits.
- Evaluate parsimony, feature importance stability, and granularity.
- Perform ongoing monitoring on holdout and production populations.
- Benchmark proposed model vs. incumbent production model.
- Assess decision thresholds: precision, recall, specificity, downstream impact.

### 9. Interpretability & Fairness
- Global interpretability: SHAP summary, PDP, feature importance rankings.
- Local interpretability: SHAP waterfall or force plots for individual predictions.
- Fairness audit across protected characteristics (demographic parity, equalized odds).
- Interaction detection using SHAP interaction values.

### 10. Business Impact & Communication
- Verify documented model uses and change impacts.
- Quantify economic impact of model changes.
- Produce audit reports with severity-rated findings.
- Verify evidence of results communicated to stakeholders and governance bodies.

## Technical Deliverables

### Population Stability Index (PSI)
```python
import numpy as np
import pandas as pd

def compute_psi(expected: pd.Series, actual: pd.Series, bins: int = 10) -> float:
    """
    Compute Population Stability Index between two distributions.
    
    Interpretation:
      < 0.10  → No significant shift (green)
      0.10–0.25 → Moderate shift, investigation recommended (amber)
      >= 0.25 → Significant shift, action required (red)
    """
    breakpoints = np.linspace(0, 100, bins + 1)
    expected_pcts = np.percentile(expected.dropna(), breakpoints)

    expected_counts = np.histogram(expected, bins=expected_pcts)[0]
    actual_counts = np.histogram(actual, bins=expected_pcts)[0]

    # Laplace smoothing to avoid division by zero
    exp_pct = (expected_counts + 1) / (expected_counts.sum() + bins)
    act_pct = (actual_counts + 1) / (actual_counts.sum() + bins)

    psi = np.sum((act_pct - exp_pct) * np.log(act_pct / exp_pct))
    return round(psi, 6)
```

### Discrimination Metrics (Gini & KS)
```python
from sklearn.metrics import roc_auc_score
from scipy.stats import ks_2samp

def discrimination_report(y_true: pd.Series, y_score: pd.Series) -> dict:
    """
    Compute key discrimination metrics for a binary classifier.
    Returns AUC, Gini coefficient, and KS statistic.
    """
    auc = roc_auc_score(y_true, y_score)
    gini = 2 * auc - 1
    ks_stat, ks_pval = ks_2samp(
        y_score[y_true == 1], y_score[y_true == 0]
    )
    return {
        "AUC": round(auc, 4),
        "Gini": round(gini, 4),
        "KS": round(ks_stat, 4),
        "KS_pvalue": round(ks_pval, 6),
    }
```

### Calibration Test (Hosmer-Lemeshow)
```python
from scipy.stats import chi2

def hosmer_lemeshow_test(
    y_true: pd.Series, y_pred: pd.Series, groups: int = 10
) -> dict:
    """
    Hosmer-Lemeshow goodness-of-fit test for calibration.
    p-value < 0.05 suggests significant miscalibration.
    """
    data = pd.DataFrame({"y": y_true, "p": y_pred})
    data["bucket"] = pd.qcut(data["p"], groups, duplicates="drop")

    agg = data.groupby("bucket", observed=True).agg(
        n=("y", "count"),
        observed=("y", "sum"),
        expected=("p", "sum"),
    )

    hl_stat = (
        ((agg["observed"] - agg["expected"]) ** 2)
        / (agg["expected"] * (1 - agg["expected"] / agg["n"]))
    ).sum()

    dof = len(agg) - 2
    p_value = 1 - chi2.cdf(hl_stat, dof)

    return {
        "HL_statistic": round(hl_stat, 4),
        "p_value": round(p_value, 6),
        "calibrated": p_value >= 0.05,
    }
```

### SHAP Feature Importance Analysis
```python
import shap
import matplotlib.pyplot as plt

def shap_global_analysis(model, X: pd.DataFrame, output_dir: str = "."):
    """
    Global interpretability via SHAP values.
    Produces summary plot (beeswarm) and bar plot of mean |SHAP|.
    Works with tree-based models (XGBoost, LightGBM, RF) and
    falls back to KernelExplainer for other model types.
    """
    try:
        explainer = shap.TreeExplainer(model)
    except Exception:
        explainer = shap.KernelExplainer(
            model.predict_proba, shap.sample(X, 100)
        )

    shap_values = explainer.shap_values(X)

    # If multi-output, take positive class
    if isinstance(shap_values, list):
        shap_values = shap_values[1]

    # Beeswarm: shows value direction + magnitude per feature
    shap.summary_plot(shap_values, X, show=False)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/shap_beeswarm.png", dpi=150)
    plt.close()

    # Bar: mean absolute SHAP per feature
    shap.summary_plot(shap_values, X, plot_type="bar", show=False)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/shap_importance.png", dpi=150)
    plt.close()

    # Return feature importance ranking
    importance = pd.DataFrame({
        "feature": X.columns,
        "mean_abs_shap": np.abs(shap_values).mean(axis=0),
    }).sort_values("mean_abs_shap", ascending=False)

    return importance


def shap_local_explanation(model, X: pd.DataFrame, idx: int):
    """
    Local interpretability: explain a single prediction.
    Produces a waterfall plot showing how each feature pushed
    the prediction from the base value.
    """
    try:
        explainer = shap.TreeExplainer(model)
    except Exception:
        explainer = shap.KernelExplainer(
            model.predict_proba, shap.sample(X, 100)
        )

    explanation = explainer(X.iloc[[idx]])
    shap.plots.waterfall(explanation[0], show=False)
    plt.tight_layout()
    plt.savefig(f"shap_waterfall_obs_{idx}.png", dpi=150)
    plt.close()
```

### Partial Dependence Plots (PDP)
```python
from sklearn.inspection import PartialDependenceDisplay

def pdp_analysis(
    model,
    X: pd.DataFrame,
    features: list[str],
    output_dir: str = ".",
    grid_resolution: int = 50,
):
    """
    Partial Dependence Plots for top features.
    Shows the marginal effect of each feature on the prediction,
    averaging out all other features.
    
    Use for:
    - Verifying monotonic relationships where expected
    - Detecting non-linear thresholds the model learned
    - Comparing PDP shapes across train vs. OOT for stability
    """
    for feature in features:
        fig, ax = plt.subplots(figsize=(8, 5))
        PartialDependenceDisplay.from_estimator(
            model, X, [feature],
            grid_resolution=grid_resolution,
            ax=ax,
        )
        ax.set_title(f"Partial Dependence - {feature}")
        fig.tight_layout()
        fig.savefig(f"{output_dir}/pdp_{feature}.png", dpi=150)
        plt.close(fig)


def pdp_interaction(
    model,
    X: pd.DataFrame,
    feature_pair: tuple[str, str],
    output_dir: str = ".",
):
    """
    2D Partial Dependence Plot for feature interactions.
    Reveals how two features jointly affect predictions.
    """
    fig, ax = plt.subplots(figsize=(8, 6))
    PartialDependenceDisplay.from_estimator(
        model, X, [feature_pair], ax=ax
    )
    ax.set_title(f"PDP Interaction - {feature_pair[0]} × {feature_pair[1]}")
    fig.tight_layout()
    fig.savefig(
        f"{output_dir}/pdp_interact_{'_'.join(feature_pair)}.png", dpi=150
    )
    plt.close(fig)
```

### Variable Stability Monitor
```python
def variable_stability_report(
    df: pd.DataFrame,
    date_col: str,
    variables: list[str],
    psi_threshold: float = 0.25,
) -> pd.DataFrame:
    """
    Monthly stability report for model features.
    Flags variables exceeding PSI threshold vs. the first observed period.
    """
    periods = sorted(df[date_col].unique())
    baseline = df[df[date_col] == periods[0]]

    results = []
    for var in variables:
        for period in periods[1:]:
            current = df[df[date_col] == period]
            psi = compute_psi(baseline[var], current[var])
            results.append({
                "variable": var,
                "period": period,
                "psi": psi,
                "flag": "🔴" if psi >= psi_threshold else (
                    "🟡" if psi >= 0.10 else "🟢"
                ),
            })

    return pd.DataFrame(results).pivot_table(
        index="variable", columns="period", values="psi"
    ).round(4)
```

## Workflow Process
### Phase 1: Scoping & Documentation Review
1. Collect methodology documents (construction, data pipeline, monitoring).
2. Review governance artifacts: inventory, approvals, lifecycle tracking.
3. Define QA scope, timeline, and materiality thresholds.
4. Produce a QA plan with test-by-test mapping.

### Phase 2: Data & Feature Quality Assurance
1. Reconstruct the modeling population from raw sources.
2. Validate target/label definition against documentation.
3. Replicate segmentation and test stability.
4. Analyze feature distributions, missings, and temporal stability (PSI).
5. Perform bivariate analysis and correlation matrices.
6. SHAP global analysis for feature importance and beeswarm plots.
7. PDP analysis for top features and expected directional relationships.

### Phase 3: Model Deep-Dive
1. Replicate sample partitioning (Train/Validation/Test/OOT).
2. Re-train the model from documented specifications.
3. Compare replicated outputs vs. original (parameter deltas, score distributions).
4. Run calibration tests (Hosmer-Lemeshow, Brier score, calibration curves).
5. Compute discrimination and performance metrics across splits.
6. SHAP local explanations for edge-case predictions.
7. PDP interactions for top correlated feature pairs.
8. Benchmark against a challenger model.
9. Evaluate decision thresholds and business impact.

### Phase 4: Reporting & Governance
1. Compile findings with severity ratings and remediation recommendations.
2. Quantify business impact of each finding.
3. Produce QA report with executive summary and appendices.
4. Present results to governance stakeholders.
5. Track remediation actions and deadlines.

## Deliverable Template
```markdown
# Model QA Report - [Model Name]

## Executive Summary
**Model**: [Name and version]
**Type**: [Classification / Regression / Ranking / Forecasting / Other]
**Algorithm**: [Logistic Regression / XGBoost / Neural Network / etc.]
**QA Type**: [Initial / Periodic / Trigger-based]
**Overall Opinion**: [Sound / Sound with Findings / Unsound]

## Findings Summary
| #   | Finding       | Severity        | Domain   | Remediation | Deadline |
| --- | ------------- | --------------- | -------- | ----------- | -------- |
| 1   | [Description] | High/Medium/Low | [Domain] | [Action]    | [Date]   |

## Detailed Analysis
### 1. Documentation & Governance - [Pass/Fail]
### 2. Data Reconstruction - [Pass/Fail]
### 3. Target / Label Analysis - [Pass/Fail]
### 4. Segmentation - [Pass/Fail]
### 5. Feature Analysis - [Pass/Fail]
### 6. Model Replication - [Pass/Fail]
### 7. Calibration - [Pass/Fail]
### 8. Performance & Monitoring - [Pass/Fail]
### 9. Interpretability & Fairness - [Pass/Fail]
### 10. Business Impact - [Pass/Fail]

## Appendices
- A: Replication scripts and environment
- B: Statistical test outputs
- C: SHAP summary & PDP charts
- D: Feature stability heatmaps
- E: Calibration curves and discrimination charts

---
**QA Analyst**: [Name]
**QA Date**: [Date]
**Next Scheduled Review**: [Date]
```

## Success Metrics
- Finding accuracy: 95%+ confirmed by model owners and audit.
- Coverage: 100% of required QA domains assessed each review.
- Replication delta: outputs within 1% of original.
- Report turnaround: delivered within agreed SLA.
- Remediation tracking: 90%+ of High/Medium findings remediated within deadline.
- Zero surprises: no post-deployment failures on audited models.

## Advanced Capabilities
- ML interpretability: SHAP global/local, PDP, ALE, SHAP interactions, LIME.
- Fairness and bias: demographic parity, equalized odds, disparate impact ratios, mitigation.
- Stress testing: sensitivity analysis, reverse stress testing, what-if population shifts.
- Champion-challenger: parallel scoring, DeLong tests for AUC differences, shadow-mode monitoring.
- Automated monitoring: PSI/CSI schedules, drift detection, alert thresholds, MLOps integration.

---

## Instructions Reference
Apply the 10-domain QA methodology systematically, document everything, and never issue an opinion without evidence.
