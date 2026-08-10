import ast
from pathlib import Path

import pandas as pd
from pandas import DataFrame

from analysis.data_preprocessor import ProductRecommendation
from common.data_paths import OUTPUT_PATH_PREPROCESSED_DATA
from common.variable_values import TOKENS_LIST


def parse_pairs(cell):
    if pd.isna(cell):
        return []
    pairs = ast.literal_eval(cell)  # safe for literal Python structures
    # pairs like [('Bitcoin','70CHF'), ...]
    out = []
    for _product, _amount in pairs:
        out.append(ProductRecommendation(product=_product, amount=_amount))
    return out


def calculate_gini_coefficient(data: list[ProductRecommendation]) -> float:
    """Calculates the Gini Index from the formula:

           sum_{i=1}^{n}((2i - n - 1) * x_i)    [= "dividend" variable]
    GI = -----------------------------------
                n * sum_{i=1}^{n}(x_i)          [= "divisor" variable]
    """
    total_times_recommended_per_product = {}
    for recommendation in data:
        total_times_recommended_per_product[recommendation.product] = (
            total_times_recommended_per_product.get(
                recommendation.product, 0
            )
            + 1
        )

    # 1. Include missing tokens (if TOKENS_LIST is fixed) so length equals n
    for token in TOKENS_LIST:
        total_times_recommended_per_product.setdefault(token, 0)

    # 2. MUST sort values in ascending order for formula validity
    sorted_counts = sorted(total_times_recommended_per_product.values())

    n = len(sorted_counts)
    total_sum_recommendations = sum(sorted_counts)

    if n == 0 or total_sum_recommendations == 0:
        return 0.0

    # 3. Apply formula with 1-based index (start=1)
    dividend = sum(
        (2 * i - n - 1) * val for i, val in enumerate(sorted_counts, start=1)
    )

    divisor = n * total_sum_recommendations

    return dividend / divisor


if __name__ == "__main__":
    df = pd.concat(
        [
            pd.read_csv(p)
            for p in Path(OUTPUT_PATH_PREPROCESSED_DATA).iterdir()
            if p.suffix.lower() == ".csv"
        ],
        ignore_index=True,
    )
    df["products_and_amounts"] = df["products_and_amounts"].apply(parse_pairs)

    # Calculate Gini coefficient per LLM model
    for model_name, model_df in df.groupby("model_name"):
        model_recommendations = [
            item
            for sublist in model_df["products_and_amounts"].tolist()
            for item in sublist
        ]

        gi = calculate_gini_coefficient(model_recommendations)

        print(f"GI for: {model_name}: {gi}")
