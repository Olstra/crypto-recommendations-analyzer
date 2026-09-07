import re
import sqlite3
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from pandas import DataFrame

from common.logger import get_logger
from constants.data_paths import (
    OUTPUT_PATH_ANALYSIS,
    OUTPUT_PATH_RESPONSES,
)
from constants.token_names import POPULAR_TOKEN_NAMES
from preprocessing.get_data_for_scenario import _get_data_for_scenario
from preprocessing.remove_unusable_responses import _remove_unusable_responses

logger = get_logger(Path(__file__).name)


def _get_normalized_aliases(
    token_dict: dict[str, list[str]],
) -> list[str]:
    return [
        str(alias).casefold().strip()
        for aliases in token_dict.values()
        for alias in aliases
        if str(alias).casefold().strip()
    ]


def _count_token_responses(
    data: DataFrame,
    token_dict: dict[str, list[str]],
) -> dict[str, int]:
    responses = data["response"].fillna("").astype(str).str.casefold()

    counts: dict[str, int] = {}

    for token_name, aliases in token_dict.items():
        normalized_aliases = [
            str(alias).casefold().strip()
            for alias in aliases
            if str(alias).casefold().strip()
        ]

        if not normalized_aliases:
            counts[token_name] = 0
            continue

        matches = [
            any(alias in response for alias in normalized_aliases)
            for response in responses
        ]

        counts[token_name] = sum(matches)

    return counts


def _count_responses_without_tokens(
    data: DataFrame,
    token_dict: dict[str, list[str]],
) -> int:
    responses = data["response"].fillna("").astype(str).str.casefold()

    normalized_aliases = _get_normalized_aliases(token_dict)

    if not normalized_aliases:
        return len(responses)

    responses_with_tokens = responses.map(
        lambda response: any(alias in response for alias in normalized_aliases)
    )

    return int((~responses_with_tokens).sum())


def _percentage_removed(before: int, removed: int) -> float:
    return removed / before * 100 if before else 0.0


def _build_alias_to_token_name(
    token_dict: dict[str, list[str]],
) -> dict[str, str]:
    alias_to_token_name: dict[str, str] = {}

    for token_name, aliases in token_dict.items():
        canonical_name = str(token_name).strip()

        if canonical_name:
            alias_to_token_name.setdefault(
                canonical_name.casefold(),
                canonical_name,
            )

        for alias in aliases:
            normalized_alias = str(alias).casefold().strip()

            if normalized_alias:
                alias_to_token_name.setdefault(
                    normalized_alias,
                    canonical_name,
                )

    return alias_to_token_name


def _normalize_response(
    response: object,
    alias_to_token_name: dict[str, str],
    alias_pattern: re.Pattern[str],
) -> str:
    if response is None:
        return ""

    def replace_alias(match: re.Match[str]) -> str:
        alias = match.group(0).casefold().strip()
        return alias_to_token_name[alias]

    return alias_pattern.sub(
        replace_alias,
        str(response),
    )


def _normalize_token_responses(
    data: DataFrame,
    token_dict: dict[str, list[str]],
) -> DataFrame:
    normalized_data = data.copy()

    alias_to_token_name = _build_alias_to_token_name(token_dict)

    if not alias_to_token_name:
        normalized_data["response"] = normalized_data["response"].fillna("").astype(str)
        return normalized_data

    aliases = sorted(
        alias_to_token_name,
        key=len,
        reverse=True,
    )

    alias_pattern = re.compile(
        "|".join(re.escape(alias) for alias in aliases),
        flags=re.IGNORECASE,
    )

    normalized_data["response"] = normalized_data["response"].map(
        lambda response: _normalize_response(
            response,
            alias_to_token_name,
            alias_pattern,
        )
    )

    return normalized_data


def _save_preprocessed_responses(
    output_path: Path,
    exchanges: DataFrame,
    tokens: DataFrame,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(output_path) as connection:
        exchanges.to_sql(
            "exchanges",
            connection,
            if_exists="replace",
            index=False,
        )

        tokens.to_sql(
            "tokens",
            connection,
            if_exists="replace",
            index=False,
        )


if __name__ == "__main__":
    input_db_path = OUTPUT_PATH_RESPONSES / "responses.db"
    output_db_path = OUTPUT_PATH_RESPONSES / "responses-preprocessed.db"
    report_path = OUTPUT_PATH_ANALYSIS / "report-preprocessing.txt"

    report_buffer = StringIO()

    with redirect_stdout(report_buffer):
        exchanges = _get_data_for_scenario(
            input_db_path,
            "exchanges",
        )
        tokens = _get_data_for_scenario(
            input_db_path,
            "tokens",
        )

        print(
            f"#####\nResults before preprocessing\nTotal entries exchanges: {len(exchanges)}\nTotal entries tokens: {len(tokens)}"
        )

        exchanges_before = len(exchanges)
        tokens_before = len(tokens)

        exchanges = _remove_unusable_responses(exchanges)
        tokens = _remove_unusable_responses(tokens)

        exchanges_removed = exchanges_before - len(exchanges)
        tokens_removed = tokens_before - len(tokens)

        exchanges_percentage = _percentage_removed(
            exchanges_before,
            exchanges_removed,
        )
        tokens_percentage = _percentage_removed(
            tokens_before,
            tokens_removed,
        )
        print(
            "\n#####"
            f"\nResults after 'remove unusable responses'"
            f"\nExchanges: {len(exchanges)}, removed: {exchanges_before - len(exchanges)} = {exchanges_percentage:.2f}%"
            f"\nTokens: {len(tokens)}, removed: {tokens_before - len(tokens)} = {tokens_percentage:.2f}%"
        )

        print("\n#####\nTOKENS")
        token_counts = _count_token_responses(
            tokens,
            POPULAR_TOKEN_NAMES,
        )

        responses_without_tokens = _count_responses_without_tokens(
            tokens,
            POPULAR_TOKEN_NAMES,
        )

        print(f"\nResponses without any recognized token: {responses_without_tokens}")

        print("\nToken response counts:")

        for token_name, count in sorted(
            token_counts.items(),
            key=lambda item: item[1],
            reverse=True,
        ):
            if count <= 0:
                continue
            print(f"{token_name}: {count}")

        tokens = _normalize_token_responses(
            tokens,
            POPULAR_TOKEN_NAMES,
        )

        _save_preprocessed_responses(
            output_db_path,
            exchanges,
            tokens,
        )

        print(f"Saved preprocessed responses to: {output_db_path}")

    report = report_buffer.getvalue()

    print(report, end="")

    report_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    report_path.write_text(
        report,
        encoding="utf-8",
    )

    logger.info(f"Saved report to: {report_path}")
