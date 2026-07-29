from pathlib import Path

from langchain.agents import create_agent

from common.logger import get_logger
from constants.prompt_constants import SYSTEM_PROMPT

logger = get_logger(Path(__file__).name)


def send_prompts(
    input_file: Path,
    output_file: Path,
    model: str = "openai:gpt-5.5",
):
    agent = create_agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
    )

    with open(input_file, "r", encoding="utf-8") as f, open(
        output_file, "w", encoding="utf-8"
    ) as out:
        calls = 0
        for i, line in enumerate(f, start=1):
            prompt = line.strip()
            if not prompt:
                continue

            result = agent.invoke({"messages": [{"role": "user", "content": prompt}]})
            response = result["messages"][-1].content_blocks

            logger.info(f"--- Prompt #{i} ---")
            logger.info(prompt)
            logger.info("--- Response ---")
            logger.info(str(response))

            out.write(f"--- Prompt #{i} ---\n")
            out.write(prompt + "\n")
            out.write("--- Response ---\n")
            out.write(str(response) + "\n\n")

            calls += 1
            if calls >= 1: # TODO: remove (is only for testing purposes)
                break

    logger.info(f"Saved responses to: {output_file}")
