from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ProductRecommendation:
    product: str
    amount: float
