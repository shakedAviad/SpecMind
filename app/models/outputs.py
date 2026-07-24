from pydantic import BaseModel, Field


class ReasoningResult(BaseModel):
    relevant_points: list[str]
    conclusion: str
    source_chunk_indexes: list[int]


class RerankResult(BaseModel):
    relevant_chunk_indexes: list[int]


class ConversationUnderstandingResult(BaseModel):
    is_follow_up: bool = Field(
        description=(
            "True only when the question cannot be fully understood without "
            "information from an earlier conversation."
        )
    )

    standalone_question: str | None = Field(
        default=None,
        description=(
            "The question as a self-contained question when it is already "
            "standalone. Otherwise, null. Do not invent missing context."
        ),
    )

    missing_context: str | None = Field(
        default=None,
        description=(
            "A concise description of the prior information required to understand "
            "the question. Null when the question is standalone."
        ),
    )
