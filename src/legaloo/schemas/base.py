from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """camelCase on the wire to match the Kotlin data classes; snake_case in Python."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
