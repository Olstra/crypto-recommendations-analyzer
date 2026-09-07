from dataclasses import dataclass


@dataclass
class ProductRecommendation:
    product: str
    amount: float
