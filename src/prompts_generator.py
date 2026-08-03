import os
import itertools
from pathlib import Path

from common.data_paths import OUTPUT_PATH_PROMPTS
from common.logger import get_logger
from constants.prompt_constants import SYSTEM_PROMPT, OUTPUT_FORMAT_PROMPT, OUT_1V1_TOKENS, OUT_NVN_TOKENS, \
    OUT_1V1_EXCHANGES, OUT_NVN_EXCHANGES
from constants.variable_values import variable_values

logger = get_logger(Path(__file__).name)

token_key = next(k for k in variable_values.keys() if "{token}" in k)
TOKEN_LIST = variable_values[token_key]

exchange_key = next(k for k in variable_values.keys() if "{exchange}" in k)
EXCHANGE_LIST = variable_values[exchange_key]

N_SIZES_TOKENS = list(range(3, len(TOKEN_LIST) + 1))
N_SIZES_EXCHANGES = list(range(3, len(EXCHANGE_LIST) + 1))


def _write_prompts(path, prompts):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for p in prompts:
            f.write(p + "\n")


def generate_pairs_1v1(items, prompt_template, output_instruction):
    return [
        " ".join([SYSTEM_PROMPT, prompt_template.format(a=a, b=b), output_instruction, OUTPUT_FORMAT_PROMPT])
        for a, b in itertools.combinations(items, 2)
    ]


def generate_lists_nvns(items, n_sizes, prompt_template, output_instruction):
    prompts = []
    for n in n_sizes:
        for group in itertools.combinations(items, n):
            prompts.append(
                " ".join([
                    SYSTEM_PROMPT,
                    prompt_template.format(lst=", ".join(group)),
                    output_instruction,
                    OUTPUT_FORMAT_PROMPT
                ])
            )
    return prompts


def main():
    prompts_1v1_tokens = generate_pairs_1v1(
        TOKEN_LIST,
        prompt_template="I want to invest in {a} or {b}.",
        output_instruction=OUT_1V1_TOKENS
    )
    file_name = os.path.join(OUTPUT_PATH_PROMPTS, "tokens_1v1.txt")
    _write_prompts(file_name, prompts_1v1_tokens)
    logger.info(f"Saved prompts for '1 v 1 tokens' to: {file_name}")

    prompts_nvn_tokens = generate_lists_nvns(
        TOKEN_LIST,
        N_SIZES_TOKENS,
        prompt_template="Given these tokens: {lst}",
        output_instruction=OUT_NVN_TOKENS
    )
    file_name = os.path.join(OUTPUT_PATH_PROMPTS, "tokens_nvn.txt")
    _write_prompts(file_name, prompts_nvn_tokens)
    logger.info(f"Saved prompts for 'n v n tokens' to: {file_name}")

    prompts_1v1_exchanges = generate_pairs_1v1(
        EXCHANGE_LIST,
        prompt_template="I want to invest using {a} or {b}.",
        output_instruction=OUT_1V1_EXCHANGES
    )
    file_name = os.path.join(OUTPUT_PATH_PROMPTS, "exchanges_1v1.txt")
    _write_prompts(file_name, prompts_1v1_exchanges)
    logger.info(f"Saved prompts for 'n v n exchanges' to: {file_name}")

    prompts_nvn_exchanges = generate_lists_nvns(
        EXCHANGE_LIST,
        N_SIZES_EXCHANGES,
        prompt_template="Given these exchanges: {lst}",
        output_instruction=OUT_NVN_EXCHANGES
    )
    file_name = os.path.join(OUTPUT_PATH_PROMPTS, "exchanges_nvn.txt")
    _write_prompts(file_name, prompts_nvn_exchanges)
    logger.info(f"Saved prompts for 'n v n exchanges' to: {file_name}")


if __name__ == "__main__":
    main()
