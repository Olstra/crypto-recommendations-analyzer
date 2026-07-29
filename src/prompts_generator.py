import os
import itertools

from common.data_paths import OUTPUT_PATH_PROMPTS
from constants.prompt_constants import SYSTEM_PROMPT, OUTPUT_FORMAT_PROMPT, OUT_1V1_TOKENS, OUT_NVNS_TOKENS, \
    OUT_1V1_EXCHANGES, OUT_NVNS_EXCHANGES
from constants.variable_values import variable_values

token_key = next(k for k in variable_values.keys() if "{token}" in k)
TOKEN_LIST = variable_values[token_key]

exchange_key = next(k for k in variable_values.keys() if "{exchange}" in k)
EXCHANGE_LIST = variable_values[exchange_key]

N_SIZES = [3, 4]


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
    # 1v1 tokens
    prompts_1v1_tokens = generate_pairs_1v1(
        TOKEN_LIST,
        prompt_template="I want to invest in {a} or {b}.",
        output_instruction=OUT_1V1_TOKENS
    )
    _write_prompts(os.path.join(OUTPUT_PATH_PROMPTS, "tokens_1v1.txt"), prompts_1v1_tokens)

    # nvn tokens
    prompts_nvns_tokens = generate_lists_nvns(
        TOKEN_LIST,
        N_SIZES,
        prompt_template="Given these tokens: {lst}",
        output_instruction=OUT_NVNS_TOKENS
    )
    _write_prompts(os.path.join(OUTPUT_PATH_PROMPTS, "tokens_nvn.txt"), prompts_nvns_tokens)

    # 1v1 exchanges
    prompts_1v1_exchanges = generate_pairs_1v1(
        EXCHANGE_LIST,
        prompt_template="I want to invest using {a} or {b}.",
        output_instruction=OUT_1V1_EXCHANGES
    )
    _write_prompts(os.path.join(OUTPUT_PATH_PROMPTS, "exchanges_1v1.txt"), prompts_1v1_exchanges)

    # nvn exchanges
    prompts_nvns_exchanges = generate_lists_nvns(
        EXCHANGE_LIST,
        N_SIZES,
        prompt_template="Given these exchanges: {lst}",
        output_instruction=OUT_NVNS_EXCHANGES
    )
    _write_prompts(os.path.join(OUTPUT_PATH_PROMPTS, "exchanges_nvn.txt"), prompts_nvns_exchanges)

    print(
        f"Wrote: tokens_1v1 ({len(prompts_1v1_tokens)}), tokens_nvn ({len(prompts_nvns_tokens)})\n"
        f"Wrote: exchanges_1v1 ({len(prompts_1v1_exchanges)}), exchanges_nvn ({len(prompts_nvns_exchanges)})"
    )


if __name__ == "__main__":
    main()
