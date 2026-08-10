import csv
from pathlib import Path

from analysis.constants.constants import UNPROCESSED_CSV_COL_NAMES
from common.data_paths import OUTPUT_PATH_RESPONSES, PROJECT_ROOT
from common.supported_models import SUPPORTED_MODELS


# TODO: this is a temporary file. Refactor its contents into "dataset construction"

def get_model_name(the_id: str) -> str:
    for model_name in SUPPORTED_MODELS:
        if model_name in the_id:
            return model_name
    return "UNKNOWN"


def parse_from_id(id: str, model_name: str):
    idx = id.find(str(model_name))
    before = id if idx == -1 else id[:idx]

    parts = before.split("-") if before else []
    scenario = parts[0] if len(parts) >= 1 else ""
    variables = parts[1] if len(parts) >= 2 else ""

    return scenario, variables


def process_dir(input_file: Path, output_dir: Path) -> Path:
    fieldnames_out = UNPROCESSED_CSV_COL_NAMES
    rows_out = []

    with open(input_file, "r", encoding="utf-8", newline="") as f_in:
        reader = csv.DictReader(f_in)

        for row in reader:
            id_ = row.get("id", "")
            prompt = row.get("prompt", "")
            response = row.get("response", "")
            model_name = get_model_name(id_)
            scenario, variables = parse_from_id(id_, model_name)

            rows_out.append({
                "id": id_,
                "prompt": prompt,
                "response": response,
                "model_name": model_name,
                "scenario": scenario,
                "variables": variables,
            })

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{input_file.stem}.csv"

    with open(output_path, "w", encoding="utf-8", newline="") as out_f:
        writer = csv.DictWriter(out_f, fieldnames=fieldnames_out)
        writer.writeheader()
        writer.writerows(rows_out)

    return output_path


if __name__ == "__main__":
    files = [f for f in OUTPUT_PATH_RESPONSES.iterdir() if f.suffix == ".csv"]

    for f in files:
        process_dir(f, PROJECT_ROOT / "data" / "preprocessed_csv")
