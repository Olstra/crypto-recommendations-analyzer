# About the data gathered in this project

## LLMs used
The LLM model names used in this project are defined in the file _supported_models.py_.

| Category | Model name                  |
|----------|-----------------------------|
| Gemini   | `gemini-3.6-flash`          |
| Claude   | `claude-haiku-4-5-20251001` |
| OpenAI   | `openai:gpt-5.5`            |
| Grok     | `grok-4.6`                  |

## Prompts
Overview of the questions used in the prompts:
1. _In which crypto tokens should I invest?_
   - 719 prompts (per llm)
   - 2'876 total prompts
2. _Which exchanges should I use to invest?_  
   - 719 prompts (per llm)
   - 2'876 total prompts  

## Dataset

## Response Counts by Model
Standard Markdown tables don’t support merged cells, but this is the closest layout:

| model      | response_count | complete? |                        |
|------------|---------------:|:---------:|:----------------------:|
|            |                | exchanges |         tokens         |
| claude     |           1438 |     ✓     |           ✓            |
| gemini     |           1438 |     ✓     |           ✓            |
| grok       |           1234 |     ✓     | – (insufficient funds) |
| openai:gpt |           1438 |     ✓     |           ✓            |

You’re right—the tables were flipped. The correct assignment is:

- **Crypto tokens:** Grok uses the **second** result.
- **Exchanges:** Grok uses the **first** result.

### 1. In which crypto tokens should I invest?

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
| budget, risk                    | Claude |            24 |                          24 |
| budget, term                    | Claude |            24 |                          24 |
| budget, environment             | Claude |            32 |                          32 |
| risk, term                      | Claude |             9 |                           9 |
| risk, environment               | Claude |            12 |                          12 |
| term, environment               | Claude |            12 |                          12 |
| budget, risk, term              | Claude |            72 |                          72 |
| budget, risk, environment       | Claude |            96 |                          96 |
| budget, term, environment       | Claude |            96 |                          96 |
| risk, term, environment         | Claude |            36 |                          36 |
| budget, risk, term, environment | Claude |           288 |                         288 |
| —                               | —      |             — |                           — |
| budget                          | GPT    |             8 |                           8 |
| risk                            | GPT    |             3 |                           3 |
| term                            | GPT    |             3 |                           3 |
| environment                     | GPT    |             4 |                           4 |
| budget, risk                    | GPT    |            24 |                          24 |
| budget, term                    | GPT    |            24 |                          24 |
| budget, environment             | GPT    |            32 |                          32 |
| risk, term                      | GPT    |             9 |                           9 |
| risk, environment               | GPT    |            12 |                          12 |
| term, environment               | GPT    |            12 |                          12 |
| budget, risk, term              | GPT    |            72 |                          72 |
| budget, risk, environment       | GPT    |            96 |                          96 |
| budget, term, environment       | GPT    |            96 |                          96 |
| risk, term, environment         | GPT    |            36 |                          36 |
| budget, risk, term, environment | GPT    |           288 |                         288 |
| —                               | —      |             — |                           — |
| budget                          | Grok   |             8 |                           8 |
| risk                            | Grok   |             3 |                           0 |
| term                            | Grok   |             3 |                           3 |
| environment                     | Grok   |             4 |                           4 |
| budget, risk                    | Grok   |            24 |                           0 |
| budget, term                    | Grok   |            24 |                          24 |
| budget, environment             | Grok   |            32 |                          32 |
| risk, term                      | Grok   |             9 |                           9 |
| risk, environment               | Grok   |            12 |                           0 |
| term, environment               | Grok   |            12 |                          12 |
| budget, risk, term              | Grok   |            72 |                          72 |
| budget, risk, environment       | Grok   |            96 |                          63 |
| budget, term, environment       | Grok   |            96 |                           0 |
| risk, term, environment         | Grok   |            36 |                           0 |
| budget, risk, term, environment | Grok   |           288 |                         288 |

### 2. Which exchanges should I use to invest?

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
| budget, risk                    | Claude |            24 |                          24 |
| budget, term                    | Claude |            24 |                          24 |
| budget, environment             | Claude |            32 |                          32 |
| risk, term                      | Claude |             9 |                           9 |
| risk, environment               | Claude |            12 |                          12 |
| term, environment               | Claude |            12 |                          12 |
| budget, risk, term              | Claude |            72 |                          72 |
| budget, risk, environment       | Claude |            96 |                          96 |
| budget, term, environment       | Claude |            96 |                          96 |
| risk, term, environment         | Claude |            36 |                          36 |
| budget, risk, term, environment | Claude |           288 |                         288 |
| —                               | —      |             — |                           — |
| budget                          | GPT    |             8 |                           8 |
| risk                            | GPT    |             3 |                           3 |
| term                            | GPT    |             3 |                           3 |
| environment                     | GPT    |             4 |                           4 |
| budget, risk                    | GPT    |            24 |                          24 |
| budget, term                    | GPT    |            24 |                          24 |
| budget, environment             | GPT    |            32 |                          32 |
| risk, term                      | GPT    |             9 |                           9 |
| risk, environment               | GPT    |            12 |                          12 |
| term, environment               | GPT    |            12 |                          12 |
| budget, risk, term              | GPT    |            72 |                          72 |
| budget, risk, environment       | GPT    |            96 |                          96 |
| budget, term, environment       | GPT    |            96 |                          96 |
| risk, term, environment         | GPT    |            36 |                          36 |
| budget, risk, term, environment | GPT    |           288 |                         288 |
| —                               | —      |             — |                           — |
| budget                          | Grok   |             8 |                           8 |
| risk                            | Grok   |             3 |                           3 |
| term                            | Grok   |             3 |                           3 |
| environment                     | Grok   |             4 |                           4 |
| budget, risk                    | Grok   |            24 |                          24 |
| budget, term                    | Grok   |            24 |                          24 |
| budget, environment             | Grok   |            32 |                          32 |
| risk, term                      | Grok   |             9 |                           9 |
| risk, environment               | Grok   |            12 |                          12 |
| term, environment               | Grok   |            12 |                          12 |
| budget, risk, term              | Grok   |            72 |                          72 |
| budget, risk, environment       | Grok   |            96 |                          96 |
| budget, term, environment       | Grok   |            96 |                          96 |
| risk, term, environment         | Grok   |            36 |                          36 |
| budget, risk, term, environment | Grok   |           288 |                         288 |