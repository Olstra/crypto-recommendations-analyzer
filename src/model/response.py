from dataclasses import dataclass, field, fields


@dataclass
class Response:
    id: str = field(metadata={"sql": "TEXT PRIMARY KEY"})
    scenario: str | None = field(metadata={"sql": "TEXT"})
    variables: str | None = field(metadata={"sql": "TEXT"})
    model: str = field(metadata={"sql": "TEXT NOT NULL"})
    model_version: str = field(metadata={"sql": "TEXT NOT NULL"})
    response_timestamp: str = field(metadata={"sql": "TEXT NOT NULL"})
    prompt: str = field(metadata={"sql": "TEXT NOT NULL"})
    response: str = field(metadata={"sql": "TEXT NOT NULL"})


RESPONSE_FIELDS = fields(Response)

RESPONSE_COLUMNS = tuple(response_field.name for response_field in fields(Response))

RESPONSE_COLUMN_DEFINITIONS = tuple(
    (
        response_field.name,
        response_field.metadata["sql"],
    )
    for response_field in RESPONSE_FIELDS
)
