from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Counter, Iterable

import pandas as pd
from pandas import DataFrame

from analysis.calculate_gini_coefficient import parse_pairs
from common.data_paths import (
    OUTPUT_PATH_RESPONSES,
    OUTPUT_PATH_ANALYSIS_RESULTS,
    OUTPUT_PATH_PREPROCESSED_DATA,
)
from common.supported_models import SUPPORTED_MODELS


@dataclass
class ProductRecommendation:
    product: str
    amount: str  # TODO: maybe change to float


def _row_products(recs: Iterable[ProductRecommendation]) -> list[str]:
    return [r.product for r in recs]


def total_products_recommended_per_llm(cleaned: DataFrame) -> DataFrame:
    work = cleaned.copy()
    total_counter: Counter[str] = Counter()
    per_llm_products: dict[str, Counter[str]] = {}

    for _, r in work.iterrows():
        recs = r["products_and_amounts"]
        model = r["model_name"]

        prods = _row_products(recs)
        total_counter.update(prods)

        if model not in per_llm_products:
            per_llm_products[model] = Counter()
        per_llm_products[model].update(prods)

    rows = []
    for model, counter in per_llm_products.items():
        distinct = sorted(counter.keys())
        nr_mentions = sum(counter.values())

        for p in distinct:
            rows.append(
                {
                    "model_name": model,
                    "product": p,
                    "mentions_per_llm": int(counter[p]),
                    "mentions_total": int(total_counter[p]),
                    "nr_distinct_products_recommended": len(distinct),
                    "nr_product_mentions": int(nr_mentions),
                }
            )

    return DataFrame(rows)


def top_products_overall(cleaned: DataFrame, top_k: int = 3) -> DataFrame:
    work = cleaned.copy()

    counts: Counter[str] = Counter()
    for _, r in work.iterrows():
        recs = r["products_and_amounts"]
        counts.update(_row_products(recs))

    ranked = counts.most_common(top_k)
    return DataFrame(
        [{"rank": i + 1, "product": p, "overall_mentions": int(c)} for i, (p, c) in enumerate(ranked)]
    )


def top_products_per_llm(cleaned: DataFrame, top_k: int = 3) -> DataFrame:
    work = cleaned.copy()

    total_counter: Counter[str] = Counter()
    per_llm_counter: dict[str, Counter[str]] = {}

    for _, r in work.iterrows():
        recs = r["products_and_amounts"]
        model = r["model_name"]
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
                    "model_name": model,
                    "rank": i + 1,
                    "product": p,
                    "mentions_per_llm": int(c),
                    "mentions_total": int(total_counter[p]),
                }
            )

    return DataFrame(rows)


def main():
    raw_data = pd.concat(
        [pd.read_csv(p) for p in Path(OUTPUT_PATH_RESPONSES).iterdir() if p.suffix.lower() == ".csv"],
        ignore_index=True,
    )

    cleaned_data = pd.concat(
        [pd.read_csv(p) for p in Path(OUTPUT_PATH_PREPROCESSED_DATA).iterdir() if p.suffix.lower() == ".csv"],
        ignore_index=True,
    )
    # reparse products and amounts from "str" (in .csv) to tuples
    cleaned_data["pairs"] = cleaned_data["products_and_amounts"].apply(parse_pairs)
    cleaned_data["products_and_amounts"] = cleaned_data["pairs"]
    cleaned_data = cleaned_data.drop(columns=["pairs"])

    total_responses_before_preprocessing = len(raw_data)
    total_responses_after_preprocessing = len(cleaned_data)
    total_models = len(SUPPORTED_MODELS)

    lines = []

    top_overall = top_products_overall(cleaned_data, top_k=3)
    top_per_llm = top_products_per_llm(cleaned_data, top_k=3)

    lines.append("=== Dataset metrics ===")
    lines.append(f"total_responses_before_preprocessing: {total_responses_before_preprocessing}")
    lines.append(f"total_responses_after_preprocessing: {total_responses_after_preprocessing}")
    lines.append(f"total_models: {total_models}")
    lines.append("")

    lines.append("=== Top 3 products overall (by mention frequency) ===")
    for _, r in top_overall.iterrows():
        lines.append(f"#{int(r['rank'])} {r['product']} (mentions={int(r['overall_mentions'])})")
    lines.append("")

    lines.append("=== Top 3 products per LLM (by mention frequency) ===")
    for model in sorted(top_per_llm["model_name"].unique()):
        sub = top_per_llm[top_per_llm["model_name"] == model].sort_values("rank")
        lines.append(f"[{model}]")
        for _, r in sub.iterrows():
            lines.append(f"  #{int(r['rank'])} {r['product']} (mentions_per_llm={int(r['mentions_per_llm'])})")
    lines.append("")

    OUTPUT_PATH_ANALYSIS_RESULTS.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH_ANALYSIS_RESULTS / "results.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("Done :-)")


if __name__ == "__main__":
    main()
