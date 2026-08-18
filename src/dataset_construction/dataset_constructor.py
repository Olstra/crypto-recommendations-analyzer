import csv
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .constants.prompt_constants import SYSTEM_PROMPT
from dotenv import load_dotenv
from google import genai
from langchain.agents import create_agent

from src.common.data_paths import OUTPUT_PATH_PROMPTS, OUTPUT_PATH_RESPONSES
from src.common.logger import get_logger
from src.common.supported_models import GEMINI_MODEL_NAME, SUPPORTED_MODELS

logger = get_logger(Path(__file__).name)

_SEPARATOR = "|"


def _generate_row_id(input_stem: str, model: str, timestamp: str, index: int) -> str:
    return f"{input_stem}{_SEPARATOR}{model}{_SEPARATOR}{timestamp}{_SEPARATOR}{index}"


def _process_request_with_gemini(
    input_file: Path,
    output_file: Path,
    model: str,
    timestamp: str,
    input_stem: str,
) -> None:
    client = genai.Client()

    with (
        open(input_file, "r", encoding="utf-8") as f,
        open(output_file, "w", encoding="utf-8", newline="") as out,
    ):
        writer = csv.writer(out)
        writer.writerow(["id", "prompt", "response"])

        for i, line in enumerate(f, start=1):
            prompt = line.strip()
            if not prompt:
                continue

            logger.info(f"Sent prompt: {prompt}...")
            response = client.models.generate_content(model=model, contents=prompt)
            response_text = (response.text or "").strip()
            logger.info(f"Received response: {response_text}...")

            row_id = _generate_row_id(input_stem, model, timestamp, i)
            writer.writerow([row_id, prompt, response_text])

            # todo: remove after test-phase
            if i >= 11:
                break

    logger.info(f"Saved CSV responses to: {output_file}")


def _process_request(
    input_file: Path,
    output_file: Path,
    model: str,
    timestamp: str,
    input_stem: str,
) -> None:
    agent = create_agent(model=model, system_prompt=SYSTEM_PROMPT)

    with (
        open(input_file, "r", encoding="utf-8") as f,
        open(output_file, "w", encoding="utf-8", newline="") as out,
    ):
        writer = csv.writer(out)
        writer.writerow(["id", "prompt", "response"])

        for i, line in enumerate(f, start=1):
            prompt = line.strip()
            if not prompt:
                continue

            logger.info(f"Sent prompt: {prompt}...")
            result = agent.invoke({"messages": [{"role": "user", "content": prompt}]})
            response_blocks = result["messages"][-1].content_blocks
            response_text = "".join(
                b.get("text", "") for b in response_blocks if b.get("type") == "text"
            ).strip()
            logger.info(f"Received response: {response_text}...")

            row_id = _generate_row_id(input_stem, model, timestamp, i)
            writer.writerow([row_id, prompt, response_text])

            # todo: remove after test-phase
            if i >= 1:
                break

    logger.info(f"Saved CSV responses to: {output_file}")


if __name__ == "__main__":
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)

    OUTPUT_PATH_RESPONSES.mkdir(parents=True, exist_ok=True)

    input_files = [f for f in (OUTPUT_PATH_PROMPTS / "delete_me").iterdir()]

    for _model in SUPPORTED_MODELS:
        for file in input_files:
            _input_stem = file.stem
            _timestamp = datetime.now(tz=ZoneInfo("Europe/Zurich")).strftime(
                "%Y%m%d_%H%M"
            )
            _output_file = (
                OUTPUT_PATH_RESPONSES
                / f"responses{_SEPARATOR}{_model}{_SEPARATOR}{_input_stem}{_SEPARATOR}{_timestamp}.csv"
            )

            if _model == GEMINI_MODEL_NAME:
                _process_request_with_gemini(
                    file, _output_file, _model, _timestamp, _input_stem
                )
            else:
                _process_request(file, _output_file, _model, _timestamp, _input_stem)
