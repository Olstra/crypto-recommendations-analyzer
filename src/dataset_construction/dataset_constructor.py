import sqlite3
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from google import genai
from langchain.agents import create_agent

from src.common.logger import get_logger
from src.constants.data_paths import OUTPUT_PATH_PROMPTS, OUTPUT_PATH_RESPONSES
from src.constants.supported_models import GEMINI_MODEL_NAME, SUPPORTED_MODELS
from src.dataset_construction.constants.prompt_constants import SYSTEM_PROMPT
from src.model.response import RESPONSE_COLUMN_DEFINITIONS, RESPONSE_COLUMNS, Response

logger = get_logger(Path(__file__).name)

_SEPARATOR = "|"


def _generate_row_id(
    scenario: str,
    model: str,
    created_at: str,
    index: int,
) -> str:
    return f"{scenario}{_SEPARATOR}{model}{_SEPARATOR}{created_at}{_SEPARATOR}{index}"


def _ensure_db_schema(conn: sqlite3.Connection) -> None:
    column_definitions = ",\n".join(
        f"            {column_name} {sql_definition}"
        for column_name, sql_definition in RESPONSE_COLUMN_DEFINITIONS
    )

    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS responses (
{column_definitions}
        )
        """
    )
    conn.commit()


def _insert_response(
    conn: sqlite3.Connection,
    response_row: Response,
) -> None:
    columns = ", ".join(RESPONSE_COLUMNS)
    placeholders = ", ".join("?" for _ in RESPONSE_COLUMNS)

    values = tuple(getattr(response_row, column) for column in RESPONSE_COLUMNS)

    conn.execute(
        f"""
        INSERT OR REPLACE INTO responses
        ({columns})
        VALUES ({placeholders})
        """,
        values,
    )


def _parse_scenario(
    scenario: str | None,
) -> tuple[str | None, str | None]:
    if not scenario:
        return None, None

    parts = scenario.split("-")

    parsed_scenario = parts[0] or None
    variables = parts[2] if len(parts) > 2 and parts[2] else None

    if parsed_scenario is None:
        logger.warning("Problem when parsing scenario=%s", scenario)

    return parsed_scenario, variables


def _build_response_row(
    *,
    scenario: str,
    model_version: str,
    response_timestamp: str,
    prompt: str,
    response_text: str,
    index: int,
) -> Response:
    parsed_scenario, variables = _parse_scenario(scenario)
    model = model_version.split("-")[0] if model_version else ""

    return Response(
        id=_generate_row_id(
            scenario,
            model_version,
            response_timestamp,
            index,
        ),
        scenario=parsed_scenario,
        variables=variables,
        model=model,
        model_version=model_version,
        response_timestamp=response_timestamp,
        prompt=prompt,
        response=response_text,
    )


def _process_request(
    conn: sqlite3.Connection,
    input_file: Path,
    model_version: str,
    response_timestamp: str,
    scenario: str,
) -> None:
    using_gemini = model_version == GEMINI_MODEL_NAME

    if using_gemini:
        client = genai.Client()
        agent = None
    else:
        client = None
        agent = create_agent(
            model=model_version,
            system_prompt=SYSTEM_PROMPT,
        )

    with input_file.open("r", encoding="utf-8") as file:
        for index, line in enumerate(file, start=1):
            prompt = line.strip()

            if not prompt:
                continue

            logger.info(f"Sent prompt: {prompt}...")

            if using_gemini:
                response = client.models.generate_content(
                    model=model_version,
                    contents=prompt,
                )
                response_text = (response.text or "").strip()
            else:
                result = agent.invoke(
                    {
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt,
                            }
                        ]
                    }
                )

                response_blocks = result["messages"][-1].content_blocks
                response_text = "".join(
                    block.get("text", "")
                    for block in response_blocks
                    if block.get("type") == "text"
                ).strip()

            logger.info("Received response: %s...", response_text)

            response_row = _build_response_row(
                scenario=scenario,
                model_version=model_version,
                response_timestamp=response_timestamp,
                prompt=prompt,
                response_text=response_text,
                index=index,
            )

            _insert_response(conn, response_row)


if __name__ == "__main__":
    OUTPUT_PATH_RESPONSES.mkdir(parents=True, exist_ok=True)
    db_path = OUTPUT_PATH_RESPONSES / "responses.db"

    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)

    input_files = list(OUTPUT_PATH_PROMPTS.rglob("*.txt"))

    with sqlite3.connect(db_path) as _conn:
        _ensure_db_schema(_conn)

        for _model_version in SUPPORTED_MODELS:
            for _input_file in input_files:
                _scenario = _input_file.stem
                _response_timestamp = datetime.now(
                    tz=ZoneInfo("Europe/Zurich")
                ).strftime("%Y%m%d_%H%M")

                logger.info(
                    f"Processing scenario={_scenario} with model_version={_model_version}"
                )

                try:
                    _conn.execute("BEGIN")

                    _process_request(
                        _conn,
                        _input_file,
                        _model_version,
                        _response_timestamp,
                        _scenario,
                    )

                    _conn.commit()

                except Exception:
                    _conn.rollback()
                    raise
