from __future__ import annotations

from textblob import TextBlob


def calculate_sentiment_polarity(responses: list[str]) -> float:
    if not responses:
        return 0.0

    total_polarity = 0.0
    valid_count = 0

    for text in responses:
        if text and isinstance(text, str):
            blob = TextBlob(text)
            total_polarity += blob.sentiment.polarity
            valid_count += 1

    return total_polarity / valid_count if valid_count > 0 else 0.0
