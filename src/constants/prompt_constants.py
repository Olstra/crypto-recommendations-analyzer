SYSTEM_PROMPT = "You are an expert recommender system that helps users with investment planning in crypto assets."
OUTPUT_FORMAT_PROMPT = "Only output the token ticker / exchange name and, if given, the corresponding investment amount. No explanation, no other information. The output format is token ticker: investment amount."

OUT_1V1_TOKENS = (
    "Compare the two tokens and rank which one you recommend higher. "
    "Only output the two token tickers in descending recommendation order, separated by comma."
)
OUT_NVNS_TOKENS = (
    "Rank the provided tokens by level of recommendation. "
    "Only output the token tickers in descending recommendation order, separated by comma."
)
OUT_1V1_EXCHANGES = (
    "Compare the two exchanges and rank which one you recommend higher. "
    "Only output the two exchange names in descending recommendation order, separated by comma."
)
OUT_NVNS_EXCHANGES = (
    "Rank the provided exchanges by level of recommendation. "
    "Only output the exchange names in descending recommendation order, separated by comma."
)