import re
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from pygini import gini

from constants.data_paths import OUTPUT_PATH_RESPONSES
from constants.token_names import POPULAR_TOKEN_NAMES
from src.model.product_recommendation import ProductRecommendation


def parse_pairs(data: str) -> list[ProductRecommendation]:
    if pd.isna(data) or not isinstance(data, str):
        return []

    # todo: check - not all recommendations have ":"
    matches = re.findall(r"([A-Za-z0-9]+):\s*([\d\.]+)", data)

    out = []
    for product, amount in matches:
        try:
            out.append(
                ProductRecommendation(product=product.strip(), amount=float(amount))
            )
        except ValueError:
            continue
    return out


def _get_sorted_counts(data: list[ProductRecommendation]) -> list[int]:
    total_times_recommended_per_product = {}
    for recommendation in data:
        total_times_recommended_per_product[recommendation.product] = (
            total_times_recommended_per_product.get(recommendation.product, 0) + 1
        )

    for token in POPULAR_TOKEN_NAMES:
        total_times_recommended_per_product.setdefault(token, 0)

    return sorted(total_times_recommended_per_product.values())


def calculate_gini_coefficient(data: list[ProductRecommendation]) -> float:
    """Calculates the Gini Index manually from the standard formula:

    $$GI = \frac{\\sum_{i=1}^{n}((2i - n - 1) \\cdot x_i)}{n \\cdot \\sum_{i=1}^{n}(x_i)}$$
    """
    sorted_counts = _get_sorted_counts(data)
    n = len(sorted_counts)
    total_sum_recommendations = sum(sorted_counts)

    if n == 0 or total_sum_recommendations == 0:
        return 0.0

    dividend = sum(
        (2 * i - n - 1) * val for i, val in enumerate(sorted_counts, start=1)
    )
    divisor = n * total_sum_recommendations

    return dividend / divisor


def gini_pygini(data: list[int]) -> float:
    data = sorted(data)
    return float(gini(np.asarray(data, dtype=float))) if len(data) else np.nan


if __name__ == "__main__":
    db_path = Path(OUTPUT_PATH_RESPONSES) / "responses-preprocessed.db"

    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query("SELECT * FROM tokens", conn)

    df["recommendations"] = df["response"].apply(parse_pairs)

    print("--- Gini Index Calculations ---")
    for model, model_df in df.groupby("model"):
        model_recommendations = [
            item for sublist in model_df["recommendations"].tolist() for item in sublist
        ]

        gi_manual = calculate_gini_coefficient(model_recommendations)

        counts = _get_sorted_counts(model_recommendations)
        gi_pygini_val = gini_pygini(counts)

        print(f"[{model}]")
        print(f"  Manual GI : {gi_manual:.4f}")
        print(f"  PyGini GI : {gi_pygini_val:.4f}")
