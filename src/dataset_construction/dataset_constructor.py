import sqlite3
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from google import genai
from langchain.agents import create_agent

from src.common.data_paths import OUTPUT_PATH_PROMPTS, OUTPUT_PATH_RESPONSES
from src.common.logger import get_logger
from src.common.supported_models import GEMINI_MODEL_NAME, SUPPORTED_MODELS
from src.dataset_construction.constants.prompt_constants import SYSTEM_PROMPT

logger = get_logger(Path(__file__).name)

_SEPARATOR = "|"


def _generate_row_id(scenario: str, model: str, created_at: str, index: int) -> str:
    return f"{scenario}{_SEPARATOR}{model}{_SEPARATOR}{created_at}{_SEPARATOR}{index}"


def _ensure_db_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS responses (
            id TEXT PRIMARY KEY,
            scenario TEXT NOT NULL,
            model TEXT NOT NULL,
            created_at TEXT NOT NULL,
            prompt TEXT NOT NULL,
            response TEXT NOT NULL
        )
        """
    )
    conn.commit()


def _insert_response(
    conn: sqlite3.Connection,
    *,
    row_id: str,
    scenario: str,
    model: str,
    created_at: str,
    prompt: str,
    response_text: str,
) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO responses
        (id, scenario, model, created_at, prompt, response)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (row_id, scenario, model, created_at, prompt, response_text),
    )


def _process_request_with_gemini(
    conn: sqlite3.Connection,
    input_file: Path,
    model: str,
    created_at: str,
    scenario: str,
) -> None:
    client = genai.Client()

    with open(input_file, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            prompt = line.strip()
            if not prompt:
                continue

            logger.info(f"Sent prompt: {prompt}...")
            response = client.models.generate_content(model=model, contents=prompt)
            response_text = (response.text or "").strip()
            logger.info(f"Received response: {response_text}...")

            row_id = _generate_row_id(scenario, model, created_at, i)

            _insert_response(
                conn,
                row_id=row_id,
                scenario=scenario,
                model=model,
                created_at=created_at,
                prompt=prompt,
                response_text=response_text,
            )

            # todo: remove after test-phase
            if i >= 1:
                break


def _process_request(
    conn: sqlite3.Connection,
    input_file: Path,
    model: str,
    created_at: str,
    scenario: str,
) -> None:
    agent = create_agent(model=model, system_prompt=SYSTEM_PROMPT)

    with open(input_file, "r", encoding="utf-8") as f:
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

            row_id = _generate_row_id(scenario, model, created_at, i)

            _insert_response(
                conn,
                row_id=row_id,
                scenario=scenario,
                model=model,
                created_at=created_at,
                prompt=prompt,
                response_text=response_text,
            )

            # todo: remove after test-phase
            if i >= 1:
                break


if __name__ == "__main__":
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    OUTPUT_PATH_RESPONSES.mkdir(parents=True, exist_ok=True)
    db_path = OUTPUT_PATH_RESPONSES / "responses.db"

    load_dotenv(dotenv_path=env_path)

    input_files = [f for f in (OUTPUT_PATH_PROMPTS / "delete_me").iterdir()]

    with sqlite3.connect(db_path) as conn:
        _ensure_db_schema(conn)

        for _model in SUPPORTED_MODELS:
            for file in input_files:
                _scenario = file.stem
                _timestamp = datetime.now(tz=ZoneInfo("Europe/Zurich")).strftime(
                    "%Y%m%d_%H%M"
                )

                logger.info(
                    f"Processing scenario={_scenario} model={_model} created_at={_timestamp}"
                )

                try:
                    conn.execute("BEGIN")
                    if _model == GEMINI_MODEL_NAME:
                        _process_request_with_gemini(
                            conn, file, _model, _timestamp, _scenario
                        )
                    else:
                        _process_request(conn, file, _model, _timestamp, _scenario)
                    conn.commit()
                except Exception:
                    conn.rollback()
                    raise
