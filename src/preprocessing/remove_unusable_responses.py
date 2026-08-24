from pandas import DataFrame

_UNUSABLE_KEYWORDS = (
    "sorry",
    "i can't",
    "i cannot",
    "cannot help",
    "can't help",
    "unable to",
    "i am unable",
    "as an ai",
    ", but i",
    "i dont",
    "i don't",
)


def _remove_unusable_responses(data: DataFrame) -> DataFrame:
    responses = data["response"].fillna("").astype(str).str.strip()

    usable_mask = responses.ne("")

    for keyword in _UNUSABLE_KEYWORDS:
        usable_mask &= ~responses.str.lower().str.contains(
            keyword,
            regex=False,
        )

    return data[usable_mask].copy()
