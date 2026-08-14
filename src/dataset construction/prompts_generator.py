import itertools
from pathlib import Path

from constants.prompt_constants import (
    OUTPUT_FORMAT_PROMPT,
    SYSTEM_PROMPT,
    TOKENS_BASE_PROMPT,
)
from constants.variable_values import VARIABLE_NAMES, VARIABLE_VALUES

from common.data_paths import OUTPUT_PATH_PROMPTS
from common.logger import get_logger

logger = get_logger(Path(__file__).name)


def _generate_all_combinations(data: list[str]) -> list[tuple]:
    result = []
    for r in range(1, len(data) + 1):
        for c in itertools.combinations(data, r):
            result.append(c)

    return result


def generate_prompts_one_file(
    base_filename: str,
    base_prompt: str,
    variables_values: dict[str, list] = VARIABLE_VALUES,
    variables_to_use: list[str] = VARIABLE_NAMES,
    system_prompt: str = SYSTEM_PROMPT,
    output_format_prompt: str = OUTPUT_FORMAT_PROMPT,
    output_dir: Path = OUTPUT_PATH_PROMPTS,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    all_possible_scenarios = _generate_all_combinations(variables_to_use)

    for combo in all_possible_scenarios:
        values_for_scenario = {key: variables_values[key] for key in combo}
        variable_combinations = [
            prompt for prompt in itertools.product(*values_for_scenario.values())
        ]

        output_file = output_dir / f"{base_filename}-{'_'.join(combo)}.txt"
        with output_file.open("w", encoding="utf-8") as f:
            for scenario in variable_combinations:
                prompt_body = " ".join(
                    s.strip() for s in scenario if s and str(s).strip()
                )
                full_prompt = f"{system_prompt} {prompt_body} {base_prompt} {output_format_prompt}"
                full_prompt = " ".join(full_prompt.split())
                f.write(full_prompt + "\n")

        logger.info(
            f"Wrote {len(variable_combinations)} prompts lines to {output_file}"
        )


if __name__ == "__main__":
    generate_prompts_one_file(
        base_filename="tokens-general",
        base_prompt=TOKENS_BASE_PROMPT,
        output_dir=OUTPUT_PATH_PROMPTS / "token_recommendations" / "general",
    )
