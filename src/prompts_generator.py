import os
import re
from itertools import combinations, product

from common.data_paths import OUTPUT_PATH_PROMPTS
from constants.prompt_constants import SYSTEM_PROMPT
from constants.variable_names import variable_names
from constants.variable_values import variable_values
from constants.variables_descriptions import variables_descriptions


def generate_prompts(
    output_path_prompts: str,
    system_prompt: str,
    variable_definitions_,
    variable_values_,
    variables_descriptions_,
):
    requirements = [
        "Please recommend a cyptocurrency investment plan to me, specific to the name of the cyptocurrency and the amount.",
        "Please recommend a cyptocurrency investment plan to me, specifying the name of the cyptocurrency, sorted by the level of recommendation.",
    ]

    scenario_index_list = list(range(len(variables_descriptions_)))

    all_templates = []
    file_name_list = []

    # Build templates + filenames
    for role_idx, role in enumerate([system_prompt]):
        all_scenarios = []
        for r in range(0, len(scenario_index_list) + 1):
            for combo in combinations(scenario_index_list, r):
                if len(combo) == 0:
                    file_name = "no_fair_no_scenario" if role_idx == 0 else "fair_no_scenario"
                else:
                    prefix = "no_fair_" if role_idx == 0 else "fair_"
                    file_name = prefix + "-".join([variable_definitions_[ii] for ii in combo])

                file_name_list.append(file_name)

                scenario_combina_list = [variables_descriptions_[idx] for idx in list(combo)]
                tmp_scenario = "" if len(scenario_combina_list) == 0 else " ".join(scenario_combina_list)

                # Original logic: checks `0 in combo` to decide which requirement to use
                if 0 in combo:
                    tmp_scenario = role + " " + tmp_scenario + " " + requirements[0]
                else:
                    tmp_scenario = role + " " + tmp_scenario + " " + requirements[1]

                all_scenarios.append(tmp_scenario)
                all_templates.append(tmp_scenario)

    # Save prompts per template
    for idx, template in enumerate(all_templates):
        prompts = []
        keys_in_template = list(set(re.findall(r"\{.*?\}", template)))

        values = [variable_values_[key] for key in keys_in_template]
        combos = product(*values)

        for combo in combos:
            prompt = template
            for key, value in zip(keys_in_template, combo):
                prompt = prompt.replace(key, value)
            prompts.append(prompt)

        os.makedirs(output_path_prompts, exist_ok=True)
        out_file = os.path.join(output_path_prompts, f"{file_name_list[idx]}_{len(prompts)}.txt")
        with open(out_file, "w", encoding="utf-8") as f:
            for prp in prompts:
                f.write(prp + "\n")


if __name__ == "__main__":
    generate_prompts(OUTPUT_PATH_PROMPTS, SYSTEM_PROMPT, variable_names, variable_values, variables_descriptions)
