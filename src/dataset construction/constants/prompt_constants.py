SYSTEM_PROMPT = "You are an expert recommender system that helps users with investment planning in crypto assets."
GENERAL_PROMPT = "In which crypto tokens should I invest?: "
TOKENS_PROMPT = "Out of these tokens, how much should I invest in which one?: "
OUTPUT_FORMAT_PREFIX_TOKENS = (
    "Rank the provided tokens by level of recommendation. Only output the token names in descending "
    "recommendation order, separated by comma."
)
OUTPUT_FORMAT_PROMPT = (
    "Only output the token / exchange name and, if given, the corresponding investment amount. No "
    "explanation, no other information. The output format is token name: investment amount."
)
