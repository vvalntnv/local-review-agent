from pydantic import BaseModel, Field, field_validator


class ShouldAskForHumanApproval(BaseModel):
    should_ask: bool
    confidence: float = Field(description="A number between 1 and 0")

    @field_validator("confidence", mode="before")
    @classmethod
    def validate_confidence(cls, value) -> float:
        if not isinstance(value, float):
            raise ValueError("Value is not of type float")

        assert value <= 1 and value >= 0, "Value must be between 1 and 0"

        return value
