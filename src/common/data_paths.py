from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_PATH = PROJECT_ROOT / ".env"

INPUT_FILE = PROJECT_ROOT / "data" / "prompts" / "dummy_prompts.txt"
OUTPUT_PATH_RESPONSES = PROJECT_ROOT / "data" / "responses"
