"""Pure IC/IR + layered backtest math shared by factor_analysis_tool and alpha_bench_tool."""

import pandas as pd

_MIN_VALID_PER_DATE = 5


def compute_ic_series(factor_df: pd.DataFrame, return_df: pd.DataFrame) -> pd.Series:
    """Compute daily Spearman rank correlation (IC) between factor values and returns.

    Vectorised via ``rank().corrwith()`` (Spearman = Pearson on ranks). A date
    is dropped if fewer than 5 instruments have both a factor and return value
    on that bar — matching the prior per-row guard.

    Args:
        factor_df: Factor values; index=date, columns=codes.
        return_df: Returns; index=date, columns=codes.

    Returns:
        IC series indexed by date.
    """
    common_dates = factor_df.index.intersection(return_df.index)
    common_codes = factor_df.columns.intersection(return_df.columns)
    if len(common_dates) == 0 or len(common_codes) == 0:
        return pd.Series(dtype=float)

    factor_df = factor_df.loc[common_dates, common_codes]
    return_df = return_df.loc[common_dates, common_codes]

    # Only rank cells where both factor and return are present (mirrors the
    # per-date ``shared = f.dropna() ∩ r.dropna()`` from the loop version).
    pair_mask = factor_df.notna() & return_df.notna()
    n_valid = pair_mask.sum(axis=1)

    factor_aligned = factor_df.where(pair_mask)
    return_aligned = return_df.where(pair_mask)

    # Spearman = Pearson on per-row ranks.
    factor_ranks = factor_aligned.rank(axis=1, method="average")
    return_ranks = return_aligned.rank(axis=1, method="average")
    ic = factor_ranks.corrwith(return_ranks, axis=1, method="pearson")

    ic = ic[n_valid >= _MIN_VALID_PER_DATE]
    ic = ic.dropna()
    if ic.empty:
        return pd.Series(dtype=float)
    return ic.astype(float)


def compute_group_equity(
    factor_df: pd.DataFrame, return_df: pd.DataFrame, n_groups: int
) -> pd.DataFrame:
    """Layered backtest: rank by factor value daily, hold equal-weight, compute cumulative NAV.

    Args:
        factor_df: Factor values; index=date, columns=codes.
        return_df: Returns; index=date, columns=codes.
        n_groups: Number of quantile groups.

    Returns:
        DataFrame with index=date and columns Group_1 ... Group_N holding cumulative NAV.
    """
    common_dates = sorted(factor_df.index.intersection(return_df.index))
    common_codes = factor_df.columns.intersection(return_df.columns)
    if len(common_dates) == 0 or len(common_codes) == 0:
        return pd.DataFrame()

    factor_df = factor_df.loc[common_dates, common_codes]
    return_df = return_df.loc[common_dates, common_codes]

    group_returns: dict[str, list[float]] = {f"Group_{i+1}": [] for i in range(n_groups)}
    valid_dates = []

    for date in common_dates:
        f = factor_df.loc[date].dropna()
        r = return_df.loc[date].dropna()
        shared = f.index.intersection(r.index)
        if len(shared) < n_groups:
            continue
        valid_dates.append(date)
        ranked = f[shared].rank(method="first")
        bins = pd.qcut(ranked, n_groups, labels=False, duplicates="drop")
        if bins.nunique() < n_groups:
            # Not enough distinct values; fall back to equal-width cut
            bins = pd.cut(ranked, n_groups, labels=False)
        for g in range(n_groups):
            members = bins[bins == g].index
            if len(members) > 0:
                group_returns[f"Group_{g+1}"].append(r[members].mean())
            else:
                group_returns[f"Group_{g+1}"].append(0.0)

    if not valid_dates:
        return pd.DataFrame()

    ret_df = pd.DataFrame(group_returns, index=valid_dates)
    equity_df = (1 + ret_df).cumprod()
    return equity_df
