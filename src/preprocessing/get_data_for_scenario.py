import sqlite3
from pathlib import Path
from typing import Literal

import pandas as pd
from pandas import DataFrame

PossibleScenarios = Literal["tokens", "exchanges"]


def _get_data_for_scenario(
    db_path: Path,
    scenario: PossibleScenarios,
) -> DataFrame:
    table_name = "responses"

    with sqlite3.connect(db_path) as conn:
        data = pd.read_sql_query(
            f"SELECT * FROM {table_name}",
            conn,
        )

    return data.loc[data["scenario"].eq(scenario)].copy()
