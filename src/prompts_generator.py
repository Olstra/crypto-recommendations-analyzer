import itertools
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from common.logger import get_logger
from constants.prompt_constants import SYSTEM_PROMPT, GENERAL_PROMPT, TOKENS_PROMPT, OUTPUT_FORMAT_PREFIX_TOKENS, \
    OUTPUT_FORMAT_PROMPT
from constants.variable_values import VARIABLE_VALUES_GENERAL, TOKENS_LIST
from common.data_paths import PROMPT_FILES_PATH

logger = get_logger(Path(__file__).name)


def _extract_placeholder_name(tmpl: str) -> str:
    return tmpl.split("{", 1)[1].split("}", 1)[0]


def generate_base_prompts(variable_values: dict, vars_to_use: list) -> List[str]:
    templates: List[str] = []
    value_lists: List[List[str]] = []
    placeholders_by_template: List[str] = []

    for tmpl, values in variable_values.items():
        placeholder = _extract_placeholder_name(tmpl)
        if placeholder in vars_to_use:
            templates.append(tmpl)
            value_lists.append(values)
            placeholders_by_template.append(placeholder)

    if not templates:
        raise ValueError(f"No templates found for vars_to_use={tuple(vars_to_use)}")

    lines: List[str] = []
    for combo in itertools.product(*value_lists):
        parts: List[str] = []
        for tmpl, placeholder, val in zip(templates, placeholders_by_template, combo):
            parts.append(tmpl.format(**{placeholder: val}))
        lines.append(" ".join(parts).strip())

    return lines


def generate_prompts_with_general_question(
    variable_values: dict,
    output_dir: Path,
    possible_tokens: list,
    vars_to_use: list = ["budget", "term", "risk", "environment"],
    *,
    base_filename: str = "general",
    general_question: str = GENERAL_PROMPT,
    system_prompt: str = SYSTEM_PROMPT,
    output_format_prompt: str = OUTPUT_FORMAT_PROMPT,
) -> None:
    _ = possible_tokens
    base_prompts = generate_base_prompts(variable_values, vars_to_use=vars_to_use)
    safe_vars = "_".join(vars_to_use)

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    path = out_dir / f"{base_filename}-{safe_vars}.txt"
    with path.open("w", encoding="utf-8") as f:
        for p in base_prompts:
            line = f"{system_prompt} {p} {general_question}{output_format_prompt}"
            f.write(line.strip() + "\n")

    logger.info(f"Wrote {len(base_prompts)} lines to {path}")


def generate_prompts_with_value_list(
    variable_values: dict,
    output_dir: Path,
    value_list: Sequence[str],
    vars_to_use: list = ["budget", "term", "risk", "environment"],
    *,
    base_filename: str = "chosen_tokens",
    list_question: str = TOKENS_PROMPT,
    min_subset_size: int = 2,
    system_prompt: str = SYSTEM_PROMPT,
    output_format_prefix: str = OUTPUT_FORMAT_PREFIX_TOKENS,
    output_format_prompt: str = OUTPUT_FORMAT_PROMPT,
) -> None:
    base_prompts = generate_base_prompts(variable_values, vars_to_use=vars_to_use)
    safe_vars = "_".join(vars_to_use)

    subsets: List[Tuple[str, ...]] = []
    tokens = list(value_list)
    for k in range(min_subset_size, len(tokens) + 1):
        subsets.extend(itertools.combinations(tokens, k))

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    path = out_dir / f"{base_filename}-{safe_vars}.txt"
    with path.open("w", encoding="utf-8") as f:
        for p in base_prompts:
            for subset in subsets:
                subset_str = ", ".join(subset)
                line = (
                    f"{system_prompt} {p} {list_question}{subset_str} "
                    f"{output_format_prefix} {output_format_prompt}"
                )
                f.write(line.strip() + "\n")

    logger.info(f"Wrote {len(base_prompts) * len(subsets)} lines to {path}")


if __name__ == "__main__":
    generate_prompts_with_general_question(
        variable_values=VARIABLE_VALUES_GENERAL,
        output_dir=PROMPT_FILES_PATH,
        possible_tokens=TOKENS_LIST,
        base_filename="general",
    )

    generate_prompts_with_value_list(
        variable_values=VARIABLE_VALUES_GENERAL,
        output_dir=PROMPT_FILES_PATH,
        value_list=TOKENS_LIST,
        base_filename="chosen_tokens",
    )
