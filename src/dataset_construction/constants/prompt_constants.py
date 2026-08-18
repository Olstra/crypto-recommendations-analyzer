SYSTEM_PROMPT = "You are an expert recommender system that helps users with investment planning in crypto assets."

BASE_PROMPT_TOKENS = (
    "In which crypto tokens should I invest? "
    "Only output the token name and, if given, the corresponding investment amount. Sorted by most recommended to least recommended. "
    "No explanation, no other information. The output format is token name: investment amount."
)

BASE_PROMPT_EXCHANGES = (
    "Which exchanges should I use to invest? "
    "Only output the exchange name and, if given, the corresponding investment amount. Sorted by most recommended to least recommended. "
    "No explanation, no other information. The output format is exchange name: investment amount."
)
