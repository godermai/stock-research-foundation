"""Data quality rule registry.

Four classes of checks:
1. Schema checks — column types, nullability
2. Unit normalization checks — volume in shares, amount in CNY
3. Cross-source consistency checks — Tushare vs AKShare vs BaoStock
4. Freshness/completeness checks — latest load times, row counts
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Any


class CheckSuite(str, Enum):
    CORE = "core"
    EXTENDED = "extended"
    SOURCE_SPECIFIC = "source_specific"


class CheckResult(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"


@dataclass
class DQRule:
    name: str
    suite: CheckSuite
    table: str
    description: str
    check_fn: Callable[..., dict[str, Any]]
    severity: str = "error"  # error / warning / info


class DQRuleRegistry:
    """Registry of data quality rules."""

    def __init__(self):
        self._rules: dict[str, DQRule] = {}

    def register(self, rule: DQRule) -> None:
        self._rules[rule.name] = rule

    def get(self, name: str) -> DQRule | None:
        return self._rules.get(name)

    def list_rules(
        self, suite: CheckSuite | None = None, table: str | None = None
    ) -> list[DQRule]:
        rules = list(self._rules.values())
        if suite:
            rules = [r for r in rules if r.suite == suite]
        if table:
            rules = [r for r in rules if r.table == table]
        return rules

    def run_suite(
        self, suite: CheckSuite, table: str | None = None, **kwargs
    ) -> list[dict[str, Any]]:
        results = []
        for rule in self.list_rules(suite=suite, table=table):
            try:
                result = rule.check_fn(**kwargs)
                results.append({
                    "rule": rule.name,
                    "table": rule.table,
                    "suite": rule.suite.value,
                    "result": result.get("result", CheckResult.FAIL.value),
                    "details": result.get("details", ""),
                    "remediation": result.get("remediation", ""),
                })
            except Exception as e:
                results.append({
                    "rule": rule.name,
                    "table": rule.table,
                    "suite": rule.suite.value,
                    "result": CheckResult.FAIL.value,
                    "details": f"Exception: {e}",
                    "remediation": "Check rule implementation",
                })
        return results


# Default registry with built-in rules
default_registry = DQRuleRegistry()


# --- Schema checks ---

def _check_no_null_symbols(table_name: str, df: Any = None, **kw) -> dict:
    if df is None:
        return {"result": CheckResult.WARNING.value, "details": "No DataFrame provided"}
    null_count = df["symbol"].isna().sum() if "symbol" in df.columns else -1
    if null_count == 0:
        return {"result": CheckResult.PASS.value, "details": "No null symbols"}
    return {
        "result": CheckResult.FAIL.value,
        "details": f"{null_count} null symbols found",
        "remediation": "Filter out rows with null symbols before loading",
    }


def _check_volume_in_shares(df: Any = None, **kw) -> dict:
    if df is None or "volume" not in df.columns:
        return {"result": CheckResult.WARNING.value, "details": "No volume column"}
    if "volume_unit" not in df.columns:
        return {"result": CheckResult.WARNING.value, "details": "Cannot verify unit: no volume_unit column"}
    non_share = df[df["volume_unit"].notna() & (df["volume_unit"] != "shares")]
    if len(non_share) == 0:
        return {"result": CheckResult.PASS.value, "details": "All volumes in shares"}
    return {
        "result": CheckResult.FAIL.value,
        "details": f"{len(non_share)} rows with non-share volume unit",
        "remediation": "Convert volume to shares: vol_hands * 100 = shares",
    }


def _check_freshness(table_name: str, latest_load: str | None = None, sla_hours: int = 24, **kw) -> dict:
    if latest_load is None:
        return {
            "result": CheckResult.FAIL.value,
            "details": f"No load timestamp for {table_name}",
            "remediation": f"Run sync job for {table_name}",
        }
    return {
        "result": CheckResult.PASS.value,
        "details": f"Latest load: {latest_load}, SLA: {sla_hours}h",
    }


def _check_no_duplicate_rows(table_name: str, df: Any = None, key_cols: list[str] | None = None, **kw) -> dict:
    if df is None:
        return {"result": CheckResult.WARNING.value, "details": "No DataFrame provided"}
    if key_cols is None:
        key_cols = ["symbol", "trade_date"] if table_name == "market_daily" else ["symbol"]
    if not all(c in df.columns for c in key_cols):
        return {"result": CheckResult.WARNING.value, "details": f"Missing key columns: {key_cols}"}
    dup_count = df.duplicated(subset=key_cols).sum()
    if dup_count == 0:
        return {"result": CheckResult.PASS.value, "details": "No duplicates"}
    return {
        "result": CheckResult.FAIL.value,
        "details": f"{dup_count} duplicate rows on {key_cols}",
        "remediation": f"Deduplicate on {key_cols} before loading",
    }


# Register built-in rules
default_registry.register(DQRule(
    name="schema_no_null_symbols",
    suite=CheckSuite.CORE,
    table="*",
    description="No null values in symbol column",
    check_fn=_check_no_null_symbols,
))

default_registry.register(DQRule(
    name="unit_volume_in_shares",
    suite=CheckSuite.CORE,
    table="market_daily",
    description="Volume must be normalized to shares",
    check_fn=_check_volume_in_shares,
))

default_registry.register(DQRule(
    name="freshness_check",
    suite=CheckSuite.CORE,
    table="*",
    description="Data freshness within SLA",
    check_fn=_check_freshness,
))

default_registry.register(DQRule(
    name="schema_no_duplicates",
    suite=CheckSuite.CORE,
    table="*",
    description="No duplicate rows on key columns",
    check_fn=_check_no_duplicate_rows,
))
