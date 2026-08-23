"""
NOTES for final report:
    - term & env same as zhi et al.
    - budget categories different
    - for risk we added "risk-seeking" (since crypto investing is generally more risky)
    - category different, only crypto related values
"""

VARIABLE_NAMES = ["budget", "risk", "term", "environment"]

VARIABLE_VALUES_DEFINITIONS: dict[str, list] = {
    "I have {budget} to invest.": [
        "100 CHF",
        "1'000 CHF",
        "10'000 CHF",
        "20'000 CHF",
        "30'000 CHF",
        "40'000 CHF",
        "50'000 CHF",
        "100'000 CHF",
    ],
    "My risk tolerance is {risk}.": ["risk-averse", "risk-neutral", "risk-seeking"],
    "My investment term is {term}.": [
        "less than  one year",
        "one to three years",
        "three to ten years",
    ],
    "The market environment is {environment}.": [
        "expansion",
        "crisis",
        "recession",
        "recovery",
    ],
    # TODO: "{category}": ["meme coins", "utility tokens", "stable coins"]
}

VARIABLE_VALUES = {
    "budget": [
        "I have 100 CHF to invest.",
        "I have 1'000 CHF to invest.",
        "I have 10'000 CHF to invest.",
        "I have 20'000 CHF to invest.",
        "I have 30'000 CHF to invest.",
        "I have 40'000 CHF to invest.",
        "I have 50'000 CHF to invest.",
        "I have 100'000 CHF to invest.",
    ],
    "risk": [
        "My risk tolerance is risk-averse.",
        "My risk tolerance is risk-neutral.",
        "My risk tolerance is risk-seeking.",
    ],
    "term": [
        "My investment term is less than  one year.",
        "My investment term is one to three years.",
        "My investment term is three to ten years.",
    ],
    "environment": [
        "The market environment is expansion.",
        "The market environment is crisis.",
        "The market environment is recession.",
        "The market environment is recovery.",
    ],
}


if __name__ == "__main__":
    """ 
    Use this helper script to generate all possible values for the variables.
    Then copy paste what was printed to the console to VARIABLE_VALUES.
    """
    VARIABLE_VALUES_DICT = {k: [] for k in VARIABLE_NAMES}

    print("{")
    for template, vals in VARIABLE_VALUES_DEFINITIONS.items():
        # find the first variable name that appears inside {var}
        var = next((v for v in VARIABLE_NAMES if f"{{{v}}}" in template), None)
        if var is None:
            continue

        replaced = [template.format(**{var: v}) for v in vals]
        VARIABLE_VALUES_DICT[var] = replaced
        print(f'\t"{var}": {replaced},')
    print("}")
