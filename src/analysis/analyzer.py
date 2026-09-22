import math
import sqlite3
from collections import Counter
from collections.abc import Iterable
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from pandas import DataFrame

from analysis.general_calculations.calculate_gini_coefficient import (
    _get_sorted_counts,
    calculate_gini_coefficient,
    gini_pygini,
    parse_pairs,
)
from analysis.general_calculations.sentiment_polarity import (
    calculate_sentiment_polarity,
)
from analysis.general_calculations.shannon_entropy import calculate_shannon_entropy
from constants.analysis_constants import EXCLUDED_TOKENS, TOP_N
from constants.data_paths import OUTPUT_PATH_ANALYSIS, OUTPUT_PATH_RESPONSES
from constants.supported_models import SUPPORTED_MODELS
from src.model.product_recommendation import ProductRecommendation


def _row_products(
    recs: Iterable[ProductRecommendation],
    exclude: set[str] | None = None,
) -> list[str]:
    exclude_lower = {e.lower() for e in exclude} if exclude else set()
    return [r.product for r in recs if r.product.lower() not in exclude_lower]


def top_products_overall(
    cleaned: DataFrame,
    top_k: int,
    exclude: set[str] | None = None,
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
    cleaned: DataFrame,
    top_k: int,
    exclude: set[str] | None = None,
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


def generate_professional_plots(df: DataFrame, title: str, output_path: Path):
    """Generates and saves a high-quality, professional subplot grid for top LLM recommendations."""
    sns.set_theme(
        style="whitegrid", rc={"axes.edgecolor": "0.15", "axes.linewidth": 1.25}
    )

    models = sorted(df["model"].unique())
    n_models = len(models)

    # Calculate grid size (2 columns, dynamic rows)
    cols = 2
    rows = math.ceil(n_models / cols)

    fig, axes = plt.subplots(rows, cols, figsize=(14, 5 * rows), sharex=False)

    # Standardize axes array for easy iteration
    if n_models == 1:
        axes = [axes]
    else:
        axes = axes.flatten()

    for i, model in enumerate(models):
        ax = axes[i]
        model_df = df[df["model"] == model].sort_values(
            "mentions_per_llm", ascending=False
        )

        sns.barplot(
            data=model_df,
            x="mentions_per_llm",
            y="product",
            ax=ax,
            hue="product",
            palette="mako",  # Professional dark blue/green gradient
            legend=False,
        )

        ax.set_title(f"{model}", fontsize=15, fontweight="bold", pad=10)
        ax.set_xlabel("Mention Frequency", fontsize=12, weight="semibold")
        ax.set_ylabel("")
        ax.tick_params(axis="y", labelsize=12)
        ax.tick_params(axis="x", labelsize=11)

    # Remove any empty subplots if n_models is odd
    for j in range(len(models), len(axes)):
        fig.delaxes(axes[j])

    fig.suptitle(title, fontsize=18, fontweight="bold", y=1.02 + (0.01 * (rows - 1)))
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def run_analysis_block(
    cleaned_data: DataFrame,
    top_k: int,
    exclude: set[str] | None = None,
) -> tuple[list[str], DataFrame]:
    lines = []

    # Top Products Overall
    exclude_label = f" (excluding {', '.join(sorted(exclude))})" if exclude else ""
    lines.append(
        f"=== Top {top_k} products overall (by mention frequency){exclude_label} ==="
    )
    top_overall = top_products_overall(cleaned_data, top_k=top_k, exclude=exclude)
    for _, r in top_overall.iterrows():
        lines.append(
            f"#{int(r['rank'])} {r['product']} (mentions={int(r['overall_mentions'])})"
        )

    # Top Products per LLM
    lines.append(
        f"\n=== Top {top_k} products per LLM (by mention frequency){exclude_label} ==="
    )
    top_per_llm = top_products_per_llm(cleaned_data, top_k=top_k, exclude=exclude)

    for model in sorted(top_per_llm["model"].unique()):
        sub = top_per_llm[top_per_llm["model"] == model].sort_values("rank")
        lines.append(f"[{model}]")
        for _, r in sub.iterrows():
            lines.append(
                f"  #{int(r['rank'])} {r['product']} (mentions_per_llm={int(r['mentions_per_llm'])})"
            )

    # Quantitative & Sentiment Metrics per LLM
    lines.append(f"\n=== Statistical & Sentiment Metrics per LLM{exclude_label} ===")
    exclude_lower = {e.lower() for e in exclude} if exclude else set()

    for model in sorted(cleaned_data["model"].unique()):
        model_df = cleaned_data[cleaned_data["model"] == model]

        # Recommendations for entropy and Gini calculations
        model_recs = [
            item
            for sublist in model_df["recommendations"].tolist()
            for item in sublist
            if item.product.lower() not in exclude_lower
        ]

        # Raw responses for sentiment analysis of the text output
        model_responses = model_df["response"].tolist()

        gi_manual = calculate_gini_coefficient(model_recs)
        counts = _get_sorted_counts(model_recs)
        gi_pygini_val = gini_pygini(counts)
        shannon_entropy = calculate_shannon_entropy(model_recs)
        sentiment_polarity = calculate_sentiment_polarity(model_responses)

        lines.append(f"[{model}]")
        lines.append(f"  Manual GI        : {gi_manual:.4f}")
        lines.append(f"  PyGini GI        : {gi_pygini_val:.4f}")
        lines.append(f"  Shannon Entropy  : {shannon_entropy:.4f}")
        lines.append(f"  Sentiment Pol.   : {sentiment_polarity:.4f}")

    return lines, top_per_llm


def main(input_data: Path, output_file: Path, top_k: int):
    table_name = "tokens"
    with sqlite3.connect(input_data) as connection:
        cleaned_data = pd.read_sql_query(f"SELECT * FROM {table_name}", connection)

    cleaned_data["recommendations"] = cleaned_data["response"].apply(parse_pairs)

    total_responses = len(cleaned_data)
    total_models = len(SUPPORTED_MODELS)

    lines = [
        "=== Dataset metrics ===",
        f"total_responses: {total_responses}",
        f"total_models: {total_models}\n",
    ]

    OUTPUT_PATH_ANALYSIS.mkdir(parents=True, exist_ok=True)

    # 1. Standard analysis (Full Dataset)
    block_lines, df_general = run_analysis_block(
        cleaned_data, top_k=top_k, exclude=None
    )
    lines.extend(block_lines)

    generate_professional_plots(
        df_general,
        title="Top Token Recommendations per LLM",
        output_path=OUTPUT_PATH_ANALYSIS / "llm_recommendations_general.png",
    )

    # 2. Secondary analysis (Excluding Specified Tokens)
    lines.append("\n" + "=" * 50)
    lines.append(
        f"=== ANALYSIS EXCLUDING {', '.join(sorted(t.upper() for t in EXCLUDED_TOKENS))} ==="
    )
    lines.append("=" * 50 + "\n")

    block_lines_excl, df_tail = run_analysis_block(
        cleaned_data, top_k=top_k, exclude=EXCLUDED_TOKENS
    )
    lines.extend(block_lines_excl)

    generate_professional_plots(
        df_tail,
        title="Top Token Recommendations per LLM (Excluding Baseline Assets)",
        output_path=OUTPUT_PATH_ANALYSIS / "llm_recommendations_tail.png",
    )

    lines.append("")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("Done :-)")


if __name__ == "__main__":
    _input_data = OUTPUT_PATH_RESPONSES / "responses-preprocessed.db"
    _output_file = OUTPUT_PATH_ANALYSIS / "report-analysis.txt"

    # Ensure matplotlib uses a non-interactive backend for script execution
    import matplotlib

    matplotlib.use("Agg")

    main(_input_data, _output_file, top_k=TOP_N)
