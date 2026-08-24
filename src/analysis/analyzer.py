from __future__ import annotations

import sqlite3
from collections import Counter
from collections.abc import Iterable
from pathlib import Path

import pandas as pd
from pandas import DataFrame

from constants.data_paths import OUTPUT_PATH_ANALYSIS, OUTPUT_PATH_RESPONSES
from constants.supported_models import SUPPORTED_MODELS
from model.ProductRecommendation import ProductRecommendation
from src.analysis.calculate_gini_coefficient import (
    _get_sorted_counts,
    calculate_gini_coefficient,
    gini_pygini,
    parse_pairs,
)


def _row_products(recs: Iterable[ProductRecommendation]) -> list[str]:
    return [r.product for r in recs]


def top_products_overall(cleaned: DataFrame, top_k: int = 3) -> DataFrame:
    counts: Counter[str] = Counter()
    for _, r in cleaned.iterrows():
        counts.update(_row_products(r["recommendations"]))

    ranked = counts.most_common(top_k)
    return DataFrame(
        [
            {"rank": i + 1, "product": p, "overall_mentions": int(c)}
            for i, (p, c) in enumerate(ranked)
        ]
    )


def top_products_per_llm(cleaned: DataFrame, top_k: int = 3) -> DataFrame:
    total_counter: Counter[str] = Counter()
    per_llm_counter: dict[str, Counter[str]] = {}

    for _, r in cleaned.iterrows():
        recs = r["recommendations"]
        model = r["model"]
        prods = _row_products(recs)

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


def main(input_data: Path, output_file: Path):
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
        "=== Top 3 products overall (by mention frequency) ===",
    ]

    top_overall = top_products_overall(cleaned_data, top_k=3)
    for _, r in top_overall.iterrows():
        lines.append(
            f"#{int(r['rank'])} {r['product']} (mentions={int(r['overall_mentions'])})"
        )

    lines.append("\n=== Top 3 products per LLM (by mention frequency) ===")
    top_per_llm = top_products_per_llm(cleaned_data, top_k=3)

    for model in sorted(top_per_llm["model"].unique()):
        sub = top_per_llm[top_per_llm["model"] == model].sort_values("rank")
        lines.append(f"[{model}]")
        for _, r in sub.iterrows():
            lines.append(
                f"  #{int(r['rank'])} {r['product']} (mentions_per_llm={int(r['mentions_per_llm'])})"
            )

    lines.append("\n=== Gini Coefficient per LLM ===")
    for model in sorted(cleaned_data["model"].unique()):
        model_df = cleaned_data[cleaned_data["model"] == model]
        model_recommendations = [
            item for sublist in model_df["recommendations"].tolist() for item in sublist
        ]

        gi_manual = calculate_gini_coefficient(model_recommendations)
        counts = _get_sorted_counts(model_recommendations)
        gi_pygini_val = gini_pygini(counts)

        lines.append(f"[{model}]")
        lines.append(f"  Manual GI : {gi_manual:.4f}")
        lines.append(f"  PyGini GI : {gi_pygini_val:.4f}")

    lines.append("")

    OUTPUT_PATH_ANALYSIS.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("Done :-)")


if __name__ == "__main__":
    _input_data = OUTPUT_PATH_RESPONSES / "responses-preprocessed.db"
    _output_file = OUTPUT_PATH_ANALYSIS / "report-analysis.txt"
    main(_input_data, _output_file)
