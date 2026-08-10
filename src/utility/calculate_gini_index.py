from dataclasses import dataclass


@dataclass
class ProductStats:
    product_name: str
    total_times_recommended: int


def calculate_gini_coefficient(values: list[ProductStats]) -> float:
    n = len(values)
    numerator = 0.0
    denominator = n * sum(p.total_times_recommended for p in values)

    for i, product in enumerate(values, start=1):
        x_i = product.total_times_recommended
        numerator += (2 * i - n - 1) * x_i

    return numerator / denominator if denominator != 0 else 0.0
