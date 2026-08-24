import json
import re
from pathlib import Path

import requests

from src.constants.data_paths import PROJECT_ROOT

API_URL = "https://api.coingecko.com/api/v3/coins/markets"
_MIN_VARIATION_LENGTH = 3


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _get_variations(*values: str | None) -> set[str]:
    variations: set[str] = set()

    for value in values:
        if not value:
            continue

        normalized = _normalize(str(value))

        if not normalized:
            continue

        variations.update(
            {
                normalized,
                normalized.replace(" ", ""),
                normalized.replace(" ", "-"),
            }
        )

    return variations


def _get_usable_variations(*values: str | None) -> set[str]:
    return {
        variation
        for variation in _get_variations(*values)
        if len(variation) >= _MIN_VARIATION_LENGTH
    }


def _get_popular_coins(number_of_coins: int) -> list[dict]:
    coins: list[dict] = []
    pages = (number_of_coins + 249) // 250

    for page in range(1, pages + 1):
        response = requests.get(
            API_URL,
            params={
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": 250,
                "page": page,
                "sparkline": "false",
            },
            timeout=30,
        )
        response.raise_for_status()
        coins.extend(response.json())

    return coins[:number_of_coins]


def _get_unique_coin_names(coins: list[dict]) -> list[str]:
    unique_names: list[str] = []
    used_names: set[str] = set()

    for coin in coins:
        coin_name = str(coin["name"])
        unique_name = coin_name

        if unique_name in used_names:
            unique_name = f"{coin_name} ({coin['id']})"

        used_names.add(unique_name)
        unique_names.append(unique_name)

    return unique_names


def _build_crypto_variations(coins: list[dict]) -> dict[str, list[str]]:
    unique_coin_names = _get_unique_coin_names(coins)
    variation_owners: dict[str, str] = {}

    for coin, unique_coin_name in zip(coins, unique_coin_names):
        variations = _get_usable_variations(
            coin.get("name"),
            coin.get("symbol"),
            coin.get("id"),
        )

        for variation in variations:
            # Higher-ranked coins appear first and win conflicts.
            variation_owners.setdefault(variation, unique_coin_name)

    crypto_variations: dict[str, list[str]] = {}

    for coin, unique_coin_name in zip(coins, unique_coin_names):
        variations = _get_usable_variations(
            coin.get("name"),
            coin.get("symbol"),
            coin.get("id"),
        )

        crypto_variations[unique_coin_name] = sorted(
            variation
            for variation in variations
            if variation_owners.get(variation) == unique_coin_name
        )

    return crypto_variations


def main(
    output_path: Path,
    number_of_coins: int = 500,
) -> None:
    coins = _get_popular_coins(number_of_coins)
    crypto_variations = _build_crypto_variations(coins)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        file.write("POPULAR_TOKEN_NAMES = ")
        file.write(
            json.dumps(
                crypto_variations,
                indent=4,
                ensure_ascii=False,
            )
        )
        file.write("\n")

    print(f"Saved {len(crypto_variations)} coins to {output_path}")


if __name__ == "__main__":
    main(PROJECT_ROOT / "src" / "constants" / "token_names.py")
