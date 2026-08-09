import csv
from datetime import datetime
from pathlib import Path

from google import genai
from langchain.agents import create_agent

from common.logger import get_logger
from constants.prompt_constants import SYSTEM_PROMPT
from constants.supported_models import GEMINI_MODEL_NAME

logger = get_logger(Path(__file__).name)


def _make_call_through_gemini(
    input_file: Path,
    output_file: Path,
    model: str,
) -> None:
    client = genai.Client()
    stamp = datetime.now().strftime("%Y_%m_%d_%H_%M")
    input_stem = input_file.stem

    with open(input_file, "r", encoding="utf-8") as f, open(
        output_file, "w", encoding="utf-8", newline=""
    ) as out:
        writer = csv.writer(out)
        writer.writerow(["id", "prompt", "response"])

        for i, line in enumerate(f, start=1):
            prompt = line.strip()
            if not prompt:
                continue

            response = client.models.generate_content(
                model=model,
                contents=prompt,
            )

            response_text = (response.text or "").strip()

            safe_model = str(model).replace(" ", "_").replace("/", "_").replace("\\", "_")
            row_id = f"{input_stem}_{safe_model}_{stamp}_{i}"

            logger.info(f"Sent prompt #{i}: {prompt}...")
            logger.info(f"Received response: {response_text}...")

            writer.writerow([row_id, prompt, response_text])

    logger.info(f"Saved CSV responses to: {output_file}")




def send_prompts(
    input_file: Path,
    output_file: Path,
    model: str,
) -> None:

    if model == GEMINI_MODEL_NAME:
        _make_call_through_gemini(
            input_file=input_file,
            output_file=output_file,
            model=model,
        )
        return

    agent = create_agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
    )

    stamp = datetime.now().strftime("%Y_%m_%d_%H_%M")
    input_stem = input_file.stem

    with open(input_file, "r", encoding="utf-8") as f, open(
        output_file, "w", encoding="utf-8", newline=""
    ) as out:
        writer = csv.writer(out)
        writer.writerow(["id", "prompt", "response"])

        for i, line in enumerate(f, start=1):
            prompt = line.strip()
            if not prompt:
                continue

            result = agent.invoke({"messages": [{"role": "user", "content": prompt}]})

            response_blocks = result["messages"][-1].content_blocks
            response_text = "".join(
                b.get("text", "") for b in response_blocks if b.get("type") == "text"
            ).strip()

            safe_model = str(model).replace(" ", "_").replace("/", "_").replace("\\", "_")
            row_id = f"{input_stem}_{safe_model}_{stamp}_{i}"

            logger.info(f"Sent prompt #{i}: {prompt}...")
            logger.info(f"Received response: {response_text}...")

            writer.writerow([row_id, prompt, response_text])

    logger.info(f"Saved CSV responses to: {output_file}")
