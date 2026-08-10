from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_PATH = PROJECT_ROOT / ".env"

OUTPUT_PATH_RESPONSES = PROJECT_ROOT / "data" / "responses"
OUTPUT_PATH_PROMPTS = PROJECT_ROOT / "data" / "prompts"
PROMPT_FILES_PATH = PROJECT_ROOT / "data" / "prompts"
OUTPUT_PATH_ANALYSIS_RESULTS = PROJECT_ROOT / "data" / "analysis_results"
OUTPUT_PATH_PREPROCESSED_DATA = PROJECT_ROOT / "data" / "preprocessed_data"
