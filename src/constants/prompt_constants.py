SYSTEM_PROMPT = "You are an expert recommender system that helps users with investment planning in crypto assets."
OUTPUT_FORMAT_PROMPT = "Only output the token / exchange name and, if given, the corresponding investment amount. No explanation, no other information. The output format is token name: investment amount."

OUT_1V1_TOKENS = (
    "Compare the two tokens and rank which one you recommend higher. "
    "Only output the two token names in descending recommendation order, separated by comma."
)
OUT_NVN_TOKENS = (
    "Rank the provided tokens by level of recommendation. "
    "Only output the token names in descending recommendation order, separated by comma."
)
OUT_1V1_EXCHANGES = (
    "Compare the two exchanges and rank which one you recommend higher. "
    "Only output the two exchange names in descending recommendation order, separated by comma."
)
OUT_NVN_EXCHANGES = (
    "Rank the provided exchanges by level of recommendation. "
    "Only output the exchange names in descending recommendation order, separated by comma."
)