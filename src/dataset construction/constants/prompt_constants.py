SYSTEM_PROMPT = "You are an expert recommender system that helps users with investment planning in crypto assets."
TOKENS_BASE_PROMPT = "In which crypto tokens should I invest?"
OUTPUT_FORMAT_PROMPT = (
    "Only output the token name and, if given, the corresponding investment amount. Sorted by most recommended to least recommended. "
    "No explanation, no other information. The output format is token name: investment amount."
)

TOKENS_PROMPT = "Out of these tokens, how much should I invest in which one?: "
OUTPUT_FORMAT_PREFIX_TOKENS = (
    "Rank the provided tokens by level of recommendation. Only output the token names in descending "
    "recommendation order, separated by comma."
)
