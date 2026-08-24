from __future__ import annotations

import sqlite3
import threading
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
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
_TIME_ZONE = ZoneInfo("Europe/Zurich")
_MAX_WORKERS = 8
_TEST_RUN = False

_thread_state = threading.local()
_runtime_init_lock = threading.Lock()


# TODO: move into models/prompt_job.py
@dataclass(frozen=True, slots=True)
class PromptJob:
    input_file: Path
    scenario: str
    model_version: str
    prompt: str
    index: int
    response_timestamp: str


def _generate_row_id(
    scenario: str,
    model: str,
    created_at: str,
    index: int,
) -> str:
    return f"{scenario}{_SEPARATOR}{model}{_SEPARATOR}{created_at}{_SEPARATOR}{index}"


def _configure_database(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA cache_size=-64000")


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


def _get_thread_runtime(model_version: str):
    runtimes = getattr(_thread_state, "runtimes", None)

    if runtimes is None:
        runtimes = {}
        _thread_state.runtimes = runtimes

    if model_version in runtimes:
        return runtimes[model_version]

    with _runtime_init_lock:
        if model_version in runtimes:
            return runtimes[model_version]

        if model_version == GEMINI_MODEL_NAME:
            runtime = genai.Client()
        else:
            runtime = create_agent(
                model=model_version,
                system_prompt=SYSTEM_PROMPT,
            )

        runtimes[model_version] = runtime
        return runtime


def _extract_agent_response(result: dict) -> str:
    messages = result.get("messages", [])

    if not messages:
        return ""

    final_message = messages[-1]
    response_blocks = getattr(final_message, "content_blocks", None)

    if response_blocks is not None:
        return "".join(
            block.get("text", "")
            for block in response_blocks
            if block.get("type") == "text"
        ).strip()

    content = getattr(final_message, "content", "")

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        return "".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        ).strip()

    return str(content).strip()


def _invoke_model(
    model_version: str,
    prompt: str,
) -> str:
    runtime = _get_thread_runtime(model_version)

    if model_version == GEMINI_MODEL_NAME:
        response = runtime.models.generate_content(
            model=model_version,
            contents=prompt,
        )
        return (response.text or "").strip()

    result = runtime.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ]
        }
    )

    return _extract_agent_response(result)


def _process_prompt(job: PromptJob) -> Response:
    logger.info(
        "Sending scenario=%s model=%s index=%d",
        job.scenario,
        job.model_version,
        job.index,
    )

    response_text = _invoke_model(
        model_version=job.model_version,
        prompt=job.prompt,
    )

    logger.info(
        "Received scenario=%s model=%s index=%d response_length=%d",
        job.scenario,
        job.model_version,
        job.index,
        len(response_text),
    )

    return _build_response_row(
        scenario=job.scenario,
        model_version=job.model_version,
        response_timestamp=job.response_timestamp,
        prompt=job.prompt,
        response_text=response_text,
        index=job.index,
    )


def _load_jobs(
    input_files: list[Path],
) -> list[PromptJob]:
    jobs: list[PromptJob] = []

    for model_version in SUPPORTED_MODELS:
        model_job_count = 0

        for input_file in input_files:
            scenario = input_file.stem
            response_timestamp = datetime.now(
                tz=_TIME_ZONE,
            ).strftime("%Y%m%d_%H%M")

            with input_file.open("r", encoding="utf-8") as file:
                for index, line in enumerate(file, start=1):
                    prompt = line.strip()

                    if not prompt:
                        continue

                    jobs.append(
                        PromptJob(
                            input_file=input_file,
                            scenario=scenario,
                            model_version=model_version,
                            prompt=prompt,
                            index=index,
                            response_timestamp=response_timestamp,
                        )
                    )

                    model_job_count += 1

                    # TEST RUN: remove this break to process every prompt.
                    if _TEST_RUN:
                        break

            if model_job_count:
                logger.info(
                    "Queued scenario=%s model=%s",
                    scenario,
                    model_version,
                )

            # TEST RUN: remove this break to process every input file.
            if _TEST_RUN and model_job_count:
                break

    return jobs


def _run_jobs(
    conn: sqlite3.Connection,
    jobs: list[PromptJob],
) -> None:
    if not jobs:
        logger.info("No prompts found")
        return

    completed = 0
    total_jobs = len(jobs)

    logger.info(
        "Processing %d prompts with %d worker threads",
        total_jobs,
        _MAX_WORKERS,
    )

    executor = ThreadPoolExecutor(
        max_workers=_MAX_WORKERS,
        thread_name_prefix="model-worker",
    )

    futures: list[Future[Response]] = [
        executor.submit(_process_prompt, job) for job in jobs
    ]

    try:
        for future in as_completed(futures):
            response_row = future.result()

            _insert_response(conn, response_row)
            conn.commit()

            completed += 1

            logger.info(
                "Saved response %d/%d to database",
                completed,
                total_jobs,
            )

    except BaseException:
        for future in futures:
            future.cancel()

        conn.rollback()
        executor.shutdown(
            wait=True,
            cancel_futures=True,
        )
        raise

    else:
        executor.shutdown(wait=True)


def main(
    input_files: list[Path],
    output_file: Path,
) -> None:
    jobs = _load_jobs(input_files)

    with sqlite3.connect(output_file, timeout=300) as conn:
        _configure_database(conn)
        _ensure_db_schema(conn)
        _run_jobs(conn, jobs)

    logger.info("Finished processing %d prompts", len(jobs))


if __name__ == "__main__":
    OUTPUT_PATH_RESPONSES.mkdir(parents=True, exist_ok=True)

    db_path = OUTPUT_PATH_RESPONSES / "responses.db"

    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)

    input_files = list(OUTPUT_PATH_PROMPTS.rglob("*.txt"))

    main(input_files, db_path)
