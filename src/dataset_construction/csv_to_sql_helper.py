import csv
import sqlite3
from pathlib import Path

from common.data_paths import OUTPUT_PATH_RESPONSES


def parse_id(identifier: str) -> dict:
    id_parts = identifier.strip().split("|")

    first_part = id_parts[0]
    first_part_parts = first_part.split("-")

    scenario = first_part_parts[0] if first_part_parts else None

    variables = first_part_parts[2] if first_part_parts[2] else None

    model_version = id_parts[1] if len(id_parts) > 1 else None

    model = model_version.split("-")[0] if model_version else None

    response_timestamp = id_parts[2] if len(id_parts) > 2 else None

    return {
        "model": model,
        "model_version": model_version,
        "response_timestamp": response_timestamp,
        "variables": variables,
        "scenario": scenario,
    }


def create_database(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS responses (
            id TEXT NOT NULL,
            prompt TEXT NOT NULL,
            response TEXT NOT NULL,
            model TEXT,
            model_version TEXT,
            response_timestamp TEXT,
            variables TEXT,
            scenario TEXT
        )
        """
    )

    connection.commit()


def import_csv_file(
    connection: sqlite3.Connection,
    csv_path: Path,
) -> None:

    with csv_path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:
        reader = csv.DictReader(csv_file)

        required_columns = {"id", "prompt", "response"}

        if not reader.fieldnames:
            print(f"Skipping empty file: {csv_path}")
            return 0, 0

        missing_columns = required_columns - set(reader.fieldnames)

        if missing_columns:
            print(
                f"Skipping {csv_path}; missing columns: "
                f"{', '.join(sorted(missing_columns))}"
            )
            return 0, 0

        for line_number, row in enumerate(reader, start=2):
            identifier = (row.get("id") or "").strip()
            prompt = row.get("prompt")
            response = row.get("response")

            if not identifier or prompt is None or response is None:
                print(
                    f"Skipping {csv_path}, line {line_number}: "
                    "missing id, prompt, or response"
                )
                continue

            parsed = parse_id(identifier)

            connection.execute(
                """
                INSERT OR IGNORE INTO responses (
                    id,
                    prompt,
                    response,
                    model,
                    model_version,
                    response_timestamp,
                    variables,
                    scenario
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    identifier,
                    prompt,
                    response,
                    parsed["model"],
                    parsed["model_version"],
                    parsed["response_timestamp"],
                    parsed["variables"],
                    parsed["scenario"],
                ),
            )

        return None


def main(input_path: Path, output_path: Path) -> None:
    if not input_path.is_dir():
        raise FileNotFoundError(f"Input directory does not exist: {input_path}")

    csv_files = list(input_path.rglob("*.csv"))

    if not csv_files:
        print(f"No CSV files found under {input_path}")
        return

    with sqlite3.connect(output_path) as connection:
        create_database(connection)

        for csv_path in csv_files:
            import_csv_file(
                connection,
                csv_path,
            )

        connection.commit()

    print(f"Output database:     {output_path}")


if __name__ == "__main__":
    _input_path = OUTPUT_PATH_RESPONSES
    _output_path = OUTPUT_PATH_RESPONSES / "responses.db"
    main(_input_path, _output_path)
