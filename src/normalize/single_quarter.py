"""Single-quarter financial derivation.

Converts cumulative financial statement values to single-quarter values.

Rules:
- Q1 (report_period = YYYY-03-31): single_quarter = cumulative (no change)
- Q2 (report_period = YYYY-06-30): single_quarter = cumulative - prev_Q1_cumulative
- Q3 (report_period = YYYY-09-30): single_quarter = cumulative - prev_Q2_cumulative
- Q4 (report_period = YYYY-12-31): single_quarter = cumulative - prev_Q3_cumulative

If previous cumulative is missing, single_quarter = NULL (do not fabricate).
"""

from typing import Any
import pandas as pd


def derive_single_quarter(df: pd.DataFrame) -> pd.DataFrame:
    """Derive single-quarter values from cumulative financial data.

    Expected input columns: symbol, report_period, statement_type, item_code, value, cumulative_or_single_quarter
    Returns a new DataFrame with both cumulative and single_quarter rows.
    """
    if df.empty:
        return df.copy()

    # Only process cumulative rows
    cumulative_df = df[df["cumulative_or_single_quarter"] == "cumulative"].copy()
    if cumulative_df.empty:
        return df.copy()

    # Sort by symbol, item, report_period
    cumulative_df = cumulative_df.sort_values(
        ["symbol", "statement_type", "item_code", "report_period"]
    )

    # Group by symbol + statement_type + item_code, shift to get previous cumulative
    group_cols = ["symbol", "statement_type", "item_code"]
    cumulative_df["prev_cumulative"] = cumulative_df.groupby(group_cols)["value"].shift(1)

    # Determine quarter from report_period
    cumulative_df["quarter"] = cumulative_df["report_period"].str.slice(5, 7).astype(int)

    # Q1: single_quarter = cumulative
    # Q2-Q4: single_quarter = cumulative - prev_cumulative
    cumulative_df["sq_value"] = cumulative_df["value"]
    mask = cumulative_df["quarter"] > 3
    cumulative_df.loc[mask, "sq_value"] = (
        cumulative_df.loc[mask, "value"] - cumulative_df.loc[mask, "prev_cumulative"]
    )

    # If prev_cumulative is NaN for Q2-Q4, sq_value should be NaN (no fabrication)
    mask_no_prev = mask & cumulative_df["prev_cumulative"].isna()
    cumulative_df.loc[mask_no_prev, "sq_value"] = None

    # Build single-quarter rows
    sq_rows = cumulative_df.copy()
    sq_rows["value"] = sq_rows["sq_value"]
    sq_rows["cumulative_or_single_quarter"] = "single_quarter"
    sq_rows = sq_rows.drop(columns=["prev_cumulative", "quarter", "sq_value"])

    # Build cumulative rows (unchanged)
    cum_rows = cumulative_df.drop(columns=["prev_cumulative", "quarter", "sq_value"])

    # Combine
    result = pd.concat([cum_rows, sq_rows], ignore_index=True)

    # Also include any original single_quarter rows from input
    original_sq = df[df["cumulative_or_single_quarter"] == "single_quarter"]
    if not original_sq.empty:
        result = pd.concat([result, original_sq], ignore_index=True)

    return result
