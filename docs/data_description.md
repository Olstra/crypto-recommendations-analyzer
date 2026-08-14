# About the data gathered in this project

## Prompts
Questions used in prompts:
1. _In which crypto tokens should I invest?_
2. _At which exchanges should I buy crypto?_  
TBD
3. _Out of these tokens, how much should I invest in which one?_  
TBD

## Dataset

### In which crypto tokens should I invest?
| scenario                        | model  | total prompts | total datapoints in dataset |
|---------------------------------|--------|--------------:|----------------------------:|
| budget                          | Gemini |             8 |                           8 |
| risk                            | Gemini |             3 |                           3 |
| term                            | Gemini |             3 |                           3 |
| environment                     | Gemini |             4 |                           4 |
| budget, risk                    | Gemini |            24 |                          24 |
| budget, term                    | Gemini |            24 |                          24 |
| budget, environment             | Gemini |            32 |                          32 |
| risk, term                      | Gemini |             9 |                           9 |
| risk, environment               | Gemini |            12 |                          12 |
| term, environment               | Gemini |            12 |                          12 |
| budget, risk, term              | Gemini |            72 |                          72 |
| budget, risk, environment       | Gemini |            96 |                          96 |
| budget, term, environment       | Gemini |            96 |                          96 |
| risk, term, environment         | Gemini |            36 |                          36 |
| budget, risk, term, environment | Gemini |           288 |                         288 |
| —                               | —      |             — |                           — |
| budget                          | Claude |             8 |                           8 |
| risk                            | Claude |             3 |                           3 |
| term                            | Claude |             3 |                           3 |
| environment                     | Claude |             4 |                           4 |
| budget, risk                    | Claude |            24 |                          11 |
| budget, term                    | Claude |            24 |                          11 |
| budget, environment             | Claude |            32 |                          11 |
| risk, term                      | Claude |             9 |                           9 |
| risk, environment               | Claude |            12 |                          11 |
| term, environment               | Claude |            12 |                          11 |
| budget, risk, term              | Claude |            72 |                          11 |
| budget, risk, environment       | Claude |            96 |                          11 |
| budget, term, environment       | Claude |            96 |                          11 |
| risk, term, environment         | Claude |            36 |                          11 |
| budget, risk, term, environment | Claude |           288 |                          11 |
| —                               | —      |             — |                           — |
| budget                          | GPT    |             8 |                           8 |
| risk                            | GPT    |             3 |                           3 |
| term                            | GPT    |             3 |                           3 |
| environment                     | GPT    |             4 |                           4 |
| budget, risk                    | GPT    |            24 |                          11 |
| budget, term                    | GPT    |            24 |                          11 |
| budget, environment             | GPT    |            32 |                          11 |
| risk, term                      | GPT    |             9 |                           9 |
| risk, environment               | GPT    |            12 |                          11 |
| term, environment               | GPT    |            12 |                          11 |
| budget, risk, term              | GPT    |            72 |                          11 |
| budget, risk, environment       | GPT    |            96 |                          11 |
| budget, term, environment       | GPT    |            96 |                          11 |
| risk, term, environment         | GPT    |            36 |                          11 |
| budget, risk, term, environment | GPT    |           288 |                          11 |
| —                               | —      |             — |                           — |
| budget                          | Grok   |             8 |                           8 |
| risk                            | Grok   |             3 |                           3 |
| term                            | Grok   |             3 |                           3 |
| environment                     | Grok   |             4 |                           4 |
| budget, risk                    | Grok   |            24 |                          11 |
| budget, term                    | Grok   |            24 |                          11 |
| budget, environment             | Grok   |            32 |                          11 |
| risk, term                      | Grok   |             9 |                           9 |
| risk, environment               | Grok   |            12 |                          11 |
| term, environment               | Grok   |            12 |                          11 |
| budget, risk, term              | Grok   |            72 |                          11 |
| budget, risk, environment       | Grok   |            96 |                          11 |
| budget, term, environment       | Grok   |            96 |                          11 |
| risk, term, environment         | Grok   |            36 |                          11 |
| budget, risk, term, environment | Grok   |           288 |                          11 |