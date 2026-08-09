from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from common.data_paths import OUTPUT_PATH_RESPONSES, PROMPT_FILES_PATH
from constants.supported_models import SUPPORTED_MODELS
from llm_response_generator import send_prompts


def main(model: str, input_file: Path) -> None:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")

    safe_model = model.replace("openai:", "").replace("/", "-").replace(":", "-")
    output_file = OUTPUT_PATH_RESPONSES / f"responses-{safe_model}-{ts}.csv"

    send_prompts(
        input_file=input_file,
        output_file=output_file,
        model=model,
    )


if __name__ == "__main__":
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
    input_files = [
        PROMPT_FILES_PATH / "chosen_tokens-budget_term_risk_environment.txt",
        PROMPT_FILES_PATH / "general-budget_term_risk_environment.txt"
    ]

    for m in SUPPORTED_MODELS:
        for file in input_files:
            main(m, file)
