import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from pandas import DataFrame

from common.data_paths import OUTPUT_PATH_PREPROCESSED_DATA, PROJECT_ROOT
from common.logger import get_logger
from common.variable_values import TOKENS_LIST

logger = get_logger(Path(__file__).name)


@dataclass
class ProductRecommendation:
    product: str
    amount: str  # TODO: maybe change to float


INVALID_PATTERNS = [
    re.compile(r"\b(i don't know|cannot|can't|unable|no data|error|as an ai)\b", re.IGNORECASE),
]


def _response_is_invalid(text: str) -> bool:
    if text is None:
        return True

    t = str(text).strip()

    if not t:
        return True

    for pat in INVALID_PATTERNS:
        if pat.search(t):
            return True

    if not any(tok.lower() in t.lower() for tok in TOKENS_LIST):
        return True

    return False


def _normalize_token_name(data: str) -> str:
    for token_name in TOKENS_LIST:
        if token_name.lower() in data.strip().lower():
            return token_name

    logger.warning(f"Token name not found in SUPPORTED_TOKENS: '{data}'")
    return data.strip()


def _normalize_amount_str(amount: str) -> str:
    # normalize number like 7'000'000, 1 000 000, 1,000,000
    return amount.replace("'", "").replace(",", "").replace(" ", "")


def _extract_recommendations(text: str, tokens_list: list[str]) -> list[ProductRecommendation]:
    """
    Find the first match of tokens_list, capture everything after it until we hit
    the next token (case-insensitive). Repeat until end of string.
    """
    if not tokens_list or not text:
        return []

    # token_pattern matches any token as a whole word
    escaped_tokens = [re.escape(t) for t in tokens_list]
    token_pattern = rf"\b({'|'.join(escaped_tokens)})\b"

    results: list[ProductRecommendation] = []
    search_start = 0

    while True:
        match = re.search(token_pattern, text[search_start:], re.IGNORECASE)
        if not match:
            break

        token_start_abs = search_start + match.start()
        token_end_abs = search_start + match.end()

        raw_token_name = match.group(1)
        # capture until next token (or end of string)
        next_match = re.search(token_pattern, text[token_end_abs:], re.IGNORECASE)
        value_end_abs = (token_end_abs + next_match.start()) if next_match else len(text)

        raw_value = text[token_end_abs:value_end_abs].strip()
        clean_value = re.sub(r"^[:\s]+", "", raw_value).strip()

        product = _normalize_token_name(raw_token_name)
        amount = _normalize_amount_str(clean_value)

        results.append(ProductRecommendation(product=product, amount=amount))

        # continue searching after the current token (NOT after the value)
        # so we can detect overlapping/nearby tokens correctly.
        search_start = token_end_abs

    return results


def extract_recommendations(text: str) -> list[ProductRecommendation]:
    if text is None:
        return []
    return _extract_recommendations(text, TOKENS_LIST)


def preprocess_dataframe(df: DataFrame) -> DataFrame:
    out_rows = []
    for _, row in df.iterrows():
        raw_text = row["response"]

        if _response_is_invalid(raw_text):
            logger.warning(f"Skipping invalid response: '{raw_text}'")
            continue

        text = str(raw_text).strip()
        recommendations = extract_recommendations(text)

        prods_and_amounts = [(r.product, r.amount) for r in recommendations]

        out_rows.append(
            {
                "id": row["id"],
                "model_name": row["model_name"],
                "products_and_amounts": prods_and_amounts,
                "cleaned_response_text": text,
                "original_response_text": row["response"],
            }
        )

    return DataFrame(out_rows)


if __name__ == "__main__":
    in_dir = PROJECT_ROOT / "data" / "preprocessed_csv"
    input_files = [f for f in in_dir.iterdir() if f.suffix == ".csv"]

    for f in input_files:
        df = pd.read_csv(f)
        cleaned_df = preprocess_dataframe(df)
        cleaned_df.to_csv(OUTPUT_PATH_PREPROCESSED_DATA / f"preprocessed-{f.stem}.csv", index=False)
