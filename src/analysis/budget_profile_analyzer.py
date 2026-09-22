import json
import re
import sqlite3
from collections import Counter
from collections.abc import Iterable
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from pandas import DataFrame, Series

from common.logger import get_logger
from constants.data_paths import OUTPUT_PATH_ANALYSIS, OUTPUT_PATH_RESPONSES
from src.analysis.general_calculations.calculate_gini_coefficient import (
    _get_sorted_counts,
    calculate_gini_coefficient,
    gini_pygini,
    parse_pairs,
)
from src.analysis.general_calculations.sentiment_polarity import (
    calculate_sentiment_polarity,
)
from src.analysis.general_calculations.shannon_entropy import calculate_shannon_entropy
from src.constants.analysis_constants import EXCLUDED_TOKENS, TOP_N
from src.model.product_recommendation import ProductRecommendation

logger = get_logger(Path(__file__).name)

BUDGET_MARKERS = [
    "100 chf",
    "1'000 chf",
    "1,000 chf",
    "10'000 chf",
    "20'000 chf",
    "30'000 chf",
    "40'000 chf",
    "50'000 chf",
    "100'000 chf",
]


# =============================================================================
# 1. DATA PROCESSING & VARIABLE EXTRACTION
# =============================================================================


def enrich_with_variables(df: DataFrame) -> DataFrame:
    """Parses budget tiers, risk profiles, and environments from JSON variables or prompt text."""

    def parse(row) -> Series:
        v = row.get("variables")
        parsed = {}
        if isinstance(v, str):
            try:
                parsed = json.loads(v.replace("'", '"'))
            except:
                try:
                    parsed = eval(v)
                except:
                    pass

        prompt_text = str(row.get("prompt", "")).lower()

        # Extract Budget
        budget = parsed.get("budget") or parsed.get("capital")
        if not budget:
            for b in BUDGET_MARKERS:
                if b in prompt_text:
                    budget = b
                    break
            if not budget:
                budget = "unknown"

        # Extract Risk (for context)
        risk = parsed.get("risk") or parsed.get("risk_profile")
        if not risk:
            if "risk-averse" in prompt_text:
                risk = "risk-averse"
            elif "risk-seeking" in prompt_text:
                risk = "risk-seeking"
            elif "risk-neutral" in prompt_text:
                risk = "risk-neutral"
            else:
                risk = "unknown"

        return Series([str(budget).lower().strip(), str(risk).lower().strip()])

    df[["budget", "risk_profile"]] = df.apply(parse, axis=1)
    return df


def _row_products(
    recs: Iterable[ProductRecommendation], exclude: set[str] | None = None
) -> list[str]:
    exclude_lower = {e.lower() for e in exclude} if exclude else set()
    return [r.product for r in recs if r.product.lower() not in exclude_lower]


def parse_budget_numeric_value(budget_str: str) -> int:
    """Extracts integer value from budget string for proper numerical sorting."""
    nums = re.findall(r"\d+", budget_str.replace("'", "").replace(",", ""))
    return int("".join(nums)) if nums else 0


# =============================================================================
# 2. FREQUENCY COUNTERS & METRICS ENGINE
# =============================================================================


def top_products_overall(
    cleaned: DataFrame, top_k: int, exclude: set[str] | None = None
) -> DataFrame:
    counts: Counter[str] = Counter()
    for _, r in cleaned.iterrows():
        counts.update(_row_products(r["recommendations"], exclude=exclude))
    ranked = counts.most_common(top_k)
    return DataFrame(
        [
            {"rank": i + 1, "product": p, "overall_mentions": int(c)}
            for i, (p, c) in enumerate(ranked)
        ]
    )


def top_products_per_llm(
    cleaned: DataFrame, top_k: int, exclude: set[str] | None = None
) -> DataFrame:
    total_counter: Counter[str] = Counter()
    per_llm_counter: dict[str, Counter[str]] = {}

    for _, r in cleaned.iterrows():
        recs = r["recommendations"]
        model = r["model"]
        prods = _row_products(recs, exclude=exclude)

        total_counter.update(prods)
        if model not in per_llm_counter:
            per_llm_counter[model] = Counter()
        per_llm_counter[model].update(prods)

    rows = []
    for model, counter in per_llm_counter.items():
        ranked = sorted(counter.items(), key=lambda x: x[1], reverse=True)[:top_k]
        for i, (p, c) in enumerate(ranked):
            rows.append(
                {
                    "model": model,
                    "rank": i + 1,
                    "product": p,
                    "mentions_per_llm": int(c),
                    "mentions_total": int(total_counter[p]),
                }
            )
    return DataFrame(rows)


def run_analysis_block(
    cleaned_data: DataFrame, top_k: int, exclude: set[str] | None = None
) -> list[str]:
    """Generates standard quantitative lines including VADER sentiment polarity and stats for any budget tier."""
    lines = []
    if cleaned_data.empty:
        return ["No data available for this budget tier block."]

    exclude_label = f" (excluding {', '.join(sorted(exclude))})" if exclude else ""

    lines.append(f"=== Top {top_k} products overall{exclude_label} ===")
    for _, r in top_products_overall(cleaned_data, top_k, exclude).iterrows():
        lines.append(
            f"#{int(r['rank'])} {r['product']} (mentions={int(r['overall_mentions'])})"
        )

    lines.append(f"\n=== Statistical & Sentiment Metrics per LLM{exclude_label} ===")
    exclude_lower = {e.lower() for e in exclude} if exclude else set()

    for model in sorted(cleaned_data["model"].unique()):
        model_df = cleaned_data[cleaned_data["model"] == model]
        model_recs = [
            item
            for sublist in model_df["recommendations"].tolist()
            for item in sublist
            if item.product.lower() not in exclude_lower
        ]
        model_responses = model_df["response"].tolist()

        try:
            gi_manual = calculate_gini_coefficient(model_recs)
            counts = _get_sorted_counts(model_recs)
            gi_pygini_val = gini_pygini(counts)
            shannon_ent = calculate_shannon_entropy(model_recs)
            sentiment_pol = calculate_sentiment_polarity(model_responses)

            lines.append(f"[{model}]")
            lines.append(f"  Manual GI        : {gi_manual:.4f}")
            lines.append(f"  PyGini GI        : {gi_pygini_val:.4f}")
            lines.append(f"  Shannon Entropy  : {shannon_ent:.4f}")
            lines.append(f"  Sentiment Pol.   : {sentiment_pol:.4f}")
        except Exception as e:
            logger.error(f"[{model}] Error computing metrics: {e}")
            lines.append(f"[{model}] Error computing metrics: {e}")

    return lines


# =============================================================================
# 3. VISUALIZATION ENGINE (Dashboard Only)
# =============================================================================


def generate_visualizations(
    df: DataFrame, group_name: str, output_dir: Path, top_k: int, exclude: set[str]
):
    """Generates the unified 5-in-1 dashboard image for the budget tier."""
    if df.empty:
        return

    group_clean = group_name.lower().replace(" ", "_").replace("'", "").replace(",", "")

    df_overall = top_products_overall(df, top_k=top_k, exclude=exclude).sort_values(
        "overall_mentions", ascending=True
    )
    df_per_llm = top_products_per_llm(df, top_k=top_k, exclude=exclude)
    models = sorted(df_per_llm["model"].unique())
    colors = ["#1B4F72", "#117A65", "#7D6608", "#6c3483"]

    x_max_overall = (
        df_overall["overall_mentions"].max() * 1.15 if not df_overall.empty else 100
    )
    x_max_llm = (
        df_per_llm["mentions_per_llm"].max() * 1.15 if not df_per_llm.empty else 100
    )

    # Initialize the 5-in-1 Dashboard Figure
    fig = plt.figure(figsize=(15, 14))

    ax_main = plt.subplot2grid((3, 2), (0, 0), colspan=2)
    axes_llm = [
        plt.subplot2grid((3, 2), (1, 0)),
        plt.subplot2grid((3, 2), (1, 1)),
        plt.subplot2grid((3, 2), (2, 0)),
        plt.subplot2grid((3, 2), (2, 1)),
    ]

    # Dashboard: Overall Graph
    if not df_overall.empty:
        bars = ax_main.barh(
            df_overall["product"],
            df_overall["overall_mentions"],
            color="#2E4053",
            alpha=0.88,
        )
        ax_main.set_title(
            f"Top {top_k} Tokens Overall - All LLMs Combined (Budget: {group_name.upper()})",
            fontsize=15,
            fontweight="bold",
            pad=12,
        )
        ax_main.set_xlabel("Mentions", fontsize=11)
        ax_main.spines["top"].set_visible(False)
        ax_main.spines["right"].set_visible(False)
        ax_main.set_xlim(0, x_max_overall)

        for bar in bars:
            ax_main.annotate(
                f"{int(bar.get_width())}",
                xy=(bar.get_width(), bar.get_y() + bar.get_height() / 2),
                xytext=(6, 0),
                textcoords="offset points",
                ha="left",
                va="center",
                fontsize=9,
                fontweight="bold",
            )
    else:
        ax_main.set_visible(False)

    # Dashboard: Per-LLM Graphs
    for i, ax in enumerate(axes_llm):
        if i < len(models):
            model = models[i]
            sub_df = df_per_llm[df_per_llm["model"] == model].sort_values(
                "mentions_per_llm", ascending=True
            )

            bars = ax.barh(
                sub_df["product"],
                sub_df["mentions_per_llm"],
                color=colors[i % len(colors)],
                alpha=0.88,
            )
            ax.set_title(model, fontsize=13, fontweight="bold", pad=8)
            ax.set_xlabel("Mentions", fontsize=10)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.set_xlim(0, x_max_llm)

            for bar in bars:
                ax.annotate(
                    f"{int(bar.get_width())}",
                    xy=(bar.get_width(), bar.get_y() + bar.get_height() / 2),
                    xytext=(6, 0),
                    textcoords="offset points",
                    ha="left",
                    va="center",
                    fontsize=9,
                    fontweight="bold",
                )
        else:
            ax.set_visible(False)

    plt.suptitle(
        f"Budget Profile Analysis: Tier {group_name.upper()}",
        fontsize=18,
        fontweight="bold",
        y=0.97,
    )
    plt.tight_layout()
    plt.subplots_adjust(top=0.92, hspace=0.35)

    dashboard_path = output_dir / f"budget_{group_clean}_dashboard_top_{top_k}.png"
    plt.savefig(dashboard_path, dpi=300, bbox_inches="tight")
    plt.close()

    logger.info(
        f"Generated 5-in-1 Dashboard for budget tier '{group_name}' at: {dashboard_path}"
    )


# =============================================================================
# 4. MASTER ANALYSIS PIPELINE
# =============================================================================


def main(input_data: Path, top_k: int):
    analysis_out_dir = OUTPUT_PATH_ANALYSIS / "budget_profile_analysis"
    analysis_out_dir.mkdir(parents=True, exist_ok=True)
    report_file = analysis_out_dir / "budget_profile_report.txt"

    logger.info("Loading and enriching data for Budget Profile analysis...")
    with sqlite3.connect(input_data) as connection:
        df = pd.read_sql_query("SELECT * FROM tokens", connection)

    df["recommendations"] = df["response"].apply(parse_pairs)
    df = enrich_with_variables(df)

    lines = [
        "===========================================================",
        " BUDGET PROFILE ANALYSIS: CAPITAL ELASTICITY & TONE REPORT",
        "===========================================================\n",
        f"Total Dataset Records: {len(df)} | Evaluated Models: {len(df['model'].unique())}\n",
    ]

    # Detect and numerically sort available budgets
    raw_budgets = [b for b in df["budget"].unique() if b != "unknown"]
    sorted_budgets = sorted(raw_budgets, key=parse_budget_numeric_value)
    logger.info(f"Detected Sorted Budget Tiers: {sorted_budgets}")

    # Select min, max, and one middle budget profile
    if len(sorted_budgets) >= 3:
        min_budget = sorted_budgets[0]
        max_budget = sorted_budgets[-1]
        mid_budget = sorted_budgets[len(sorted_budgets) // 2]
        target_budgets = [min_budget, mid_budget, max_budget]
    elif len(sorted_budgets) > 0:
        target_budgets = sorted_budgets
    else:
        target_budgets = ["unknown"]

    logger.info(f"Selected Budget Tiers for Analysis (Min, Mid, Max): {target_budgets}")

    # --- ITERATE THROUGH SELECTED BUDGET TIERS ---
    for budget in target_budgets:
        logger.info(f"Processing Budget Tier: {budget.upper()}...")
        df_budget = df[df["budget"] == budget].copy()

        budget_clean = (
            budget.lower().replace(" ", "_").replace("'", "").replace(",", "")
        )
        subset_csv_path = analysis_out_dir / f"budget_{budget_clean}_subset.csv"
        df_budget.to_csv(subset_csv_path, index=False)

        lines.extend(
            [
                "\n\n" + "=" * 60,
                f" BUDGET TIER: {budget.upper()} (N={len(df_budget)})",
                "=" * 60,
            ]
        )
        lines.extend(
            run_analysis_block(df_budget, top_k=top_k, exclude=EXCLUDED_TOKENS)
        )

        # Generate dashboard for the budget tier
        generate_visualizations(
            df_budget, budget, analysis_out_dir, top_k, EXCLUDED_TOKENS
        )

    # --- SAVE TEXT REPORT ---
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info(f"Success! Budget Profile analysis files saved to: {analysis_out_dir}")


if __name__ == "__main__":
    _input_db = OUTPUT_PATH_RESPONSES / "responses-preprocessed.db"
    main(input_data=_input_db, top_k=TOP_N)
