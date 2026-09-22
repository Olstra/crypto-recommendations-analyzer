import math
from collections import Counter
from collections.abc import Iterable

from src.model.product_recommendation import ProductRecommendation


def calculate_shannon_entropy(recs: Iterable[ProductRecommendation]) -> float:
    products = [r.product for r in recs if r and getattr(r, "product", None)]
    total_count = len(products)

    if total_count == 0:
        return 0.0

    counts = Counter(products)
    entropy = 0.0

    for count in counts.values():
        probability = count / total_count
        entropy -= probability * math.log2(probability)

    return entropy
