from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv

from common.data_paths import OUTPUT_PATH_RESPONSES, INPUT_FILE
from constants.model_versions import supported_models
from llm_response_generator import send_prompts


def main(model: str) -> None:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")

    safe_model = model.replace("openai:", "").replace("/", "-").replace(":", "-")
    output_file = OUTPUT_PATH_RESPONSES / f"responses-{safe_model}-{ts}.txt"

    send_prompts(
        input_file=INPUT_FILE,
        output_file=output_file,
        model=model,
    )


if __name__ == "__main__":
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)

    for model in supported_models:
        main(model)
