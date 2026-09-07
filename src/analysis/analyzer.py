import sqlite3
from collections import Counter
from collections.abc import Iterable
from pathlib import Path

import pandas as pd
from pandas import DataFrame

from constants.data_paths import OUTPUT_PATH_ANALYSIS, OUTPUT_PATH_RESPONSES
from constants.supported_models import SUPPORTED_MODELS
from src.analysis.calculate_gini_coefficient import (
    _get_sorted_counts,
    calculate_gini_coefficient,
    gini_pygini,
    parse_pairs,
)
from src.model.product_recommendation import ProductRecommendation

EXCLUDED_TOKENS = {"bitcoin", "ethereum", "solana"}


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


def run_analysis_block(
    cleaned_data: DataFrame,
    top_k: int,
    exclude: set[str] | None = None,
) -> list[str]:
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

    # Gini Coefficients
    lines.append(f"\n=== Gini Coefficient per LLM{exclude_label} ===")
    exclude_lower = {e.lower() for e in exclude} if exclude else set()

    for model in sorted(cleaned_data["model"].unique()):
        model_df = cleaned_data[cleaned_data["model"] == model]
        model_recs = [
            item
            for sublist in model_df["recommendations"].tolist()
            for item in sublist
            if item.product.lower() not in exclude_lower
        ]

        gi_manual = calculate_gini_coefficient(model_recs)
        counts = _get_sorted_counts(model_recs)
        gi_pygini_val = gini_pygini(counts)

        lines.append(f"[{model}]")
        lines.append(f"  Manual GI : {gi_manual:.4f}")
        lines.append(f"  PyGini GI : {gi_pygini_val:.4f}")

    return lines


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

    # Standard analysis (Full Dataset)
    lines.extend(run_analysis_block(cleaned_data, top_k=top_k, exclude=None))

    # Secondary analysis (Excluding Specified Tokens)
    lines.append("\n" + "=" * 50)
    lines.append(
        f"=== ANALYSIS EXCLUDING {', '.join(sorted(t.upper() for t in EXCLUDED_TOKENS))} ==="
    )
    lines.append("=" * 50 + "\n")
    lines.extend(run_analysis_block(cleaned_data, top_k=top_k, exclude=EXCLUDED_TOKENS))

    lines.append("")

    OUTPUT_PATH_ANALYSIS.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("Done :-)")


if __name__ == "__main__":
    _input_data = OUTPUT_PATH_RESPONSES / "responses-preprocessed.db"
    _output_file = OUTPUT_PATH_ANALYSIS / "report-analysis.txt"
    _top_k = 10
    main(_input_data, _output_file, top_k=_top_k)
