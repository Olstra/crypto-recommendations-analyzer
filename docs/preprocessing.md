# About the prerocessing steps used in this project  

--  
The preprocessing steps are the following:
1. remove unusable responses
2. response normalization
   1. Tokens: normalize token names
   2. Exchanges: TODO
3. Furhter steps: TODO

## 1. Remove unusable responses
Unusable responses are regarded as responses that:
- are empty
- contain keywords that hint at the llm rejecting the user query (example "i cannot"). 
The full list of such keywords can be found in the constant __UNUSABLE_KEYWORDS_.

## 2. Response normalization
### Tokens
First, we collect the most popular token names and their different wrtings from the coingeko API.  
So far, we use the 500 most popular ones.
We construct a dictionary from this info in this format
```
POPULAR_TOKEN_NAMES = {
    "Bitcoin": ["bitcoin", "btc"],
    "Ethereum": ["eth", "ethereum"],
    "Tether": ["tether", "usdt"],
    ...
}
```
Then all token names found in the response are normalized to equal the key in the above dictionary.

TODO: check for overlapping matches. - fix regex
Due to overlaps token names that have a length of <= 2 are not regarded.
Next task is to check how many overlappt there are for 3 letters (e.g. make sure "eth" is not matching other token names).
This can be fixed by implementing a regex that uses "end of word" signalization.

### Exchanges
TODO